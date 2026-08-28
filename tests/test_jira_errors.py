from urllib.error import HTTPError

import pytest

from rag_framework.tools.jira_mcp import JiraMCPAdapter


def test_http_error_becomes_actionable_mcp_error() -> None:
    def request_call(request, timeout):
        raise HTTPError(request.full_url, 403, "Forbidden", {}, None)

    adapter = JiraMCPAdapter.from_url("https://jira.example/mcp", request_call, initialize=False)
    with pytest.raises(RuntimeError, match="JIRA MCP HTTP error 403"):
        adapter.execute("issue_search", {})
