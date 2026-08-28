"""Generic task and subtask execution."""

from typing import Any, Callable

from rag_framework.domain import ExecutorRequest, ExecutorResponse
from rag_framework.registry.model_registry import ModelRegistry
from rag_framework.registry.tool_registry import ToolRegistry
from rag_framework.schemas import EXECUTOR_REQUEST_SCHEMA, EXECUTOR_RESPONSE_SCHEMA, validate_json


class TaskExecutorAgent:
    def __init__(self, tools: ToolRegistry, models: ModelRegistry | None = None, model_call: Callable[..., dict[str, Any]] | None = None) -> None:
        self.tools = tools
        self.models = models
        self.model_call = model_call

    def execute(self, request: ExecutorRequest) -> ExecutorResponse:
        validate_json(request.model_dump(), EXECUTOR_REQUEST_SCHEMA)
        result: dict[str, Any] = {}
        model_execution = None
        if request.model_requirement.required:
            if self.models is None or self.model_call is None:
                raise RuntimeError("a model is required but no model gateway is configured")
            resolved = self.models.resolve(request.model_requirement.size or "small")
            result = self.model_call(resolved, request)
            model_execution = {"provider": resolved.provider, "model": resolved.model, "size": resolved.size}
        for tool_id in request.tools:
            tool_result = self.tools.execute(tool_id, request.inputs)
            result.update(tool_result)
        validation = {"status": "passed", "checks": ["execution returned without error"]}
        if model_execution:
            validation["model_execution"] = model_execution
        response = ExecutorResponse(
            request_id=request.request_id,
            status="success",
            result=result,
            output_for_next_executor=result,
            validation=validation,
            retry={"required": False, "attempt": request.attempt, "max_attempts": request.max_attempts},
        )
        validate_json(response.model_dump(), EXECUTOR_RESPONSE_SCHEMA)
        return response


class SubtaskExecutorAgent(TaskExecutorAgent):
    def execute_subtask(self, request: ExecutorRequest) -> ExecutorResponse:
        """Execute a subtask through the same registry and model boundaries."""
        request.executor_type = "subtask_executor"
        return self.execute(request)
