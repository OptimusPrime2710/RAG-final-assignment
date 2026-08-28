"""Planner agent for business use-case files."""

import re
from pathlib import Path
from typing import Any, Callable

from rag_framework.domain import Goal, Plan, PlanInput, SuccessCriterion, Task
from rag_framework.registry.model_registry import ModelRegistry


class PlannerAgent:
    """Create plans deterministically or through an injected structured model."""

    def __init__(self, models: ModelRegistry | None = None, model_call: Callable[..., dict[str, Any]] | None = None, model_size: str = "medium") -> None:
        self.models = models
        self.model_call = model_call
        self.model_size = model_size

    def create_plan(self, source_path: str | Path, plan_id: str) -> Plan:
        path = Path(source_path)
        if path.suffix.lower() not in {".txt", ".md", ".markdown"}:
            raise ValueError("business use-case files must be .txt, .md, or .markdown")
        text = path.read_text(encoding="utf-8")
        if self.models is not None and self.model_call is not None:
            model = self.models.resolve(self.model_size)
            result = self.model_call(model, [{
                "role": "system",
                "content": "Return only a JSON execution plan with plan_id, source, use_case, inputs, and goals.",
            }, {"role": "user", "content": text}])
            model_execution = result.pop("_model_execution", None)
            result["plan_id"] = plan_id
            result.setdefault("source", {"path": str(path), "format": path.suffix.lower()})
            plan = Plan.model_validate(result)
            if model_execution:
                plan.source["model_execution"] = model_execution
            return plan
        title = next((line.lstrip("# ").strip() for line in text.splitlines() if line.strip()), path.stem)
        retrieval = bool(re.search(r"search|retriev|similar|query", text, re.IGNORECASE))
        population = bool(re.search(r"load|index|populate|chrom", text, re.IGNORECASE))
        goals: list[Goal] = []
        if population:
            goals.append(Goal(
                goal_id="goal_population",
                goal="Populate ChromaDB",
                description="Load and index source documents incrementally.",
                success_criteria=[SuccessCriterion(criterion_id="criteria_population", description="Documents are indexed successfully")],
                tasks=[Task(task_id="task_population", task="Populate knowledge base", description=text, inputs={"directory": str(path.parent)}, tool_required=["rag.index_directory"])],
            ))
        if retrieval:
            goals.append(Goal(
                goal_id="goal_retrieval",
                goal="Retrieve semantically similar documents",
                description="Search the indexed documents using a natural-language query.",
                success_criteria=[SuccessCriterion(criterion_id="criteria_retrieval", description="Relevant documents are returned")],
                tasks=[Task(task_id="task_retrieval", task="Retrieve relevant documents", description=text, inputs={"query": text.strip(), "top_k": 5}, tool_required=["rag.search_similar"])],
            ))
        if not goals:
            goals.append(Goal(
                goal_id="goal_001", goal=title, description=text.strip(),
                success_criteria=[SuccessCriterion(criterion_id="criteria_001", description="The requested task completes successfully")],
                tasks=[Task(task_id="task_001", task=title, description=text)],
            ))
        return Plan(
            plan_id=plan_id,
            source={"path": str(path), "format": path.suffix.lower()},
            use_case={"title": title, "objective": text.strip()},
            inputs=[PlanInput(input_id="top_k", name="top_k", type="integer", default_value=5)],
            goals=goals,
        )
