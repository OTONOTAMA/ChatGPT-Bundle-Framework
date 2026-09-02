# ChatGPT Bundle Framework v0.11
## 基本設計・日本語解説

### 1. このFrameworkは何か

`ChatGPT Bundle Framework` は、特定用途のChatGPT専用ソフトウェアBundleを作るための共通開発基盤である。

特定分野の知識を持つBundleではなく、設計、正本管理、Version管理、Dependency管理、テスト、Release、Bootstrapの共通ルールだけを定義する。

位置付けとしては、**ChatGPT専用Software Bundleを作るためのSDK＋パッケージ仕様＋開発標準**に近い。

---

## 2. 最重要目標

Frameworkの最重要要件は、**他ユーザーの真っ新なChatGPT環境でもBundle単体から起動できること**である。

Fresh ChatGPT + Domain Bundle だけで Bootstrap → Validation → Runtime Ready → Execute まで到達することを要求する。作成者のMemoryや過去チャットを必要としてはならない。

---

## 3. Bootstrap

正式用語として「復旧」ではなく `Bootstrap` を使用する。

Bootstrapとは、事前のDomain状態を何も持たないChatGPTが、Bundleだけを読んで実行可能な状態を構築すること。

基本順序は、Bundle識別 → Manifest読込 → Version確認 → Lock確認 → 必須Component確認 → Source of Truth確立 → Dependency解決 → Integrity確認 → Runtime Contract読込 → Language Policy解決 → Preflight Validation → Runtime Ready。

Restoreは将来、以前存在した中断Runtime状態を再構築する別概念としてのみ使用する。

---

## 4. 禁止する暗黙依存

正式Bundleは、Memory、Custom Instructions、過去チャット、Project固有文脈、開発者との暗黙知、未宣言ファイル、未宣言Dependencyに依存してはならない。必要な情報はBundle自身に含めるかManifestで明示する。

---

## 5. Frameworkと完成Bundle

Frameworkは主に開発時に使う。完成したDomain Bundleは通常Runtime時にFramework全文を必要としない。

**Framework = 工場**、**Domain Bundle = 完成製品**という関係。

---

## 6. Small Core

Frameworkに入れるのは、Manifest、Version、Source of Truth、Dependency、Integrity、Bootstrap、Validation、Test、Release、Runtime Contract、Multi-Language、Trust Boundaryなど、Domainが変わっても共通して必要になるものだけ。Domain固有ロジックはDomain Bundle側へ置く。

---

## 7. Manifest

全Bundleに `bundle.yaml` を持たせる。これはBundleがどうあるべきかを宣言する正本。Bundle ID、Name、Version、Framework Version、Objective、Required Components、Source of Truth、Dependencies、Entrypoint、Bootstrap Policy、Runtime Contract、Language Policy、Compatibility、Release Stateなどを管理する。

---

## 8. Lock

`bundle.lock.yaml` は正式Releaseで実際に解決された状態を固定する。Manifestが「こうあるべき」なら、Lockは「実際にこうなっている」。Exact Version、Component files、Hash、Size、Dependency version、Validation stateなどを保持する。

---

## 9. Source of Truth

各Bundleは何を正しい情報源として扱うかを明示する。上位Sourceと下位Sourceが競合した場合は上位を採用する。競合が解決できなければ推測せず `UNRESOLVED` にする。

---

## 10. Dependency

外部Componentを暗黙利用しない。DependencyはManifestへ明示し、可能な限りExact Versionを固定する。単なる `REFERENCE` と実行に必要な `DEPENDENCY` は区別する。

---

## 11. Integrity

正式Releaseでは重要ファイルのFilename、Version、Size、Hash、Roleなどを保持できるようにする。未検証HashやSizeをChatGPTが推測して作ってはいけない。

---

## 12. Multi-Language

Frameworkは最初からMulti-Language対応とする。日本語版仕様と英語版仕様を別々に持たず、**Canonical Semantic Layer + Presentation Language Layer**に分ける。内部Identifierは翻訳せず、表示言語だけを変える。意味体系は1つ。

---

## 13. Trust Boundary

情報を `CANONICAL / DEPENDENCY / REFERENCE / RUNTIME_INPUT / UNTRUSTED` に分類し、低いTrust Levelの情報が高いTrust Levelの規則を上書きできないようにする。

---

## 14. Development ModeとRuntime Mode

Bundle開発・改修時は `DEVELOPMENT`、正式利用時は `RUNTIME`。Runtime中の通常入力は `RUNTIME_INPUT` として扱い、Bundle仕様自体を暗黙変更しない。

---

## 15. Test体系

共通Test分類は、Structural Test、Contract Test、Behavioral Test、Regression Test、Bootstrap Test、E2E Test。Domain固有のTest内容そのものはFrameworkで固定しない。

---

## 16. Clean-Room Bootstrap Test

最重要Test。Memoryなし、Custom Instructionsなし、過去チャットなし、Project Contextなし、事前Domain Stateなしの真っ新なChatGPTへBundleだけを渡し、Runtime Readyまで到達できるか確認する。

---

## 17. Validation Gates

G0 STRUCTURE、G1 RESOLUTION、G2 BEHAVIOR、G3 RELEASE、G4 CLEAN ROOM BOOTSTRAP、G5 E2E。特にG4を最重要Gateとする。

---

## 18. Failure Model

共通状態は `PASS / WARN / FAIL / UNRESOLVED`。`UNRESOLVED` をChatGPTの推測で `PASS` に変えてはいけない。継続にはDomain Bundle側の明示的Fallback Policyが必要。

---

## 19. Release State

共通Release状態は `DEVELOPMENT / PREVIEW / RELEASE_CANDIDATE / STABLE / DEPRECATED`。通常の正式利用は `STABLE` を基本とする。

---

## 20. Runtime時のContext節約

各Componentを `RUNTIME_REQUIRED / RUNTIME_OPTIONAL / DEVELOPMENT_ONLY / REFERENCE_ONLY` に分類する。通常実行時はManifest、Minimal Runtime Contract、Runtime Required Componentsだけを基本ロードする。

---

## 21. Framework自身のBootstrap

Framework自身もFresh ChatGPTへ渡して `Framework Bootstrap -> Bundle Development Ready` に到達できなければならない。

---

## 22. 標準開発フロー

Framework Bootstrap → Requirements → Objective → Scope → Source of Truth → Domain Architecture → Bootstrap Contract → Runtime Contract → Dependencies → Manifest → Tests → Implement → Validate → Lock → Clean-Room Bootstrap Test → E2E Test → Release。

---

## 23. 完成Bundleに要求する性質

Self Identifying、Self Describing、Self Bootstrapping、Zero Context Capable、Source of Truth Explicit、Versioned、Dependencies Explicit、Integrity Verifiable、Multi-Language Safe、Semantically Single Source、Runtime Self Contained、Validated、Tested。

---

## 24. v0.11では入れないもの

他LLM互換、他Agent Platform互換、公開Registry、Dependency自動Download、Transitive Dependency Manager、本格CI/CD、SBOM、自動Migration、Framework自動Update、Cross-Bundle Runtimeは初版では除外する。必要性が実証されてから追加する。

---

## 25. 最終思想

**FrameworkがBundleを作る。**

**完成Bundleは自分自身をBootstrapする。**

**過去のユーザー固有ChatGPT状態には依存しない。**

**意味の正本は1つで、表示言語だけを変える。**

**通常RuntimeではFramework全文を必要としない。**


---

## 26. Reasoning と正式実行の分離

ChatGPTの自由な判断をすべて禁止するのではなく、役割を分ける。

- `DELIBERATIVE`: 調査、解釈、曖昧さの検討、説明など、ChatGPTの柔軟性が価値を持つ領域。
- `CONSTRAINED_REASONING`: ChatGPTが考えることはできるが、正式に戻す結果は宣言済みSchemaへ変換する領域。
- `CONTROLLED_EXECUTION`: 正式な処理順や次のActionをChatGPTが自由選択せず、State Controllerが決める領域。

このControl Modeは `DEVELOPMENT / RUNTIME` とは別概念である。前者は「ChatGPTの裁量と正式処理の制御」、後者は「Bundleの開発中か正式利用中か」を表す。

## 27. State Controller

複数段階の正式処理を行うBundleでは、ChatGPTに毎回「次にどの内部処理を呼ぶか」を選ばせない。

State Controllerが現在State、正式入力、Receiptを確認し、次に許可されたActionを決める。Host側からの基本操作は `BEGIN_WORKFLOW / ADVANCE / INSPECT_STATE` のような狭い形を推奨する。

FrameworkはDomain固有の処理内容を決めない。何を計算するか、何を生成するか、どんなDomain Stateを持つかはDomain Bundle側の責任である。

## 28. 「呼べる」と「正式」は別

内部関数やTest helperを物理的に呼べる可能性があっても、それだけで正式処理とは認めない。

正式なAuthorityは、宣言されたWorkflow、正しいState、必要なExecution Permit、Receiptなどを通じた有効なTransitionによってのみ得られる。

つまり、**動かせることと正式結果を作れることを分離する**。

## 29. Execution Permit と Receipt

`Execution Permit` は「このWorkflowの、このStateで、このActionを、この入力に対して実行してよい」という機械的な許可情報。

`Receipt` は「その正式Actionが実際に完了し、どのStateへ進んだか」を示す機械検証可能な証拠。

自然文で「実行した」と書くだけではReceiptの代わりにならない。

## 30. 中断からのRecovery

途中でProcessやWrapperが失敗しても、すべてを最初からやり直すとは限らない。

StateとReceiptを確認し、有効に完了済みの処理は保存する。無効・古い・不足している処理だけを再実行する。外側のWrapper失敗を、内側の処理失敗と自動的に同一視しない。

## 31. 正式成果物とProvenance

正式成果物は、見た目が正しいだけでは正式とは認めない。

どのWorkflow、正式結果、Finalization Receiptから生成されたかを追跡できることを要求できる。ChatGPTが正式ルートを使わず手作業で似た成果物を再構成しても、正式Authorityは自動的には与えない。

正式な事実を固定した後、ChatGPTが読みやすい説明へ戻ることは許可できる。ただし、固定済みの正式数値・分類・結果を変更してはいけない。

さらに、正式成果物を発行する場合は、Domain Bundleが宣言した `Artifact Validator` で、成果物の内容が正式結果とOutput Contractに一致していることを確認する。FrameworkはDomain固有の正しさそのものは定義せず、「宣言されたValidatorが存在し、PASSした」というAuthority条件だけを共通管理する。

## 32. Bundleが制御できる範囲

Frameworkは、Bundle Runtimeが機械的に拒否できることと、ChatGPT Host側の遵守に依存することを区別する。

- `RUNTIME_ENFORCED`: Runtime/Controller自身が拒否可能。
- `AUTHORITY_ENFORCED`: 実行自体は可能でも正式Authorityを与えない。
- `AGENT_CONTRACT`: ChatGPT Host側がBundle契約に従う必要がある。
- `HOST_PLATFORM_LIMIT`: Bundleの物理的制御範囲外。

BundleがChatGPT製品全体を物理的に支配できるような表現は禁止する。

## 33. Simple Bundleとの互換性

この仕組みはすべてのBundleへ強制しない。

単純なBundleは従来のv0.1 Runtime Contractのままでもよい。複数段階の正式処理、厳密なState遷移、正式Artifact Authorityなどが必要なBundleだけがControlled Executionを宣言する。

Small Coreの原則は維持する。

## 34. G5 E2Eの強化

Controlled Executionを使うBundleでは、G5は「正しい見た目の結果が出た」だけではPASSにしない。

正式なPublic Execution Routeを通り、必要なReceiptとArtifact Provenanceを確認できることまでE2E成功条件に含める。
