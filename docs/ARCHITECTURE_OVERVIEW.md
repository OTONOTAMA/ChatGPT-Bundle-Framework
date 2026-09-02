# Architecture Overview

ChatGPT Bundle Framework separates flexible reasoning from authoritative execution.

```text
User
 ↓
LLM intent / reasoning
 ↓
State Controller
 ↓
Public Execution Facade
 ↓
Controlled Runtime
 ↓
Receipt / Evidence
 ↓
State Controller
 ↓
Authorized output / artifact provenance
```

The Framework does not attempt to make all LLM behavior deterministic. It constrains the portions where authoritative state, workflow order, provenance, and reproducibility require explicit control.
