# Cleanup Report - 2026-06-13

## Scope

Cleanup was limited to the Wuhan Kaiming OpMe project workspace:

`/Users/linzezhang/Documents/Codex/2026-06-04/files-mentioned-by-the-user-wuhan`

No unrelated user folders were cleaned.

## GitHub Backup

Repository:

`https://github.com/LinzeColin/KM_IDSystem`

Backed up files:

- 52 source/config/documentation/app-entry files in commit `f003d18`.
- 9 generated artifact backup files in commit `650468f`.
- 1 cleanup report file in the follow-up commit containing this document.

Generated artifacts were backed up under:

`backups/generated-artifacts/2026-06-13/`

The local checkout uses sparse checkout to exclude that generated-artifacts backup directory from this Mac.

S4PCT01 note: these generated-artifacts backup files were later archived under
`governance/archive/other8_wave1_pending/KM_IDSystem/backups/generated-artifacts/2026-06-13/`
to keep historical truth while removing backup artifacts from the active project surface.

## Deleted Locally

Cache/dependency/build files removed:

- Files: 10,420
- Approximate size: 229,404,672 bytes
- Categories: `.venv/`, `frontend/node_modules/`, `frontend/dist/`, `.pytest_cache/`, Python `__pycache__/`

Generated local files removed after GitHub backup:

- Files: 8
- Approximate size: 135,168 bytes
- Categories: `outputs/*.pdf`, `outputs/*.zip`, `reports/*.pdf`

Total files removed locally:

- 10,428 files

## Local Files Retained

Necessary local files retained:

- Source code under `backend/` and `frontend/src/`
- Dependency manifests: `backend/requirements.txt`, `frontend/package.json`, `frontend/package-lock.json`
- Docker and local launch config: `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile`
- Scripts: `scripts/dev.sh`, `scripts/run_local_services.sh`, `scripts/install_app_entries.sh`, `scripts/smoke_test.sh`, `scripts/generate_sample_reports.py`
- App bundle source: `app_bundle/Wuhan Kaiming OpMe.app/`
- Project documentation: `README.md`, `docs/HANDOFF.md`, `docs/PROJECT_STATUS.md`, `docs/CLEANUP_POLICY.md`
- Original ChatGPT/reference prototype files under `work/original/` were later archived by S4PCT01 under `governance/archive/other8_wave1_pending/KM_IDSystem/work/original/`
- Sample input data under `samples/`
- Empty `outputs/` and `reports/` directories for future regenerated deliverables

Installed local app entries retained:

- `/Users/linzezhang/Downloads/Wuhan Kaiming OpMe.app`
- `/Applications/Wuhan Kaiming OpMe.app`

## Recovery

After cleanup, dependencies and generated files can be restored by running:

```bash
./scripts/run_local_services.sh
```

or:

```bash
./scripts/smoke_test.sh
```

Generated PDFs can be recreated with:

```bash
PYTHONPATH=backend python scripts/generate_sample_reports.py
```

