# IDS v0.1 STAGE-001 Phase 4 Closeout

## Identity

- Stage: `STAGE-001`
- Phase: `Phase 4`
- Task ID: `IDS-V0_1-STAGE001-P4`
- Acceptance ID: `ACC-STAGE-001`
- Stage title: `IDS 产品命名合同`
- Recorded at UTC: `2026-07-02T04:54:05Z`

## ACC-STAGE-001 Decision

`ACC-STAGE-001` is locally satisfied for the current `STAGE-001` stage. The
active product name for new UI, reports, active launcher metadata, health
identity, formal documentation, and generated PDF title text is now
`IDS / Industrial Data System`.

This does not authorize a GitHub upload yet. The current local batch remains
`STAGE-001..STAGE-010`, and the batch upload gate still requires all 10 stages
to be complete, reviewed, and repaired.

## Phase Evidence

| Phase | Status | Evidence |
|---|---|---|
| Phase 1 | completed | `STAGE001_PHASE1_SCOPE_BOUNDARY.md` |
| Phase 2 | completed | `STAGE001_PHASE2_NAMING_IMPLEMENTATION.md` |
| Phase 3 | completed | `STAGE001_PHASE3_VALIDATION_SCAN.md` |
| Phase 4 | completed locally | this closeout |

## Changed File Summary

Phase 1 established the naming contract boundary and local batch upload lock.

Phase 2 implemented the minimum active naming slice across:

- formal docs: `README.md`, `docs/HANDOFF.md`;
- frontend display: `frontend/index.html`, `frontend/src/App.jsx`;
- backend product/report identity: `backend/app/core/config.py`,
  `backend/app/api/routes.py`, `backend/app/__init__.py`;
- launcher scripts and app bundle metadata:
  `scripts/build_app_bundle.sh`, `scripts/install_app_entries.sh`,
  `scripts/run_local_services.sh`, `scripts/diagnose_app_entry.sh`,
  `scripts/stop_local_services.sh`;
- regression test: `backend/tests/test_stage001_naming_contract.py`.

Phase 3 validated and repaired exceptions:

- `app_bundle/native_launcher.c` now receives current worktree paths from
  `scripts/build_app_bundle.sh` at compile time;
- `scripts/stop_local_services.sh` is executable in the git index;
- `README.md` and `docs/CLEANUP_POLICY.md` classify legacy runtime database
  names as compatibility identifiers.

Governance and human entry files updated across the stage:

- `docs/governance/roadmap.yaml`
- `docs/governance/events.jsonl`
- `功能清单.md`
- `开发记录.md`
- `模型参数文件.md`
- `docs/pursuing_goal/ids_v0_1/BATCH001_010_UPLOAD_LOCK.yaml`

## Legacy Alias Summary

The following legacy references remain allowed and classified:

- `Wuhan Kaiming OpMe`, `OpMe`, and the old Chinese display name in explicit
  legacy notes, historical cleanup records, changelog entries, or governance
  provenance.
- `OPME_*` environment variables and `opme-test` temporary test names as
  compatibility/runtime identifiers.
- `data/wuhan_kaiming.sqlite` as a legacy runtime SQLite filename.
- `OpMeIcon.*` as legacy asset filenames used by the icon pipeline.
- `docs/OpMe_structure_report.md` as a legacy structure report path.
- `武汉开明高科技有限公司` in `model_router.py` as company/source prompt context,
  not a product display name.

## Validation Evidence

Fresh validation for this closeout must include:

- lifecycle test with Codex bundled Python: 5 tests OK;
- naming contract test with Codex bundled Python: 2 tests OK;
- project-file legacy scan: 87 files scanned, 564 classified legacy hits,
  1 non-blocking review item, and 0 active blockers;
- script and native launcher syntax checks: OK;
- `check-render --project KM_IDSystem`: `drift_count=0`;
- marker, JSONL, changed-scope, and `git diff --check`: OK;
- full semantic governance validate remains blocked by sparse worktree
  omissions and must not be solved by expanding unrelated projects.

## Rollback

Rollback `STAGE-001` by reverting the local STAGE-001 commits on
`codex/ids-v0-1-stages-001-010`:

1. `56d20040 IDS v0.1 stage001 phase3 validation scan`
2. `8038e27c IDS v0.1 stage001 phase2 naming slice`
3. `55279c8e IDS v0.1 stage001 phase1 boundary`

Do not delete or modify runtime `data/`, generated `reports/`, `outputs/`,
dependency directories, raw materials, historical evidence, or Stage 0 root
lock files when rolling back.

## No-Upload Stop Line

No GitHub push, PR, or merge is allowed from this closeout because only
`STAGE-001` of the `STAGE-001..STAGE-010` batch is complete. The next run may
enter `STAGE-002` under the same one-phase-per-run rule.
