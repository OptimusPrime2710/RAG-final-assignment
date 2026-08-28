from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.agents.planner import PlannerAgent
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.orchestrator import Orchestrator
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


def test_planner_accepts_markdown(tmp_path: Path) -> None:
    source = tmp_path / "use_case.md"
    source.write_text("# Semantic Search\nSearch documents and return top results.", encoding="utf-8")
    plan = PlannerAgent().create_plan(source, "001")
    assert plan.goals[0].tasks[0].task == "Retrieve relevant documents"


def test_orchestrator_executes_registered_tool(tmp_path: Path) -> None:
    tools = ToolRegistry()
    tools.register(ToolDescriptor("echo", "echo", "Echo", "python"), lambda inputs: {"value": inputs["value"]})
    plan = PlannerAgent().create_plan(tmp_path / "case.txt", "002") if False else None
    from rag_framework.domain import Goal, Plan, Task
    plan = Plan(plan_id="002", goals=[Goal(goal_id="g", goal="test", tasks=[Task(task_id="t", task="echo", tool_required=["echo"], inputs={"value": 7})])])
    result = Orchestrator(PlanStore(tmp_path / "plans"), TaskExecutorAgent(tools), ValidatorAgent()).execute(plan)
    assert result.status == "completed"
    assert result.goals[0].tasks[0].execution["result"] == {"value": 7}
