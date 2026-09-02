# Quick Start

## Use the Framework as a development reference

1. Read `framework/v0.11/01_CANONICAL_NORMATIVE_SPECIFICATION.md`.
2. Design a Domain Bundle with explicit source-of-truth, version, dependency, integrity, runtime, validation, and release contracts.
3. Keep Domain-specific semantics in the Domain Bundle.
4. Validate the Bundle in a fresh / zero-context ChatGPT environment.
5. Do not require the full Framework at runtime unless the Domain Bundle explicitly declares that dependency.

## Run the reference tests

```bash
cd framework/v0.11
python tests/control/run_tests.py
```

The stable release records 34/34 PASS for the reference control suite.
