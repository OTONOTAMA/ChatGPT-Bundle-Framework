# ChatGPT Bundle Framework v0.11 — Stable
## Validation Evidence Register

Classification: REFERENCE / VALIDATION EVIDENCE (non-normative)

Canonical semantics remain in `01_CANONICAL_NORMATIVE_SPECIFICATION.md`.

## E-001 — Framework reference control tests

Target: generic Controlled Execution reference implementation.

Result on source Working build.004, qualified RC, and Stable package: **34/34 PASS**.

Coverage includes normal progression, forbidden transitions, Permit/Receipt binding, stale input/Receipt rejection, tamper rejection, recovery, terminal authority, artifact provenance, Artifact Validator enforcement, and schema alignment.

## E-002 — First external fresh-chat Controlled Execution UAT

Artifact: `Synthetic_Number_Summary_Bundle_WORKING_v0.1-build.001.zip`

Result: PASS for the Controlled Execution mechanism. This artifact intentionally did not represent the complete baseline Domain Bundle packaging contract, so its evidence scope is limited to the control mechanism and runtime self-containment.

## E-003 — Full-package synthetic internal validation

Artifact: `Synthetic_Number_Summary_Bundle_WORKING_v0.2-build.001.zip`

Internal result: **25 checks PASS**, including package/lock validation, Bootstrap, formal E2E, Receipt chain, authority, Artifact Validator, adversarial probes, and full-Framework runtime independence.

## E-004 — External fresh-chat Framework build.004 Bootstrap

Reported result on the exact Working build.004 artifact:

- Manifest integrity: **20/20 PASS**.
- Reference control tests: **34/34 PASS**.
- Canonical specification / guidance / schemas / runtime contract loaded.
- Controlled Execution / Permit / Receipt / Provenance rules active.
- Framework self-bootstrap: **PASS**.
- State: `BUNDLE_DEVELOPMENT_READY`.
- Working artifact correctly remained classified as `WORKING_DRAFT`.

## E-005 — External full-package synthetic clean-room UAT

Artifact: `Synthetic_Number_Summary_Bundle_WORKING_v0.2-build.001.zip`

Reported result:

- Declared Manifest / resolved Lock: **PASS**.
- Lock-recorded file size/SHA-256: **14/14 PASS**.
- Source of Truth / Runtime Contract resolution: **PASS**.
- `bootstrap.py`: **PASS / RUNTIME_READY**.
- Formal public-route E2E: **PASS**.
- Three action Receipts: **PASS**.
- Terminal authority: `EMISSION_AUTHORIZED`.
- Artifact Validator: **PASS**.
- Formal provenance: **PASS**.
- Direct internal shortcut remained non-authoritative.
- Altered artifact rejected.
- Stale final Receipt invalidated after canonical input change.
- Adversarial probes: **3/3 PASS**.
- Full Framework runtime dependency: **false**.

The test chat was fresh before its initial Bootstrap; executing the UAT after Bootstrap in the same fresh test chat is the intended clean-room sequence. Therefore this evidence satisfies the external clean-room qualification requirement.

## E-006 — RC package internal reconstruction verification

The RC package was constructed from Working build.004 with release metadata/evidence updates only; no reference-control algorithm or schema behavior changed. RC construction verification: Framework reference tests **34/34 PASS**, release inventory integrity recorded, and undeclared Python bytecode caches excluded.

## E-007 — Exact RC external fresh-chat Bootstrap

Artifact: `ChatGPT_Bundle_Framework_v0.1-rc.1.zip`

Reported result:

- Release ID recognized: `0.1-rc.1`.
- Release state recognized: `RELEASE_CANDIDATE`.
- Manifest integrity: **21/21 PASS**.
- SHA-256 / file-size verification: **21/21 PASS**.
- Reference control tests: **34/34 PASS**.
- Missing or modified files: none.
- Bootstrap state reached successfully.
- Hidden context / prior-chat dependency used as required Bundle dependency: none.

This satisfied the final RC-to-Stable promotion condition.

## E-008 — Stable package reconstruction verification

Stable `v0.11` is promoted from the qualified RC with Framework release identity/status/evidence updates only. Reference controller code and control schemas remain behaviorally unchanged. The exact Stable package is revalidated after construction; results are recorded in `06_RELEASE_VALIDATION_RECEIPT.md` and `RELEASE_MANIFEST.json`.
