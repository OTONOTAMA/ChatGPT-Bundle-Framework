# ChatGPT Bundle Framework

**A domain-independent development framework for building self-contained, portable ChatGPT Domain Bundles with zero-context Bootstrap, explicit source-of-truth management, validation, Controlled Execution, receipts, authority, and artifact provenance.**

[日本語 README](README.ja.md)

## Status

- Framework version: **v0.11**
- Release state: **STABLE**
- Target platform: **ChatGPT**
- License: **MIT**
- Canonical specification: [`framework/v0.11/01_CANONICAL_NORMATIVE_SPECIFICATION.md`](framework/v0.11/01_CANONICAL_NORMATIVE_SPECIFICATION.md)

This repository is an independent project. It is not affiliated with or endorsed by OpenAI.

## What is this?

ChatGPT Bundle Framework defines common engineering rules for creating **Domain Bundles** that can bootstrap themselves in a fresh ChatGPT environment without relying on prior user-specific state.

```text
Fresh ChatGPT + Released Domain Bundle
                ↓
            Bootstrap
                ↓
             Validate
                ↓
          Runtime Ready
                ↓
             Execute
```

The full Framework is primarily a development and validation standard. A completed Domain Bundle is expected to carry the runtime contract it needs and normally does **not** require the full Framework package at runtime.

## Core ideas

- **Zero-context Bootstrap** — no hidden dependence on user Memory, prior chat history, Custom Instructions, undeclared files, or project-specific context.
- **Source of Truth first** — version, dependencies, integrity, runtime contracts, and release state are explicit.
- **Small Core / Domain isolation** — Domain-specific algorithms and semantics stay in Domain Bundles.
- **Reasoning / Controlled Execution separation** — preserve LLM flexibility where useful; constrain authoritative workflow transitions where reproducibility matters.
- **Callability is not authority** — discoverable/callable internals are not automatically authoritative.
- **Provenance before formal emission** — formal artifacts can be bound to authoritative workflow evidence before emission.

## Repository layout

```text
.
├── README.md
├── README.ja.md
├── LICENSE
├── NOTICE.md
├── CHANGELOG.md
├── docs/
├── framework/v0.11/
├── releases/
└── examples/
```

## v0.11 validation summary

The stable package records:

- Framework reference control tests: **34/34 PASS**
- External fresh-chat Framework Bootstrap: **PASS**
- Fully conforming synthetic Domain Bundle external clean-room UAT: **PASS**
- Synthetic lock integrity: **14/14 PASS**
- Formal Controlled Execution E2E: **PASS**
- Adversarial probes: **3/3 PASS**
- Full-Framework runtime dependency for the synthetic release test: **false**
- Exact Release Candidate fresh-chat Bootstrap: **PASS**

See [`framework/v0.11/04_VALIDATION_EVIDENCE.md`](framework/v0.11/04_VALIDATION_EVIDENCE.md) and [`framework/v0.11/06_RELEASE_VALIDATION_RECEIPT.md`](framework/v0.11/06_RELEASE_VALIDATION_RECEIPT.md).

## Quick start

See [`docs/QUICK_START.md`](docs/QUICK_START.md). For authoritative Framework semantics, use the canonical specification.

## Reference implementation tests

From `framework/v0.11`:

```bash
python tests/control/run_tests.py
```

## Release integrity

```text
SHA-256
4f7db7f271705105355e856f4a3bce60169bda7f202d8cb9d9905f1901854390  ChatGPT_Bundle_Framework_v0.11.zip
```

## License

Licensed under the [MIT License](LICENSE).
