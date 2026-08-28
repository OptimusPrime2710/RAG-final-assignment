"""Resolve later user requests to reusable plan goals."""

from rag_framework.domain import Goal, Plan


class GoalResolutionError(ValueError):
    pass


class GoalResolver:
    def resolve(self, plan: Plan, request: str) -> Goal:
        terms = set(request.lower().split())
        scored = []
        for goal in plan.goals:
            words = set(f"{goal.goal} {goal.description}".lower().split())
            score = len(terms & words)
            if "populate" in terms or "add" in terms or "index" in terms:
                score += 3 if "populate" in goal.goal.lower() else 0
            if "search" in terms or "find" in terms or "retrieve" in terms:
                score += 3 if "retrieve" in goal.goal.lower() else 0
            scored.append((score, goal))
        score, goal = max(scored, key=lambda item: item[0], default=(0, None))
        if goal is None or score == 0:
            raise GoalResolutionError(f"no reusable goal matches request: {request}")
        return goal
