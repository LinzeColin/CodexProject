# IDS v0.1 STAGE-001 Phase 2 Naming Implementation

## Identity

- Stage: `STAGE-001`
- Phase: `Phase 2`
- Task ID: `IDS-V0_1-STAGE001-P2`
- Acceptance ID: `ACC-STAGE-001`
- Stage title: `IDS 产品命名合同`
- Recorded at UTC: `2026-07-02T04:40:40Z`

## Goal

Implement the minimum active product-name slice required by STAGE-001:
new UI, reports, active launcher metadata, service health identity, and formal
documentation must use `IDS / Industrial Data System`.

## Changed Active Surfaces

- `KM_IDSystem/README.md`
  - Formal project title now uses `IDS / Industrial Data System`.
  - Legacy names are explicitly constrained to migration, historical evidence,
    compatibility paths, and rollback context.
- `KM_IDSystem/docs/HANDOFF.md`
  - Handoff title and GitHub continuity rule now point to
    `LinzeColin/CodexProject` and `KM_IDSystem/`.
  - Legacy aliases are documented as non-current display names.
- `KM_IDSystem/frontend/index.html`
  - Browser title now uses `IDS / Industrial Data System`.
- `KM_IDSystem/frontend/src/App.jsx`
  - Sidebar brand and topbar eyebrow now show IDS identity.
- `KM_IDSystem/backend/app/core/config.py`
  - `APP_NAME` now uses `IDS / Industrial Data System`, affecting FastAPI title
    and generated PDF title text.
- `KM_IDSystem/backend/app/api/routes.py`
  - Health service id now uses `ids-industrial-data-system`.
- `KM_IDSystem/scripts/build_app_bundle.sh`
  - Generated macOS app bundle name, executable, bundle identifier, and display
    name now use IDS identity.
- `KM_IDSystem/scripts/install_app_entries.sh`
  - Installed `.app` and `.command` launcher names now use IDS identity.
- `KM_IDSystem/scripts/run_local_services.sh`
  - Notification title, health probes, and terminal banner now use IDS identity.
- `KM_IDSystem/scripts/diagnose_app_entry.sh`
  - Diagnostic paths now use IDS launcher names.
- `KM_IDSystem/scripts/stop_local_services.sh`
  - Ownership log messages now use IDS identity.
- `KM_IDSystem/backend/tests/test_stage001_naming_contract.py`
  - Adds a focused text-contract regression test for active IDS product surfaces.

## Preserved Legacy Context

These legacy terms remain intentionally allowed because Phase 2 does not rewrite
history or compatibility identifiers:

- `OPME_*` environment variables and temporary test database names;
- `OpMeIcon.*` asset file names;
- historical/legacy structure report paths such as `OpMe_structure_report.md`;
- older test class names and migration entries;
- README/HANDOFF legacy alias notes.

Phase 3 must perform the broader customer-visible scan and classify any
remaining legacy references as allowed or blocking.

## Validation Results

- Red scan before implementation: failed on README, HANDOFF, frontend title,
  frontend brand, backend `APP_NAME`, health service id, and launcher scripts.
- Green scan after implementation: `stage001_phase2_naming_contract_scan_ok`.
- Focused regression test:
  `python3 -m unittest KM_IDSystem/backend/tests/test_stage001_naming_contract.py -q`
  ran 2 tests and returned `OK`.
- Script syntax check: `bash -n` passed for `build_app_bundle.sh`,
  `install_app_entries.sh`, `run_local_services.sh`, `diagnose_app_entry.sh`,
  and `stop_local_services.sh`.
- `check-render --project KM_IDSystem`: passed with `drift_count=0`.
- Stage001 Phase2 marker check: passed.
- Changed scope check: passed; changed paths remain under `KM_IDSystem/`.
- `git diff --check`: passed.
- `validate --project KM_IDSystem --semantic`: blocked by the existing sparse
  worktree omission of root governance schemas/workflows/hooks and unrelated
  registered project directories. No unrelated project expansion was performed.

## No-Upload Decision

This is local batch work only. The current `STAGE-001..STAGE-010` batch remains
below the 10-stage upload threshold, so no GitHub push, PR, or merge is allowed
from this phase.

## Rollback

Revert this phase commit to restore the pre-Phase-2 active display names. Do
not touch data, generated reports, dependency folders, historical evidence, or
the Stage 0 root lock.
