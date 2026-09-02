import copy
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from runtime.control.state_controller import (
    StateController,
    ControlError,
    AuthorityError,
)
from runtime.control.provenance import create_artifact_provenance


def executor_a(payload):
    return {"step": "A", "seen": payload["value"]}


def executor_b(payload):
    return {"step": "B", "seen": payload["value"]}


def failing_executor(payload):
    raise RuntimeError("synthetic executor failure")


def artifact_validator(artifact, authoritative_result):
    return artifact == {"authoritative_result": authoritative_result}


def workflow():
    return {
        "workflow_id": "GENERIC_TEST_WORKFLOW",
        "workflow_version": "1",
        "initial_state": "S0",
        "canonical_input_schema": {"id": "GENERIC_INPUT", "version": "1"},
        "entry_action": "A1",
        "final_authority_condition": {"authority_class": "EMISSION_AUTHORIZED", "terminal": True},
        "output_contract": {"id": "GENERIC_OUTPUT", "version": "1", "artifact_validator_reference": "V1"},
        "states": {
            "S0": {"control_mode": "CONTROLLED_EXECUTION", "authority_class": "CANDIDATE", "terminal": False},
            "S1": {"control_mode": "CONTROLLED_EXECUTION", "authority_class": "AUTHORITATIVE", "terminal": False},
            "S2": {"control_mode": "DELIBERATIVE", "authority_class": "EMISSION_AUTHORIZED", "terminal": True},
        },
        "actions": {
            "A1": {
                "allowed_control_mode": "CONTROLLED_EXECUTION",
                "executor_reference": "E1",
                "receipt_required": True,
                "authority_effect": "PROMOTE",
                "success_transition": "S1",
                "failure_transition": "S0",
            },
            "A2": {
                "allowed_control_mode": "CONTROLLED_EXECUTION",
                "executor_reference": "E2",
                "receipt_required": True,
                "authority_effect": "PROMOTE",
                "success_transition": "S2",
                "failure_transition": "S1",
            },
        },
        "transitions": [
            {"from_state": "S0", "action_id": "A1", "to_state": "S1"},
            {"from_state": "S1", "action_id": "A2", "to_state": "S2"},
        ],
    }


def make_controller(executors=None, validators=None):
    return StateController(
        workflow(),
        executors or {"E1": executor_a, "E2": executor_b},
        validators if validators is not None else {"V1": artifact_validator},
    )


def assert_raises(exc, fn):
    try:
        fn()
    except exc:
        return
    raise AssertionError(f"expected {exc.__name__}")


def test_happy_path_controller_selects_next_action():
    c = make_controller()
    s = c.begin_workflow({"value": 7})
    wid = s["current_state"]["workflow_instance_id"]
    r1 = c.advance(wid)
    assert r1["action_id"] == "A1"
    assert r1["receipt"]["authority_after"] == "AUTHORITATIVE"
    assert c.validate_receipt(r1["receipt"]["receipt_id"]) is True
    r2 = c.advance(wid)
    assert r2["action_id"] == "A2"
    assert r2["current_state"]["authority_class"] == "EMISSION_AUTHORIZED"
    assert r2["current_state"]["status"] == "COMPLETED"
    assert c.validate_receipt(r2["receipt"]["receipt_id"]) is True


def test_direct_internal_execution_is_non_authoritative():
    c = make_controller()
    s = c.begin_workflow({"value": 9})
    wid = s["current_state"]["workflow_instance_id"]
    before = c.inspect_state(wid)["current_state"].copy()
    result = c.execute_internal_without_permit(wid, "E1")
    after = c.inspect_state(wid)["current_state"]
    assert result["authority"] == "NON_AUTHORITATIVE"
    assert before == after
    assert after["last_receipt_id"] is None


def test_unrequested_payload_rejected():
    c = make_controller()
    wid = c.begin_workflow({"value": 2})["current_state"]["workflow_instance_id"]
    assert_raises(ControlError, lambda: c.advance(wid, requested_payload={"override": True}))
    assert c.inspect_state(wid)["current_state"]["current_state_id"] == "S0"


def test_permit_is_consumed_and_bound_to_receipt_and_commit():
    c = make_controller()
    wid = c.begin_workflow({"value": 1})["current_state"]["workflow_instance_id"]
    r = c.advance(wid)
    permit = c.get_permit(r["receipt"]["permit_id"])
    assert permit["permit_status"] == "CONSUMED"
    assert permit["canonical_commit_id"] == r["receipt"]["canonical_commit_id"]
    assert permit["input_digest"] == r["receipt"]["input_digest"]


def test_unresolved_input_pauses_authority_and_reuses_pending_request():
    c = make_controller()
    wid = c.begin_workflow({"value": 5})["current_state"]["workflow_instance_id"]
    c.commit_canonical_input(wid, {"value": None}, resolution_status="UNRESOLVED")
    r1 = c.advance(wid)
    r2 = c.advance(wid)
    assert r1["result"] == "RESOLUTION_REQUIRED"
    assert r1["resolution_request_id"] == r2["resolution_request_id"]
    assert r1["current_state"]["authority_class"] == "CANDIDATE"
    assert r1["current_state"]["last_receipt_id"] is None


def test_resolved_commit_clears_waiting_state_and_allows_advance():
    c = make_controller()
    wid = c.begin_workflow({"value": 5})["current_state"]["workflow_instance_id"]
    c.commit_canonical_input(wid, {"value": None}, resolution_status="UNRESOLVED")
    c.advance(wid)
    c.commit_canonical_input(wid, {"value": 5}, resolution_status="RESOLVED")
    state = c.inspect_state(wid)
    assert state["current_state"]["status"] == "ACTIVE"
    assert state["current_state"]["pending_resolution_request_id"] is None
    assert state["next_controller_status"] == "ADVANCE_AVAILABLE"
    assert c.advance(wid)["action_id"] == "A1"


def test_terminal_advance_does_not_invent_action():
    c = make_controller()
    wid = c.begin_workflow({"value": 3})["current_state"]["workflow_instance_id"]
    c.advance(wid)
    c.advance(wid)
    r = c.advance(wid)
    assert r["result"] == "WORKFLOW_COMPLETED"


def test_new_canonical_commit_invalidates_prior_authority_and_receipt_even_same_payload():
    c = make_controller()
    wid = c.begin_workflow({"value": 10})["current_state"]["workflow_instance_id"]
    r1 = c.advance(wid)
    old_receipt = r1["receipt"]["receipt_id"]
    assert c.validate_receipt(old_receipt) is True
    c.commit_canonical_input(wid, {"value": 10}, resolution_status="RESOLVED")
    state = c.inspect_state(wid)["current_state"]
    assert state["current_state_id"] == "S0"
    assert state["authority_class"] == "CANDIDATE"
    assert state["last_receipt_id"] is None
    assert c.validate_receipt(old_receipt) is False


def test_recover_reports_only_receipts_matching_current_commit():
    c = make_controller()
    wid = c.begin_workflow({"value": 4})["current_state"]["workflow_instance_id"]
    r1 = c.advance(wid)
    receipt_id = r1["receipt"]["receipt_id"]
    assert receipt_id in c.recover(wid)["valid_receipt_ids"]
    c.commit_canonical_input(wid, {"value": 99})
    assert receipt_id not in c.recover(wid)["valid_receipt_ids"]


def test_executor_failure_does_not_advance_or_create_receipt_and_invalidates_permit():
    c = make_controller({"E1": failing_executor, "E2": executor_b})
    wid = c.begin_workflow({"value": 4})["current_state"]["workflow_instance_id"]
    assert_raises(RuntimeError, lambda: c.advance(wid))
    state = c.inspect_state(wid)["current_state"]
    assert state["current_state_id"] == "S0"
    assert state["last_receipt_id"] is None
    assert len(c._permits) == 1
    permit = next(iter(c._permits.values()))
    assert permit.permit_status == "INVALIDATED"
    assert len(c._receipts) == 0


def test_state_change_during_executor_makes_permit_stale_and_blocks_authority():
    c = make_controller()
    wid = c.begin_workflow({"value": 4})["current_state"]["workflow_instance_id"]

    def mutating_executor(payload):
        c._states[wid].state_revision += 1
        return {"step": "mutated"}

    c.executors["E1"] = mutating_executor
    assert_raises(AuthorityError, lambda: c.advance(wid))
    assert c.inspect_state(wid)["current_state"]["current_state_id"] == "S0"
    assert len(c._receipts) == 0
    assert next(iter(c._permits.values())).permit_status == "INVALIDATED"


def test_tampered_receipt_is_not_reported_as_valid():
    c = make_controller()
    wid = c.begin_workflow({"value": 4})["current_state"]["workflow_instance_id"]
    r = c.advance(wid)
    rid = r["receipt"]["receipt_id"]
    c._receipts[rid].input_digest = "sha256:tampered"
    assert c.validate_receipt(rid) is False
    assert c.inspect_state(wid)["last_valid_receipt"] is None


def test_tampered_permit_invalidates_bound_receipt():
    c = make_controller()
    wid = c.begin_workflow({"value": 4})["current_state"]["workflow_instance_id"]
    r = c.advance(wid)
    rid = r["receipt"]["receipt_id"]
    pid = r["receipt"]["permit_id"]
    c._permits[pid].permit_status = "INVALIDATED"
    assert c.validate_receipt(rid) is False
    assert c.inspect_state(wid)["last_valid_receipt"] is None


def test_artifact_provenance_requires_emission_authority():
    c = make_controller()
    wid = c.begin_workflow({"value": 8})["current_state"]["workflow_instance_id"]
    r1 = c.advance(wid)
    assert_raises(
        AuthorityError,
        lambda: create_artifact_provenance(
            controller=c,
            workflow_instance_id=wid,
            final_receipt_id=r1["receipt"]["receipt_id"],
            artifact={"text": "x"},
            output_contract_id="GENERIC_OUTPUT",
            output_contract_version="1",
            authoritative_result=r1["output"],
        ),
    )


def test_artifact_provenance_rejects_wrong_authoritative_result():
    c = make_controller()
    wid = c.begin_workflow({"value": 8})["current_state"]["workflow_instance_id"]
    c.advance(wid)
    r2 = c.advance(wid)
    assert_raises(
        AuthorityError,
        lambda: create_artifact_provenance(
            controller=c,
            workflow_instance_id=wid,
            final_receipt_id=r2["receipt"]["receipt_id"],
            artifact={"authoritative_result": r2["output"]},
            output_contract_id="GENERIC_OUTPUT",
            output_contract_version="1",
            authoritative_result={"forged": True},
        ),
    )


def test_artifact_provenance_rejects_wrong_output_contract():
    c = make_controller()
    wid = c.begin_workflow({"value": 8})["current_state"]["workflow_instance_id"]
    c.advance(wid)
    r2 = c.advance(wid)
    assert_raises(
        AuthorityError,
        lambda: create_artifact_provenance(
            controller=c,
            workflow_instance_id=wid,
            final_receipt_id=r2["receipt"]["receipt_id"],
            artifact={"authoritative_result": r2["output"]},
            output_contract_id="WRONG_OUTPUT",
            output_contract_version="1",
            authoritative_result=r2["output"],
        ),
    )


def test_artifact_provenance_succeeds_only_for_current_final_receipt_and_result():
    c = make_controller()
    wid = c.begin_workflow({"value": 8})["current_state"]["workflow_instance_id"]
    c.advance(wid)
    r2 = c.advance(wid)
    prov = create_artifact_provenance(
        controller=c,
        workflow_instance_id=wid,
        final_receipt_id=r2["receipt"]["receipt_id"],
        artifact={"authoritative_result": r2["output"]},
        output_contract_id="GENERIC_OUTPUT",
        output_contract_version="1",
        authoritative_result=r2["output"],
    )
    assert prov["authority_status"] == "EMISSION_AUTHORIZED"
    assert prov["finalization_receipt_id"] == r2["receipt"]["receipt_id"]


def test_prior_receipt_cannot_finalize_current_terminal_state():
    c = make_controller()
    wid = c.begin_workflow({"value": 8})["current_state"]["workflow_instance_id"]
    r1 = c.advance(wid)
    r2 = c.advance(wid)
    assert_raises(
        AuthorityError,
        lambda: create_artifact_provenance(
            controller=c,
            workflow_instance_id=wid,
            final_receipt_id=r1["receipt"]["receipt_id"],
            artifact={"authoritative_result": r2["output"]},
            output_contract_id="GENERIC_OUTPUT",
            output_contract_version="1",
            authoritative_result=r2["output"],
        ),
    )


def test_invalid_workflow_missing_required_control_field_rejected():
    w = workflow()
    del w["output_contract"]
    assert_raises(ControlError, lambda: StateController(w, {"E1": executor_a, "E2": executor_b}))


def test_invalid_workflow_ambiguous_next_transition_rejected():
    w = workflow()
    w["transitions"].append({"from_state": "S0", "action_id": "A2", "to_state": "S2"})
    assert_raises(ControlError, lambda: StateController(w, {"E1": executor_a, "E2": executor_b}))


def test_invalid_workflow_entry_action_mismatch_rejected():
    w = workflow()
    w["entry_action"] = "A2"
    assert_raises(ControlError, lambda: StateController(w, {"E1": executor_a, "E2": executor_b}))


def test_invalid_workflow_transition_target_mismatch_rejected():
    w = workflow()
    w["actions"]["A1"]["success_transition"] = "S2"
    assert_raises(ControlError, lambda: StateController(w, {"E1": executor_a, "E2": executor_b}))


def test_invalid_workflow_terminal_outgoing_transition_rejected():
    w = workflow()
    w["transitions"].append({"from_state": "S2", "action_id": "A2", "to_state": "S2"})
    assert_raises(ControlError, lambda: StateController(w, {"E1": executor_a, "E2": executor_b}))


def test_invalid_workflow_missing_executor_rejected_before_execution():
    assert_raises(ControlError, lambda: StateController(workflow(), {"E1": executor_a}))


def test_manual_state_promotion_without_receipt_cannot_create_provenance():
    c = make_controller()
    wid = c.begin_workflow({"value": 6})["current_state"]["workflow_instance_id"]
    # Simulate a host-side/manual attempt to label the workflow final without
    # executing the authorized route. Authority evidence is still absent.
    c._states[wid].current_state_id = "S2"
    c._states[wid].current_control_mode = "DELIBERATIVE"
    c._states[wid].authority_class = "EMISSION_AUTHORIZED"
    c._states[wid].status = "COMPLETED"
    c._states[wid].state_revision += 1
    assert_raises(
        AuthorityError,
        lambda: create_artifact_provenance(
            controller=c,
            workflow_instance_id=wid,
            final_receipt_id="rcpt_manual_claim",
            artifact={"text": "manual"},
            output_contract_id="GENERIC_OUTPUT",
            output_contract_version="1",
            authoritative_result={"step": "manual"},
        ),
    )


def test_artifact_provenance_rejects_artifact_content_mismatch():
    c = make_controller()
    wid = c.begin_workflow({"value": 8})["current_state"]["workflow_instance_id"]
    c.advance(wid)
    r2 = c.advance(wid)
    assert_raises(
        AuthorityError,
        lambda: create_artifact_provenance(
            controller=c,
            workflow_instance_id=wid,
            final_receipt_id=r2["receipt"]["receipt_id"],
            artifact={"authoritative_result": {"forged": True}},
            output_contract_id="GENERIC_OUTPUT",
            output_contract_version="1",
            authoritative_result=r2["output"],
        ),
    )


def test_artifact_provenance_requires_declared_validator_implementation():
    c = make_controller(validators={})
    wid = c.begin_workflow({"value": 8})["current_state"]["workflow_instance_id"]
    c.advance(wid)
    r2 = c.advance(wid)
    assert_raises(
        AuthorityError,
        lambda: create_artifact_provenance(
            controller=c,
            workflow_instance_id=wid,
            final_receipt_id=r2["receipt"]["receipt_id"],
            artifact={"authoritative_result": r2["output"]},
            output_contract_id="GENERIC_OUTPUT",
            output_contract_version="1",
            authoritative_result=r2["output"],
        ),
    )


def test_emission_workflow_missing_artifact_validator_reference_rejected():
    w = workflow()
    del w["output_contract"]["artifact_validator_reference"]
    assert_raises(ControlError, lambda: StateController(w, {"E1": executor_a, "E2": executor_b}, {"V1": artifact_validator}))


def test_minimal_action_contract_uses_target_state_as_authority_source():
    w = workflow()
    for action in w["actions"].values():
        action.pop("authority_effect", None)
        action.pop("failure_transition", None)
    c = StateController(w, {"E1": executor_a, "E2": executor_b}, {"V1": artifact_validator})
    wid = c.begin_workflow({"value": 4})["current_state"]["workflow_instance_id"]
    r1 = c.advance(wid)
    assert r1["receipt"]["authority_after"] == w["states"]["S1"]["authority_class"]
    r2 = c.advance(wid)
    assert r2["receipt"]["authority_after"] == w["states"]["S2"]["authority_class"]
