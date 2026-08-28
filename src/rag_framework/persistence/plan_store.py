"""Atomic local persistence for plan JSON."""

import json
import os
from pathlib import Path

from rag_framework.domain import Plan, Status


class PlanStore:
    def __init__(self, directory: str | Path = "plans") -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def path_for(self, plan_id: str) -> Path:
        return self.directory / f"plan_{plan_id}.json"

    def save(self, plan: Plan) -> Path:
        destination = self.path_for(plan.plan_id)
        temporary = destination.with_suffix(".json.tmp")
        temporary.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        os.replace(temporary, destination)
        return destination

    def load(self, plan_id: str) -> Plan:
        plan = Plan.model_validate_json(self.path_for(plan_id).read_text(encoding="utf-8"))
        self.recover_interrupted(plan)
        return plan

    @staticmethod
    def recover_interrupted(plan: Plan) -> bool:
        """Make work interrupted by a process stop eligible for resumption."""
        recovered = plan.status == Status.RUNNING
        if recovered:
            plan.status = Status.PENDING
        for goal in plan.goals:
            if goal.status == Status.RUNNING:
                goal.status = Status.PENDING
                recovered = True
            for task in goal.tasks:
                if task.status == Status.RUNNING:
                    task.status = Status.PENDING
                    task.retry.attempt = max(0, task.retry.attempt - 1)
                    recovered = True
                for subtask in task.subtasks:
                    if subtask.status == Status.RUNNING:
                        subtask.status = Status.PENDING
                        recovered = True
        return recovered
