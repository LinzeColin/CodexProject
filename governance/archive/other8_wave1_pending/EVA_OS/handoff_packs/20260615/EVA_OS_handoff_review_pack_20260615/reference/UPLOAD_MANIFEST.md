# GitHub Upload Manifest

Target repository: `LinzeColin/EVA_OS`

Upload date: 2026-06-13

## Goal

Upload enough project state for any future agent to continue development safely and efficiently, including unfinished work, without exposing unnecessary local/private data in a public repository.

## Included

| Category | Included paths |
| --- | --- |
| Project entry | `README.md`, `AGENTS.md`, `AGENT_CONTINUITY.md`, public-safe `HANDOFF.md`, `15_OPEN_QUESTIONS.md`, `UPLOAD_MANIFEST.md` |
| Plans/prompts | `CODEX_PROMPTS.md`, `CODEX_TASK_PACK.md`, `PLANS.md` |
| Python source | `src/**` |
| Tests | `tests/**`, excluding caches |
| Scripts | `scripts/**`, `StartQuantLab.command`, `StopQuantLab.command` |
| macOS entry apps | `macos/EVA_OS.app/**`, `macos/README.md`, `scripts/installEVAOSEntryApps.sh` |
| Docs | `docs/**` |
| Assets | `assets/**` |
| Safe configuration | `.env.example`, `.gitignore`, `pyproject.toml` |
| Continuity data snapshots | selected public-safe `data/**` JSON/CSV/MD latest and small deterministic sample artifacts |

## Excluded

| Category | Reason |
| --- | --- |
| `.venv/**` | Rebuildable dependency environment; too large for source control. |
| `__pycache__/**`, `.pytest_cache/**`, `*.pyc` | Rebuildable cache. |
| `data/holdings/**` except `.gitkeep` | May contain private portfolio or account-derived information. |
| `data/imports/**` | Raw portfolio video frames and extracted account screenshots; private and large. |
| `data/researchBus/*.sqlite` | Runtime database; large and may contain local private notes. |
| `data/researchBus/*.sqlite-shm`, `data/researchBus/*.sqlite-wal` | SQLite runtime sidecars. |
| `data/cache/*.log`, `*.pid`, `*.lock` | Local runtime logs/locks; not source of truth. |
| `HANDOFF_PRIVATE_LOCAL.md` | Local-only long history handoff; may include private local paths or run traces. |
| Large PDFs and images generated from private runs | Public repo risk and unnecessary for agent continuity. |
| Long-form historical local `HANDOFF.md` | Preserved locally as `HANDOFF_PRIVATE_LOCAL.md`; public repo uses a public-safe handoff summary. |

## Latest Verified Artifacts

The following continuity artifacts should be present after upload:

```text
data/dataLake/DataLakeManifest_latest.json
data/dataLake/DataLakeManifest_latest_assets.csv
data/dataLake/DataLakeManifest_latest_replay_cursors.json
data/marketEvents/MarketEventLog_latest.json
data/marketEvents/MarketEventLog_latest.jsonl
data/replay/EventReplay_latest.json
data/replay/EventReplay_latest.csv
data/replay/EventReplay_latest.md
assets/EVA_OSAppIcon.icns
assets/EVA_OSAppIconPreview.png
assets/EVA_OSAppIconConfig.json
macos/EVA_OS.app/Contents/Info.plist
macos/EVA_OS.app/Contents/MacOS/EVA_OS
macos/EVA_OS.app/Contents/Resources/EVA_OSAppIcon.icns
cleanup/EVA_OS_GitHub_Sync_Local_Slimming_20260613.md
```

## Validation State

Latest target validation:

```text
EVA_OS app plist/icon check: passed for Desktop, Downloads, and Applications
legacy-name scan: no deprecated product-name text or filename residue in scoped project
target report regeneration: Token ROI, Policy Radar, Consumption Guard, Report Decision Support, and Command Center regenerated
py_compile: passed for renamed app/report/data/integration modules
target pytest: 28 passed in 31.48s
```

## Handoff Rule

Future agents should update `HANDOFF.md` only after meaningful subsystem progress, verified outputs, or a change in next-step priority. Do not rewrite history or remove unfinished items unless current evidence proves they are complete.
