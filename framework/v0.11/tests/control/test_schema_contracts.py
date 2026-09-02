from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[2]
SCHEMAS = ROOT / "schemas" / "control"


def load(name):
    return yaml.safe_load((SCHEMAS / name).read_text())


def test_all_control_schemas_parse_and_have_identity():
    files = sorted(SCHEMAS.glob("*.yaml"))
    assert len(files) == 7
    for path in files:
        data = yaml.safe_load(path.read_text())
        assert data["schema_id"].startswith("FRAMEWORK_")
        assert data["schema_version"] == 0.1
        assert data["type"] == "object"
        assert isinstance(data["required"], list)


def test_workflow_schema_matches_reference_mapping_representation():
    data = load("workflow.schema.yaml")
    assert data["representation"]["states"] == "mapping_by_state_id"
    assert data["representation"]["actions"] == "mapping_by_action_id"
    assert data["properties"]["canonical_input_schema"]["required"] == ["id", "version"]
    assert data["properties"]["output_contract"]["required"] == ["id", "version", "artifact_validator_reference"]


def test_permit_and_receipt_bind_canonical_commit():
    permit = load("execution_permit.schema.yaml")
    receipt = load("receipt.schema.yaml")
    assert "canonical_commit_id" in permit["required"]
    assert "canonical_commit_id" in receipt["required"]
    assert "permit_id" in receipt["required"]
    assert "output_digest" in receipt["required"]


def test_artifact_provenance_schema_records_output_validation():
    data = load("artifact_provenance.schema.yaml")
    assert "artifact_validator_reference" in data["required"]
    assert "artifact_validation_status" in data["required"]


def test_workflow_action_schema_does_not_duplicate_authority_source_of_truth():
    data = load("workflow.schema.yaml")
    required = data["properties"]["actions"]["additional_properties"]["required"]
    assert "authority_effect" not in required
    assert "failure_transition" not in required
    assert "success_transition" in required
