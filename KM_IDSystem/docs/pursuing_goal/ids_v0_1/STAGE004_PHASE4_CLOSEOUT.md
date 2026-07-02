# IDS v0.1 STAGE-004 Phase 4 Closeout

## Identity

- Stage: `STAGE-004`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE004-P4`
- Acceptance ID: `ACC-STAGE-004`
- Stage title: `旧名称引用扫描`
- Recorded at UTC: `2026-07-02T06:32:47Z`

## Goal

Close out STAGE-004 by recording the changed-file list, final reference-scan
decision, legacy alias retention reasons, rollback path, and Chinese owner
feedback.

This phase does not replace old names, does not modify runtime code, does not
enter STAGE-005, and does not push to GitHub because the STAGE-001..010 batch
is not complete.

## Whole-Stage Review

| Phase | Evidence | Decision |
|---|---|---|
| Phase 1 | `STAGE004_ENTRY_CONTRACT.md`, `STAGE004_PHASE1_SCOPE_BOUNDARY.md` | Boundary is complete. Old-name families, allowed contexts, forbidden paths, and false-positive exclusions are recorded. |
| Phase 2 | `STAGE004_PHASE2_LEGACY_NAME_SCAN.md`, `validate_stage004_legacy_name_scan.py`, `tests/test_stage004_legacy_name_scan.py` | Minimum repeatable validator and unittest slice is complete. Accepted names are excluded from old-name debt. |
| Phase 3 | `STAGE004_PHASE3_VALIDATION_SCAN.md` | Active/customer-visible references, secret-pattern contexts, runtime-output boundaries, and false-positive guards are validated. |
| Phase 4 | this closeout file | ACC evidence, rollback, owner feedback, and no-upload stop line are recorded. |

## Changed Files For STAGE-004

STAGE-004 changed only governance, validator, test, and rendered owner-entry
files:

- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_ENTRY_CONTRACT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_PHASE1_SCOPE_BOUNDARY.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_PHASE2_LEGACY_NAME_SCAN.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_PHASE3_VALIDATION_SCAN.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/STAGE004_PHASE4_CLOSEOUT.md`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage004_legacy_name_scan.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage004_legacy_name_scan.py`
- `KM_IDSystem/docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`
- `KM_IDSystem/docs/governance/roadmap.yaml`
- `KM_IDSystem/docs/governance/events.jsonl`
- `KM_IDSystem/功能清单.md`
- `KM_IDSystem/开发记录.md`
- `KM_IDSystem/模型参数文件.md`

No backend route, frontend route, app bundle display name, runtime database,
schema migration, worker, external API path, raw-material copy, generated
data, report output, dependency folder, GitHub push, PR, or merge was added.

## Final Scan Decision

ACC-STAGE-004 is locally satisfied because the STAGE-004 validator is now a
repeatable local gate and the Phase 3 review found no active display-name debt.

Required final stable checks:

- STAGE-004 unittest returns `OK`;
- legacy-name validator returns `valid=true`;
- legacy-name validator returns `issues=[]`;
- `active_display_debt=0`;
- `forbidden_changed_paths=[]`;
- active/customer-visible scan has no unclassified references;
- secret scan has no actual credential hits;
- no tracked runtime-output files appear under `data/`, `reports/`,
  `outputs/`, `.venv/`, or `frontend/node_modules/`;
- rendered Chinese owner entries are in sync;
- changed scope remains within the allowed STAGE-004 governance and rendered
  owner-entry paths.

## Retained Legacy Alias Reasons

Remaining legacy aliases are retained only for these accepted reasons:

- migration notes that explain the transition to `IDS / Industrial Data System`;
- historical evidence and archived reports that must remain auditable;
- compatibility identifiers and legacy file paths such as `OpMeIcon`,
  `OpMe_structure_report`, `wuhan_kaiming.sqlite`, and old taskpack aliases;
- tests and validators that explicitly assert old-name detection or blocking;
- rollback instructions and stage evidence that must identify earlier names;
- company/source context that is not a new product display name;
- STAGE-003 migration context for standalone `MetaDatabase`;
- accepted current names `ProductMetaDatabase` and `FinanceMetaDatabase`, which
  are not old-name debt.

Old names are not accepted as new formal UI, report, generated-title, schema,
manifest, or formal-document display names.

## Acceptance Evidence

ACC-STAGE-004 evidence consists of:

- Stage entry contract: `STAGE004_ENTRY_CONTRACT.md`;
- scope boundary: `STAGE004_PHASE1_SCOPE_BOUNDARY.md`;
- validator and unit tests:
  `validate_stage004_legacy_name_scan.py` and
  `tests/test_stage004_legacy_name_scan.py`;
- validation evidence: `STAGE004_PHASE3_VALIDATION_SCAN.md`;
- closeout evidence: this file;
- batch lock: `BATCH001_010_UPLOAD_LOCK.yaml`;
- governance roadmap and event log updates;
- rendered Chinese owner entries.

## Rollback

Rollback Phase 4 by reverting the local commit
`IDS v0.1 stage004 phase4 closeout`.

If the whole stage must be rolled back, revert the STAGE-004 commits in reverse
order:

1. Phase 4 closeout.
2. Phase 3 validation evidence.
3. Phase 2 validator, unittest, and scan-slice evidence.
4. Phase 1 entry contract and boundary evidence.

Because this stage did not alter runtime code, data, schema, reports,
dependencies, raw materials, external APIs, or GitHub state, rollback does not
require data cleanup, schema rollback, service restart, dependency
restoration, report cleanup, runtime file restore, or remote PR cleanup.

## Chinese Owner Feedback

STAGE-004 已完成本地验收：旧名称引用已经有可重复扫描工具、分类规则、单测和交付
证据。保留的旧名称只用于迁移说明、历史证据、兼容路径、测试、回滚或来源说明；
不作为新的正式产品显示名。

本阶段未触碰真实原始资料、secrets、本地数据目录、报告输出、依赖目录、后端路由、
前端路由或 macOS 交付显示名。`ProductMetaDatabase` 和
`FinanceMetaDatabase` 保持为已验收的当前名称，不按旧名称债务处理。

## Stop Line

Stop after STAGE-004 Phase 4. Do not enter STAGE-005 in this run.

Do not push, open a PR, merge, or upload to GitHub main until STAGE-001 through
STAGE-010 are all complete, reviewed, repaired, and explicitly ready for the
single 10-stage batch upload.
