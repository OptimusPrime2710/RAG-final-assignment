import pytest

from rag_framework.transformer import ContractMappingError, transform_output


def test_transformer_maps_only_declared_fields() -> None:
    assert transform_output({"answer": 4, "secret": 9}, {"value": "answer"}, {"value": "answer"}) == {"value": 4}


def test_transformer_reports_mapping_failure() -> None:
    with pytest.raises(ContractMappingError, match="CONTRACT_MAPPING_FAILED"):
        transform_output({}, {"value": "answer"}, {"value"})
