from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.agents.planner import PlannerAgent
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.domain import Goal, Plan, Task
from rag_framework.goal_resolver import GoalResolver
from rag_framework.orchestrator import Orchestrator
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


def test_planner_creates_independent_goals(tmp_path: Path) -> None:
    source = tmp_path / "case.md"
    source.write_text("# Search\nLoad documents, then retrieve similar results.", encoding="utf-8")
    plan = PlannerAgent().create_plan(source, "goals")
    assert {goal.goal_id for goal in plan.goals} == {"goal_population", "goal_retrieval"}
    assert GoalResolver().resolve(plan, "Find the top 5 documents") .goal_id == "goal_retrieval"
    assert GoalResolver().resolve(plan, "Add new documents") .goal_id == "goal_population"


def test_retrigger_executes_only_selected_goal(tmp_path: Path) -> None:
    tools = ToolRegistry()
    tools.register(ToolDescriptor("echo", "echo", "Echo", "python"), lambda inputs: {"ok": True})
    plan = Plan(plan_id="retrigger", goals=[
        Goal(goal_id="population", goal="Populate ChromaDB", tasks=[Task(task_id="p", task="populate", tool_required=["echo"])]),
        Goal(goal_id="retrieval", goal="Retrieve semantically similar documents", tasks=[Task(task_id="r", task="retrieve", tool_required=["echo"])]),
    ])
    result = Orchestrator(PlanStore(tmp_path), TaskExecutorAgent(tools), ValidatorAgent()).retrigger(plan, "Find relevant documents", GoalResolver())
    assert result.goals[1].status == "completed"
    assert result.goals[0].status == "pending"
