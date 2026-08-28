import json

import pytest

from rag_framework.tools.jira_mcp import JiraMCPAdapter


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def read(self):
        return json.dumps(self.body).encode("utf-8")


class EventResponse(FakeResponse):
    headers = {"Content-Type": "text/event-stream"}

    def read(self):
        return f"event: message\ndata: {json.dumps(self.body)}\n\n".encode("utf-8")


def test_http_mcp_transport_sends_tools_call() -> None:
    captured = {}

    def request_call(request, timeout):
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return FakeResponse({"jsonrpc": "2.0", "id": 1, "result": {"issues": []}})

    adapter = JiraMCPAdapter.from_url("https://jira.example/mcp", request_call, initialize=False)
    assert adapter.execute("issue_search", {"jql": "project = DEMO"}) == {"issues": []}
    assert captured["url"] == "https://jira.example/mcp"
    assert captured["payload"]["method"] == "tools/call"
    assert captured["payload"]["params"] == {"name": "issue_search", "arguments": {"jql": "project = DEMO"}}


def test_http_mcp_transport_surfaces_protocol_errors() -> None:
    adapter = JiraMCPAdapter.from_url("https://jira.example/mcp", lambda request, timeout: FakeResponse({"error": {"message": "denied"}}), initialize=False)
    with pytest.raises(RuntimeError, match="denied"):
        adapter.execute("issue_search", {})


def test_http_mcp_transport_initializes_and_authenticates() -> None:
    requests = []
    responses = iter([
        FakeResponse({"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-06-18"}}),
        FakeResponse({"jsonrpc": "2.0"}),
        FakeResponse({"jsonrpc": "2.0", "id": 3, "result": {"issues": []}}),
    ])

    def request_call(request, timeout):
        requests.append((json.loads(request.data), dict(request.header_items())))
        return next(responses)

    adapter = JiraMCPAdapter.from_url("https://jira.example/mcp", request_call, api_token="secret", email="user@example.com")
    assert adapter.execute("issue_search", {}) == {"issues": []}
    assert [request[0]["method"] for request in requests] == ["initialize", "notifications/initialized", "tools/call"]
    assert "id" not in requests[1][0]
    assert requests[0][1]["Authorization"] == "Basic dXNlckBleGFtcGxlLmNvbTpzZWNyZXQ="
    assert requests[0][1]["User-agent"] == "multi-agent-rag/0.1.0"


def test_http_mcp_transport_parses_event_stream_response() -> None:
    adapter = JiraMCPAdapter.from_url(
        "https://jira.example/mcp",
        lambda request, timeout: EventResponse({"result": {"issues": []}}),
        initialize=False,
    )
    assert adapter.execute("issue_search", {}) == {"issues": []}
