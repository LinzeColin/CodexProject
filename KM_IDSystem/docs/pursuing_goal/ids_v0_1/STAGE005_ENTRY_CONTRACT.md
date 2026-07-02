# IDS v0.1 STAGE-005 Entry Contract

## Identity

- Stage: `STAGE-005`
- Local code: `D01-S005`
- Title: `仓库治理回归验证`
- Version: `v0.1`
- Domain: `D01 · 一次性仓库治理与产品命名`
- Entrance: `IDS 系统运营入口`
- Acceptance ID: `ACC-STAGE-005`
- Parallel: `否`
- Estimated time: `4-8 小时`
- P0 taskpack file:
  `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-005_仓库治理回归验证.md`
- P0 stage file SHA-256:
  `7b3d826fb04ed557667e5b25f9d4c4bf301ede24e102cd602ef7ebac602b2716`

## Pursuing Goal

验证一次性仓库治理没有破坏 README、governance、脚本、测试和路径引用。

## Required Reads For STAGE-005

1. `AGENTS.md`
2. `KM_IDSystem/AGENTS.md`
3. `KM_IDSystem/README.md`
4. `KM_IDSystem/docs/HANDOFF.md`
5. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_ROOT_LOCK.yaml`
6. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/V0_1_STAGE_EXECUTION_INDEX.csv`
7. `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
8. P0 taskpack stage file:
   `IDS_v0_1_Final_Chinese_Revised/stages/STAGE-005_仓库治理回归验证.md`

## Governance Regression Boundary

STAGE-005 validates the repository governance surface created or touched by
STAGE-001 through STAGE-004. It is a regression-validation stage, not a broad
cleanup stage.

The validation target includes:

- `README.md` and `docs/HANDOFF.md` owner-facing continuity text;
- `docs/governance/` Lean governance sources and event logs;
- `docs/pursuing_goal/ids_v0_1/` stage contracts, batch lock, validators, and
  tests;
- `scripts/` launcher, smoke-test, and app-entry scripts;
- `backend/tests/` focused regression tests;
- active path references in `backend/app/`, `frontend/`, and `app_bundle/`;
- static metadata contract references under `product_meta_database/`.

The validation target explicitly excludes:

- real raw materials and any `00_ORIGINAL_RAW_DATA` path;
- runtime SQLite/log files under `data/`;
- generated PDF/report artifacts under `reports/`;
- generated or local output folders under `outputs/`;
- dependency folders such as `.venv/`, `frontend/node_modules/`, and build
  caches;
- unrelated CodexProject directories and sparse-checkout expansion.

## Phase Boundary

STAGE-005 must be split into phase-limited runs. Do not implement all of
STAGE-005 in one run.

### Phase 1：范围、输入输出与边界确认

1. Confirm repository governance regression inputs, outputs, allowed paths, and
   forbidden paths.
2. List affected README, governance, roadmap, scripts, tests, and path-reference
   groups.
3. Confirm legacy aliases remain allowed only in migration, historical,
   compatibility, test, rollback, or source-context explanations.

### Phase 2：实现、接入与最小可运行切片

1. Add a minimum repeatable governance regression validator or contract slice.
2. Cover README/governance/script/test/path-reference invariants without runtime
   coupling.
3. Preserve migration notes and rollback context.

### Phase 3：仓库治理回归验证专项验证与异常场景

1. Validate customer-visible wording and current product-name usage.
2. Validate README, governance files, tests, scripts, and path references.
3. Confirm this stage does not touch real materials, secrets, or local data
   directories.

### Phase 4：仓库治理回归验证交付证据、回滚与中文反馈

1. Record changed files, validation results, and rollback steps.
2. Record any retained legacy aliases and reasons.
3. Generate `ACC-STAGE-005` evidence. Unfinished validation cannot pass.

## Acceptance Summary

- The pursuing-goal capability is runnable, or an executable, testable, and
  rollback-safe engineering contract exists.
- Failure states, stop conditions, audit records, and rollback paths are clear.
- Original materials, manifests, evidence ledgers, audit logs, and delivered
  reports are not damaged.
- Tests, scenario checks, or document evidence exist and are truthful.
- Chinese owner-facing feedback is clear, restrained, and business-usable.

## Stop Conditions

- A regression check requires real data but no fixture or owner-authorized
  sample exists.
- Any action may move, delete, overwrite, or clean original files.
- Runtime code, schema migration, or scripts must be changed before a narrow
  Phase 2 contract exists.
- Validation fails for an unknown reason.
- The run tries to enter another phase or another stage.
- Sparse-worktree validation errors are solved by expanding unrelated projects.
- The run tries to push before STAGE-001..010 are complete, reviewed, and
  repaired.

## Rollback

Rollback STAGE-005 governance, validator, test, configuration, UI, or document
changes from the selected phase only. Do not alter original materials,
manifest, evidence ledger, audit log, delivered reports, STAGE-001 naming
contract, STAGE-002 ProductMetaDatabase contract, STAGE-003
FinanceMetaDatabase contract, or STAGE-004 legacy-name scan evidence.
