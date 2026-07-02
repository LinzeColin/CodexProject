# IDS v0.1 STAGE-004 Phase 2 Legacy Name Scan Slice

## Identity

- Stage: `STAGE-004`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE004-P2`
- Acceptance ID: `ACC-STAGE-004`
- Stage title: `旧名称引用扫描`
- Recorded at UTC: `2026-07-02T06:18:23Z`

## Goal

Create the smallest repeatable legacy-name scan slice for STAGE-004. This
phase adds a deterministic validator and focused unittest coverage so old
name references can be classified before any replacement or cleanup is
proposed.

This phase does not replace old names, does not modify runtime code, and does
not enter Phase 3.

## Implemented Slice

Phase 2 added:

- `validate_stage004_legacy_name_scan.py`
- `tests/test_stage004_legacy_name_scan.py`
- this Phase 2 evidence file
- governance, batch-lock, events, and rendered Chinese owner entry updates

The validator scans tracked text files under `KM_IDSystem/`, excluding
runtime output, dependency, cache, report, and data folders. It classifies
legacy-name hits into:

- `allowed_legacy_context`
- `active_display_debt`

The first implementation deliberately treats active display debt as a blocking
issue. Phase 3 is responsible for broader validation and abnormal scenarios.

## TDD Evidence

Red:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage004_legacy_name_scan.py -q`
- Result before implementation: 2 expected errors because
  `validate_stage004_legacy_name_scan.py` did not exist.

Green:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage004_legacy_name_scan.py -q`
- Result after implementation: 2 tests returned `OK`.
- Command:
  `Codex bundled python -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage004_legacy_name_scan.py`
- Result after implementation: `valid=true`, `issues=[]`,
  `files_scanned=103`, `legacy_name_hits=956`,
  `allowed_legacy_context=956`, `active_display_debt=0`,
  `unique_paths_with_legacy_hits=46`, and `forbidden_changed_paths=[]`.

## False-Positive Exclusions

The validator keeps accepted names out of old-name debt:

| Name | Classification |
|---|---|
| `IDS / Industrial Data System` | accepted current product name |
| `ProductMetaDatabase` | accepted STAGE-002 subsystem, not old-name debt |
| `FinanceMetaDatabase` | accepted STAGE-003 canonical finance metadata name, not old-name debt |
| standalone `MetaDatabase` | legacy finance metadata name, allowed only in STAGE-003/taskpack/rollback context |

The focused unittest calls `find_legacy_hits()` directly and verifies
`ProductMetaDatabase` and `FinanceMetaDatabase` do not appear as old-name debt
while standalone `MetaDatabase` and word-boundary `OpMe` are still detected.

## Classification Summary

Pattern counts from the Phase 2 validator run:

| Pattern family | Hits |
|---|---:|
| `Wuhan Kaiming OpMe` | 19 |
| `武汉开明智能工业运维助手` | 8 |
| `wuhan-kaiming-assistant` | 6 |
| `OpMe_System` | 9 |
| `opme-system` | 9 |
| word-boundary `OpMe`/`OPME`/`opme` | 771 |
| `wuhan_kaiming` | 9 |
| `Wuhan Kaiming` | 23 |
| `武汉开明` | 18 |
| `OpMeIcon` | 16 |
| `OpMe_structure_report` | 9 |
| standalone `MetaDatabase` | 59 |

All 956 hits are classified as allowed legacy context in this Phase 2 slice.
The classification is conservative: if a future old-name reference appears
outside allowed migration, historical, compatibility, test, rollback, or
source/company context, the validator reports it in `active_display_debt_refs`
and returns invalid.

## Boundary

No backend route, frontend route, runtime database, schema migration, worker,
external API path, raw-material copy, generated data, report output,
dependency folder, GitHub push, PR, or merge was added.

No `KM_IDSystem/product_meta_database/` file was modified. STAGE-002
`ProductMetaDatabase` and STAGE-003 `FinanceMetaDatabase` remain accepted
subsystems/names.

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE004-P2` commit. This
removes the validator, unittest, Phase 2 evidence, and governance status
updates. Because this phase is governance/validator-only, rollback does not
require data cleanup, schema rollback, service restart, dependency
restoration, report cleanup, runtime file restore, or old-name replacement
reversal.

## Decision

STAGE-004 Phase 2 is locally satisfied when the focused unittest, validator,
render check, marker/scope checks, and `git diff --check` pass. The next run
may enter STAGE-004 Phase 3 for broader validation and abnormal scenario
checks. The `STAGE-001..010` batch remains locked from upload.
