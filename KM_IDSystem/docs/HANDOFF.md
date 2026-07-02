# IDS / Industrial Data System Handoff

## Purpose

IDS / Industrial Data System turns the original industrial-operations CLI prototype into a local Web + PDF industrial data and operations console. It provides dashboard views, module-specific analysis, visualization, report generation, model routing configuration, and recoverable local app launchers.

Legacy aliases such as `Wuhan Kaiming OpMe`, `OpMe`, and the Chinese legacy display name may remain only in migration notes, historical evidence, compatibility paths, or rollback context. New UI, reports, generated titles, and formal documentation should use `IDS / Industrial Data System`.

## Delivery Standard

Any future agent should preserve these standards:

- The app must start locally from `./scripts/run_local_services.sh` or the macOS click entry. Prefer the installed `.command` launcher when Gatekeeper blocks the `.app`.
- The backend health endpoint must return ok at `http://127.0.0.1:8000/api/health`.
- The frontend must load at `http://127.0.0.1:5173/`.
- Four core modules must keep working: dynamic kiln monitoring, fault diagnosis, gear repair, machining service.
- Every case should support dashboard visualization and PDF report generation.
- Missing model API keys must not block operation; offline rules must remain the fail-closed fallback.
- Formal user-facing outputs should remain PDF-first; JSON, CSV, SQLite, and Markdown are support artifacts.

## Current Architecture

- `backend/`: FastAPI service, SQLite persistence, rule analysis, model routing, PDF generation.
- `frontend/`: React + ECharts dashboard and workbench UI.
- `samples/`: small JSON/CSV inputs for demos and tests.
- `scripts/`: local service launcher, smoke test, sample report generation.
- `docs/`: handoff, cleanup, and continuity documents.
- `app_bundle/`: source macOS `.app` bundle resources and icon assets. `scripts/install_app_entries.sh` also installs `.command` launchers to Downloads and Applications.

## Runbook

```bash
./scripts/run_local_services.sh
```

Install local click entries:

```bash
./scripts/install_app_entries.sh
```

Installed entries:

- `/Applications/IDS Industrial Data System.command`
- `/Users/linzezhang/Downloads/IDS Industrial Data System.command`
- `/Applications/IDS Industrial Data System.app`
- `/Users/linzezhang/Downloads/IDS Industrial Data System.app`

Use `.command` as the primary local double-click entry. It runs the same service launcher in Terminal and avoids macOS LaunchServices/Gatekeeper silently blocking ad-hoc `.app` bundles. Keep the Terminal window open while using the app; closing it stops the local runtime.

Regenerate the macOS app icon:

```bash
.venv/bin/python scripts/generate_app_icon.py
./scripts/install_app_entries.sh
```

The tracked final assets remain `app_bundle/assets/OpMeIcon.png` and `app_bundle/assets/OpMeIcon.icns` as legacy asset paths; the intermediate `.iconset` directory is intentionally ignored.

For verification:

```bash
./scripts/smoke_test.sh
```

Quick launcher verification:

```bash
OPEN_BROWSER=0 ./scripts/run_local_services.sh
cat data/backend_port data/frontend_port
curl -fsS "http://127.0.0.1:$(cat data/backend_port)/api/health"
curl -fsS "http://127.0.0.1:$(cat data/frontend_port)/api/health"
```

If dependencies were removed during cleanup, the launcher restores them from:

- `backend/requirements.txt`
- `frontend/package-lock.json`

## GitHub Continuity Rule

All future development for this system should be synchronized into:

`LinzeColin/CodexProject`

Use the subdirectory:

`KM_IDSystem/`

Commit/PR summaries must include:

- task purpose
- changed subsystems
- validation commands and results
- remaining risks
- local files that are intentionally not tracked

## Local Files Intentionally Not Tracked

- `.venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `.pytest_cache/`
- `__pycache__/`
- runtime SQLite/log files under `data/`
- generated PDF/ZIP artifacts under `reports/` and `outputs/`

These are recoverable from source, scripts, and GitHub.

## Known Limits

- Docker was not available on this Mac during validation, so Docker Compose syntax could not be executed locally.
- macOS may reject the ad-hoc `.app` bundle through Gatekeeper/LaunchServices. The `.command` launcher is the current reliable click path.
- Real MQTT/OPC-UA/Modbus device ingestion is not implemented in this version.
- Model providers are configurable, but no plaintext API keys should be committed.
