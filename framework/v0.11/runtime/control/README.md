# Generic Control Reference Runtime

Non-domain-specific reference implementation of the Framework controlled-execution contract.

Host-facing reference operations: `begin_workflow`, `advance`, `inspect_state`.
Canonical-resolution support: `commit_canonical_input`.
Authority validation support: `validate_receipt`, `recover`, `validate_emission_context`.

Reference design rules:

- the controller selects the authoritative next action;
- controlled actions bind an Execution Permit to workflow instance, state revision, canonical commit, and input digest;
- successful authority transitions produce a bound Receipt;
- direct internal execution can create data but not formal authority;
- formal artifact provenance requires controller-validated current final authority.

This code is subordinate to `01_CANONICAL_NORMATIVE_SPECIFICATION.md`. It is a reference implementation, not a domain runtime. Domain Bundles provide workflow declarations and executor functions.


## build.003 artifact validation

Emission-authorized workflows declare an `artifact_validator_reference`. The Domain Bundle supplies the validator implementation when constructing the controller. `create_artifact_provenance()` refuses authority unless the controller validates the final artifact against the authoritative result through that declared validator.
