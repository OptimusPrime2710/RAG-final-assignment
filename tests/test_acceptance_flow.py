from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.agents.planner import PlannerAgent
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.orchestrator import Orchestrator
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.tool_registry import ToolRegistry
from rag_framework.tools.chroma import ChromaStore
from rag_framework.tools.rag_registry import register_rag_tools


def test_markdown_to_population_and_retrieval(tmp_path: Path) -> None:
    source = tmp_path / "business_use_case.md"
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "cancellation.md").write_text("Cancellation policy allows thirty days.", encoding="utf-8")
    source.write_text("# Semantic Search\nLoad documents and retrieve cancellation policy results.", encoding="utf-8")

    plan = PlannerAgent().create_plan(source, "acceptance")
    plan.goals[0].tasks[0].inputs["directory"] = str(documents)
    store = PlanStore(tmp_path / "plans")
    vector_store = ChromaStore(tmp_path / "chroma")
    tools = ToolRegistry()
    register_rag_tools(tools, vector_store)
    result = Orchestrator(store, TaskExecutorAgent(tools), ValidatorAgent()).execute(plan)

    assert result.status == "completed"
    assert {goal.status for goal in result.goals} == {"completed"}
    assert vector_store.search_similar("cancellation policy", 1)[0]["metadata"]["path"].endswith("cancellation.md")
    assert store.load("acceptance").status == "completed"
