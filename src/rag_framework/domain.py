"""Typed JSON contracts used throughout the framework."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Status(StrEnum):
    PENDING = "pending"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    SKIPPED = "skipped"
    PAUSED = "paused"


class ModelRequirement(BaseModel):
    required: bool = False
    size: str | None = None

    @model_validator(mode="after")
    def validate_size(self) -> "ModelRequirement":
        if self.required and self.size not in {"small", "medium"}:
            raise ValueError("required model size must be small or medium")
        if not self.required:
            self.size = None
        return self


class RetryState(BaseModel):
    attempt: int = 0
    max_attempts: int = Field(default=3, ge=1)
    last_error: str | None = None
    failure_input: dict[str, Any] | None = None


class SuccessCriterion(BaseModel):
    criterion_id: str
    description: str
    achieved: bool = False


class PlanInput(BaseModel):
    input_id: str
    name: str
    type: str
    required: bool = False
    user_value: Any = None
    default_value: Any = None
    effective_value: Any = None
    source: str | None = None

    @model_validator(mode="after")
    def resolve(self) -> "PlanInput":
        if self.user_value is not None:
            self.effective_value = self.user_value
            self.source = "user"
        elif self.default_value is not None:
            self.effective_value = self.default_value
            self.source = "default"
        elif self.required:
            self.source = None
        if self.effective_value is not None:
            valid = {
                "string": isinstance(self.effective_value, str),
                "integer": isinstance(self.effective_value, int) and not isinstance(self.effective_value, bool),
                "int": isinstance(self.effective_value, int) and not isinstance(self.effective_value, bool),
                "number": isinstance(self.effective_value, (int, float)) and not isinstance(self.effective_value, bool),
                "float": isinstance(self.effective_value, (int, float)) and not isinstance(self.effective_value, bool),
                "boolean": isinstance(self.effective_value, bool),
                "bool": isinstance(self.effective_value, bool),
            }.get(self.type)
            if valid is False:
                raise ValueError(f"input {self.name} does not match declared type {self.type}")
        return self


class Subtask(BaseModel):
    subtask_id: str
    task: str
    description: str = ""
    status: Status = Status.PENDING
    dependencies: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    tool_required: list[str] = Field(default_factory=list)
    execution: dict[str, Any] = Field(default_factory=dict)


class Task(BaseModel):
    task_id: str
    task: str
    description: str = ""
    status: Status = Status.PENDING
    critical: bool = False
    dependencies: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    expected_output: dict[str, Any] = Field(default_factory=dict)
    output_mapping: dict[str, str] = Field(default_factory=dict)
    model_requirement: ModelRequirement = Field(default_factory=ModelRequirement)
    tool_required: list[str] = Field(default_factory=list)
    subtasks: list[Subtask] = Field(default_factory=list)
    retry: RetryState = Field(default_factory=RetryState)
    execution: dict[str, Any] = Field(default_factory=dict)


class Goal(BaseModel):
    goal_id: str
    goal: str
    description: str = ""
    status: Status = Status.PENDING
    critical: bool = True
    success_criteria: list[SuccessCriterion] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)


class Plan(BaseModel):
    model_config = ConfigDict(extra="forbid")

    plan_id: str
    version: int = 1
    status: Status = Status.PENDING
    source: dict[str, Any] = Field(default_factory=dict)
    use_case: dict[str, Any] = Field(default_factory=dict)
    inputs: list[PlanInput] = Field(default_factory=list)
    goals: list[Goal] = Field(default_factory=list)


class ExecutorRequest(BaseModel):
    request_id: str
    plan_id: str
    goal_id: str
    task_id: str
    subtask_id: str | None = None
    executor_type: str
    task: dict[str, str]
    inputs: dict[str, Any] = Field(default_factory=dict)
    tools: list[str] = Field(default_factory=list)
    model_requirement: ModelRequirement = Field(default_factory=ModelRequirement)
    success_criteria: list[SuccessCriterion] = Field(default_factory=list)
    attempt: int = Field(default=1, ge=1)
    max_attempts: int = Field(default=3, ge=1)
    previous_failure: dict[str, Any] | None = None


class ExecutorResponse(BaseModel):
    request_id: str
    status: str
    result: dict[str, Any] = Field(default_factory=dict)
    output_for_next_executor: dict[str, Any] = Field(default_factory=dict)
    validation: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None
    retry: dict[str, Any] = Field(default_factory=dict)


class ValidatorRequest(BaseModel):
    plan_id: str
    goal_id: str
    task_id: str
    success_criteria: list[SuccessCriterion] = Field(default_factory=list)
    executor_result: dict[str, Any] = Field(default_factory=dict)
    executor_validation: dict[str, Any] = Field(default_factory=dict)


class ValidatorResponse(BaseModel):
    status: str
    criteria: list[dict[str, Any]] = Field(default_factory=list)
    reason: str | None = None
    retry_recommended: bool = False
