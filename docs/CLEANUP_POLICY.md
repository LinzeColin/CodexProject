# Local Cleanup Policy

## Keep Locally

- Source code and project config.
- `backend/requirements.txt` and `frontend/package-lock.json`.
- `scripts/run_local_services.sh`, `scripts/smoke_test.sh`, and sample data.
- `docs/HANDOFF.md`, `docs/PROJECT_STATUS.md`, and this policy.
- macOS launcher source under `app_bundle/`.

## Remove Locally After GitHub Backup

These are recoverable and should not be kept in the local workspace after backup:

- `.venv/`
- `frontend/node_modules/`
- `frontend/dist/`
- `.pytest_cache/`
- `__pycache__/`
- transient generated packages in `outputs/`

## Keep If Needed For Current Demo

- `data/wuhan_kaiming.sqlite`
- latest PDF reports under `reports/`

If disk pressure is more important than immediate demo readiness, regenerate them with:

```bash
PYTHONPATH=backend python scripts/generate_sample_reports.py
```

