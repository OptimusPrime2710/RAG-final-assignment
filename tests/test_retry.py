from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.domain import Goal, Plan, Task
from rag_framework.orchestrator import Orchestrator
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


def test_task_retries_three_times_and_fails(tmp_path: Path) -> None:
    tools = ToolRegistry()
    calls = {"count": 0}

    def fail(_inputs):
        calls["count"] += 1
        raise RuntimeError("failure")

    tools.register(ToolDescriptor("fail", "fail", "Fail", "python"), fail)
    plan = Plan(plan_id="retry", goals=[Goal(goal_id="g", goal="retry", tasks=[Task(task_id="t", task="fail", tool_required=["fail"])])])
    result = Orchestrator(PlanStore(tmp_path), TaskExecutorAgent(tools), ValidatorAgent()).execute(plan)
    assert result.goals[0].tasks[0].status == "failed"
    assert calls["count"] == 3
