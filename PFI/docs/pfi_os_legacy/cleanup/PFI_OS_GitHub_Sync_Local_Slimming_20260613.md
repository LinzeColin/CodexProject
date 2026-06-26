# PFI_OS / PFI_OS GitHub Sync and Local Slimming Report

Date: 2026-06-13

GitHub verification commit:

```text
7969e2a5b3f61d09dc196b54bc56fc6ec15d5d48
```

## Purpose

Make `LinzeColin/PFI_OS` the durable project handoff surface for PFI_OS so any future agent can continue development from GitHub without replaying the full Codex thread.

## Delivery Standard

- GitHub contains source, tests, scripts, docs, task pack, handoff files, public-safe sample outputs, and macOS launcher templates.
- Local machine keeps only the active working copy, the two PFI_OS app entry points, and private/runtime state that should not be pushed to a public repo.
- Rebuildable caches, duplicate historical workspaces, and redundant local upload packages are deleted after GitHub verification.
- Handoff must state current development step, unresolved issues, evidence boundaries, and recommended next run.

## Public GitHub Boundary

Uploaded to GitHub:

- `src/**`
- `tests/**`
- `scripts/**`
- `docs/**`
- `macos/PFI_OS.app/**`
- `README.md`, `AGENTS.md`, `AGENT_CONTINUITY.md`, `HANDOFF.md`, `15_OPEN_QUESTIONS.md`, `UPLOAD_MANIFEST.md`
- public-safe deterministic sample data and generated latest artifacts

Not uploaded to public GitHub:

- `.venv/**`
- Python/test/build caches
- `.env` or secrets
- `data/holdings/**` except `.gitkeep`
- `data/imports/**` except `.gitkeep`
- `data/researchBus/*.sqlite*`
- local logs, pid files, locks, and private raw account/import screenshots

## Local Retention Policy

Keep locally:

- `$PFI_OS_HOME`
- `~/Downloads/PFI_OS.app`
- `/Applications/PFI_OS.app`
- private runtime files inside the active working copy when not safely publishable

Delete after verified push:

- historical duplicate project:
  `$PFI_OS_HOME`
- redundant local GitHub upload archive:
  `~/Documents/Codex/2026-06-13/files-mentioned-by-the-user-eva/work/github-upload`
- private raw import frame cache:
  `data/imports/portfolioVideo`

## Cleanup Metrics

GitHub backup:

```text
First full push commit: 492 changed files
Approx staged payload: 19,773,191 bytes
Remote branch verified: main -> 7969e2a5b3f61d09dc196b54bc56fc6ec15d5d48
Remote key files verified: HANDOFF.md, macos/PFI_OS.app/Contents/Info.plist, this cleanup report
```

Planned local deletion after remote verification:

| Target | Files | Bytes | Reason |
| --- | ---: | ---: | --- |
| Historical duplicate `2026-06-04/.../CodexFinance` | 567 | 72,677,953 | Duplicate subset of current working copy; GitHub now holds public-safe source. |
| Redundant `work/github-upload` archive | 3 | 1,849,711 | Superseded by direct GitHub push. |
| Active copy raw import frame cache `data/imports/portfolioVideo` | 71 | 35,204,487 | Private raw import/account frames; not safe for public GitHub and not needed for code continuity. |
| Temporary push clone `work/PFI_OS_repo` | 1,111 | 75,520,890 | Temporary Git working tree used only for authenticated push. |
| **Total** | **1,752** | **185,253,041** | Local slimming after verified backup. |

Cache cleanup:

```text
Rebuildable cache files/directories found in the scoped PFI_OS project paths before deletion: 0
Cache bytes deleted in this cleanup pass: 0
```

## Current Development State

Completed local engineering layers:

1. Market Event Layer MVP
2. Reproducible Data Lake MVP
3. Event Replay MVP
4. Executive Command Center draft
6. PFI_OS macOS entry app template and local entry points

Current stopping point:

- The latest implemented subsystem is `Event Replay MVP`.
- The next recommended subsystem is `Vectorized Research Mode MVP`.

## Unresolved Issues

- Three-mode backtest/simulation core is not complete.
- TradingView-like chart/strategy UX is not complete.
- Moomoo-like realtime research flow is not complete.
- 52ETF integration is not complete.
- Hotspot analysis still needs runtime optimization beyond the prior stability fixes.
- Local `.venv` was deleted during earlier slimming; tests require recreating dependencies.

## Acceptance Criteria for Next Agent

Before claiming a subsystem complete, a future agent must:

1. update `HANDOFF.md` with the exact changed files and verification results;
2. run focused tests or explain precisely why tests could not run;
3. keep private holdings, screenshots, secrets, SQLite runtime files, and caches out of the public repo;
4. push changes to `LinzeColin/PFI_OS`;
5. keep changes scoped to one subsystem per run unless the user explicitly expands scope.
