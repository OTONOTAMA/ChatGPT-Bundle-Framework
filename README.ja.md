# ChatGPT Bundle Framework

ChatGPT上で動作する自己完結型Domain Bundleを設計・検証・公開するための、Domain非依存の開発Frameworkです。

- Version: **v0.11 STABLE**
- 対象: **ChatGPT**
- License: **MIT**
- 正本仕様: [`framework/v0.11/01_CANONICAL_NORMATIVE_SPECIFICATION.md`](framework/v0.11/01_CANONICAL_NORMATIVE_SPECIFICATION.md)

このRepositoryは独立したプロジェクトであり、OpenAI公式プロジェクトではありません。

## 目的

Fresh ChatGPT + Domain Bundleだけから、Bootstrap → Validation → Runtime Ready → Executeへ到達できるBundleを作るための共通ルールを定義します。

主な考え方は、Zero-context Bootstrap、Source of Truth、Small Core、ReasoningとControlled Executionの分離、Execution Permit / Receipt、Artifact Provenance、Multi-Language Safetyです。

完成したDomain Bundleは通常Runtime時にFramework全文を必要としません。Frameworkは主に**開発時の工場**として使います。

## 公開物

- `framework/v0.11/` — v0.11展開内容
- `releases/ChatGPT_Bundle_Framework_v0.11.zip` — 正式Stable ZIP
- `examples/` — Framework検証用Synthetic Bundle
- `docs/` — Quick Start、Architecture、Release Notes、GitHub公開手順

正式ZIP SHA-256:

```text
4f7db7f271705105355e856f4a3bce60169bda7f202d8cb9d9905f1901854390  ChatGPT_Bundle_Framework_v0.11.zip
```

## ライセンス

[MIT License](LICENSE) で公開します。第三者の商標・名称等については `NOTICE.md` を参照してください。
