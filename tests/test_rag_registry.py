from pathlib import Path

from rag_framework.registry.tool_registry import ToolRegistry
from rag_framework.tools.chroma import ChromaStore
from rag_framework.tools.rag_registry import register_rag_tools


def test_registered_rag_tools_index_and_search(tmp_path: Path) -> None:
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "policy.md").write_text("Cancellation policy allows thirty days.", encoding="utf-8")
    registry = ToolRegistry()
    register_rag_tools(registry, ChromaStore(tmp_path / "chroma"))
    assert registry.execute("rag.index_directory", {"directory": str(documents)}) == {"processed": 1, "skipped": 0}
    results = registry.execute("rag.search_similar", {"query": "cancellation", "top_k": 1})
    assert len(results["results"]) == 1
