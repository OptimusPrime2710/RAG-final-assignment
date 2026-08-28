"""Central discovery and dispatch for Python, API, and MCP tools."""

from dataclasses import dataclass, field
from typing import Any, Callable

from rag_framework.schemas import validate_json


@dataclass(frozen=True)
class ToolDescriptor:
    toolid: str
    tool_name: str
    description: str
    type: str
    input_schema: dict[str, Any] = field(default_factory=dict)
    output_schema: dict[str, Any] = field(default_factory=dict)
    capabilities: list[str] = field(default_factory=list)
    enabled: bool = True


@dataclass
class RegisteredTool:
    descriptor: ToolDescriptor
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, RegisteredTool] = {}

    def register(self, descriptor: ToolDescriptor, handler: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        if descriptor.toolid in self._tools:
            raise ValueError(f"tool already registered: {descriptor.toolid}")
        if descriptor.type not in {"python", "api", "mcp"}:
            raise ValueError(f"unsupported tool type: {descriptor.type}")
        self._tools[descriptor.toolid] = RegisteredTool(descriptor, handler)

    def discover(self, capability: str | None = None) -> list[ToolDescriptor]:
        tools = [tool.descriptor for tool in self._tools.values() if tool.descriptor.enabled]
        if capability is not None:
            tools = [tool for tool in tools if capability in tool.capabilities]
        return tools

    def execute(self, toolid: str, inputs: dict[str, Any]) -> dict[str, Any]:
        registered = self._tools.get(toolid)
        if registered is None or not registered.descriptor.enabled:
            raise KeyError(f"tool is not enabled or registered: {toolid}")
        validate_json(inputs, registered.descriptor.input_schema)
        result = registered.handler(inputs)
        validate_json(result, registered.descriptor.output_schema)
        return result
