from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.domain import Goal, Plan, Status, Task
from rag_framework.orchestrator import Orchestrator
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


def test_running_work_is_recovered_without_repeating_completed_tasks(tmp_path: Path) -> None:
    store = PlanStore(tmp_path)
    plan = Plan(plan_id="resume", status=Status.RUNNING, goals=[Goal(
        goal_id="g", status=Status.RUNNING, goal="resume", tasks=[
            Task(task_id="done", task="done", status=Status.COMPLETED, execution={"result": {"done": True}}),
            Task(task_id="interrupted", task="interrupted", status=Status.RUNNING, retry={"attempt": 3}),
        ],
    )])
    store.save(plan)
    recovered = store.load("resume")
    assert recovered.status == Status.PENDING
    assert recovered.goals[0].status == Status.PENDING
    assert recovered.goals[0].tasks[0].status == Status.COMPLETED
    assert recovered.goals[0].tasks[1].status == Status.PENDING
    assert recovered.goals[0].tasks[1].retry.attempt == 2


def test_resumed_task_executes_again(tmp_path: Path) -> None:
    store = PlanStore(tmp_path)
    plan = Plan(plan_id="resume-run", status=Status.RUNNING, goals=[Goal(
        goal_id="g", status=Status.RUNNING, goal="resume", tasks=[Task(task_id="t", task="run", status=Status.RUNNING, retry={"attempt": 2}, tool_required=["run"])],
    )])
    store.save(plan)
    tools = ToolRegistry()
    tools.register(ToolDescriptor("run", "run", "Run", "python"), lambda _: {"ok": True})
    result = Orchestrator(store, TaskExecutorAgent(tools), ValidatorAgent()).execute(store.load("resume-run"))
    assert result.status == Status.COMPLETED
    assert result.goals[0].tasks[0].status == Status.COMPLETED
