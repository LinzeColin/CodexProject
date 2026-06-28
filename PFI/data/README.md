# PFI Data

This directory is intentionally lightweight after root unification.

The previous generated runtime outputs and cache artifacts were excluded from
the active product root and preserved in the local migration backup archive.
PFI runtime scripts may recreate local cache and report folders as needed.

## Committed contract data

`fx_snapshots/` contains small, source-traceable exchange-rate snapshots that
are part of v0.2.2 governance evidence. They are not disposable runtime cache.

Current Stage 2 snapshot:

- `fx_snapshots/AUD_CNY/2026-06-28.json`
- pair: `AUD/CNY`
- meaning: `1 AUD = 4.6874 CNY`
- source: `Frankfurter v2 public API`
- ordinary runtime network refresh: `false`

## Disposable runtime data

Large imports, user private raw data, generated reports, local database files,
and cache artifacts must stay outside the product root unless a task explicitly
promotes a small contract fixture for GitHub review.
