# Stage 7 Phase 7.2 Risk and Rollback

## Risk

- `PFI/web/app/pages/reports.js` now exposes the v0.2.4 Phase 7.2 report center view model while preserving existing v0.2.3 exports.
- `PFI/web/app/shell.js` consumes the Phase 7.1 report schema through the new v0.2.4 report page API; if the embedded schema is missing, the static preview falls back to the current checkout's Stage 7 report display text.
- `PFI/src/pfi_os/app/streamlit_app.py` now inlines `reports.js` and `pfi-stage7-report-schema` so PFI.app can display the same report center source after app refresh.
- Phase 7.3 browser screenshot/evidence, whole-stage review, GitHub upload and app reinstall are explicitly not done in this phase.

## Rollback

Revert the Stage 7 Phase 7.2 commit or remove:

- `PFI/tests/test_v024_stage7_phase72_report_page_display.py`
- `PFI/reports/pfi_v024/stage_7/phase_7_2/`
- v0.2.4 Phase 7.2 additions in `PFI/web/app/pages/reports.js`
- `reports.js` script loading and `pfi-stage7-report-schema` in `PFI/web/index.html`
- `reports_page_path` / `stage7_report_schema_path` in `PFI/src/pfi_os/app/streamlit_app.py`
- v0.2.4 report center consumption in `PFI/web/app/shell.js`

No user financial data, app bundle installation, GitHub main upload or data migration is part of this rollback.
