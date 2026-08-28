from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.domain import Goal, Plan, Status, Task
from rag_framework.orchestrator import Orchestrator
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


def failing_registry() -> ToolRegistry:
    registry = ToolRegistry()
    registry.register(ToolDescriptor("fail", "fail", "Fail", "python"), lambda _: (_ for _ in ()).throw(RuntimeError("failure")))
    return registry


def test_critical_failure_pauses_plan(tmp_path: Path) -> None:
    plan = Plan(plan_id="critical", goals=[Goal(goal_id="g", goal="critical", critical=True, tasks=[Task(task_id="t", task="fail", critical=True, tool_required=["fail"])])])
    result = Orchestrator(PlanStore(tmp_path), TaskExecutorAgent(failing_registry()), ValidatorAgent()).execute(plan)
    assert result.status == Status.PAUSED
    assert result.goals[0].status == Status.PAUSED
    assert result.goals[0].tasks[0].status == Status.FAILED


def test_noncritical_failure_allows_independent_task(tmp_path: Path) -> None:
    calls = {"success": 0}
    registry = failing_registry()
    registry.register(ToolDescriptor("success", "success", "Success", "python"), lambda _: calls.update(success=calls["success"] + 1) or {"ok": True})
    plan = Plan(plan_id="noncritical", goals=[Goal(goal_id="g", goal="optional work", critical=False, tasks=[
        Task(task_id="fail", task="fail", critical=False, tool_required=["fail"]),
        Task(task_id="success", task="success", critical=False, tool_required=["success"]),
    ])])
    result = Orchestrator(PlanStore(tmp_path), TaskExecutorAgent(registry), ValidatorAgent()).execute(plan)
    assert result.status == Status.FAILED
    assert result.goals[0].tasks[0].status == Status.FAILED
    assert result.goals[0].tasks[1].status == Status.COMPLETED
    assert calls["success"] == 1
