# Codex Numeric Token Usage Export

Created on 2026-06-30.

This package exports numeric token usage from local Codex log databases only.
It does not include full session history.

Included:

- `data/raw_extracted_usage_rows.csv`
- `data/deduped_usage_rows.csv`
- `data/daily_usage_summary.csv`
- `data/monthly_usage_summary.csv`
- `data/summary.json`
- `scripts/export_numeric_token_usage.py`

Excluded:

- `~/.codex/sessions/`
- `~/.codex/archived_sessions/`
- prompt text
- response text
- tool output text
- `feedback_log_body`
- `auth.json`
- `.env`
- API keys and tokens
- SQLite databases and WAL/SHM files

## Which File To Use

Use `deduped_usage_rows.csv` for normal analysis. It removes exact mirrored log
duplicates using:

```text
thread_id + second-level timestamp + numeric usage fields
```

Use `raw_extracted_usage_rows.csv` only when you want to audit every extracted
local log row.

Use `daily_usage_summary.csv` and `monthly_usage_summary.csv` for charts or
quick review.

## Important

This is local log-derived history, not an official billing statement. It is
useful for migration continuity and rough local analysis, but official usage
should still come from the provider account dashboard/API.
