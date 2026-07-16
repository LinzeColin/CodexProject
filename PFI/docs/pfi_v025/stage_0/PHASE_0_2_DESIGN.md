# PFI v0.2.5 Stage 0 Phase 0.2 Design

## 0. Decision Record

| Field | Value |
|---|---|
| Version / Stage / Phase | `v0.2.5 / Stage 0 / Phase 0.2` |
| Phase title | 最新需求与历史去影响 |
| Roadmap tasks | `S0-P2-T1`, `S0-P2-T2`, `S0-P2-T3`, `S0-P2-T4` |
| Acceptance target | `ACC-PFI-V025-S0-P02-ACTIVE-CONTRACT` |
| Acceptance target origin | Phase-local identifier defined by this approved design; not a Task Pack-provided ID |
| Risk tier | `T2` — machine contract, release policy, data and product boundaries |
| Design status | `spec_approved_for_plan_and_implementation` |
| Approval reference | User explicitly replied `批准，再完成前不要再block，全部都同意` in the active Codex task on 2026-07-11 |
| Approval scope | The committed specification, exact twenty-file Phase implementation override, and later in-goal execution gates are authorized; future completion claims still require their own evidence |
| Selected approach | Strict auditable contract with an isolated Stage 1 candidate App |
| Maximum execution scope | One Phase; no automatic Phase 0.3 or Stage 1 entry |

Authoritative source snapshots:

- Roadmap: `/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md`
  - SHA-256: `fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b`
- Task Pack: `/Users/linzezhang/Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip`
  - SHA-256: `591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2`
- Repository baseline for this design: `332953e002162bce1b28aa616b24ddaa936f1935`
- Live remote observation at design preflight: `origin/main = 385402f7f665fc67ae5d61b566f783691635b22f`;
  it descends from the locally tracked baseline and has no PFI subtree change relative
  to `3c7626008c25aeb6b71ddccc0eb9b999e5d3aedb`.

The hashes above identify the inputs used to make this design. Phase execution must
re-check the source hashes, worktree, branch, HEAD, tracking ref and live remote rather
than treating this design-time observation as permanently current.

## 1. Problem and Required Outcome

PFI currently contains multiple generations of completion claims, navigation rules,
release identities and product-boundary descriptions. Several are useful evidence of
past failures, but they cannot continue to drive v0.2.5. Phase 0.2 must freeze one
machine-readable active contract and three human-readable policies without rewriting
historical records or claiming that current owner views are already unified.

The Phase succeeds only when all of the following are true:

1. Exactly ten primary entries, their order, canonical routes and alias roles are frozen.
2. Superseded history cannot be interpreted as an active requirement.
3. PFI remains the only product and active UI; Alpha, PFI OS and Cloudflare have explicit
   non-overlapping boundaries.
4. Every run remains limited to one Phase and every Stage requires explicit user
   acceptance before the next Stage.
5. Per-Stage GitHub main upload and canonical App reinstall are prohibited. Stage 1 uses
   an isolated candidate App; the one canonical install occurs at `S12-P2-T1`, and the
   one final main upload occurs only after `S12-P3-T4` explicit acceptance.
6. README, HANDOFF, owner documents, VERSION and page/build identity conflicts remain
   visible blockers until their assigned Roadmap work resolves them.

## 2. Scope and Non-Goals

### 2.1 Roadmap core artifacts

The implementation requires exactly these eight Roadmap core artifacts:

1. `PFI/config/pfi_v025_active_requirements.json`
2. `PFI/docs/pfi_v025/stage_0/history_deprecation.md`
3. `PFI/docs/pfi_v025/stage_0/scope_boundary.md`
4. `PFI/docs/pfi_v025/stage_0/run_contract.md`
5. `PFI/reports/pfi_v025/stage_0/phase_0_2/evidence.json`
6. `PFI/reports/pfi_v025/stage_0/phase_0_2/terminal.log`
7. `PFI/reports/pfi_v025/stage_0/phase_0_2/changed_files.txt`
8. `PFI/reports/pfi_v025/stage_0/phase_0_2/risk_and_rollback.md`

### 2.2 Conditional governance companions

Root governance makes the core contract auditable only when these twelve PFI companion
files travel with it:

1. `PFI/docs/governance/MODEL_SPEC.md`
2. `PFI/docs/governance/model_registry.yaml`
3. `PFI/docs/governance/formula_registry.yaml`
4. `PFI/docs/governance/parameter_registry.csv`
5. `PFI/docs/governance/DEVELOPMENT_LEDGER.md`
6. `PFI/docs/governance/development_events.jsonl`
7. `PFI/docs/governance/delivery_tasks.yaml`
8. `PFI/docs/governance/TRACEABILITY_MATRIX.csv`
9. `PFI/docs/governance/VERSION_MATRIX.yaml`
10. `PFI/docs/governance/STATUS.md`
11. `PFI/docs/governance/OWNER_STATUS.md`
12. `PFI/CHANGELOG.md`

They are a proposed user override to the Roadmap Stage 0 allowlist, not authority inferred
from option `1`. Explicit approval of this written specification activates that override
and makes the implementation diff exactly twenty files: eight core artifacts plus twelve
governance companions. The companions may record only this contract iteration,
traceability, evidence and status; they may not invent model, formula or parameter changes.

This design and the later implementation plan are committed separately and are not
counted in the twenty-file implementation diff. If the user does not approve the companion
override, Phase 0.2 remains `blocked_before_write` and the eight core artifacts are not
partially implemented.

Roadmap task binding is exact:

| Task | Deliverable | Candidate acceptance |
|---|---|---|
| `S0-P2-T1` | `pfi_v025_active_requirements.json` | Ten entries, current requirements and boundaries are semantically correct |
| `S0-P2-T2` | `history_deprecation.md` | Superseded history cannot drive development |
| `S0-P2-T3` | `scope_boundary.md` | No second product root or active UI |
| `S0-P2-T4` | `run_contract.md` | One Phase per run, no automatic advancement |

### 2.3 Explicit non-goals

Phase 0.2 does not:

- change UI, routes, runtime code, tests, formulas, parameters, SQLite or real data;
- edit README, HANDOFF, VERSION, `功能清单.md`, `开发记录.md` or `模型参数文件.md`;
- remove compatibility routes or create a second schema/validator implementation;
- launch, install, replace or repair an App bundle;
- mutate `/Applications`, Desktop, Downloads, caches or user data;
- update any ref through ordinary fetch, rebase, merge, push or enter a GitHub upload
  gate; when an advertised live-main SHA is absent locally, one exact object-only
  hydration with `--no-write-fetch-head --no-tags` is allowed only if the complete ref
  snapshot is byte-identical before and after;
- execute Phase 0.3, whole-Stage review, Stage 1 or any later Stage;
- claim Stage 0, v0.2.5 or the overall product goal complete.

## 3. Considered Approaches

### 3.1 Selected — strict auditable contract

Use one normalized JSON contract, three focused human policies and the mandatory four
evidence files. Validate both the weak Task Pack schema and stronger semantic assertions.
Record current conflicts as blockers with resolution routes instead of rewriting them.

This approach was selected because it is the smallest design that satisfies every
Roadmap deliverable and the Task Pack evidence contract without weakening auditability.

### 3.2 Rejected — compressed JSON with summary documents

Keeping nearly all semantics in JSON would reduce prose but make historical disposition,
integration boundaries and policy overrides difficult for a human reviewer to audit.
It also increases the risk that future work reads a boolean without its evidence or
prohibited-use context.

### 3.3 Rejected — immediate owner-view normalization

Editing README, HANDOFF, VERSION and the three owner documents would make the repository
look more consistent, but it violates the Stage 0 allowed-file boundary and would erase
the distinction between recording a conflict and proving that it is resolved.

## 4. Authority and Fact Model

The active contract must encode this exact precedence:

1. Latest explicit user decision in the active task.
2. The pinned v0.2.5 Task Pack and Roadmap snapshots.
3. Current repository, runtime, App, database and test evidence.
4. Historical material only where it does not conflict and is explicitly classified.
5. Historical completion claims, old HTML and old navigation rules have no active
   authority by themselves.

Every requirement or repository/history claim that appears in a decision table or
evidence record uses three separate dimensions:

1. `requirement_disposition`: `ACTIVE`, `SUPERSEDED`,
   `REFERENCE_ONLY_FAILURE_EVIDENCE`, `REFERENCE_ONLY_ARCHITECTURE`,
   `REFERENCE_ONLY_DIRECTION` or `BLOCKING_CURRENT_CONFLICT`.
2. Canonical `fact_level`: `EXTRACTED`, `RECONSTRUCTED`, `PROPOSED`, `UNKNOWN` or
   `NOT_APPLICABLE`, exactly as defined by `docs/governance/STANDARD.md`.
3. Optional `owner_evidence_state`: `VERIFIED`, `PARTIALLY_VERIFIED`, `CONTRADICTED`
   or `STALE`.

Disposition never replaces provenance. For example, a Roadmap target is
`ACTIVE + EXTRACTED`, while a reproduced current route that contradicts that target is
`BLOCKING_CURRENT_CONFLICT + EXTRACTED + VERIFIED`. An unresolved fact is not converted
to `false`, zero or pass; `UNKNOWN` always carries an evidence reference and a concrete
Roadmap resolution task.

## 5. Artifact Architecture

| Component | Single purpose | Depends on | Consumed by |
|---|---|---|---|
| Active Requirements JSON | Machine-enforceable current contract | Task Pack, Roadmap, approved user override, verified route truth | Semantic gate and all later Stages |
| History deprecation policy | Decide what history may and may not do | Task Pack deprecation policy and bounded repository evidence | Reviewers and future implementation plans |
| Scope boundary policy | Prevent second product/UI and unsafe integration | Product boundary contract and current implementation topology | Alpha, PFI OS, Cloudflare and App work |
| Run contract | Freeze one-Phase execution, files, gates and rollback | Roadmap, project governance and final-delivery policy | Every later Phase run |
| Evidence quartet | Prove actual execution and preserve residual risk | All four deliverables and real command output | Phase review and Stage review |

Data flows in one direction:

`pinned sources + verified repo facts + approved user override`
→ `active requirements JSON`
→ `three human policies`
→ `schema + semantic + repository validation`
→ `Phase evidence and candidate result`.

Historical documents never flow directly into implementation. They first pass through
the explicit disposition table.

## 6. Active Requirements JSON Design

The JSON uses schema identifier `PFIV025ActiveRequirementsV1` and contract identifier
`PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS`. Its root key set is exact:

1. `schema`
2. `contract_id`
3. `version`
4. `authority_order`
5. `source_hashes`
6. `official_nav`
7. `navigation_policy`
8. `product_boundaries`
9. `experience_policy`
10. `data_policy`
11. `financial_policy`
12. `retained_business_rules`
13. `execution_policy`
14. `delivery_policy`
15. `blocking_conflicts`
16. `policy_overrides`

The Task Pack schema validates only five structural fields and does not constrain most
values. Phase validation must therefore assert the exact root keys, types, enums, arrays,
booleans and cross-field invariants described below.

The exact top-level identity fields are:

- `schema = "PFIV025ActiveRequirementsV1"`;
- `contract_id = "PFI-V025-STAGE0-PHASE02-ACTIVE-REQUIREMENTS"`;
- `version = "v0.2.5"`;
- `source_hashes.roadmap_sha256` and `source_hashes.task_pack_sha256` equal the hashes in
  Section 0.

### 6.1 Official navigation

`official_nav` is an ordered array of exactly these ten unique strings:

1. 首页总览
2. 账户与资产
3. 账本流水
4. 投资管理
5. 消费管理
6. 数据源与上传
7. 建议与复盘
8. 报告与洞察
9. 市场与研究
10. 设置

`navigation_policy.target_primary_routes` freezes the v0.2.5 target mappings from
Roadmap Appendix A:

| Entry | Route |
|---|---|
| 首页总览 | `/overview` |
| 账户与资产 | `/accounts` |
| 账本流水 | `/ledger` |
| 投资管理 | `/investment` |
| 消费管理 | `/consumption` |
| 数据源与上传 | `/data` |
| 建议与复盘 | `/review` |
| 报告与洞察 | `/reports` |
| 市场与研究 | `/market-research` |
| 设置 | `/settings` |

`navigation_policy.target_compatibility_aliases` freezes the Roadmap compatibility
inputs. They must never appear in primary navigation, the accessibility tree or the
no-JS primary-entry list:

| Input | Canonical route |
|---|---|
| `/home` | `/overview` |
| `/market` | `/market-research/market` |
| `/research` | `/market-research/research` |
| `/holdings` | `/investment/holdings` |
| `/strategy-lab` | `/market-research/strategy-lab` |
| `/investment/strategy-lab` | `/market-research/strategy-lab` |
| `/data-system` | `/settings/data-system` |

Current repository route truth is evidence, not the target contract. The current primary
inventory uses `/home` instead of `/overview` and `/sources-upload` instead of `/data`.
Its six declared command/search inputs currently resolve as follows:

| Current input | Current resolved route |
|---|---|
| `/home/today` | `/home` |
| `/market/watch` | `/market-research?tab=market` |
| `/market/research` | `/market-research?tab=research` |
| `/investment/holdings` | `/investment?tab=holdings` |
| `/market/lab` | `/market-research/strategy-lab` |
| `/settings/data` | `/settings?tab=data-system` |

The shell additionally accepts `/`, `/market`, `/research`, `/holdings`,
`/strategy-lab`, `/data-system`, `/investment?tab=market`,
`/investment?tab=research` and `/investment/strategy-lab`. Some labels overlap the target
alias inventory, but their current destinations and query-based secondary routes are not
the complete Appendix A target.

The JSON therefore separates `target_primary_routes`,
`target_compatibility_aliases`, `verified_current_primary_routes`,
`verified_current_declared_aliases` and `verified_current_shell_compatibility_inputs`,
with `current_gap_status="blocked_pending_S6-P1"`. Current mappings are
verified current implementation facts, including the current internal workspace bindings
`home/accounts/ledger/investment/consumption/sync/recommendations/insights/market_research/settings`;
those workspace identifiers are repository evidence, not Appendix A target requirements.
The target/current mismatch is a
`BLOCKING_CURRENT_CONFLICT` resolved only by `S6-P1-T1`, `S6-P1-T2` and `S6-P1-T3`.
Phase 0.2 must not change route code or relabel current mappings as target-complete.

The only target canonical Strategy Lab route is `/market-research/strategy-lab` with
primary route `/market-research`. The current implementation binds it to internal
workspace ID `market_research`; that workspace ID is verified repository evidence, not an
Appendix A requirement.

### 6.2 Product and integration boundaries

The machine contract must express all of these typed invariants:

- `product_boundaries.pfi_only`, `alpha_read_only`, `no_ralpha` and
  `exclude_serenity_alipay` are boolean `true`, as required by the Task Pack schema.
- PFI is the only product subject and the only active UI.
- Alpha remains independently operated and may only read a minimized, versioned PFI
  Context. It may not become a PFI primary entry or write back ledger, holdings or trades.
- Alpha Context data fields are exactly `net_worth_state`, `investable_cash_state`,
  `cashflow_pressure`, `asset_allocation`, `risk_budget`,
  `investment_behavior_tags`, `consumption_pressure_summary` and `data_freshness`.
- Alpha Context metadata includes `schema_version`, `as_of`, source/read-model hash and
  privacy classification.
- Ralpha does not exist; Serenity-Alipay is excluded.
- `PFI/src/pfi_os` may remain an internal implementation namespace. Historical PFI OS
  architecture is reference-only and may not become a second product root or second UI.
- Cloudflare public shell is an isolated, qualitative and redacted public surface. It may
  not read private accounts, holdings, reports, SQLite, credentials or absolute paths,
  and it cannot replace local PFI acceptance.
- QBVS and QuantLab remain internal or independent capabilities, never primary PFI
  navigation entries.
- Live trading, automated orders and payment execution remain unauthorized.

### 6.3 Experience, data and financial policies

`experience_policy` freezes a bright, high-quality, restrained Chinese software
experience; independent secondary-page semantics; real URL/history/deep-link/refresh,
focus and error behavior; Settings-only feedback/configuration; and reduced-motion
support. `motion_user_disable_supported=true`, `haptics_user_disable_supported=true` and
`unsupported_feedback_silently_degrades=true`; the controls live only in Settings. A
title-swapped template, anchor-only long page or internal review console cannot satisfy it.

`data_policy` requires real financial inputs through read-only copies or isolated
snapshots; no financial fallback; `blocked` or `not_run` when real input is unavailable;
no non-ready financial zero; and source, coverage, as-of, formula, parameter and
read-model hashes for every metric. Private values may not enter Git or evidence.
Its schema-required fields are exactly typed booleans:
`real_financial_data_only=true` and `no_financial_fallback=true`.

Metric state distinguishes at least `ready`, `confirmed_zero`, `partial_coverage`,
`source_missing`, `not_loaded`, `path_error`, `parse_failed`, `outdated_snapshot`,
`permission_denied`, `calculation_failed`, `reconciliation_failed`, `valuation_missing`
and `filtered_empty`. Only `ready` or a `confirmed_zero` backed by source, record count,
coverage, as-of, formula, read-model hash and confidence/coverage evidence may render a
financial zero.

`financial_policy` freezes CNY as the primary display currency; AUD/CNY direction as
`1 AUD = X CNY`; `4.81` is an explanatory example and may never be hardcoded as a
production value. FX is read once daily at 06:00 Australia/Sydney with no ordinary-run
network dependency; before 06:00, on weekends and on NSW holidays, the previous valid
publication day remains effective. The UI and reports expose `消费总流出金额（用户定义活动口径）`,
`生活消费金额` and `投资资金流出/配置金额` from the same sources. Investment funding and
purchases may enter the user-defined total-outflow view without becoming living
consumption or net-worth loss. Source-record deduplication, Economic Event lineage and
formula rules jointly prevent double counting.

### 6.4 Retained business rules

`retained_business_rules` freezes the Task Pack section 3.6 rules as typed values:

- source/account roles are not hardcoded; multiple roles and effective periods are allowed;
- `category_limits = {l1_max: 12, l2_per_l1_max: 5, l2_total_max: 50}` and each
  transaction has exactly one primary category;
- default/custom tags support create, update, disable, history, persistence and view filters;
- classification confidence weights are field completeness `30`, amount direction `10`,
  rule match `20`, merchant/counterparty `15`, Interconnection `15` and historical
  consistency `10`, with threshold `70`;
- cash-flow windows are exactly `[7, 21, 30, 60, 90, 180, 360]` days;
- Parameter Center and Interconnection Map are formal secondary pages in the single PFI UI.

### 6.5 Execution and delivery policies

`execution_policy` must assert:

- `max_phases_per_run` is integer `1`, not boolean `true` or a truthy value;
- `stage_requires_user_acceptance` is boolean `true`;
- automatic Phase and Stage advancement are both false;
- `stage_requires_independent_review=true`;
- `stage_findings_must_be_remediated_before_acceptance=true`; a blocked finding blocks
  Stage acceptance rather than bypassing remediation;
- `stage_requires_rereview_pass=true`;
- the required sequence is whole-Stage fresh review → findings remediation → re-review
  pass → explicit user acceptance → next Stage;
- documentation, toast, marker, screenshot path or a single number cannot prove completion;
- review findings and evidence may be persisted, but private chain-of-thought or internal
  review transcripts may not become product artifacts.

`delivery_policy` must assert:

- `local_phase_commits_allowed=true`;
- `per_stage_github_main_upload_allowed=false`;
- `per_stage_app_reinstall_allowed=false`;
- `stage_1_validation_mode="isolated_candidate_app"` and isolated validation is required;
- the isolated candidate may be launched through Finder but may not replace or mutate
  `/Applications/PFI.app`, Desktop or Downloads entry candidates;
- `final_delivery_stage=12`, `final_app_reinstall_required=true` and
  `final_app_reinstall_gate="S12-P2-T1"`;
- `final_github_main_upload_required=true` and
  `final_github_main_upload_gate="after_S12-P3-T4_explicit_acceptance"`;
- `expected_remote_main_sha_required=true`,
  `final_remote_parity_verification_required=true` and force push is prohibited;
- final remote parity, installed-App identity and local owner-view consistency are separate
  evidence gates and all must pass.

### 6.6 Blocking conflicts and policy overrides

At minimum, `blocking_conflicts` records:

1. README, HANDOFF and the three owner documents still present v0.2.4/final-delivery
   state as current; routed through `S0-P3-T1` gap registration and finalized by
   `S12-P3-T1`.
2. `PFI/VERSION`, page metadata, launcher markers and App plist/executable identify
   different versions/builds; release identity resolution begins at `S1-P1-T1` and
   final normalization is `S12-P3-T1`.
3. Repository and installed App executable hashes differ, repository codesign is not
   healthy, and canonical entries must not be described as a v0.2.5 install before
   `S12-P2-T1` evidence.
4. Two canonical-root Streamlit listeners were observed during Phase 0.1; the preferred
   runtime is resolved at `S1-P3-T2` and finally re-verified at `S12-P2-T2`.
5. Route modules contain stale v0.2.3/v0.2.4 stage identifiers and duplicate route
   inventories; release identity is routed to `S1-P1-T1`/`S12-P3-T1`, while navigation
   inventory convergence is routed to `S6-P1-T1`, `S6-P1-T2` and `S6-P1-T3`.
6. Current primary and compatibility routes do not yet match Roadmap Appendix A. The
   target is frozen now, while implementation and browser proof remain blocked on
   `S6-P1-T1`, `S6-P1-T2` and `S6-P1-T3`.
7. Root governance requires meaningful config/evidence changes to travel with canonical
   governance records, but the Roadmap Stage 0 allowlist permits only the eight core
   artifacts. The current project-level sparse worktree also makes changed-scope CI fail
   on tracked-but-unmaterialized root/project paths. This conflict is registered under
   `S0-P3-T1` and blocks Phase 0.2 candidate pass until the user explicitly authorizes a
   bounded governance-companion scope or a separate root-governance compatibility run.

Every item has a unique conflict ID, lifecycle status, evidence reference, affected
surfaces, prohibited claims, `blocks_phase_0_2_candidate` and a concrete resolution
route. Unresolved items use `status="blocked"`. Ordinary current-state blockers are
expected outputs of the contract freeze and do not by themselves fail it; item 7 is a
governance precondition and does. Phase 0.2 may not claim `release_identity_unified`,
`v0.2.5_accepted` or final-delivery readiness.

`blocking_conflicts` is an object with `unresolved_result="blocked"`,
`self_declared_unified_allowed=false`, `evidence_reference_required=true`, a
`blocks_claims` array containing those three prohibited claims, and an `items` array for
the conflict records above. `policy_overrides` is an array of versioned override records.

Item 7 has an explicit lifecycle:

1. Before written-spec approval: `status="blocked"`,
   `blocks_phase_0_2_candidate=true`.
2. After approval activates the exact twenty-file scope but before validation:
   `status="approved_pending_validation"`, block remains true.
3. After staged companion coverage, sparse-aware preflight and clean post-commit
   changed-scope attestation all pass: the external attestation records
   `status="resolved_by_approved_override"` and
   `blocks_phase_0_2_candidate=false`, bound to the override ID, Phase commit and CI
   evidence reference.
4. Any missing companion or failed preflight/attestation returns or retains
   `status="blocked"` and the Phase cannot reach candidate pass.

The committed contract/evidence may truthfully remain
`approved_pending_postcommit_attestation`; the authoritative final run result comes from
the external attestation and must not be back-written into the same commit.

`policy_overrides` explicitly records that the latest user decision supersedes the
canonical-install portion of Roadmap `S1-P3-T1` and the mutating interpretation of
`S1-P3-T3`. The replacement is isolated-candidate validation in Stage 1, read-only entry
inventory, canonical install at `S12-P2-T1`, and final main upload only after
`S12-P3-T4`. This override must appear consistently in the JSON, history policy and run
contract; it must never be applied silently.

Each override record has `override_id`, `authority="latest_user_decision"`,
`source_contract`, `original_action`, `status="superseded"`, `effective_rule`,
`replacement_gate` and `evidence_ref`.

Approval of this written specification activates a second override,
`PFI-V025-S0-GOVERNANCE-COMPANIONS`: the Roadmap's eight core artifacts remain unchanged,
while the twelve root-required PFI governance companions in Section 2.2 become allowed
same-Phase audit files. It authorizes no root tool, classifier, project-registry or
unrelated-project change.

Final delivery uses three explicit commit identities. `release_content_commit` is frozen
after final remote synchronization and Stage 12.1 regression; the fresh final candidate
App is built from and embeds that commit. `acceptance_candidate_commit` is its descendant
and contains final owner-document candidates, evidence index and a pending acceptance
request without changing runtime content. Human acceptance binds that existing commit,
`release_content_commit` and the evidence-index/acceptance-request content hashes.
`final_record_commit` is created only after acceptance to append the accepted release
record; it does not contain or claim its own SHA. An external post-commit attestation binds
its SHA, the accepted content hashes and the push/parity result.

Before the single canonical install, the run fetches/read-checks live main, integrates it
without force, freezes `expected_remote_main_sha`, proves the release branch will be a
strict fast-forward, and then forbids rebase/merge or runtime-content commits. After
`S12-P3-T4`, the single push must fast-forward that exact remote SHA to
`final_record_commit`. Pre-push remote drift, or a failed push that leaves the remote ref
unchanged, keeps delivery `blocked`, restores the saved canonical App and requires a new
explicit user decision. If the remote ref did update but post-push verification or parity
fails, freeze the remote/local/App state, keep delivery `blocked`, and prohibit automatic
App rollback, remote rewrite or force push pending an explicit recovery decision. No path
silently reconciles drift or performs a second automatic install.

### 6.7 Governance preflight blocker

A read-only design preflight reproduced two independent governance problems:

1. `lean_governance.py ci --changed-only` fails in this project-level sparse worktree
   because tracked root schemas/tools and other registered project paths are not
   materialized, and existing PFI governance references a missing test path.
2. The proposed core diff is classified as parameter/config, test/evidence and—because
   `risk_and_rollback.md` contains `risk` in its path—model-behavior change. Current sync
   rules therefore demand these twelve companion files outside the Roadmap allowlist:
   `PFI/docs/governance/MODEL_SPEC.md`, `model_registry.yaml`, `formula_registry.yaml`,
   `parameter_registry.csv`, `DEVELOPMENT_LEDGER.md`, `development_events.jsonl`,
   `delivery_tasks.yaml`, `TRACEABILITY_MATRIX.csv`, `VERSION_MATRIX.yaml`, `STATUS.md`
   and `OWNER_STATUS.md` under the same directory, plus `PFI/CHANGELOG.md`.

No validator result is downgraded and no companion file is added silently. Approval of
this written specification activates the exact twenty-file scope in Section 2 and requires
a sparse-aware, non-private validation method. If that approval is declined, a separate
root-governance compatibility run and a revised/re-approved design are the only remaining
path; the current eight-core-only Phase remains `blocked_before_write`.

## 7. History Deprecation Design

`history_deprecation.md` is a decision table, not a narrative archive. Each row contains:

- stable item ID;
- historical rule or artifact class;
- disposition from Section 4;
- evidence reference;
- prohibited use;
- active replacement or retained principle;
- resolution task where applicable.

The table must cover at least:

- old 8/9/6/15/16 primary-navigation contracts;
- the ban on Market & Research as a primary entry;
- old aliases presented as primary navigation;
- dark AI console, Task Pack page, long-page anchors and phone mockups;
- old version completion and closeout text;
- PFI OS as a product root or six-workspace UI;
- side-review HTML and internal review consoles;
- demo, sample, synthetic, fixture or fake financial acceptance;
- old HTML/screenshots, shell/test failures and Stage/closeout prose as failure evidence;
- single UI, real routes/API/SQLite/evidence, immutable raw data, read-model provenance,
  reliable tasks, backup/restore, deterministic core and no auto-trading as retained
  architecture principles;
- Fast/Deep Path only as future performance-architecture reference, never as a new
  v0.2.5 product feature or Stage expansion;
- approved HTML only as bright/software/data-gated interaction direction;
- per-Stage upload and Stage 1 canonical reinstall rules superseded by the approved
  final-delivery policy.

Historical test results remain historical facts. The policy changes their applicability,
not their recorded result.

## 8. Scope Boundary Design

`scope_boundary.md` defines the formal PFI UI as `PFI/web/index.html`, its route/shell
modules and the local App/localhost wrapper serving that same product. Streamlit or
`pfi_os` implementation paths do not create a second product when they serve this formal
UI and obey the same release identity.

App and localhost are two entry surfaces to one build and one canonical runtime, not two
active UIs. During any Acceptance there is exactly one designated canonical listener and
one render implementation. `pfi_os`/Streamlit may host backend or shell plumbing but may
not expose independent navigation, widgets or a parallel product surface. Multiple live
listeners remain a blocker until the runtime task identifies and proves the canonical one.

The document uses a boundary matrix with columns for owner, allowed reads, allowed writes,
prohibited behavior, privacy class, release identity and evidence gate. It covers PFI,
Alpha, PFI OS, Cloudflare public shell, QBVS/QuantLab and the isolated Stage 1 candidate
App.

No integration is allowed merely because a directory or old document exists. A boundary
becomes executable only in the Roadmap Phase that owns its schema, tests, privacy review
and evidence.

## 9. Stage 1 Candidate App Override

The approved override preserves real App/browser evidence without violating the one-time
canonical-install policy:

| Stage 1 task | Approved interpretation |
|---|---|
| `S1-P3-T1` | Build or repair an isolated/repository candidate `PFI.app`; do not install it into a canonical user entry |
| `S1-P3-T2` | Launch that candidate through Finder and verify localhost, new profile, cache behavior and one release identity |
| `S1-P3-T3` | Read-only inventory `/Applications`, Desktop and Downloads; prove they were not mutated and do not call them v0.2.5 |
| `S1-P3-T4` | Produce Stage 1 evidence, disclose the canonical-install deferment and stop for user acceptance |

Stage 1 may reach candidate pass only if the isolated candidate genuinely launches the
current checkout and its frontend, backend, manifest, asset and commit identities match.
If that cannot be proved, Stage 1 is `blocked`; documentation cannot substitute for the
App run.

Stage 1 uses an explicit candidate path and checkout-binding hash. It must not invoke
`installPFIEntryApps.sh` in a mode that targets Downloads or all canonical entries. Its
HOME, `PFI_DATA_HOME`, browser profile, runtime/cache directories and ports are isolated;
hashes and link targets for `/Applications/PFI.app`, Desktop and Downloads are captured
before and after. LaunchServices registration and process cleanup are recorded. The
Stage 1 candidate is disposable and is never promoted as the final App.

The candidate source is `PFI/macos/PFI.app`. Runtime validation copies it only to
`$STAGE1_TEMP_ROOT/PFI.app`, where `$STAGE1_TEMP_ROOT` is a run-created `mktemp` directory
recorded in evidence and never equals `/Applications`, Desktop or Downloads. The run
records the source tree hash, copied bundle hash and resolved project-root binding before
Finder launch.

At Stage 12.1, after real-data workflows and release regression pass, a fresh final
candidate is rebuilt from `release_content_commit`; its build, asset and commit hashes are
re-verified. At `S12-P2-T1`, the pre-existing canonical App is hashed and backed up, then
that fresh final candidate receives the one successful canonical promotion. Failure
restores the old bundle, leaves the release blocked and prohibits automatic retry. Stage
12.2 then performs the real Finder lifecycle and UAT. GitHub main is not uploaded until
the bound release/evidence is explicitly accepted at `S12-P3-T4`.

## 10. Run Contract Design

`run_contract.md` must bind each future run to:

1. one Stage, one Phase, one Acceptance target;
2. exact read, write and explicitly-not-modified paths;
3. exact commands and expected evidence, including real exit codes;
4. data, database, App and migration impact;
5. risk tier, stop conditions and append-only-safe rollback;
6. immutable source hashes and pre/post Git/runtime/data invariants;
7. candidate-only completion language and a mandatory stop statement.

At Stage boundaries the run contract additionally enforces whole-Stage fresh review,
finding remediation, re-review pass and explicit user acceptance in that order. A blocked
finding blocks the Stage; it does not become an acceptance waiver.

The Phase 0.2 implementation run stops immediately for an unexplained dirty worktree,
unconfirmable branch/live remote, PFI changes on live remote, source-hash drift, private
data access requiring modification/decryption/upload, runtime provenance outside the
canonical checkout, or any needed write outside the approved twenty-file implementation
set.

Root-governance companion files are not silently added. Until the conditional scope in
Sections 2.2 and 6.7 receives explicit user approval, Phase 0.2 implementation is
`blocked_before_write`; a plan may describe the gate but may not claim that skipping
changed-scope governance is acceptable.

## 11. Validation Design

The implementation plan must instantiate the pre-commit checks below with exact commands
and capture their exit codes in `terminal.log`:

1. **JSON syntax:** `jq -e` on the Active Requirements JSON and evidence.
2. **Active Requirements schema:** stream `active_requirements.schema.json` from the
   pinned ZIP, run `Draft202012Validator.check_schema`, then validate the JSON.
3. **Evidence schema:** stream `evidence_pack.schema.json` from the same ZIP, run
   `check_schema`, then validate `evidence.json`.
4. **Semantic contract:** inline Python asserts exact root keys, types, ten-entry order,
   canonical targets, aliases, boundaries, data/financial/retained-business rules,
   Stage review/remediation, one-Phase policy, final-delivery gates, conflict structure
   and policy overrides.
5. **Cross-document parity:** inline checks prove IDs, source hashes, dispositions,
   Stage 1 override and stop rules agree across all four deliverables.
6. **Route target and current truth:** semantic assertions prove the target mappings equal
   Roadmap Appendix A. Separate read-only Node assertions load current route/navigation
   modules, reproduce the verified-current snapshots and prove every target/current
   mismatch is present in `blocking_conflicts`. No current-to-target parity is claimed
   before Stage 6.
7. **Affected regressions:** run only explicitly enumerated read-only contract regressions
   after inspecting their I/O. Use dedicated temporary `HOME`, `PFI_DATA_HOME`, `TMPDIR`,
   pytest base/cache directories, browser profile and ports, plus before/after hashes for
   real `~/.pfi`, canonical Apps, repository data and SQLite. Tests that require tracked
   `MetaDatabase/PFI`, private values, inherited App entries or a default operational DB
   remain `not_run`; the legacy full PFI suite must not run against this sparse worktree
   or inherited user environment and is not claimed as a Phase 0.2 pass.
8. **Governance diff preflight:** classify the staged names and prove the authorized
   companion set covers every required governance file. This is not changed-scope CI and
   cannot be reported as its substitute.
9. **Repository quality:** privacy scan, forbidden-path diff, exact authorized-file
   boundary, `git diff --check` and staged-name parity.

On the clean Phase commit, run the real
`lean_governance.py ci --changed-only --base-ref $PHASE_BASE` contract as an external
post-commit attestation. Clean worktree, final Phase commit SHA, live-remote recheck and
commit-content verification are attested in the same out-of-band result. They are never
appended back into `terminal.log`, which would create a self-referential dirty commit. A
failed post-commit attestation invalidates the pre-commit candidate and leaves the Phase
blocked until remediation.

Active Requirements schema success alone is never a pass because that schema accepts
semantically wrong booleans, arbitrary ten-entry labels and invalid phase counts.

## 12. Evidence and Result Semantics

`evidence.json` uses a versioned schema name and satisfies every required field in the
Task Pack Evidence schema:

- `version="v0.2.5"`, integer `stage=0`, string `phase="0.2"`, tasks, Acceptance ID and
  `requires_user_acceptance=true`;
- `status` is exactly one of `candidate_pass`, `fail`, `blocked` or `not_run`;
- `git_commit` is the audited implementation-plan/base commit `$PHASE_BASE`, not the
  evidence-containing final commit; optional tree/content hashes bind staged content
  without requiring an artifact to contain its own future SHA;
- `allowed_files_obeyed` is a real boolean and can be true only for the explicitly
  authorized diff;
- pinned source hashes and exact design/plan/base references;
- per-task status and evidence references;
- `commands` contains objects with `command`, integer `exit_code` and factual `summary`;
- semantic, boundary, privacy and no-side-effect checks;
- `changed_files`, `explicitly_not_done` and `risks` are string arrays;
- `rollback` is a concrete string and `contains_private_values=false`;
- open blocking conflicts and their Phase-blocking classification;
- confirmation that no push, canonical App install, real-data mutation, Phase 0.3 or
  Stage 1 execution occurred.

An evidence status of `candidate_pass` is explicitly pre-commit-candidate status and
requires a successful external post-commit governance attestation. If that attestation
fails, the authoritative run result is `blocked`/`fail`; the committed candidate evidence
is not presented as the final Phase result and must be remediated in a later local commit.

`terminal.log` contains commands and bounded outputs, not private financial values.
After written-spec approval, `changed_files.txt` contains the exact twenty authorized
implementation files from Sections 2.1 and 2.2 in sorted order.
`risk_and_rollback.md` separates current blockers, residual risks, stop conditions and
the append-only-safe compensating rollback procedure.

Candidate pass means only that Phase 0.2 contract freeze met its Acceptance. It does not
resolve the recorded blockers or accept Stage 0.
Before the conditional governance-companion scope is approved, Phase 0.2 cannot claim
candidate pass or begin implementation.

## 13. Error Handling and Rollback

- Source drift before implementation: stop and re-baseline; do not silently update hashes.
- Repository/history conflict without a disposition: record `BLOCKING_CURRENT_CONFLICT`
  and fail the relevant task.
- When an actually executed financial workflow or metric Acceptance requires missing real
  input: `blocked` or `not_run`; never use fallback or financial zero. Phase 0.2 itself
  validates the policy contract and does not require reading account or holding values.
- Schema pass with semantic failure: Phase result is fail.
- A transient mutation proven by the run-created manifest may be restored only to its
  exact pre-snapshot and then verified. For an unknown or pre-existing mutation, stop,
  preserve the diagnostic and perform no destructive cleanup without user direction.
- Partial artifacts: do not label candidate pass or commit the Phase as complete.

Repository rollback before the Phase implementation commit deletes only the eight new core
artifacts and restores each modified governance companion to its exact `$PHASE_BASE`
content through a reviewed reverse patch; unknown or pre-existing changes are never
overwritten. After commit, a raw `git revert` is prohibited because it would remove the
committed append-only `development_events.jsonl` event. Rollback uses a new compensating
commit: reverse the other Phase changes, preserve every prior event line, append a
rollback/supersession event, and synchronize the governance views required for that
rollback. This repository rollback is separate from the transient-runtime rule above. The
design and plan commits remain separate, reviewable history unless explicitly reverted.

## 14. Review and Next Gate

This document records the approved design direction. Its single local design commit is
valid only after a fresh spec self-review confirms no placeholders, contradictions, scope
drift or ambiguity; any self-review correction is folded into that same commit.

The written specification is now explicitly approved under the standing user decision
recorded in Section 0. The implementation plan may therefore be committed separately and
executed under the exact twenty-file scope; completion claims remain evidence-bound.

If the governance precondition is explicitly resolved and all Phase checks pass, Phase
0.2 implementation later stops with:

`Stage 0 / Phase 0.2 candidate_pass accepted by Codex; Phase 0.3 remains not_started.`

Phase 0.3 may begin only in a new one-Phase run under the standing user authorization.

Otherwise it stops with a factual `blocked` or `fail` result and does not enter Phase 0.3.

Phase 0.3, whole-Stage review, review remediation, Stage 1, real-data work, final GitHub
upload and final canonical App install all remain outside this design-doc run.
