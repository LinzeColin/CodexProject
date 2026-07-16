# PFI v0.2.5 Stage 0 Phase 0.3 设计

## 1. 决策

本轮只执行 `Stage 0 / Phase 0.3 — 差距与修复排序`，覆盖：

- `S0-P3-T1`：把历史 finding 归一化为 `StillPresent / Fixed / Regressed / N/A / New`，且每项绑定当前证据；
- `S0-P3-T2`：把 current gaps 聚合为可执行的 P0/P1 队列，并对 P2 明确记录 zero executable / out-of-scope disposition；
- `S0-P3-T3`：生成 Roadmap 点名的 Stage 0 Evidence Pack 与 Phase 四件套；
- `S0-P3-T4`：生成验收请求并停止，不进入 Stage 0 whole-stage review 或 Stage 1。

本 Phase 是只读审计与治理产物，不修改业务 UI、产品逻辑、公式/模型/参数值、真实数据、数据库、App bundle、启动脚本或服务。

## 2. Authority 与固定身份

Authority order 沿用 `PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS`：

1. 用户最新明确决定；
2. pinned v0.2.5 Roadmap 与 Task Pack；
3. 当前仓库、runtime、App、data、test 的 verified evidence；
4. 不冲突且已分类的历史事实；
5. 历史完成声明没有独立 authority。

固定输入：

| source | identity |
|---|---|
| Roadmap | `/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md` |
| Roadmap SHA-256 | `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b` |
| Task Pack | `/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip` |
| Task Pack SHA-256 | `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2` |
| Active Requirements | `PFI/config/pfi_v025_active_requirements.json` |
| Phase 0.2 content commit | `7433be0d70bdae42959c1b71753d93f8737db60d` |
| Phase 0.2 final attestation SHA-256 | `8b579f727c9fdbe55fe8e9455ec28a4d7c6c45b4caf47fb7dbe1d6226859c60a` |

Phase 0.3 identities：

```text
iteration_id = ITER-20260711-PFI-V025-S0-P03
contract_id = PFI-V025-STAGE0-PHASE03-GAP-EVIDENCE
acceptance_id = ACC-PFI-V025-S0-P03-GAP-EVIDENCE
governance_override_id = PFI-V025-S0-P03-GOVERNANCE-COMPANIONS
```

`acceptance_id` 是 Phase candidate gate，不是 Stage 0 user acceptance。Stage 0 的 whole-stage review、finding remediation、re-review、Codex 明确验收与用户明确接受必须在后续独立 run 完成。

## 3. 方案选择

### 3.1 采用：25-path normalized pack

Roadmap 的 13 个 Phase/Stage artifacts 按精确 basename 创建；现有 governance validator 因 `.json`、`evidence` 和 `risk` 路径分类而强制同步 12 个 companions。既有证据通过路径、JSON pointer 与 SHA-256 引用，不复制 raw/private content，不把 derived pack 变成第二 canonical fact source。

### 3.2 不采用：最小 7-path pack

它会遗漏 Roadmap 点名的 `baseline.json`、`git_state.txt`、`current_state_matrix.md`、`data_root_inventory.json`、Stage-level `history_deprecation.md` 与 `terminal.log`，并使 `validate_governance_sync --enforce-sync` 缺少 companions。

### 3.3 不采用：额外 evidence index

不新增第 26 个 `evidence_index.json`。Phase 0.3 `evidence.json` 同时承担 Phase envelope 与 Stage 0 evidence index；`acceptance_request.md` 绑定其 finalized SHA-256。这样避免重复可编辑事实源。

## 4. Exact implementation file map

设计与实施计划各自先单独提交，不计入 implementation ledger。Phase implementation commit 精确修改 25 个路径。

### 4.1 Roadmap core artifacts：13

```text
PFI/docs/pfi_v025/stage_0/acceptance_request.md
PFI/docs/pfi_v025/stage_0/finding_ledger.csv
PFI/docs/pfi_v025/stage_0/gap_register.md
PFI/reports/pfi_v025/stage_0/baseline.json
PFI/reports/pfi_v025/stage_0/current_state_matrix.md
PFI/reports/pfi_v025/stage_0/data_root_inventory.json
PFI/reports/pfi_v025/stage_0/git_state.txt
PFI/reports/pfi_v025/stage_0/history_deprecation.md
PFI/reports/pfi_v025/stage_0/terminal.log
PFI/reports/pfi_v025/stage_0/phase_0_3/changed_files.txt
PFI/reports/pfi_v025/stage_0/phase_0_3/evidence.json
PFI/reports/pfi_v025/stage_0/phase_0_3/risk_and_rollback.md
PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log
```

### 4.2 Governance companions：12

```text
PFI/CHANGELOG.md
PFI/docs/governance/DEVELOPMENT_LEDGER.md
PFI/docs/governance/MODEL_SPEC.md
PFI/docs/governance/OWNER_STATUS.md
PFI/docs/governance/STATUS.md
PFI/docs/governance/TRACEABILITY_MATRIX.csv
PFI/docs/governance/VERSION_MATRIX.yaml
PFI/docs/governance/delivery_tasks.yaml
PFI/docs/governance/development_events.jsonl
PFI/docs/governance/formula_registry.yaml
PFI/docs/governance/model_registry.yaml
PFI/docs/governance/parameter_registry.csv
```

### 4.3 新 governance override

Phase 0.2 的 override 只授权 Phase 0.2，不能静默继承。用户 standing authorization 在本 Phase 收敛为：

```text
override_id = PFI-V025-S0-P03-GOVERNANCE-COMPANIONS
original_boundary = Stage 0 writes only pfi_v025 stage docs/reports and active requirements config
effective_rule = Phase 0.3 allows exact 13 Roadmap artifacts plus exact 12 validator-required governance companions
scope_limit = exact 25 implementation paths; no 26th path
state_before_postcommit = approved_pending_postcommit_attestation
```

该 override 不授权 README、HANDOFF、功能清单、开发记录、模型参数文件、VERSION、ASSURANCE_STATUS、DELIVERY_PLAN、project.yaml、roadmap.yaml、任何 business/runtime/data/App path 或其他项目。

## 5. Finding ledger 模型

### 5.1 CSV schema

`finding_ledger.csv` 使用固定列顺序：

```text
finding_id
source_ids
history_item_ids
domain
summary
current_status
priority
fact_level
priority_basis
prior_evidence_refs
prior_evidence_as_of
current_evidence_refs
current_evidence_as_of
current_evidence_result
roadmap_resolution_tasks
blocks_phase_0_3_candidate
blocks_v025_production_acceptance
rationale
```

多值字段使用 `;` 分隔；缺少 prior/history item 时，相关 ref 与 as-of 都写 `NOT_APPLICABLE`。每行全部 18 列，不允许空 `finding_id/current_status/priority/priority_basis/fact_level/current_evidence_refs/current_evidence_as_of/current_evidence_result/roadmap_resolution_tasks/rationale`。`prior_evidence_as_of` 与 `current_evidence_as_of` 只允许 RFC 3339 或 `NOT_APPLICABLE`；多证据时填最新一项时间，逐项时间保存在 evidence registry。`roadmap_resolution_tasks` 的每个 `;` token 必须逐字匹配 pinned Roadmap 的真实 `Sx-Py-Tz`，禁止范围缩写或说明文字。有效分类完成后每行 `blocks_phase_0_3_candidate=false`；未关闭的 P0/P1 finding 以 `blocks_v025_production_acceptance=true` 保持 fail-closed。

### 5.2 Status 语义

| status | exact meaning |
|---|---|
| `StillPresent` | fresh current evidence 仍复现 historical finding，或 required production proof 尚未存在 |
| `Fixed` | fresh current evidence 在明确 scope 内证明 finding 消失；scope 必须写入 rationale |
| `Regressed` | 旧 evidence 曾证明通过，但 fresh current evidence 再次出现冲突 |
| `N/A` | 最新 Active Requirements/scope 使该历史 finding 不再适用于当前 product contract |
| `New` | Phase 0.1/0.2/current recheck 新发现，不能归并到既有 finding |

这些词只用于 finding ledger，不替代 Phase evidence 的 `candidate_pass/fail/blocked/not_run`，也不替代 conflict lifecycle 的 `blocked/approved_pending_validation/resolved_by_approved_override`。

Status evidence tuple 是强制规则：

| status | required tuple |
|---|---|
| `StillPresent` + reproduced | `current_evidence_refs` 指向 fresh reproduction，registry 含该 ref 的 RFC 3339 `observed_at`，`current_evidence_result=reproduced` |
| `StillPresent` + missing proof | 指向 current `not_run/blocked` evidence及其 RFC 3339 `observed_at`，`current_evidence_result=required_production_proof_missing`；不得写成 fresh failure |
| `Fixed` | current-scope negative/pass proof，`current_evidence_result` 必须使用 `fixed_within_<named_scope>` 形式，rationale 必须限定同一 scope |
| `Regressed` | `prior_evidence_refs` 必须含同一 predicate 的旧 pass，prior/current registry records 都有 RFC 3339 `observed_at`，`current_evidence_result=fresh_failure`，且机器校验 `prior_evidence_as_of < current_evidence_as_of` |
| `N/A` | current authority/scope evidence，`current_evidence_result=superseded_or_non_applicable`，并给 non-gap reason |
| `New` | fresh evidence + source-universe non-match rationale，`current_evidence_result=new_current_fact` |

### 5.3 Row universe 与覆盖

Ledger 固定 38 rows，ID 为 `PFI-V025-FND-001..038`。Canonical evidence keys：

```text
P01_ENTRY = PFI/reports/pfi_v025/stage_0/phase_0_1/entry_inventory.json
P01_REPO = PFI/reports/pfi_v025/stage_0/phase_0_1/repository_inventory.json
P01_EVID = PFI/reports/pfi_v025/stage_0/phase_0_1/evidence.json
P01_RISK = PFI/reports/pfi_v025/stage_0/phase_0_1/risk_and_rollback.md
P02_ACTIVE = PFI/config/pfi_v025_active_requirements.json
P02_EVID = PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json
P02_ATTEST = .git/codex-review/pfi-v025/stage_0/phase_0_2/7433be0d70bdae42959c1b71753d93f8737db60d.attempt.id9uiuo8/phase_0_2_attestation.json
P03_TERM = PFI/reports/pfi_v025/stage_0/phase_0_3/terminal.log
CURRENT_OWNER = PFI/README.md;PFI/HANDOFF.md;PFI/功能清单.md;PFI/开发记录.md;PFI/模型参数文件.md;PFI/VERSION
CURRENT_WEB = PFI/web/index.html;PFI/web/app/shell.js;PFI/web/app/routes.js;PFI/web/app/version.js
CURRENT_RUNTIME_APP = P03_TERM#current-runtime-app-recheck
TASKPACK_AUDIT = TaskPack/docs/CURRENT_GITHUB_AUDIT_2026-07-10.md
TASKPACK_RISK = TaskPack/docs/RISK_REGISTER.md
TASKPACK_SURPRISE = TaskPack/docs/SURPRISE_FINDINGS_AND_DESIGN_DECISIONS.md
```

`phase_0_3/evidence.json` 必须同时包含 machine-readable `source_registry` 与 `evidence_registry`。CSV 的每个 `source_ids` token 必须 resolve 到 `source_registry`；每个 prior/current evidence key 必须 resolve 到 `evidence_registry`。Registry record 固定含 `artifact_ref`、`artifact_sha256`、`selector`、`source_text_sha256`、`observed_at`、`fact_level`；collection key 还含按稳定路径排序的 member hashes。`observed_at` 只允许 artifact 内时间、producing commit RFC 3339 时间或 fresh Phase 0.3 command 时间，不允许文件 mtime 猜测。

Source normalization registry 固定为：

| source IDs | artifact SHA-256 | exact selector rule |
|---|---|---|
| `R-01..R-15` | `450c39e8b9a56d24b9a5a02f017a6a10aba76fbda352e74706aa9dc7664ec03c` | `RISK_REGISTER.md` table 的原生 `ID`，不得重编号 |
| `SUR-01..SUR-12` | `b64edf32506b2590b22f81eded952756edd9ff515036bb697972972c87f79e95` | Surprise 文档 `## 1..12` 的 heading number，store heading/body SHA |
| `AUD-01..AUD-15` | `e2739d9c77f7098ab5c6aba7ca8fb4a1ff1420e63a614a4ad35bd221cd728626` | Audit `## 事实矩阵` 的 ordered data rows 1..15；store domain key与完整 row SHA；`AUD-15` 固定是 `SQLite/持仓` |
| `P01-RISK-01..10` | `2f45b6b9774b24a0bc990d9476e13448604cdd9169e82e37f0c14c7c8daddf35` | JSON pointers `/risks/0..9`，1-based source ID 对应 0-based pointer |
| `P01-CONFLICT:<exact-id>` | `3e06443abfa65234b0735350e44de656dcd921fd5ddc05c401c11a4777013199` | `/conflicts/*/id` 的 exact value；禁止 `RELEASE`、`HOME` 等短别名 |
| `PFI-V025-CONFLICT-*` | `b77e1ac78e8842d9a58d76d07a491f80e7a010b3cc91fb4ca7cf24ba10457d37` | `/blocking_conflicts/items/*/conflict_id` 的 exact value |
| `P02-RISK-01..05` | `d0e7e3c4413404c0dee91b1173b8d3e270c50faa6f06c3fc4cdd24ff90b6a1f8` | JSON pointers `/risks/0..4` |
| `P02-LIFECYCLE-COMPARISON` | evidence `d0e7e3c4413404c0dee91b1173b8d3e270c50faa6f06c3fc4cdd24ff90b6a1f8` + attestation `8b579f727c9fdbe55fe8e9455ec28a4d7c6c45b4caf47fb7dbe1d6226859c60a` | `/governance_override_state` 与 attestation `/status`、`/blocks_phase_0_2_candidate` 的 typed pair |

Current owner/web/runtime source collections不是 historical source IDs；它们只进入 `evidence_registry`，以 ordered member hash、fresh command time与 selector 解析。`P03_TERM` 在 Layer 1 finalized 后登记其 SHA；registry 内容不得反向写入 terminal log，因此不形成 hash cycle。

Canonical 38-row crosswalk（表内 `FND-NNN` 是 `PFI-V025-FND-NNN` 的唯一短写；实际 CSV 只允许完整 ID）：

| ID | canonical concept | primary source IDs | history item IDs | status / priority | fact level / priority basis | current evidence / result | prior evidence | exact resolution tasks |
|---|---|---|---|---|---|---|---|---|
| FND-001 | 旧 closeout 不证明当前 v0.2.5 完成 | AUD-01 | HIST-OLD-CLOSEOUT-CLAIMS | StillPresent / P0 | VERIFIED / AUDIT-P0-OWNER | CURRENT_OWNER / reproduced | NOT_APPLICABLE | S0-P3-T1;S12-P3-T1 |
| FND-002 | owner views 与 v0.2.5 governance 状态分裂 | AUD-12;R-12;SUR-03;P02-RISK-01;PFI-V025-CONFLICT-OWNER-VIEWS | NOT_APPLICABLE | StillPresent / P0 | VERIFIED / R-12 | CURRENT_OWNER;P03_TERM / reproduced | NOT_APPLICABLE | S0-P3-T1;S12-P3-T1 |
| FND-003 | VERSION/page/launcher/App/target identity 混合 | AUD-11;P01-RISK-02;P01-CONFLICT:RELEASE_IDENTITY_MIXED_VERSIONS;PFI-V025-CONFLICT-RELEASE-IDENTITY | NOT_APPLICABLE | StillPresent / P0 | VERIFIED / AUDIT-P0-APP | P01_ENTRY;CURRENT_WEB;CURRENT_OWNER;P03_TERM / reproduced | NOT_APPLICABLE | S1-P1-T1;S1-P1-T2;S1-P1-T3;S1-P1-T4;S12-P3-T1 |
| FND-004 | canonical App/cache/reinstall identity 未闭环 | AUD-02;R-01;SUR-02;PFI-V025-CONFLICT-APP-IDENTITY | OVERRIDE-PER-STAGE-DELIVERY | StillPresent / P0 | VERIFIED / R-01 | P01_ENTRY;CURRENT_RUNTIME_APP / reproduced | NOT_APPLICABLE | S1-P1-T2;S1-P2-T1;S1-P2-T2;S1-P2-T3;S1-P2-T4;S12-P2-T1 |
| FND-005 | repo App executable 与用户入口不一致 | P01-RISK-05;P01-CONFLICT:APP_EXECUTABLE_HASH_MISMATCH | NOT_APPLICABLE | New / P0 | VERIFIED / R-01 | P03_TERM / new_current_fact | NOT_APPLICABLE | S1-P1-T2;S1-P1-T3;S12-P2-T1 |
| FND-006 | repo App strict codesign 失败 | P01-RISK-04;P01-CONFLICT:REPOSITORY_APP_CODESIGN_FAILED;P01-CONFLICT:APP_CODESIGN_EXIT_CODES_PARTIALLY_UNAVAILABLE | NOT_APPLICABLE | New / P0 | VERIFIED / R-01 | P03_TERM / new_current_fact | NOT_APPLICABLE | S1-P1-T2;S12-P2-T1 |
| FND-007 | 两个 canonical listeners 同时运行 | P01-RISK-06;P01-CONFLICT:MULTIPLE_CANONICAL_RUNTIME_SERVICES;PFI-V025-CONFLICT-RUNTIME-LISTENERS | NOT_APPLICABLE | New / P0 | VERIFIED / AUDIT-P0-APP | P03_TERM / new_current_fact | NOT_APPLICABLE | S1-P3-T2;S12-P2-T2 |
| FND-008 | PFI_DATA_HOME 未设且 data-root truth 分裂 | AUD-03;P01-RISK-07 | NOT_APPLICABLE | StillPresent / P0 | VERIFIED / AUDIT-P0-DATA | P01_REPO;P03_TERM / reproduced | NOT_APPLICABLE | S2-P1-T1;S2-P1-T2;S2-P1-T3 |
| FND-009 | transaction rows 不能替代 account/holding/net-worth inputs | AUD-04;AUD-05;AUD-06;SUR-01;P01-RISK-08 | ARCH-IMMUTABLE-RAW-READMODEL-PROVENANCE | StillPresent / P0 | VERIFIED / R-02 | P01_REPO / reproduced | NOT_APPLICABLE | S2-P1-T4;S4-P1-T1;S4-P1-T2;S4-P1-T3;S4-P1-T4;S4-P2-T1;S4-P2-T2;S4-P2-T3;S4-P2-T4 |
| FND-010 | no-false-zero 缺 fresh production gate | R-02 | HIST-FAKE-FINANCIAL-ACCEPTANCE | StillPresent / P0 | EXTRACTED / R-02 | P01_EVID / required_production_proof_missing | NOT_APPLICABLE | S4-P3-T1;S12-P1-T4 |
| FND-011 | temporal/timezone truth 未闭环 | SUR-06 | NOT_APPLICABLE | StillPresent / P1 | EXTRACTED / AUDIT-P1-FORMULA | P03_TERM / required_production_proof_missing | NOT_APPLICABLE | S2-P2-T1;S2-P2-T2;S2-P2-T3 |
| FND-012 | frontend 仍硬编码旧 FX snapshot/rate | SUR-12 | NOT_APPLICABLE | StillPresent / P0 | VERIFIED / AUDIT-P0-METRIC | CURRENT_WEB;P03_TERM / reproduced | NOT_APPLICABLE | S2-P2-T2;S2-P2-T3;S5-P1-T3 |
| FND-013 | 单一 confidence 混合质量维度 | SUR-04 | NOT_APPLICABLE | StillPresent / P1 | VERIFIED / AUDIT-P1-FORMULA | CURRENT_WEB;PFI/src/pfi_os/application/read_model_status.py;P03_TERM / reproduced | NOT_APPLICABLE | S5-P1-T4 |
| FND-014 | dual-consumption gross activity/lineage 未 fresh 验证 | R-03;SUR-05 | NOT_APPLICABLE | StillPresent / P0 | EXTRACTED / R-03 | P03_TERM / required_production_proof_missing | NOT_APPLICABLE | S3-P2-T2;S3-P2-T3;S5-P2-T1 |
| FND-015 | static source primary labels 已固定为 10 | AUD-07 | HIST-NAV-COUNT-06;HIST-NAV-COUNT-08;HIST-NAV-COUNT-09;HIST-NAV-COUNT-15;HIST-NAV-COUNT-16;HIST-MARKET-PRIMARY-BAN;HIST-ALIASES-AS-PRIMARY | Fixed / P0 | VERIFIED / AUDIT-P0-ROUTE | CURRENT_WEB;P02_ACTIVE;P03_TERM / fixed_within_static_source_scope | NOT_APPLICABLE | S6-P1-T1;S12-P1-T1 |
| FND-016 | rendered DOM/a11y/no-JS 无 no-16-stack evidence | AUD-08;R-04;SUR-07 | NOT_APPLICABLE | StillPresent / P0 | EXTRACTED / R-04 | P01_EVID;P03_TERM / required_production_proof_missing | NOT_APPLICABLE | S6-P1-T4;S6-P2-T4;S6-P3-T3 |
| FND-017 | target routes/current aliases 与旧 markers 不一致 | PFI-V025-CONFLICT-STALE-ROUTE-MARKERS;PFI-V025-CONFLICT-ROUTE-TARGET-GAP | NOT_APPLICABLE | StillPresent / P0 | VERIFIED / AUDIT-P0-ROUTE | P02_ACTIVE;CURRENT_WEB;P03_TERM / reproduced | NOT_APPLICABLE | S1-P1-T1;S6-P1-T1;S6-P1-T2;S6-P1-T3;S12-P3-T1 |
| FND-018 | click/deep-link/history/back-forward 未 fresh 验证 | AUD-09 | NOT_APPLICABLE | StillPresent / P0 | EXTRACTED / AUDIT-P0-ROUTE | P01_EVID;P03_TERM / required_production_proof_missing | NOT_APPLICABLE | S6-P3-T1;S6-P3-T2;S6-P3-T3;S12-P1-T1 |
| FND-019 | mechanical shell/template text 仍存在 | AUD-10;R-06 | HIST-DARK-AI-CONSOLE;HIST-TASKPACK-LONGPAGE-PHONE-MOCKUP;HIST-SIDE-REVIEW-HTML;REF-APPROVED-HTML-DIRECTION | StillPresent / P0 | VERIFIED / R-06 | CURRENT_WEB;P03_TERM / reproduced | NOT_APPLICABLE | S6-P2-T1;S6-P2-T2;S8-P1-T2;S12-P1-T4 |
| FND-020 | localStorage/toast 可能冒充 persistence | R-05 | NOT_APPLICABLE | StillPresent / P0 | VERIFIED / R-05 | CURRENT_WEB;P03_TERM / reproduced | NOT_APPLICABLE | S7-P2-T1;S7-P2-T2;S7-P2-T3;S7-P2-T4 |
| FND-021 | report source 已有 formula/parameter/sample/source fields | R-07 | NOT_APPLICABLE | Fixed / P0 | VERIFIED / R-07 | PFI/web/app/pages/reports.js;CURRENT_WEB;P03_TERM / fixed_within_static_structure_scope | NOT_APPLICABLE | S9-P1-T1;S9-P1-T2;S9-P1-T3;S9-P1-T4;S9-P2-T1;S9-P2-T2;S9-P2-T3;S9-P2-T4 |
| FND-022 | timer-driven fake progress path 仍存在 | R-08 | NOT_APPLICABLE | StillPresent / P1 | VERIFIED / R-08 | CURRENT_WEB;P03_TERM / reproduced | NOT_APPLICABLE | S8-P2-T2;S8-P2-T4;S10-P1-T4 |
| FND-023 | SQLite version/WAL/holding production gate 未完成 | AUD-15;R-09;SUR-11 | NOT_APPLICABLE | StillPresent / P0 | EXTRACTED / R-09 | P01_EVID;P01_REPO;P03_TERM / required_production_proof_missing | NOT_APPLICABLE | S11-P1-T1;S11-P1-T2 |
| FND-024 | backup/restore/atomic rollback 无 fresh proof | R-10 | ARCH-DURABLE-OPS-BACKUP-RESTORE | StillPresent / P0 | EXTRACTED / R-10 | P01_EVID;P03_TERM / required_production_proof_missing | NOT_APPLICABLE | S11-P2-T1;S11-P2-T2;S11-P2-T3;S11-P2-T4;S12-P2-T3 |
| FND-025 | public shell/PFI OS 非第二 UI 尚未 runtime 验证 | AUD-13;R-11;SUR-08 | HIST-PFI-OS-SECOND-ROOT;ARCH-SINGLE-UI-AND-REAL-RUNTIME | StillPresent / P1 | EXTRACTED / R-11 | P01_EVID;P03_TERM / required_production_proof_missing | NOT_APPLICABLE | S11-P3-T1;S11-P3-T3 |
| FND-026 | Phase 0.1/0.2 evidence privacy scan 为零 | R-13;SUR-10 | NOT_APPLICABLE | Fixed / P0 | VERIFIED / R-13 | P01_EVID;P02_EVID;P02_ATTEST;P03_TERM / fixed_within_stage0_evidence_scope | NOT_APPLICABLE | S2-P3-T2;S10-P3-T2;S11-P3-T3 |
| FND-027 | 旧 owner docs 仍用 bare `1` 作 acceptance source | R-14;SUR-09 | NOT_APPLICABLE | StillPresent / P0 | VERIFIED / R-14 | CURRENT_OWNER;P03_TERM / reproduced | NOT_APPLICABLE | S0-P3-T1;S12-P3-T3;S12-P3-T4 |
| FND-028 | v0.2.5 LLM/advanced-model scope expansion 已被禁止 | R-15 | ARCH-DETERMINISTIC-CORE-NO-AUTOTRADE | Fixed / P1 | EXTRACTED / R-15 | P02_ACTIVE;PFI/docs/pfi_v025/stage_0/scope_boundary.md / fixed_within_scope_contract | NOT_APPLICABLE | S0-P2-T3 |
| FND-029 | full tests/browser/UAT 尚未运行 | P01-RISK-10 | HIST-FAILURE-EVIDENCE;REF-FAST-DEEP-PATH | StillPresent / P0 | EXTRACTED / AUDIT-P0-PRODUCTION | P01_EVID;P03_TERM / required_production_proof_missing | NOT_APPLICABLE | S12-P1-T1;S12-P1-T2;S12-P1-T3;S12-P1-T4;S12-P2-T4 |
| FND-030 | `PFI/web/app/home.js` 缺失 | P01-RISK-03;P01-CONFLICT:FORMAL_UI_HOME_SOURCE_MISSING | NOT_APPLICABLE | New / P1 | VERIFIED / SUBFINDING-FND-003-P1 | P03_TERM / new_current_fact | NOT_APPLICABLE | S1-P1-T3;S6-P2-T1;S6-P2-T2 |
| FND-031 | read_model_hash 含 generated_at 导致跨调用不稳 | P01-RISK-09 | NOT_APPLICABLE | New / P1 | VERIFIED / AUDIT-P1-FORMULA | P01_RISK;PFI/src/pfi_os/application/read_model_status.py;P03_TERM / new_current_fact | NOT_APPLICABLE | S4-P3-T2 |
| FND-032 | shell.js syntax unknown 已消除 | AUD-14 | NOT_APPLICABLE | Fixed / P1 | VERIFIED / SUBFINDING-FND-029-P1 | P03_TERM / fixed_within_syntax_scope | NOT_APPLICABLE | S12-P1-T1 |
| FND-033 | Phase 0.2 governance override 已由 external attestation 解析 | P02-RISK-02;PFI-V025-CONFLICT-GOVERNANCE-SCOPE | NOT_APPLICABLE | Fixed / P1 | VERIFIED / PHASE-GATE-P1 | P02_ATTEST / fixed_within_phase02_scope | P02_EVID | S0-P3-T1;S0-P3-T3 |
| FND-034 | tracked precommit pending 与 external final resolved 是设计分层 | P02-LIFECYCLE-COMPARISON | NOT_APPLICABLE | N/A / P0 | EXTRACTED / PHASE-GATE-P0 | P02_EVID;P02_ATTEST / superseded_or_non_applicable | NOT_APPLICABLE | S0-P3-T3 |
| FND-035 | legacy parameter owner consistency baseline 仍为 3 pass/5 fail | P02-RISK-03 | NOT_APPLICABLE | StillPresent / P0 | VERIFIED / R-12 | P02_EVID;P03_TERM / reproduced | NOT_APPLICABLE | S0-P3-T1;S12-P3-T1 |
| FND-036 | v0.2.4 live verifier 不可重放 | P01-RISK-01 | NOT_APPLICABLE | N/A / P2 | EXTRACTED / DIAGNOSTIC-P2 | P01_EVID / superseded_or_non_applicable | NOT_APPLICABLE | S12-P3-T2;S12-P3-T4 |
| FND-037 | PyYAML 缺失由 repository fallback 等价 gate处理 | P02-RISK-04 | NOT_APPLICABLE | N/A / P2 | EXTRACTED / DIAGNOSTIC-P2 | P02_EVID / superseded_or_non_applicable | NOT_APPLICABLE | S0-P3-T3 |
| FND-038 | Phase 0.2 remote movement由 no-ref-mutation attestation处理 | P02-RISK-05 | NOT_APPLICABLE | Fixed / P1 | VERIFIED / PHASE-GATE-P1 | P02_ATTEST / fixed_within_phase02_remote_scope | P02_EVID | S12-P3-T4 |

Frozen counts：`StillPresent=23`、`Fixed=7`、`Regressed=0`、`N/A=3`、`New=5`；`P0=26`、`P1=10`、`P2=2`；eligible/open P0/P1 findings `=28`，non-gap `=10`。Crosswalk 的 `current evidence / result` 与 `fact level / priority basis` 是双字段短写；CSV 必须展开为独立列，并令 ref 列的 as-of 等于 registry 中所列 refs 的最大 `observed_at`。

Exact source coverage maps（每个 source item 恰好一个 primary finding；合并发生在同一 finding 的 `source_ids`，不得吞掉 evidence）：

```text
R-01..R-15 = FND-004,FND-010,FND-014,FND-016,FND-020,FND-019,FND-021,FND-022,FND-023,FND-024,FND-025,FND-002,FND-026,FND-027,FND-028
SUR-01..SUR-12 = FND-009,FND-004,FND-002,FND-013,FND-014,FND-011,FND-016,FND-025,FND-027,FND-026,FND-023,FND-012
AUD-01..AUD-15 = FND-001,FND-004,FND-008,FND-009,FND-009,FND-009,FND-015,FND-016,FND-018,FND-019,FND-003,FND-002,FND-025,FND-032,FND-023
P01-RISK-01..10 = FND-036,FND-003,FND-030,FND-006,FND-005,FND-007,FND-008,FND-009,FND-031,FND-029
P01-CONFLICT:RELEASE_IDENTITY_MIXED_VERSIONS->FND-003;P01-CONFLICT:FORMAL_UI_HOME_SOURCE_MISSING->FND-030;P01-CONFLICT:REPOSITORY_APP_CODESIGN_FAILED->FND-006;P01-CONFLICT:APP_EXECUTABLE_HASH_MISMATCH->FND-005;P01-CONFLICT:APP_CODESIGN_EXIT_CODES_PARTIALLY_UNAVAILABLE->FND-006;P01-CONFLICT:MULTIPLE_CANONICAL_RUNTIME_SERVICES->FND-007
PFI-V025-CONFLICT-OWNER-VIEWS->FND-002;PFI-V025-CONFLICT-RELEASE-IDENTITY->FND-003;PFI-V025-CONFLICT-APP-IDENTITY->FND-004;PFI-V025-CONFLICT-RUNTIME-LISTENERS->FND-007;PFI-V025-CONFLICT-STALE-ROUTE-MARKERS->FND-017;PFI-V025-CONFLICT-ROUTE-TARGET-GAP->FND-017;PFI-V025-CONFLICT-GOVERNANCE-SCOPE->FND-033
P02-RISK-01..05 = FND-002,FND-033,FND-035,FND-037,FND-038
P02 derived comparison = P02-LIFECYCLE-COMPARISON->FND-034
```

`priority_registry` 必须把每个 `priority_basis` 解析到 pinned source：`R-xx` 直接继承 Risk Register level；`AUDIT-P0-APP/DATA/METRIC/ROUTE/OWNER/PRODUCTION` 分别绑定 Audit `## 当前 P0/P1/P2` 中 App、data、financial metric、route/workflow、owner truth 与 production acceptance bullets；`AUDIT-P1-FORMULA` 绑定 formula/FX/model bullet。`SUBFINDING-FND-003-P1` 表示 home.js 文件缺失是 FND-003 的 subordinate implementation predicate，不重复提升为第二个 P0；`SUBFINDING-FND-029-P1` 表示 syntax 是 full regression 的已修复子谓词；`PHASE-GATE-P0/P1` 只排序 Stage 0 lifecycle diagnostics；`DIAGNOSTIC-P2` 只排序不适用的 historical/tooling diagnostics。每个 registry record 都含 source selector、source text SHA 与最终 P0/P1/P2 值；禁止凭实现者直觉重排。

五个 `New` 的 non-match 与 priority rationale 固定为：

| finding | non-match proof | priority rationale |
|---|---|---|
| FND-005 | v0.2.4 evidence只证明三个用户入口/compiled launcher code一致，没有 repository App executable full-file 与用户入口相等这一 predicate；因此没有 same-predicate prior pass，不能写 `Regressed` | App identity P0，继承 R-01；fresh full-file hashes写入 P03_TERM |
| FND-006 | 历史 source universe没有 repository bundle strict codesign pass/fail 的同一 predicate | canonical App delivery P0，继承 R-01 |
| FND-007 | 历史 source universe没有 simultaneous healthy canonical listener count/preferrence predicate | App/runtime acceptance P0，继承 `AUDIT-P0-APP` |
| FND-030 | 它只陈述 designated `home.js` source absent，不等同于 FND-003 的整体四方 release identity；absence由 fresh path test证明 | subordinate P1，避免与 FND-003 重复 P0 |
| FND-031 | 它只陈述 `generated_at` 进入 hash input 的 determinism predicate，既有 sources无同一 finding | read-model correctness P1，绑定 S4-P3-T2 |

FND-035 不是 `New`：它是 FND-002 owner-view conflict 下可单独执行的 parameter-owner consistency predicate，source 仅为 `P02-RISK-03`，fresh isolated rerun仍为 3 pass/5 fail时分类 `StillPresent/P0`；不把同一个 active conflict source ID重复分配给两个 primary findings。

All 21 history IDs must occur exactly once in machine-readable `history_item_ids`; free-form rationale never counts as coverage：

```text
FND-001 = HIST-OLD-CLOSEOUT-CLAIMS
FND-004 = OVERRIDE-PER-STAGE-DELIVERY
FND-009 = ARCH-IMMUTABLE-RAW-READMODEL-PROVENANCE
FND-010 = HIST-FAKE-FINANCIAL-ACCEPTANCE
FND-015 = HIST-NAV-COUNT-06;HIST-NAV-COUNT-08;HIST-NAV-COUNT-09;HIST-NAV-COUNT-15;HIST-NAV-COUNT-16;HIST-MARKET-PRIMARY-BAN;HIST-ALIASES-AS-PRIMARY
FND-019 = HIST-DARK-AI-CONSOLE;HIST-TASKPACK-LONGPAGE-PHONE-MOCKUP;HIST-SIDE-REVIEW-HTML;REF-APPROVED-HTML-DIRECTION
FND-024 = ARCH-DURABLE-OPS-BACKUP-RESTORE
FND-025 = HIST-PFI-OS-SECOND-ROOT;ARCH-SINGLE-UI-AND-REAL-RUNTIME
FND-028 = ARCH-DETERMINISTIC-CORE-NO-AUTOTRADE
FND-029 = HIST-FAILURE-EVIDENCE;REF-FAST-DEEP-PATH
```

Validation must assert exact 38 rows, exact status/priority/evidence tuples, exact source maps, and exact 21-history-ID single coverage; row count alone is not acceptance。

They cover：

- Task Pack `R-01..R-15` 全部 15 个风险；
- Surprise findings `1..12` 全部 12 项；
- Current GitHub audit 的 product/data/UI/release/owner/SQLite/public-shell/test facts；
- Phase 0.1 的 10 项 risks 与 6 个 entry conflicts；
- Active Requirements 的 7 个 current conflicts；
- Phase 0.2 的 governance override、PyYAML diagnostic、remote drift/attestation facts；
- `history_deprecation.md` 的 21 个 stable item IDs，全部由 `history_item_ids` exact-once crosswalk 映射。

Priority 只继承上面的 `priority_registry`；五个 New findings 使用冻结的 non-match/priority table。Direct fresh command 可令 finding `fact_level=VERIFIED`，但 priority inference 仍必须写入 rationale；不得把 P2 提升为当前执行范围。

### 5.4 重要 scope-limited Fixed

以下 `Fixed` 只能在明确 scope 内成立，不能扩大为 production acceptance：

- static source 具有 10 个 primary labels；rendered DOM/a11y/no-JS 仍为独立 open gap；
- report source 存在 formula/parameter/sample/source fields；fresh production report verification 仍未完成；
- Phase 0.1/0.2 evidence privacy scan 为零 findings；privacy 仍是全程 gate；
- Phase 0.2 governance override 由外部 attestation 解析；tracked Phase 0.2 evidence 保持 precommit lifecycle 是设计行为；
- `shell.js` syntax gate 已通过；runtime/browser correctness 尚未证明。

## 6. Gap register 模型

`gap_register.md` 不复制 38 rows，而把 findings 聚合为 executable gaps。每个 gap 必须含：

```text
gap_id
priority
linked_finding_ids
current_state
target_state
roadmap_resolution_tasks
dependencies
required_acceptance_evidence
stop_condition
status
```

Eligibility 与去重规则：

- 只有 `StillPresent/Regressed/New` 进入 executable gaps；
- 每个 eligible finding 恰好映射到一个 primary gap；不允许重复计数；
- `Fixed/N/A` 进入 non-gap disposition table，并写 `non_gap_reason`；
- gap priority 必须与 linked findings 相同；若混合 P0/P1，必须拆 gap，禁止用较低级覆盖较高级；
- `N/A` 与 scope-limited `Fixed` 只能留在 non-gap disposition，禁止同时标为 deferred work；
- executable mapping 固定为 13 gaps / 28 eligible findings：

```text
GAP-P0-01 = FND-001;FND-002;FND-027;FND-035
GAP-P0-02 = FND-003;FND-004;FND-005;FND-006;FND-007
GAP-P0-03 = FND-008
GAP-P0-04 = FND-009;FND-010
GAP-P0-05 = FND-012;FND-014
GAP-P0-06 = FND-016;FND-017;FND-018;FND-019
GAP-P0-07 = FND-020
GAP-P0-08 = FND-023;FND-024
GAP-P0-09 = FND-029
GAP-P1-01 = FND-011;FND-013;FND-031
GAP-P1-02 = FND-022
GAP-P1-03 = FND-025
GAP-P1-04 = FND-030
NON_GAP = FND-015;FND-021;FND-026;FND-028;FND-032;FND-033;FND-034;FND-036;FND-037;FND-038
```

排序规则：

1. P0 先按 Roadmap dependency：Stage 0 truth → Stage 1 release → Stage 2 data/time → Stage 3 ledger → Stage 4 core metrics → Stage 5 formulas → Stage 6 route/pages → Stage 7 workflows → Stage 9 reports → Stage 11 SQLite/backup → Stage 12 regression/delivery。
2. P1 绑定 Stage 5/8/10/11 的 confidence、WCAG、durable jobs、cache、boundary 与 reliability gates。
3. 当前 executable P2 gaps 固定为 0；FND-028 是已经生效的 P1 scope control，FND-036/037 是当前合同不适用的 P2 diagnostics，三者均只出现在 `NON_GAP`。不得把 out-of-scope advanced models 偷换为 v0.2.5 deferred backlog。

`gap_register.md` 不宣称修复业务 gaps；它只证明优先级、依赖、owner task 与验收证据可执行。

## 7. Stage 0 Evidence Pack

### 7.1 `baseline.json`

Machine-readable aggregate，包含：source hashes、Phase 0.1/0.2 identities/statuses、Phase 0.2 external attestation、current HEAD/remote snapshot、active contract/projection identity、finding/gap summary、privacy boundary。它只引用既有 evidence，不复制 private rows或 owner claims。

### 7.2 `git_state.txt`

记录 implementation-base 前的 cwd、git root、branch/upstream、HEAD、advertised remote main、merge-base、PFI remote-diff result、clean status、最近 5 条 commit 的 40-char id + one-line subject，以及 `candidate_commit_binding=external_attestation_required`。不得写未来 commit SHA；commit subject 只来自当前 Git history，不含 author/email/message body。

### 7.3 `current_state_matrix.md`

按 Git/repo、formal UI、release identity、App、runtime listeners、data roots、read model、route/nav、owner views、privacy、tests、Phase evidence、Stage acceptance 分层；状态只用 `VERIFIED/CONFLICTED/BLOCKED/NOT_RUN/REFERENCE_ONLY`，每行绑定 evidence。

### 7.4 `data_root_inventory.json`

逐候选、逐 redacted raw source 与逐 redacted database 记录 Roadmap 要求的 metadata，禁止 raw filenames/rows/amounts/accounts/counterparties/absolute private DB filename或 credentials。顶层 schema 固定为 `PFIV025Stage0DataRootInventoryV1`，候选集合和顺序不可由实现者扩张：

| order | id | symbolic path | boundary |
|---:|---|---|---|
| 1 | `ROOT-01` | `env:PFI_DATA_HOME` | 环境变量只读解析；unset 是显式状态 |
| 2 | `ROOT-02` | `repo-worktree:MetaDatabase/PFI` | sparse working-tree candidate，不 materialize |
| 3 | `ROOT-03` | `repo-worktree:PFI/MetaDatabase` | repository-local candidate |
| 4 | `ROOT-04` | `user-state:~/.pfi` | 只读 metadata；不输出 private absolute filename |

另固定一个非 working-tree surface：`GIT-DATA-01 = PHASE_BASE:MetaDatabase/PFI`。它不是第 5 个 candidate root；它只解释 `ROOT-02` 在 sparse worktree absent 而 Git tree object存在的双层事实。`raw_sources` 精确为 `RAW-01..RAW-04`，按 Git tree path stable sort 后分配 ID并全部绑定 `GIT-DATA-01`；`databases` 精确预期一个 Phase 0.1 已发现的 `DB-01` 并绑定 `ROOT-04`。fresh candidate count 不再等于 1 时立即 stop，不静默增删 ID。

所有可能缺失的 metadata 使用同一 typed measurement union，任何 required key 都不得省略或写 JSON null：

```text
present:
  {state: "present", value_type: <enum>, value: <typed value>}
not present:
  {state: "metadata_unavailable" | "not_applicable",
   value_type: <enum>, reason: <nonempty string>,
   resolution_tasks: [<exact Roadmap task IDs>]}

value_type enums and value constraints:
  integer       -> JSON integer >= 0
  epoch_integer -> JSON integer >= 0
  date          -> YYYY-MM-DD
  date_range    -> {start: YYYY-MM-DD, end: YYYY-MM-DD}, start <= end
  sha256        -> ^[0-9a-f]{64}$
  permission    -> readable_no_write_attempt | not_readable | git_object_readable
  string_enum   -> field-specific closed enum
```

Required shape：

```text
candidate_roots[4]:
  root_id, order, symbolic_path,
  existence: present | absent | unset,
  status: ready | source_missing | metadata_only | blocked,
  permission_class, file_count, record_count, date_range, as_of,
  aggregate_sha256: <typed measurements>,
  source_evidence_ref, source_evidence_sha256
repository_object_surfaces[1]:
  surface_id="GIT-DATA-01", related_root_id="ROOT-02",
  git_commit=PHASE_BASE, tree_hash, file_count, bytes,
  extension_counts, permission_class, source_evidence_ref,
  source_evidence_sha256
raw_sources[4]:
  raw_source_id, source_surface_id="GIT-DATA-01",
  source_class, storage_mode="git_tree_object", status,
  record_count, date_range, as_of, bytes, content_sha256,
  permission_class: <typed measurements>,
  source_path_redacted=true
databases[1]:
  database_id="DB-01", root_id="ROOT-04", status,
  candidate_count, bytes, mtime_epoch, permission_class, content_sha256,
  record_count, date_range, as_of: <typed measurements>,
  query_mode="ro&immutable=1", query_only=true,
  quick_check, table_count, unchanged_before_after,
  database_path_redacted=true
read_model:
  storage_mode, raw_file_count, record_count, date_range, as_of,
  evidence_hash, read_model_hash, metric_states, blocked_metric_ids
privacy:
  contains_private_values=false, raw_filenames_emitted=0,
  raw_rows_emitted=0, financial_values_emitted=0,
  credentials_emitted=0, absolute_private_paths_emitted=0
```

四个 raw sources 只通过 Git object stream 只读解析；仅输出 per-file counts/ranges/as-of/bytes/SHA/permission class。`DB-01` 只允许 query-only aggregate count/date metadata；若 schema 无法安全确定 date semantics，则 `date_range/as_of` 使用 typed `metadata_unavailable` 并绑定 `S2-P1-T3`，不得猜测。`ROOT-03` 的非数据说明文件不伪装成 raw source。所有 before/after database hash、bytes、mtime 与 candidate count必须相等。

### 7.5 `history_deprecation.md`

Stage-level immutable reference view，指向 canonical `PFI/docs/pfi_v025/stage_0/history_deprecation.md`，记录其 SHA-256、21 item IDs、projection SHA 与 reference-only rule；不复制 decision table。

### 7.6 Stage-level `terminal.log`

只汇总 Phase 0.1/0.2/0.3 command results、exit codes、external attestation refs/hashes与 known expected failures。Phase 0.3 detailed ledger 保存在 `phase_0_3/terminal.log`。

Phase 0.3 detailed log 必须为每个 fresh claim提供 stable record ID、RFC 3339 `observed_at`、exact command、integer exit code与 outcome enum。至少覆盖 `CURRENT_OWNER`、`CURRENT_WEB`、`CURRENT_RUNTIME_APP`、data-root recheck、五个 New predicates、Fixed scope rechecks，以及 FND-011/014/016/018/023/024/025/029 的 `required_production_proof_missing`。后者 outcome 只允许 `not_run_by_phase_contract` 或 `blocked_missing_required_proof`，不能把需求/范围文档本身冒充 current not-run evidence。

### 7.7 Phase 0.3 quartet

`phase_0_3/evidence.json` 使用 Task Pack Draft 2020-12 schema，并叠加强语义字段：

- exact contract/iteration/Acceptance/override IDs；
- `git_commit=PHASE_BASE`、`git_commit_semantics=implementation_base_before_phase_commit`；
- implementation base、initial/final remote identities与 hydration booleans；
- exact 25 changed files；
- 4 exact task IDs及 candidate status；
- 38-row finding summary与 status/priority counts；
- gap IDs/counts与 P2 zero-executable/out-of-scope disposition；
- acyclic Stage 0 artifact paths + SHA-256；
- commands with integer exit codes；
- privacy/no-side-effect facts；
- `requires_user_acceptance=true`、`contains_private_values=false`；
- `stage_0_whole_review_status=not_started`、`stage_1_status=not_started`。

它是 Stage 0 evidence index。Hash DAG 固定为：

```text
Layer 0: pinned inputs + Phase 0.1/0.2 artifacts + Phase 0.2 external attestation
Layer 1: finding ledger, gap register, baseline, current-state matrix,
         data-root inventory, stage git state, stage history reference,
         stage terminal, phase terminal, risk/rollback, changed-files ledger
Layer 2: phase_0_3/evidence.json hashes Layer 0/1 only
Layer 3: acceptance_request.md hashes finalized evidence.json only
Layer 4: governance companions reference evidence/request paths and status, no reverse content hashes
Layer 5: implementation commit binds all exact 25 files
Layer 6: external attestation binds commit, remote, no-side-effect and CI evidence
```

`evidence.json` 的 `artifact_hashes` **排除自身、acceptance_request.md 与全部 governance companions**；对 excluded items 只在 `changed_files` 记录 path，不记录内容 hash。`acceptance_request.md` 单向绑定 finalized evidence SHA-256。不存在 evidence↔request 或 evidence↔event 互哈希。

## 8. Acceptance request

`acceptance_request.md` 状态固定为：

```text
prepared_pending_whole_stage_review
```

它必须列出：

- version、Stage、Phase、contract/Acceptance；
- Roadmap/Task Pack hashes；
- Phase 0.1/0.2/0.3 evidence paths与 hashes；
- Stage 0 evidence index (`phase_0_3/evidence.json`) SHA-256；
- accepted scope candidate；
- known defects、open P0/P1 gaps与 P2 zero-executable/out-of-scope disposition；
- candidate commit 由 external attestation 绑定，不在 tracked file 预写未来 SHA；
- bare `1` 或任何不绑定 scope/version/commit/evidence/time/defects 的回复无效；
- 下一步只能是 Stage 0 whole-stage fresh review，不是 Stage 1。

本 Phase 不生成 `human_acceptance.json`。Task Pack human schema要求 `accepted_at` 与 acceptance statement，不支持 pending；提前生成会伪造用户验收。

## 9. Governance companion design

### 9.1 Model/formula/parameter

- `MODEL_SPEC.md` 追加 Phase 0.3 非模型审计合同；
- model/formula registries 追加同一 `phase_contracts` record；
- existing `models[]/assumptions[]/formulas[]` byte/structure unchanged；
- `PARAM-PFI-003` 只扩充 evidence/provenance rationale，`config_ref` 和所有 value/version/status/date fields 不变；
- changed IDs 全为空，counts 保持 `1/1/23/10/10`。

### 9.2 Ledger/event/delivery/traceability

- DEVELOPMENT_LEDGER 追加 `ITER-20260711-PFI-V025-S0-P03`；
- development_events 只 append 一个 event，precommit lifecycle 为 `candidate_pass_pending_postcommit_attestation`；
- delivery_tasks 只追加 phase contract，不新增第 11 个 canonical task；
- TRACEABILITY_MATRIX 追加 `S0-P3-T1`、`S0-P3-T2`、`S0-P3-T3`、`S0-P3-T4` 四行，model/formula/parameter 为 `NOT_APPLICABLE`；
- VERSION_MATRIX/STATUS/OWNER_STATUS/CHANGELOG 只追加 candidate overlay，不修改 actual product/version/runtime truth；
- Phase 0.2 external resolution在新 overlay 中明确，旧 tracked historical lines保持不改。

## 10. Validation architecture

### 10.1 Preflight

- exact source hashes与 ZIP integrity；
- clean HEAD、branch/upstream、current remote；
- final Phase 0.2 attestation hash/status/commit；
- 13 core new paths absent、12 companions present；
- protected metadata fingerprint baseline：`~/.pfi`、repository data/MetaDatabase、repository/Applications/Downloads/Desktop App entries；
- no normal fetch/ref update/rebase/merge/push。

### 10.2 Artifact gates

- evidence/human schemas `check_schema`；只验证 evidence instance，不生成 pending human acceptance instance；
- finding CSV exact 18-column header、38 IDs、frozen status/priority/fact counts、nonempty evidence、source coverage、21 history IDs coverage；
- status-specific prior/current evidence tuples、RFC 3339 registry timestamps、CSV max-as-of projection与 `Regressed` same-predicate时间顺序；当前 `Regressed=0` 也必须验证；
- exact source crosswalk、source/evidence/priority registries、AUD-15→FND-023、P01/active exact conflict IDs、five-New non-match rationales与 exact-once history crosswalk；
- all evidence refs resolve to tracked paths, pinned external inputs, finalized `P03_TERM`, or verified local-only attestations；
- `roadmap_resolution_tasks` 每个 token 属于 pinned Roadmap exact task-ID set；禁止 `..` ranges、`Scope Gate` 或说明文字进入该列；
- gap register IDs、priority ordering、finding coverage、Roadmap tasks与 P2 disposition；
- Stage pack exact six basenames、JSON parse、candidate roots exact `ROOT-01..04` order、`GIT-DATA-01`、raw exact `RAW-01..04`、database exact `DB-01`、typed measurement required keys、root/raw/database record-count/time-range/as-of/hash/permission coverage、before/after invariants、artifact hashes与 no-private-value scan；
- stage git state contains exact five recent commit id/subject pairs；
- acceptance request binds finalized evidence SHA，且包含 `prepared_pending_whole_stage_review` 与 no-Stage-1 stop；
- Phase evidence exact 25 paths、4 tasks、integer exits、no future commit SHA；
- registry definitions/values/counts unchanged；event append-only；
- `git diff --check`、Node syntax、isolated collect-only与 known parameter-test baseline真实记录。

### 10.3 Selective governance

Canonical sparse worktree的 all-project semantic expansion不是 Phase gate。最终 staged diff在 guarded detached selective shadow上运行：

```text
validate_project_governance --changed-only --base-ref PHASE_BASE --enforce-sync --semantic
validate_governance_sync --changed-only --base-ref PHASE_BASE --enforce-sync --semantic
```

必须为 selected project PFI、missing companions 0、errors 0、warnings 0，且 shadow worktree清理成功。

### 10.4 Review、commit 与 postcommit attestation

- 至少两名 fresh read-only reviewers：spec/finding fidelity 与 governance/evidence/privacy；
- 所有 findings 必须在同一 25 paths内修复并重跑完整 gates；
- 单一 implementation commit，exact 25-path diff、clean worktree、不 push；
- postcommit guarded selective Lean CI，验证 `SHIP`、selected PFI、legacy exit 0、selector parity、zero tracked write；
- final authoritative remote object-only hydration不得改变 refs、FETCH_HEAD、shallow boundary；
- remote PFI drift quiet、clean worktree、exact commit ledger、protected metadata before/after一致；
- postcommit identity fixed as `conflict_id=PFI-V025-CONFLICT-PHASE03-GOVERNANCE-SCOPE` and `override_id=PFI-V025-S0-P03-GOVERNANCE-COMPANIONS`；
- CI binding and final attestation use the phase-generic boolean `blocks_phase_candidate`，不得沿用 `blocks_phase_0_2_candidate`；
- immutable external attestation schema `PFIV025Phase03AttestationV1` lifecycle从 blocking candidate转为 `resolved_by_approved_override`；tracked evidence不回写未来事实。

## 11. Data/DB/App/runtime impact

```text
business UI change = none
model/formula/parameter value change = none
private data read = none beyond previously approved aggregate metadata
database write/migration = none
App write/install/launch/stop = none
runtime service mutation = none
GitHub push/merge = none
Stage 0 whole-stage review = not_started
Stage 1 = not_started
```

Read-only localhost health、metadata hash、codesign、source marker、Git object和aggregate inventory checks允许；不得输出 private values。

## 12. Risks、rollback 与 stop

### Risks

- Historical sources overlap；coverage map必须保留 source IDs而不是制造重复 rows。
- `Fixed` 很容易被扩大为 production pass；每个 Fixed必须写 scope limitation。
- Stage evidence引用旧 capture；registry `observed_at` 与 CSV prior/current as-of必须保留，fresh recheck与历史 snapshot分开。
- Remote main可移动；最终 attestation必须重新读取 advertised SHA并 fail-closed。
- Sparse governance若直接扩张全项目会产生非本 Phase缺失；只允许 selective shadow，不得把 baseline drift伪装成 pass。

### Rollback

- 设计/计划提交各自可单独 revert；
- implementation commit前只移除 exact 25-path diff；
- commit后使用 append-only-safe compensating commit，保留原 event/evidence与 attestation；
- 不回滚/重写 remote，不删除历史 evidence，不触碰 App/data/DB。

### Stop conditions

- 任一第 26 个 implementation path；
- README/HANDOFF/三基/VERSION/business/UI/data/DB/App/runtime write；
- source hash、Phase 0.2 attestation、finding coverage、schema、privacy、registry invariant、event prefix、governance、review、remote/no-side-effect任一不通过；
- 需要修改/移动/解密/上传 private data；
- 当前 runtime provenance不属于 canonical PFI root；
- 自动进入 Stage 0 whole-stage review 或 Stage 1。

## 13. Mandatory stop statement

```text
Stage 0 / Phase 0.3 candidate result only; Stage 0 whole-stage review and Stage 1 remain not_started in this run.
```
