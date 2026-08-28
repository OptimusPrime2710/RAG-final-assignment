from pathlib import Path

import pytest
from jsonschema import ValidationError

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.domain import ExecutorRequest
from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


def test_tool_input_schema_blocks_handler() -> None:
    calls = {"count": 0}
    registry = ToolRegistry()
    registry.register(
        ToolDescriptor("typed", "typed", "Typed tool", "python", input_schema={"type": "object", "required": ["value"]}),
        lambda inputs: calls.update(count=calls["count"] + 1) or inputs,
    )
    with pytest.raises(ValidationError):
        registry.execute("typed", {})
    assert calls["count"] == 0


def test_tool_output_schema_blocks_invalid_result() -> None:
    registry = ToolRegistry()
    registry.register(
        ToolDescriptor("typed", "typed", "Typed tool", "python", output_schema={"type": "object", "required": ["value"]}),
        lambda _: {"wrong": True},
    )
    with pytest.raises(ValidationError):
        registry.execute("typed", {})


def test_executor_validates_request_before_tool_call(tmp_path: Path) -> None:
    registry = ToolRegistry()
    registry.register(ToolDescriptor("echo", "echo", "Echo", "python"), lambda _: {})
    request = ExecutorRequest(
        request_id="req", plan_id="plan", goal_id="goal", task_id="task", executor_type="task_executor",
        task={"name": "echo", "description": "Echo"}, tools=["echo"],
    )
    request.executor_type = ""
    with pytest.raises(ValidationError):
        TaskExecutorAgent(registry).execute(request)
