# IDS v0.1 STAGE-003 Phase 2 Reference Migration

## Identity

- Stage: `STAGE-003`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE003-P2`
- Acceptance ID: `ACC-STAGE-003`
- Stage title: `MetaDatabase 更名为 FinanceMetaDatabase`
- Recorded at UTC: `2026-07-02T05:46:30Z`

## Goal

Complete the smallest safe reference migration from standalone legacy
`MetaDatabase` to `FinanceMetaDatabase` without changing `ProductMetaDatabase`,
runtime code, schema migrations, data paths, report outputs, dependency
folders, or external API behavior.

## Implemented Slice

Phase 2 performed only a narrow documentation/governance migration:

- updated STAGE-002 migration wording so finance metadata ownership points to
  STAGE-003 `FinanceMetaDatabase`;
- kept `ProductMetaDatabase` as an active STAGE-002 subsystem name;
- added `validate_stage003_finance_meta_rename.py` to distinguish standalone
  `MetaDatabase` from `ProductMetaDatabase`;
- added focused unittest coverage for the validator;
- updated batch lock, roadmap, events, and rendered Chinese owner entries.

No backend, frontend, script, app bundle, ProductMetaDatabase contract,
runtime data, report output, dependency directory, raw material, or GitHub
upload was changed.

## TDD Evidence

Red:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage003_finance_meta_rename.py -q`
- Result before implementation: 1 error because
  `validate_stage003_finance_meta_rename.py` did not exist.

Green:

- Command:
  `Codex bundled python -B -m unittest KM_IDSystem/docs/pursuing_goal/ids_v0_1/tests/test_stage003_finance_meta_rename.py -q`
- Result after implementation: 1 test returned `OK`.
- Command:
  `Codex bundled python -B KM_IDSystem/docs/pursuing_goal/ids_v0_1/validate_stage003_finance_meta_rename.py`
- Result after final render: `valid=true`, `issues=[]`,
  `runtime_target_hits=[]`, `product_meta_path_touched=[]`,
  `finance_meta_hits=66`, `standalone_old_hits=53`, and
  `product_meta_hits=166`.

Final checks also recorded:

- ProductMetaDatabase unittest: 2 tests returned `OK`;
- ProductMetaDatabase validator: `valid=true`, `issues=[]`;
- `check-render --project KM_IDSystem`: `drift_count=0`;
- marker, JSONL, and changed-scope check:
  `stage003_phase2_marker_jsonl_scope_ok=True`;
- `git diff --check`: exit 0;
- full semantic governance validate remains blocked by the known sparse
  worktree omissions: 28 errors for missing root governance schemas,
  workflows/hooks, governance tests, skill/config files, and unrelated
  registered project directories.

## Migration Classification

The validator treats these as distinct:

| Name | Classification | Phase 2 action |
|---|---|---|
| `FinanceMetaDatabase` | canonical finance metadata subsystem name | allowed and required |
| standalone `MetaDatabase` | legacy finance metadata name | allowed only in task title, migration notes, P0 source references, or rollback context |
| `ProductMetaDatabase` | active STAGE-002 product metadata subsystem | preserved; not a target |

## Rollback

Rollback Phase 2 by reverting the local `IDS-V0_1-STAGE003-P2` commit. This
restores the previous migration wording, removes the Phase 2 evidence and
validator, and does not require data cleanup, schema rollback, service restart,
dependency restoration, report cleanup, or ProductMetaDatabase changes.

## Decision

STAGE-003 Phase 2 is locally satisfied when the focused unittest, validator,
render check, marker/scope checks, and `git diff --check` pass. The next run
may enter STAGE-003 Phase 3 for broader validation and abnormal scenario
checks. The `STAGE-001..010` batch remains locked from upload.
