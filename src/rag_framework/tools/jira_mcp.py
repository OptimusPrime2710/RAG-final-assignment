"""JIRA MCP adapter registered as ordinary tools."""

import base64
import json
from itertools import count
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry


class JiraMCPAdapter:
    def __init__(self, transport: Callable[[str, dict[str, Any]], dict[str, Any]] | None = None, discovery: Callable[[], list[dict[str, Any]]] | None = None) -> None:
        self.transport = transport or (lambda tool, inputs: {"tool": tool, "inputs": inputs})
        self.discovery = discovery

    @classmethod
    def from_url(cls, url: str, request_call: Callable[..., Any] | None = None, api_token: str | None = None, email: str | None = None, initialize: bool = True) -> "JiraMCPAdapter":
        """Create an HTTP JSON-RPC MCP adapter for a configured endpoint."""
        caller = request_call or urlopen
        request_ids = count(1)
        session_id: str | None = None
        initialized = False

        def rpc(method: str, params: dict[str, Any], expect_response: bool = True) -> dict[str, Any] | None:
            nonlocal session_id
            message = {"jsonrpc": "2.0", "method": method, "params": params}
            if expect_response:
                message["id"] = next(request_ids)
            payload = json.dumps(message).encode("utf-8")
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json, text/event-stream",
                "User-Agent": "multi-agent-rag/0.1.0",
            }
            if api_token and email:
                credentials = base64.b64encode(f"{email}:{api_token}".encode("utf-8")).decode("ascii")
                headers["Authorization"] = f"Basic {credentials}"
            if session_id:
                headers["Mcp-Session-Id"] = session_id
            try:
                response = caller(Request(url, data=payload, headers=headers, method="POST"), timeout=60)
            except HTTPError as error:
                raise RuntimeError(f"JIRA MCP HTTP error {error.code}: {error.reason}") from error
            except URLError as error:
                raise RuntimeError(f"JIRA MCP connection error: {error.reason}") from error
            response_session = getattr(response, "headers", {}).get("Mcp-Session-Id")
            if response_session:
                session_id = response_session
            if not expect_response:
                return None
            raw_body = response.read().decode("utf-8")
            content_type = getattr(response, "headers", {}).get("Content-Type", "")
            if "text/event-stream" in content_type:
                events = [line[5:].strip() for line in raw_body.splitlines() if line.startswith("data:")]
                if not events:
                    raise RuntimeError("JIRA MCP returned an empty event stream")
                raw_body = events[-1]
            body = json.loads(raw_body)
            if "error" in body:
                raise RuntimeError(f"JIRA MCP error: {body['error']}")
            result = body.get("result")
            if not isinstance(result, dict):
                raise RuntimeError("JIRA MCP returned an invalid tool result")
            return result

        def ensure_initialized() -> None:
            nonlocal initialized
            if initialize and not initialized:
                rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "multi-agent-rag", "version": "0.1.0"}})
                rpc("notifications/initialized", {}, expect_response=False)
                initialized = True

        def transport(tool_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
            ensure_initialized()
            return rpc("tools/call", {"name": tool_name, "arguments": inputs}) or {}

        def discovery() -> list[dict[str, Any]]:
            ensure_initialized()
            result = rpc("tools/list", {}) or {}
            tools = result.get("tools", [])
            if not isinstance(tools, list):
                raise RuntimeError("JIRA MCP returned an invalid tools list")
            return tools

        return cls(transport, discovery)

    def execute(self, tool_name: str, inputs: dict[str, Any]) -> dict[str, Any]:
        return self.transport(tool_name, inputs)

    def register_tools(self, registry: ToolRegistry, tool_names: list[str]) -> None:
        """Expose MCP operations through the same registry as local tools."""
        for tool_name in tool_names:
            registry.register(
                ToolDescriptor(
                    toolid=f"jira.{tool_name}",
                    tool_name=tool_name,
                    description=f"JIRA MCP operation: {tool_name}",
                    type="mcp",
                    capabilities=["jira", f"jira_{tool_name}"],
                ),
                lambda inputs, name=tool_name: self.execute(name, inputs),
            )

    def discover_tools(self) -> list[dict[str, Any]]:
        if self.discovery is None:
            raise RuntimeError("tool discovery is unavailable for this transport")
        return self.discovery()

    def register_discovered_tools(self, registry: ToolRegistry) -> list[str]:
        """Discover MCP tools and register their server-provided schemas."""
        names = []
        for tool in self.discover_tools():
            name = tool.get("name")
            if not isinstance(name, str) or not name:
                continue
            registry.register(ToolDescriptor(
                toolid=f"jira.{name}", tool_name=name,
                description=tool.get("description", f"JIRA MCP operation: {name}"), type="mcp",
                input_schema=tool.get("inputSchema", {"type": "object"}),
                output_schema=tool.get("outputSchema", {"type": "object"}),
                capabilities=["jira", f"jira_{name}"],
            ), lambda inputs, operation=name: self.execute(operation, inputs))
            names.append(name)
        return names
