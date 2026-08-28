from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.domain import Goal, Plan, Status, Subtask, Task
from rag_framework.orchestrator import Orchestrator
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


def test_subtasks_execute_in_dependency_order(tmp_path: Path) -> None:
    tools = ToolRegistry()
    calls: list[str] = []

    def run(inputs):
        calls.append(inputs["name"])
        return {"done": inputs["name"]}

    tools.register(ToolDescriptor("run", "run", "Run subtask", "python"), run)
    plan = Plan(plan_id="subtasks", goals=[Goal(goal_id="g", goal="work", tasks=[Task(
        task_id="t", task="parent", subtasks=[
            Subtask(subtask_id="first", task="first", tool_required=["run"], inputs={"name": "first"}),
            Subtask(subtask_id="second", task="second", dependencies=["first"], tool_required=["run"], inputs={"name": "second"}),
        ],
    )])])
    result = Orchestrator(PlanStore(tmp_path), TaskExecutorAgent(tools), ValidatorAgent()).execute(plan)
    assert result.status == Status.COMPLETED
    assert calls == ["first", "second"]
    assert all(subtask.status == Status.COMPLETED for subtask in result.goals[0].tasks[0].subtasks)
    assert result.goals[0].tasks[0].subtasks[0].execution["result"] == {"done": "first"}


def test_blocked_subtask_prevents_parent_execution(tmp_path: Path) -> None:
    tools = ToolRegistry()
    calls = {"count": 0}
    tools.register(ToolDescriptor("run", "run", "Run", "python"), lambda _: calls.update(count=calls["count"] + 1) or {})
    plan = Plan(plan_id="blocked-subtask", goals=[Goal(goal_id="g", goal="work", tasks=[Task(
        task_id="t", task="parent", subtasks=[Subtask(subtask_id="second", task="second", dependencies=["missing"], tool_required=["run"])],
    )])])
    result = Orchestrator(PlanStore(tmp_path), TaskExecutorAgent(tools), ValidatorAgent()).execute(plan)
    assert result.status == Status.PAUSED
    assert result.goals[0].tasks[0].status == Status.FAILED
    assert result.goals[0].tasks[0].subtasks[0].status == Status.BLOCKED
    assert calls["count"] == 0
