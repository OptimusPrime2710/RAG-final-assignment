from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.domain import Goal, Plan, PlanInput, Status, Task
from rag_framework.orchestrator import Orchestrator
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


def test_default_input_is_injected_into_task(tmp_path: Path) -> None:
    tools = ToolRegistry()
    received = {}
    tools.register(ToolDescriptor("capture", "capture", "Capture", "python"), lambda inputs: received.update(inputs) or {"ok": True})
    plan = Plan(
        plan_id="default-input",
        inputs=[PlanInput(input_id="top_k", name="top_k", type="integer", default_value=5)],
        goals=[Goal(goal_id="g", goal="retrieve", tasks=[Task(task_id="t", task="retrieve", tool_required=["capture"])])],
    )
    result = Orchestrator(PlanStore(tmp_path), TaskExecutorAgent(tools), ValidatorAgent()).execute(plan)
    assert result.status == Status.COMPLETED
    assert received["top_k"] == 5


def test_missing_required_input_blocks_before_execution(tmp_path: Path) -> None:
    tools = ToolRegistry()
    calls = {"count": 0}
    tools.register(ToolDescriptor("capture", "capture", "Capture", "python"), lambda _: calls.update(count=calls["count"] + 1) or {})
    plan = Plan(
        plan_id="missing-input",
        inputs=[PlanInput(input_id="query", name="query", type="string", required=True)],
        goals=[Goal(goal_id="g", goal="retrieve", tasks=[Task(task_id="t", task="retrieve", tool_required=["capture"])])],
    )
    result = Orchestrator(PlanStore(tmp_path), TaskExecutorAgent(tools), ValidatorAgent()).execute(plan)
    assert result.status == Status.BLOCKED
    assert result.goals[0].status == Status.BLOCKED
    assert calls["count"] == 0
