from pathlib import Path

from rag_framework.query_service import NO_RESPONSE, QueryService
from rag_framework.tools.chroma import ChromaStore
from rag_framework.tools.document import index_directory


def make_store(tmp_path: Path) -> ChromaStore:
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "INC-0005.txt").write_text("INC-0005\nIssue: Users are being forced to authenticate several times during the same work session.\n", encoding="utf-8")
    (documents / "INC-0015.txt").write_text("INC-0015\nIssue: Authenticator application stopped generating codes accepted by the service.\n", encoding="utf-8")
    store = ChromaStore(tmp_path / "chroma")
    index_directory(documents, store)
    return store


def test_simple_query_returns_evidence(tmp_path: Path) -> None:
    result = QueryService(make_store(tmp_path)).execute("Users are being forced to authenticate several times during the same work session.")
    assert result["status"] == "success"
    assert result["results"][0]["metadata"]["path"].endswith("INC-0005.txt")


def test_missing_evidence_returns_no_response(tmp_path: Path) -> None:
    result = QueryService(make_store(tmp_path)).execute("What is the issue with INC-9999?")
    assert result == {"status": "no_response", "answer": NO_RESPONSE, "results": []}


def test_complex_query_computes_from_anchored_retrieval(tmp_path: Path) -> None:
    result = QueryService(make_store(tmp_path)).execute("What is the average word count in the top 5 documents similar to INC-0005?", top_k=5)
    assert result["status"] == "success"
    assert result["answer"]["document_ids"]
    assert "average_word_count" in result["answer"]
    assert all("INC-0005" not in identifier for identifier in result["answer"]["document_ids"])
