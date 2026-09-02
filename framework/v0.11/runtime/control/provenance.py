"""Generic artifact provenance helper for the Framework reference implementation."""
from __future__ import annotations
from typing import Any, Dict
import uuid

from .state_controller import StateController, stable_digest, AuthorityError


def create_artifact_provenance(
    *,
    controller: StateController,
    workflow_instance_id: str,
    final_receipt_id: str,
    artifact: Any,
    output_contract_id: str,
    output_contract_version: str,
    authoritative_result: Any,
) -> Dict[str, Any]:
    """Create provenance only from controller-validated current final authority."""
    context = controller.validate_emission_context(
        workflow_instance_id=workflow_instance_id,
        final_receipt_id=final_receipt_id,
        authoritative_result=authoritative_result,
    )
    declared = controller.workflow["output_contract"]
    if declared["id"] != output_contract_id or str(declared["version"]) != str(output_contract_version):
        raise AuthorityError("output contract does not match declared workflow contract")
    validation = controller.validate_artifact_contract(artifact, authoritative_result)
    return {
        "artifact_id": "artifact_" + uuid.uuid4().hex,
        "workflow_instance_id": workflow_instance_id,
        "output_contract_id": output_contract_id,
        "output_contract_version": str(output_contract_version),
        "authoritative_result_digest": stable_digest(authoritative_result),
        "finalization_receipt_id": context["receipt"]["receipt_id"],
        "artifact_digest": stable_digest(artifact),
        "artifact_validator_reference": validation["validator_reference"],
        "artifact_validation_status": validation["status"],
        "authority_status": "EMISSION_AUTHORIZED",
    }
