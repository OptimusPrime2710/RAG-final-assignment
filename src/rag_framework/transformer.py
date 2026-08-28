"""Controlled executor-output transformation."""

from typing import Any


class ContractMappingError(ValueError):
    code = "CONTRACT_MAPPING_FAILED"


def transform_output(output: dict[str, Any], mapping: dict[str, str], required_fields: set[str] | None = None) -> dict[str, Any]:
    transformed = {destination: output[source] for destination, source in mapping.items() if source in output}
    missing = (required_fields or set()) - transformed.keys()
    if missing:
        raise ContractMappingError(f"{ContractMappingError.code}: missing {sorted(missing)}")
    return transformed
