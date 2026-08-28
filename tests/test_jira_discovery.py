import json

from rag_framework.registry.tool_registry import ToolRegistry
from rag_framework.tools.jira_mcp import JiraMCPAdapter


class Response:
    def __init__(self, body):
        self.body = body

    def read(self):
        return json.dumps(self.body).encode()


def test_mcp_tools_are_discovered_with_server_schema() -> None:
    responses = iter([
        Response({"result": {"protocolVersion": "2025-06-18"}}),
        Response({}),
        Response({"result": {"tools": [{
            "name": "issue_search", "description": "Search issues",
            "inputSchema": {"type": "object", "required": ["jql"]},
            "outputSchema": {"type": "object", "required": ["issues"]},
        }]}}),
    ])
    adapter = JiraMCPAdapter.from_url("https://jira.example/mcp", lambda request, timeout: next(responses))
    registry = ToolRegistry()
    assert adapter.register_discovered_tools(registry) == ["issue_search"]
    descriptor = registry.discover("jira_issue_search")[0]
    assert descriptor.input_schema["required"] == ["jql"]
