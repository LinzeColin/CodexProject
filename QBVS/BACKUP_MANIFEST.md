# 大数据模拟器 GitHub Backup Manifest

Backup date: 2026-06-20 Australia/Sydney

Source path before cleanup:

`/Users/linzezhang/Documents/Codex/2026-06-19/current-phase-phase-0-goal-scope/work/CodexProject/QBVS`

GitHub target path:

`LinzeColin/CodexProject/QBVS`

## Included In Git

- `README.md`
- `HANDOFF.md`
- `AGENTS.md`
- `BACKUP_MANIFEST.md`
- `HANDSHAKE_PROTOCOL.json`
- `QUANTLAB_INTEGRATION_CONTRACT.json`
- `qbvs/`
- `tests/`
- `tools/`
- `config/`
- `handoff/`
- `reports/`
- `runs/` top-level status files only

## Excluded From Git

These were intentionally not copied to GitHub because they are large,
runtime-derived, reproducible, or unsafe to keep in a normal git repo:

- `data_cache_*`
- `runs/*/`
- `runs/manifests/`
- `campaigns/`
- `warehouse/`
- `warehouse_smoke/`
- `*.sqlite`
- `*.db`
- `*.pdf`
- `*.zip`
- Python and test caches

Observed source size before cleanup: about `1.5G`.

Large source directories before cleanup:

| Path | Size |
| --- | ---: |
| `runs/` | `919M` |
| `campaigns/` | `251M` |
| `warehouse/` | `197M` |
| `warehouse_smoke/` | `428K` |
| `qbvs/` | `300K` |
| `tests/` | `44K` |
| `tools/` | `68K` |
| `config/` | `344K` |
| `handoff/` | `1.0M` |
| `reports/` | `344K` |

## Continuation Notes

- Product display name is now 大数据模拟器.
- Historical package name remains `qbvs`.
- QuantLab integration remains ReviewOnly.
- Do not treat public Yahoo data, Moomoo cache, or SQLite warehouse data as
  proof of account-tradable live execution.
- Rebuild heavy artifacts by rerunning CLI commands from `README.md` and
  `HANDOFF.md`; do not commit regenerated runtime data unless a separate
  storage policy is approved.
- PDF reports and ZIP handoff packages are excluded from this Git backup to
  keep diffs reviewable; their source Markdown/CSV/JSON evidence is retained
  where available.
