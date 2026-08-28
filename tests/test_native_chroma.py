from typing import Any

from rag_framework.tools.chroma import NativeChromaStore


class FakeCollection:
    def __init__(self) -> None:
        self.records: dict[str, dict[str, Any]] = {}

    def upsert(self, ids, documents, metadatas, embeddings) -> None:
        self.records[ids[0]] = {"text": documents[0], "metadata": metadatas[0], "embedding": embeddings[0]}

    def query(self, query_embeddings, n_results):
        identifiers = list(self.records)[:n_results]
        return {
            "ids": [identifiers],
            "documents": [[self.records[identifier]["text"] for identifier in identifiers]],
            "metadatas": [[self.records[identifier]["metadata"] for identifier in identifiers]],
            "distances": [[0.1 for _ in identifiers]],
        }

    def count(self):
        return len(self.records)


class FakeClient:
    def __init__(self) -> None:
        self.collection = FakeCollection()

    def get_or_create_collection(self, name):
        return self.collection


def test_native_chroma_backend_uses_persistent_client_shape() -> None:
    store = NativeChromaStore(client=FakeClient())
    store.store_embedding("doc-1", "policy", {"path": "policy.md"})
    assert store.search_similar("policy", 1)[0]["document_id"] == "doc-1"
    assert store.validate_collection() == {"valid": True, "count": 1}
