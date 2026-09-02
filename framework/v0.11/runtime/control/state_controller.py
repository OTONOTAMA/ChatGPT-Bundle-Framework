"""Domain-independent reference State Controller for ChatGPT Bundle Framework.

This module demonstrates authority-controlled orchestration only. It contains no
domain-specific algorithm or workflow semantics.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Callable, Dict, Optional
import hashlib
import json
import uuid

CONTROL_MODES = {"DELIBERATIVE", "CONSTRAINED_REASONING", "CONTROLLED_EXECUTION"}
AUTHORITY_CLASSES = {"NON_AUTHORITATIVE", "CANDIDATE", "AUTHORITATIVE", "EMISSION_AUTHORIZED"}
STATE_STATUSES = {"ACTIVE", "WAITING_FOR_RESOLUTION", "BLOCKED", "FAILED", "COMPLETED", "CANCELLED"}
PERMIT_STATUSES = {"ISSUED", "CONSUMED", "INVALIDATED"}
CONTROLLER_ID = "FRAMEWORK_REFERENCE_STATE_CONTROLLER"


class ControlError(Exception):
    pass


class InvalidTransition(ControlError):
    pass


class AuthorityError(ControlError):
    pass


class ResolutionRequired(ControlError):
    pass


def stable_digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


@dataclass
class WorkflowState:
    workflow_instance_id: str
    workflow_id: str
    workflow_version: str
    state_revision: int
    current_state_id: str
    current_control_mode: str
    authority_class: str
    status: str = "ACTIVE"
    canonical_commit_id: Optional[str] = None
    last_receipt_id: Optional[str] = None
    pending_resolution_request_id: Optional[str] = None


@dataclass
class ExecutionPermit:
    permit_id: str
    workflow_instance_id: str
    action_id: str
    expected_state_revision: int
    canonical_commit_id: str
    input_digest: str
    issued_by_controller: str = CONTROLLER_ID
    permit_status: str = "ISSUED"


@dataclass
class Receipt:
    receipt_id: str
    workflow_instance_id: str
    workflow_id: str
    workflow_version: str
    action_id: str
    permit_id: str
    canonical_commit_id: str
    previous_state_id: str
    previous_state_revision: int
    result_state_id: str
    input_digest: str
    status: str
    authority_before: str
    authority_after: str
    output_digest: Optional[str] = None


class StateController:
    """Small reference controller. Domain Bundles supply declarations and executors."""

    def __init__(
        self,
        workflow: Dict[str, Any],
        executors: Dict[str, Callable[[Any], Any]],
        artifact_validators: Optional[Dict[str, Callable[[Any, Any], bool]]] = None,
    ):
        self.workflow = workflow
        self.executors = executors
        self.artifact_validators = artifact_validators or {}
        self._states: Dict[str, WorkflowState] = {}
        self._permits: Dict[str, ExecutionPermit] = {}
        self._receipts: Dict[str, Receipt] = {}
        self._canonical_inputs: Dict[str, Dict[str, Any]] = {}
        self._validate_workflow()

    # ---------- public host-facing reference surface ----------

    def begin_workflow(self, initial_runtime_input: Dict[str, Any]) -> Dict[str, Any]:
        instance_id = "wf_" + uuid.uuid4().hex
        initial_id = self.workflow["initial_state"]
        decl = self.workflow["states"][initial_id]
        state = WorkflowState(
            workflow_instance_id=instance_id,
            workflow_id=self.workflow["workflow_id"],
            workflow_version=self.workflow["workflow_version"],
            state_revision=0,
            current_state_id=initial_id,
            current_control_mode=decl["control_mode"],
            authority_class=decl["authority_class"],
        )
        self._states[instance_id] = state
        self._canonical_inputs[instance_id] = self._new_commit(instance_id, initial_runtime_input, "RESOLVED")
        state.canonical_commit_id = self._canonical_inputs[instance_id]["commit_id"]
        return self.inspect_state(instance_id)

    def advance(self, workflow_instance_id: str, requested_payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        state = self._state(workflow_instance_id)
        action_id = self._next_action(state)
        if action_id is None:
            return {"result": "WORKFLOW_COMPLETED", **self.inspect_state(workflow_instance_id)}

        action = self.workflow["actions"][action_id]
        if state.current_control_mode != action["allowed_control_mode"]:
            raise InvalidTransition("action is not allowed in current control mode")

        canonical = self._canonical_inputs[workflow_instance_id]
        if canonical["resolution_status"] != "RESOLVED" and action.get("requires_resolved_input", True):
            state.status = "WAITING_FOR_RESOLUTION"
            if not state.pending_resolution_request_id:
                state.pending_resolution_request_id = "resolve_" + uuid.uuid4().hex
            return {
                "result": "RESOLUTION_REQUIRED",
                "resolution_request_id": state.pending_resolution_request_id,
                **self.inspect_state(workflow_instance_id),
            }

        if requested_payload is not None:
            raise ControlError("reference ADVANCE does not accept free-form requested payload")

        permit = self._issue_permit(state, action_id, canonical)
        executor_ref = action["executor_reference"]
        before = state.authority_class
        previous_state_id = state.current_state_id
        previous_revision = state.state_revision

        try:
            result = self.executors[executor_ref](canonical["payload"])
        except Exception:
            permit.permit_status = "INVALIDATED"
            raise

        # Recheck the permit immediately before authority changes. This protects
        # against stale state/input if execution orchestration is later extended.
        if not self._permit_matches_execution(permit, state, action_id, canonical, previous_revision):
            permit.permit_status = "INVALIDATED"
            raise AuthorityError("execution permit became stale before completion")

        permit.permit_status = "CONSUMED"
        target = action["success_transition"]
        target_decl = self.workflow["states"][target]
        state.current_state_id = target
        state.current_control_mode = target_decl["control_mode"]
        state.authority_class = target_decl["authority_class"]
        state.state_revision += 1
        state.status = "COMPLETED" if target_decl.get("terminal", False) else "ACTIVE"

        receipt = Receipt(
            receipt_id="rcpt_" + uuid.uuid4().hex,
            workflow_instance_id=workflow_instance_id,
            workflow_id=state.workflow_id,
            workflow_version=state.workflow_version,
            action_id=action_id,
            permit_id=permit.permit_id,
            canonical_commit_id=canonical["commit_id"],
            previous_state_id=previous_state_id,
            previous_state_revision=previous_revision,
            result_state_id=target,
            input_digest=canonical["input_digest"],
            status="PASS",
            authority_before=before,
            authority_after=state.authority_class,
            output_digest=stable_digest(result),
        )
        self._receipts[receipt.receipt_id] = receipt
        state.last_receipt_id = receipt.receipt_id
        return {
            "result": "ACTION_COMPLETED",
            "action_id": action_id,
            "receipt": asdict(receipt),
            "output": result,
            **self.inspect_state(workflow_instance_id),
        }

    def inspect_state(self, workflow_instance_id: str) -> Dict[str, Any]:
        state = self._state(workflow_instance_id)
        last = None
        if state.last_receipt_id and self.validate_receipt(state.last_receipt_id):
            last = asdict(self._receipts[state.last_receipt_id])
        return {
            "current_state": asdict(state),
            "canonical_input": dict(self._canonical_inputs[workflow_instance_id]),
            "last_valid_receipt": last,
            "next_controller_status": self._next_status(state),
        }

    # ---------- explicit canonical-resolution surface ----------

    def commit_canonical_input(
        self,
        workflow_instance_id: str,
        payload: Dict[str, Any],
        resolution_status: str = "RESOLVED",
    ) -> Dict[str, Any]:
        if resolution_status not in {"RESOLVED", "PARTIALLY_RESOLVED", "UNRESOLVED"}:
            raise ControlError("invalid resolution_status")
        state = self._state(workflow_instance_id)

        # A new canonical commit is a new authority boundary. Any progressed
        # downstream authority is conservatively reset and all outstanding permits
        # for this workflow are invalidated.
        if state.current_state_id != self.workflow["initial_state"]:
            self._reset_to_initial_authority(state)
        self._invalidate_issued_permits(workflow_instance_id)

        commit = self._new_commit(workflow_instance_id, payload, resolution_status)
        self._canonical_inputs[workflow_instance_id] = commit
        state.canonical_commit_id = commit["commit_id"]
        state.pending_resolution_request_id = None
        state.last_receipt_id = None
        state.status = "ACTIVE" if resolution_status == "RESOLVED" else "WAITING_FOR_RESOLUTION"
        state.state_revision += 1
        return dict(commit)

    # ---------- validation/recovery/authority helpers ----------

    def validate_receipt(self, receipt_id: str) -> bool:
        receipt = self._receipts.get(receipt_id)
        if receipt is None or receipt.status != "PASS" or not receipt.output_digest:
            return False

        state = self._states.get(receipt.workflow_instance_id)
        canonical = self._canonical_inputs.get(receipt.workflow_instance_id)
        permit = self._permits.get(receipt.permit_id)
        if state is None or canonical is None or permit is None:
            return False
        if receipt.workflow_id != state.workflow_id or receipt.workflow_version != state.workflow_version:
            return False
        if receipt.canonical_commit_id != canonical["commit_id"]:
            return False
        if receipt.input_digest != canonical["input_digest"]:
            return False
        if permit.permit_status != "CONSUMED" or permit.issued_by_controller != CONTROLLER_ID:
            return False
        if permit.workflow_instance_id != receipt.workflow_instance_id or permit.action_id != receipt.action_id:
            return False
        if permit.expected_state_revision != receipt.previous_state_revision:
            return False
        if permit.canonical_commit_id != receipt.canonical_commit_id or permit.input_digest != receipt.input_digest:
            return False
        if receipt.previous_state_id not in self.workflow["states"] or receipt.result_state_id not in self.workflow["states"]:
            return False
        action = self.workflow["actions"].get(receipt.action_id)
        if action is None or not action.get("receipt_required", False):
            return False
        if action["success_transition"] != receipt.result_state_id:
            return False
        if not self._declared_transition_exists(receipt.previous_state_id, receipt.action_id, receipt.result_state_id):
            return False
        if receipt.authority_before != self.workflow["states"][receipt.previous_state_id]["authority_class"]:
            return False
        if receipt.authority_after != self.workflow["states"][receipt.result_state_id]["authority_class"]:
            return False
        if receipt.previous_state_revision >= state.state_revision:
            return False
        return True

    def recover(self, workflow_instance_id: str) -> Dict[str, Any]:
        state = self._state(workflow_instance_id)
        valid = [
            r for r in self._receipts.values()
            if r.workflow_instance_id == workflow_instance_id and self.validate_receipt(r.receipt_id)
        ]
        valid.sort(key=lambda r: r.previous_state_revision)
        return {
            "workflow_instance_id": workflow_instance_id,
            "valid_receipt_ids": [r.receipt_id for r in valid],
            "current_state": asdict(state),
            "next_controller_status": self._next_status(state),
        }

    def validate_emission_context(
        self,
        workflow_instance_id: str,
        final_receipt_id: str,
        authoritative_result: Any,
    ) -> Dict[str, Any]:
        state = self._state(workflow_instance_id)
        receipt = self._receipts.get(final_receipt_id)
        if receipt is None or not self.validate_receipt(final_receipt_id):
            raise AuthorityError("final receipt is not valid authority evidence")
        current_decl = self.workflow["states"][state.current_state_id]
        if not current_decl.get("terminal", False):
            raise AuthorityError("workflow is not in a terminal state")
        if state.authority_class != "EMISSION_AUTHORIZED":
            raise AuthorityError("workflow is not emission authorized")
        if state.last_receipt_id != final_receipt_id:
            raise AuthorityError("final receipt is not the workflow's current final receipt")
        if receipt.result_state_id != state.current_state_id or receipt.authority_after != state.authority_class:
            raise AuthorityError("final receipt does not bind the current authoritative state")
        if stable_digest(authoritative_result) != receipt.output_digest:
            raise AuthorityError("authoritative result does not match final receipt output digest")

        condition = self.workflow["final_authority_condition"]
        if condition.get("authority_class") and condition["authority_class"] != state.authority_class:
            raise AuthorityError("declared final authority condition is not satisfied")
        if condition.get("terminal") is True and not current_decl.get("terminal", False):
            raise AuthorityError("declared final terminal condition is not satisfied")
        return {"state": asdict(state), "receipt": asdict(receipt)}

    def validate_artifact_contract(self, artifact: Any, authoritative_result: Any) -> Dict[str, Any]:
        """Validate final artifact content through the Domain Bundle-declared validator."""
        declared = self.workflow["output_contract"]
        validator_ref = declared.get("artifact_validator_reference")
        if not validator_ref:
            raise AuthorityError("output contract does not declare an artifact validator")
        validator = self.artifact_validators.get(validator_ref)
        if validator is None:
            raise AuthorityError("declared artifact validator is unavailable")
        try:
            valid = validator(artifact, authoritative_result)
        except Exception as exc:
            raise AuthorityError("artifact validator failed") from exc
        if valid is not True:
            raise AuthorityError("artifact does not satisfy the declared output contract")
        return {"validator_reference": validator_ref, "status": "PASS"}

    def execute_internal_without_permit(self, workflow_instance_id: str, executor_reference: str) -> Dict[str, Any]:
        """Direct internal execution can create data but cannot create authority."""
        if executor_reference not in self.executors:
            raise ControlError(f"executor unavailable: {executor_reference}")
        canonical = self._canonical_inputs[workflow_instance_id]
        result = self.executors[executor_reference](canonical["payload"])
        return {"authority": "NON_AUTHORITATIVE", "output": result, "output_digest": stable_digest(result)}

    def get_permit(self, permit_id: str) -> Optional[Dict[str, Any]]:
        permit = self._permits.get(permit_id)
        return asdict(permit) if permit else None

    def get_receipt(self, receipt_id: str) -> Optional[Dict[str, Any]]:
        receipt = self._receipts.get(receipt_id)
        return asdict(receipt) if receipt else None

    # ---------- internal mechanics ----------

    def _validate_workflow(self) -> None:
        required = (
            "workflow_id", "workflow_version", "initial_state", "states", "actions", "transitions",
            "canonical_input_schema", "entry_action", "final_authority_condition", "output_contract",
        )
        for key in required:
            if key not in self.workflow:
                raise ControlError(f"missing workflow field: {key}")
        if not isinstance(self.workflow["states"], dict) or not self.workflow["states"]:
            raise ControlError("states must be a non-empty mapping")
        if not isinstance(self.workflow["actions"], dict) or not self.workflow["actions"]:
            raise ControlError("actions must be a non-empty mapping")
        if not isinstance(self.workflow["transitions"], list):
            raise ControlError("transitions must be a list")
        if self.workflow["initial_state"] not in self.workflow["states"]:
            raise ControlError("initial_state does not resolve")
        if self.workflow["entry_action"] not in self.workflow["actions"]:
            raise ControlError("entry_action does not resolve")
        if not isinstance(self.workflow["canonical_input_schema"], dict):
            raise ControlError("canonical_input_schema must declare id and version")
        if not {"id", "version"}.issubset(self.workflow["canonical_input_schema"]):
            raise ControlError("canonical_input_schema missing id/version")
        if not isinstance(self.workflow["output_contract"], dict) or not {"id", "version"}.issubset(self.workflow["output_contract"]):
            raise ControlError("output_contract must declare id and version")
        emission_used = (
            self.workflow.get("final_authority_condition", {}).get("authority_class") == "EMISSION_AUTHORIZED"
            or any(st.get("authority_class") == "EMISSION_AUTHORIZED" for st in self.workflow["states"].values())
        )
        if emission_used:
            validator_ref = self.workflow["output_contract"].get("artifact_validator_reference")
            if not isinstance(validator_ref, str) or not validator_ref:
                raise ControlError("emission-authorized workflow output_contract must declare artifact_validator_reference")
        if not isinstance(self.workflow["final_authority_condition"], dict):
            raise ControlError("final_authority_condition must be an object")

        for state_id, state in self.workflow["states"].items():
            for key in ("control_mode", "authority_class", "terminal"):
                if key not in state:
                    raise ControlError(f"state {state_id} missing {key}")
            if state["control_mode"] not in CONTROL_MODES:
                raise ControlError(f"invalid control mode: {state_id}")
            if state["authority_class"] not in AUTHORITY_CLASSES:
                raise ControlError(f"invalid authority class: {state_id}")
            if not isinstance(state["terminal"], bool):
                raise ControlError(f"terminal must be boolean: {state_id}")

        for action_id, action in self.workflow["actions"].items():
            for key in (
                "allowed_control_mode", "executor_reference", "receipt_required", "success_transition",
            ):
                if key not in action:
                    raise ControlError(f"action {action_id} missing {key}")
            if action["allowed_control_mode"] not in CONTROL_MODES:
                raise ControlError(f"invalid action control mode: {action_id}")
            if action["success_transition"] not in self.workflow["states"]:
                raise ControlError(f"action success transition target does not resolve: {action_id}")
            if "failure_transition" in action and action["failure_transition"] not in self.workflow["states"]:
                raise ControlError(f"action failure transition target does not resolve: {action_id}")
            if action["executor_reference"] not in self.executors:
                raise ControlError(f"executor unavailable: {action['executor_reference']}")
            if action["receipt_required"] is not True:
                raise ControlError(f"reference controlled action must require receipt: {action_id}")

        seen = set()
        transitions_by_state: Dict[str, list] = {sid: [] for sid in self.workflow["states"]}
        for t in self.workflow["transitions"]:
            for key in ("from_state", "action_id", "to_state"):
                if key not in t:
                    raise ControlError(f"transition missing {key}")
            if t["from_state"] not in self.workflow["states"] or t["to_state"] not in self.workflow["states"]:
                raise ControlError("transition state does not resolve")
            if t["action_id"] not in self.workflow["actions"]:
                raise ControlError("transition action does not resolve")
            signature = (t["from_state"], t["action_id"], t["to_state"])
            if signature in seen:
                raise ControlError("duplicate transition")
            seen.add(signature)
            if self.workflow["actions"][t["action_id"]]["success_transition"] != t["to_state"]:
                raise ControlError("transition target disagrees with action success_transition")
            transitions_by_state[t["from_state"]].append(t)

        for state_id, state in self.workflow["states"].items():
            count = len(transitions_by_state[state_id])
            if state["terminal"] and count != 0:
                raise ControlError(f"terminal state has outgoing transition: {state_id}")
            if not state["terminal"] and count != 1:
                raise ControlError(f"reference controller requires exactly one outgoing transition from {state_id}; found {count}")

        initial_transitions = transitions_by_state[self.workflow["initial_state"]]
        if initial_transitions[0]["action_id"] != self.workflow["entry_action"]:
            raise ControlError("entry_action does not match initial authoritative transition")

    def _new_commit(self, workflow_instance_id: str, payload: Dict[str, Any], resolution_status: str) -> Dict[str, Any]:
        schema = self.workflow["canonical_input_schema"]
        return {
            "commit_id": "commit_" + uuid.uuid4().hex,
            "workflow_instance_id": workflow_instance_id,
            "schema_id": schema["id"],
            "schema_version": str(schema["version"]),
            "payload": payload,
            "resolved_payload": payload,
            "input_digest": stable_digest(payload),
            "resolution_status": resolution_status,
        }

    def _issue_permit(self, state: WorkflowState, action_id: str, canonical: Dict[str, Any]) -> ExecutionPermit:
        permit = ExecutionPermit(
            permit_id="permit_" + uuid.uuid4().hex,
            workflow_instance_id=state.workflow_instance_id,
            action_id=action_id,
            expected_state_revision=state.state_revision,
            canonical_commit_id=canonical["commit_id"],
            input_digest=canonical["input_digest"],
        )
        self._permits[permit.permit_id] = permit
        return permit

    def _permit_matches_execution(
        self,
        permit: ExecutionPermit,
        state: WorkflowState,
        action_id: str,
        canonical: Dict[str, Any],
        previous_revision: int,
    ) -> bool:
        return (
            permit.permit_status == "ISSUED"
            and permit.issued_by_controller == CONTROLLER_ID
            and permit.workflow_instance_id == state.workflow_instance_id
            and permit.action_id == action_id
            and permit.expected_state_revision == previous_revision == state.state_revision
            and permit.canonical_commit_id == canonical["commit_id"] == state.canonical_commit_id
            and permit.input_digest == canonical["input_digest"]
        )

    def _reset_to_initial_authority(self, state: WorkflowState) -> None:
        initial_id = self.workflow["initial_state"]
        initial_decl = self.workflow["states"][initial_id]
        state.current_state_id = initial_id
        state.current_control_mode = initial_decl["control_mode"]
        state.authority_class = initial_decl["authority_class"]
        state.status = "ACTIVE"
        state.last_receipt_id = None

    def _invalidate_issued_permits(self, workflow_instance_id: str) -> None:
        for permit in self._permits.values():
            if permit.workflow_instance_id == workflow_instance_id and permit.permit_status == "ISSUED":
                permit.permit_status = "INVALIDATED"

    def _declared_transition_exists(self, from_state: str, action_id: str, to_state: str) -> bool:
        return any(
            t["from_state"] == from_state and t["action_id"] == action_id and t["to_state"] == to_state
            for t in self.workflow["transitions"]
        )

    def _state(self, workflow_instance_id: str) -> WorkflowState:
        if workflow_instance_id not in self._states:
            raise ControlError("unknown workflow instance")
        return self._states[workflow_instance_id]

    def _next_action(self, state: WorkflowState) -> Optional[str]:
        if self.workflow["states"][state.current_state_id].get("terminal", False):
            return None
        candidates = [t for t in self.workflow["transitions"] if t["from_state"] == state.current_state_id]
        if len(candidates) != 1:
            raise InvalidTransition(f"reference controller requires exactly one authoritative next transition; found {len(candidates)}")
        return candidates[0]["action_id"]

    def _next_status(self, state: WorkflowState) -> str:
        if state.status == "WAITING_FOR_RESOLUTION":
            return "RESOLUTION_REQUIRED"
        if self.workflow["states"][state.current_state_id].get("terminal", False):
            return "WORKFLOW_COMPLETED"
        return "ADVANCE_AVAILABLE"
