# AI-Research-System Sample Data

These fixtures support parser, reporting, monitoring, and bridge tests. They are public-safe examples, not real account exports.

Notes:

- `holdings.csv` contains zero-value demo rows only.
- `watchlist_moomoo.csv` is a research watchlist fixture, not a moomoo account database.
- `watchlist_snapshot.csv` and `opend_quote_diagnostics_2026-06-05.csv` are sample quote snapshots used for fail-closed testing.
- `opend_status.json` is sanitized and must not contain local paths, tracebacks, account state, or credentials.

Do not place real Alipay exports, screenshots, broker data, or private holdings in this directory.
