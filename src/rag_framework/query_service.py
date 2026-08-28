"""Controlled simple and complex business-query execution."""

import re
from typing import Any, Callable

from rag_framework.tools.chroma import ChromaStore


NO_RESPONSE = "No response found"


class QueryService:
    def __init__(self, store: Any, final_model_call: Callable[..., dict[str, Any]] | None = None) -> None:
        self.store = store
        self.final_model_call = final_model_call

    def execute(self, query: str, top_k: int = 5) -> dict[str, Any]:
        retrieval_query = query
        anchor = self._find_document_anchor(query)
        if anchor:
            anchor_matches = [record for record in getattr(self.store, "records", []) if anchor.lower() in record["document_id"].lower()]
            if not anchor_matches:
                return {"status": "no_response", "answer": NO_RESPONSE, "results": []}
            retrieval_query = anchor_matches[0]["text"]
        retrieval = self.store.search_similar(retrieval_query, top_k)
        if anchor:
            retrieval = [item for item in retrieval if anchor.lower() not in item["document_id"].lower()] or retrieval
        if not retrieval:
            return {"status": "no_response", "answer": NO_RESPONSE, "results": []}
        if not self._is_complex(query):
            return {"status": "success", "answer": retrieval[0]["text"], "results": retrieval}
        word_counts = [{"document_id": item["document_id"], "word_count": len(item["text"].split())} for item in retrieval]
        average = sum(item["word_count"] for item in word_counts) / len(word_counts)
        result = {"document_ids": [item["document_id"] for item in retrieval], "word_counts": word_counts, "average_word_count": average}
        if self.final_model_call is not None:
            result["model_answer"] = self.final_model_call({"query": query, "evidence": result})
        return {"status": "success", "answer": result, "results": retrieval}

    @staticmethod
    def _is_complex(query: str) -> bool:
        return bool(re.search(r"\b(average|avg|mean|sum|count|total|calculate|compare)\b", query, re.IGNORECASE))

    @staticmethod
    def _find_document_anchor(query: str) -> str | None:
        match = re.search(r"\bINC[- ]?\d+\b", query, re.IGNORECASE)
        return match.group(0).replace(" ", "-").upper() if match else None
