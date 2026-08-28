"""Plan execution state machine."""

from uuid import uuid4

from rag_framework.agents.executor import SubtaskExecutorAgent, TaskExecutorAgent
from rag_framework.agents.validator import ValidatorAgent
from rag_framework.domain import ExecutorRequest, Plan, Status, ValidatorRequest
from rag_framework.persistence.plan_store import PlanStore
from rag_framework.transformer import transform_output


class Orchestrator:
    def __init__(self, store: PlanStore, executor: TaskExecutorAgent, validator: ValidatorAgent, max_attempts: int = 3, subtask_executor: SubtaskExecutorAgent | None = None) -> None:
        self.store = store
        self.executor = executor
        self.validator = validator
        self.max_attempts = max_attempts
        self.subtask_executor = subtask_executor or SubtaskExecutorAgent(executor.tools, executor.models, executor.model_call)

    def execute(self, plan: Plan, goal_ids: set[str] | None = None) -> Plan:
        if not self._resolve_inputs(plan, goal_ids):
            plan.status = Status.BLOCKED
            for goal in plan.goals:
                if goal_ids is None or goal.goal_id in goal_ids:
                    goal.status = Status.BLOCKED
                    for task in goal.tasks:
                        if task.status not in {Status.COMPLETED, Status.SKIPPED}:
                            task.status = Status.BLOCKED
            self.store.save(plan)
            return plan
        plan.status = Status.RUNNING
        self.store.save(plan)
        for goal in plan.goals:
            if goal_ids is not None and goal.goal_id not in goal_ids:
                continue
            goal.status = Status.RUNNING
            for task in goal.tasks:
                if task.status == Status.COMPLETED:
                    continue
                if any(self._task_status(plan, dependency) != Status.COMPLETED for dependency in task.dependencies):
                    task.status = Status.BLOCKED
                    continue
                task.inputs.update(self._mapped_dependency_inputs(plan, task))
                succeeded = self._execute_task(plan, goal, task)
                if not succeeded and (task.critical or goal.critical):
                    goal.status = Status.PAUSED
                    plan.status = Status.PAUSED
                    self.store.save(plan)
                    return plan
            goal.status = Status.COMPLETED if all(task.status == Status.COMPLETED for task in goal.tasks) else Status.FAILED
        evaluated_goals = [goal for goal in plan.goals if goal_ids is None or goal.goal_id in goal_ids]
        plan.status = Status.COMPLETED if evaluated_goals and all(goal.status == Status.COMPLETED for goal in evaluated_goals) else Status.FAILED
        self.store.save(plan)
        return plan

    def retrigger(self, plan: Plan, request: str, resolver) -> Plan:
        goal = resolver.resolve(plan, request)
        goal.status = Status.PENDING
        for task in goal.tasks:
            task.status = Status.PENDING
            task.retry.attempt = 0
            task.retry.last_error = None
            task.execution = {}
        return self.execute(plan, {goal.goal_id})

    def _execute_task(self, plan: Plan, goal, task) -> bool:
        if task.subtasks and not self._execute_subtasks(plan, goal, task):
            task.status = Status.FAILED
            self.store.save(plan)
            return False
        for attempt in range(task.retry.attempt + 1, self.max_attempts + 1):
            task.status = Status.RUNNING
            task.retry.attempt = attempt
            self.store.save(plan)
            request = ExecutorRequest(
                request_id=f"req_{uuid4().hex[:8]}", plan_id=plan.plan_id, goal_id=goal.goal_id, task_id=task.task_id,
                executor_type="task_executor", task={"name": task.task, "description": task.description},
                inputs=task.inputs, tools=task.tool_required, model_requirement=task.model_requirement,
                success_criteria=goal.success_criteria, attempt=attempt, max_attempts=self.max_attempts,
                previous_failure=task.execution.get("previous_failure"),
            )
            try:
                response = self.executor.execute(request)
                validation = self.validator.validate(ValidatorRequest(
                    plan_id=plan.plan_id, goal_id=goal.goal_id, task_id=task.task_id,
                    success_criteria=goal.success_criteria, executor_result=response.result,
                    executor_validation=response.validation,
                ))
                task.execution = {"result": response.result, "validation": validation.model_dump()}
                if validation.status == "passed":
                    task.status = Status.COMPLETED
                    self.store.save(plan)
                    return True
                task.retry.last_error = validation.reason
            except Exception as error:
                task.retry.last_error = str(error)
            task.execution["previous_failure"] = {"attempt": attempt, "error": task.retry.last_error, "input": task.inputs}
            self.store.save(plan)
        task.status = Status.FAILED
        self.store.save(plan)
        return False

    def _execute_subtasks(self, plan: Plan, goal, task) -> bool:
        completed: set[str] = set()
        for subtask in task.subtasks:
            if subtask.status == Status.COMPLETED:
                completed.add(subtask.subtask_id)
                continue
            if any(dependency not in completed for dependency in subtask.dependencies):
                subtask.status = Status.BLOCKED
                self.store.save(plan)
                return False
            subtask.status = Status.RUNNING
            self.store.save(plan)
            request = ExecutorRequest(
                request_id=f"req_{uuid4().hex[:8]}", plan_id=plan.plan_id, goal_id=goal.goal_id,
                task_id=task.task_id, subtask_id=subtask.subtask_id, executor_type="subtask_executor",
                task={"name": subtask.task, "description": subtask.description}, inputs=subtask.inputs,
                tools=subtask.tool_required, success_criteria=goal.success_criteria,
            )
            try:
                response = self.subtask_executor.execute_subtask(request)
            except Exception as error:
                subtask.status = Status.FAILED
                subtask.execution = {"error": str(error)}
                self.store.save(plan)
                return False
            if response.status != "success":
                subtask.status = Status.FAILED
                subtask.execution = {"result": response.result, "error": response.error}
                self.store.save(plan)
                return False
            subtask.status = Status.COMPLETED
            subtask.execution = {"result": response.result, "validation": response.validation}
            completed.add(subtask.subtask_id)
            self.store.save(plan)
        return True

    @staticmethod
    def _resolve_inputs(plan: Plan, goal_ids: set[str] | None) -> bool:
        missing = [value.name for value in plan.inputs if value.required and value.effective_value is None]
        if missing:
            return False
        resolved = {value.name: value.effective_value for value in plan.inputs if value.effective_value is not None}
        for goal in plan.goals:
            if goal_ids is not None and goal.goal_id not in goal_ids:
                continue
            for task in goal.tasks:
                for name, value in resolved.items():
                    task.inputs.setdefault(name, value)
        return True

    @staticmethod
    def _task_status(plan: Plan, task_id: str) -> Status:
        for goal in plan.goals:
            for task in goal.tasks:
                if task.task_id == task_id:
                    return task.status
        return Status.BLOCKED

    @staticmethod
    def _mapped_dependency_inputs(plan: Plan, task) -> dict:
        inputs = {}
        for dependency_id in task.dependencies:
            for goal in plan.goals:
                for dependency in goal.tasks:
                    if dependency.task_id == dependency_id and dependency.output_mapping:
                        result = dependency.execution.get("result", {})
                        inputs.update(transform_output(result, dependency.output_mapping))
        return inputs
