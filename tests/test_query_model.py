from rag_framework.query_service import QueryService


def test_complex_query_sends_only_retrieved_evidence_to_final_model() -> None:
    class Store:
        def search_similar(self, query, top_k):
            return [{"document_id": "INC-1", "text": "Issue: auth failure", "score": 1.0}]

    captured = {}

    def final_model(evidence):
        captured.update(evidence)
        return {"summary": "computed from evidence"}

    result = QueryService(Store(), final_model).execute("What is the average word count?", 5)
    assert result["answer"]["model_answer"] == {"summary": "computed from evidence"}
    assert captured["evidence"]["word_counts"][0]["document_id"] == "INC-1"
