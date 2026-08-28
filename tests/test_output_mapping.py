from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.domain import Goal, Plan, Task
from rag_framework.orchestrator import Orchestrator
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


def test_dependency_output_mapping_feeds_next_task(tmp_path: Path) -> None:
    tools = ToolRegistry()
    tools.register(ToolDescriptor("source", "source", "Source", "python"), lambda _: {"query": "policy"})
    tools.register(ToolDescriptor("sink", "sink", "Sink", "python"), lambda inputs: {"received": inputs["query"]})
    plan = Plan(plan_id="mapping", goals=[Goal(goal_id="g", goal="flow", tasks=[
        Task(task_id="source", task="source", tool_required=["source"], output_mapping={"query": "query"}),
        Task(task_id="sink", task="sink", dependencies=["source"], tool_required=["sink"]),
    ])])
    result = Orchestrator(PlanStore(tmp_path), TaskExecutorAgent(tools), ValidatorAgent()).execute(plan)
    assert result.goals[0].tasks[1].execution["result"] == {"received": "policy"}
