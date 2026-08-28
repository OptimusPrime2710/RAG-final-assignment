from pathlib import Path

from rag_framework.tools.chroma import ChromaStore
from rag_framework.tools.document import index_directory


QUERY = "Users are being forced to authenticate several times during the same work session."


def test_exact_incident_sentence_ranks_first(tmp_path: Path) -> None:
    documents = tmp_path / "documents"
    documents.mkdir()
    (documents / "INC-0005.txt").write_text(
        "INC-0005\nIssue: " + QUERY + "\nResolution: Fixed SSO token renewal.\nStatus: Resolved\n",
        encoding="utf-8",
    )
    (documents / "INC-0153.txt").write_text(
        "INC-0153\nIssue: Inventory count does not change after an order is completed.\n",
        encoding="utf-8",
    )
    store = ChromaStore(tmp_path / "chroma")
    index_directory(documents, store)
    results = store.search_similar(QUERY, top_k=5)
    assert results[0]["metadata"]["path"].endswith("INC-0005.txt")
    assert QUERY.lower() in results[0]["text"].lower()
