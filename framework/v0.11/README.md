# ChatGPT Bundle Framework v0.11 — Stable

Release ID: `0.11`  
Release state: `STABLE`  
Source Working build: `004`  
Qualified Release Candidate: `0.1-rc.1`

This package is the stable release promoted from the exact qualified `v0.1-rc.1` artifact. The Framework version number is `0.11` by explicit release-version decision; reference runtime algorithms and control schemas are unchanged from the qualified RC.

## Primary authority

1. `01_CANONICAL_NORMATIVE_SPECIFICATION.md` — canonical normative source of truth.
2. `02_JA_HUMAN_GUIDANCE.md` — Japanese non-normative human guidance.
3. `03_IMPLEMENTATION_STATUS.md` — implementation status and known limits.
4. `04_VALIDATION_EVIDENCE.md` — validation evidence register.
5. `05_PROMOTION_REVIEW.md` — stable-promotion decision record.
6. `06_RELEASE_VALIDATION_RECEIPT.md` — stable release validation receipt.
7. `schemas/control/` — machine-readable generic control schemas.
8. `runtime/control/` — domain-independent reference controller/provenance implementation.
9. `tests/control/` — normal, forbidden-path, tamper, recovery, provenance, artifact-validation, and schema tests.
10. `RELEASE_MANIFEST.json` — exact stable-release inventory and integrity snapshot.

## Stable qualification

- Working build.004 external fresh-chat Framework Bootstrap: **PASS**.
- Framework reference control tests: **34/34 PASS**.
- Fully conforming synthetic Domain Bundle external clean-room UAT: **PASS**.
- Synthetic lock integrity: **14/14 PASS**.
- Formal Controlled Execution E2E: **PASS**.
- Adversarial probes: **3/3 PASS**.
- Runtime independence from full Framework package: **PASS**.
- Exact `v0.1-rc.1` fresh-chat Bootstrap: **PASS**.

## Release boundary

This artifact is `STABLE`. The stable Framework version is `v0.11`. Internal control-schema versions remain at `0.1` because no schema semantics changed during RC-to-Stable promotion. Domain-specific logic is not part of this Framework package.
