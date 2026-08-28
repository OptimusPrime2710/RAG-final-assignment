"""Command-line workflows for planning, execution, and retrieval."""

import argparse
import json
from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.agents.planner import PlannerAgent
from rag_framework.goal_resolver import GoalResolver
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.config import load_settings
from rag_framework.orchestrator import Orchestrator
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.tool_registry import ToolRegistry
from rag_framework.registry.model_registry import ModelRegistry
from rag_framework.providers.openrouter import OpenRouterGateway
from rag_framework.tools.chroma import ChromaStore
from rag_framework.tools.document import index_directory
from rag_framework.tools.rag_registry import register_rag_tools
from rag_framework.tools.jira_mcp import JiraMCPAdapter
from rag_framework.query_service import QueryService


def _apply_user_inputs(plan, assignments: list[str]) -> None:
    """Apply CLI name=value assignments using each plan input's declared type."""
    declared = {value.name: value for value in plan.inputs}
    for assignment in assignments:
        if "=" not in assignment:
            raise ValueError(f"input must use name=value syntax: {assignment}")
        name, raw_value = assignment.split("=", 1)
        if name not in declared:
            raise ValueError(f"unknown plan input: {name}")
        value = declared[name]
        if value.type in {"integer", "int"}:
            parsed: object = int(raw_value)
        elif value.type in {"number", "float"}:
            parsed = float(raw_value)
        elif value.type in {"boolean", "bool"}:
            if raw_value.lower() not in {"true", "false"}:
                raise ValueError(f"boolean input must be true or false: {name}")
            parsed = raw_value.lower() == "true"
        else:
            parsed = raw_value
        value.user_value = parsed
        value.effective_value = parsed
        value.source = "user"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rag-framework")
    subparsers = parser.add_subparsers(dest="command")

    plan = subparsers.add_parser("plan", help="create and persist a plan")
    plan.add_argument("source", type=Path)
    plan.add_argument("--plan-id", required=True)
    plan.add_argument("--plans-dir", type=Path)
    plan.add_argument("--live-model", action="store_true", help="use configured OpenRouter planning")

    for name in ("execute", "resume"):
        command = subparsers.add_parser(name, help="execute a persisted plan")
        command.add_argument("plan_id")
        command.add_argument("--plans-dir", type=Path)
        command.add_argument("--live-model", action="store_true", help="use configured OpenRouter validation")
        command.add_argument("--live-jira", action="store_true", help="discover and use configured JIRA MCP tools")
        command.add_argument("--input", action="append", default=[], help="override a plan input using name=value")

    goal = subparsers.add_parser("goal", help="retrigger a reusable goal")
    goal.add_argument("plan_id")
    goal.add_argument("request")
    goal.add_argument("--plans-dir", type=Path)
    goal.add_argument("--live-model", action="store_true", help="use configured OpenRouter validation")
    goal.add_argument("--live-jira", action="store_true", help="discover and use configured JIRA MCP tools")
    goal.add_argument("--input", action="append", default=[], help="override a plan input using name=value")

    index = subparsers.add_parser("index", help="incrementally index documents")
    index.add_argument("directory", type=Path)
    index.add_argument("--chroma-dir", type=Path)

    search = subparsers.add_parser("search", help="search indexed documents")
    search.add_argument("query")
    search.add_argument("--top-k", type=int, default=5)
    search.add_argument("--chroma-dir", type=Path)

    query = subparsers.add_parser("query", help="run a simple or complex evidence-based query")
    query.add_argument("request")
    query.add_argument("--top-k", type=int, default=5)
    query.add_argument("--chroma-dir", type=Path)
    query.add_argument("--live-model", action="store_true", help="use configured OpenRouter for complex-query synthesis")

    config = subparsers.add_parser("config-check", help="validate configured runtime integrations")
    config.add_argument("--openrouter", action="store_true", help="require OpenRouter settings")
    config.add_argument("--jira", action="store_true", help="require JIRA MCP settings")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command is None:
        build_parser().print_help()
    elif args.command == "plan":
        settings = load_settings()
        plans_dir = args.plans_dir or settings.plans_directory
        planner = PlannerAgent()
        if args.live_model:
            settings.validate_for(openrouter=True)
            gateway = OpenRouterGateway(settings)
            planner = PlannerAgent(ModelRegistry(settings), gateway.complete, settings.planner_model_size)
        plan = planner.create_plan(args.source, args.plan_id)
        destination = PlanStore(plans_dir).save(plan)
        print(json.dumps({"plan_id": plan.plan_id, "path": str(destination)}, indent=2))
    elif args.command in {"execute", "resume"}:
        settings = load_settings()
        store = PlanStore(args.plans_dir or settings.plans_directory)
        tools = ToolRegistry()
        register_rag_tools(tools, ChromaStore(settings.chroma_persist_directory))
        if args.live_jira:
            settings.validate_for(jira=True)
            JiraMCPAdapter.from_url(settings.jira_mcp_url, api_token=settings.jira_api_token, email=settings.jira_email).register_discovered_tools(tools)
        validator = ValidatorAgent()
        if args.live_model:
            settings.validate_for(openrouter=True)
            gateway = OpenRouterGateway(settings)
            validator = ValidatorAgent(ModelRegistry(settings), gateway.complete, settings.validator_model_size)
        plan = store.load(args.plan_id)
        _apply_user_inputs(plan, args.input)
        plan = Orchestrator(store, TaskExecutorAgent(tools), validator).execute(plan)
        print(json.dumps({"plan_id": plan.plan_id, "status": plan.status}, indent=2))
    elif args.command == "goal":
        settings = load_settings()
        store = PlanStore(args.plans_dir or settings.plans_directory)
        tools = ToolRegistry()
        register_rag_tools(tools, ChromaStore(settings.chroma_persist_directory))
        if args.live_jira:
            settings.validate_for(jira=True)
            JiraMCPAdapter.from_url(settings.jira_mcp_url, api_token=settings.jira_api_token, email=settings.jira_email).register_discovered_tools(tools)
        validator = ValidatorAgent()
        if args.live_model:
            settings.validate_for(openrouter=True)
            gateway = OpenRouterGateway(settings)
            validator = ValidatorAgent(ModelRegistry(settings), gateway.complete, settings.validator_model_size)
        plan = store.load(args.plan_id)
        _apply_user_inputs(plan, args.input)
        plan = Orchestrator(store, TaskExecutorAgent(tools), validator).retrigger(
            plan, args.request, GoalResolver()
        )
        print(json.dumps({"plan_id": plan.plan_id, "status": plan.status}, indent=2))
    elif args.command == "index":
        settings = load_settings()
        result = index_directory(args.directory, ChromaStore(args.chroma_dir or settings.chroma_persist_directory))
        print(json.dumps(result, indent=2))
    elif args.command == "search":
        settings = load_settings()
        result = ChromaStore(args.chroma_dir or settings.chroma_persist_directory).search_similar(args.query, args.top_k)
        print(json.dumps(result, indent=2))
    elif args.command == "query":
        settings = load_settings()
        final_model_call = None
        if args.live_model:
            settings.validate_for(openrouter=True)
            gateway = OpenRouterGateway(settings)
            model = ModelRegistry(settings).resolve(settings.executor_model_size)
            final_model_call = lambda evidence: gateway.complete(model, [
                {"role": "system", "content": "Return a concise JSON answer using only the supplied evidence. If evidence is insufficient, return No response found."},
                {"role": "user", "content": json.dumps(evidence)},
            ])
        result = QueryService(ChromaStore(args.chroma_dir or settings.chroma_persist_directory), final_model_call).execute(args.request, args.top_k)
        print(json.dumps(result, indent=2))
    elif args.command == "config-check":
        settings = load_settings()
        settings.validate_for(openrouter=args.openrouter, jira=args.jira)
        print(json.dumps({
            "valid": True,
            "openrouter": args.openrouter,
            "jira": args.jira,
            "plans_directory": str(settings.plans_directory),
            "chroma_persist_directory": str(settings.chroma_persist_directory),
        }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
