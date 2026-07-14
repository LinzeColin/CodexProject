# Serenity Production Preflight

- Generated at: 2026-07-14T09:30:21+08:00
- Production ready: True
- Shadow ready: True

## Blockers

- None

## Warnings

- **moomoo_opend**: moomoo_OpenD socket not reachable at 127.0.0.1:11111: ConnectionRefusedError: [Errno 61] Connection refused; Python import `moomoo` is available; installed distribution version=10.8.6808. Live moomoo_OpenD is unavailable, so runtime should stay degraded for live collection, but benchmark_sources remains the production gate.
  - Evidence: `{"json_path": "outputs/preflight/moomoo_smoke_latest.json", "markdown_path": "outputs/preflight/moomoo_smoke_latest.md"}`
- **alipay_positions**: Optional Alipay CSV appears to be sample data; ignored for production baseline
  - Evidence: `{"path": "data/imports/alipay_positions.csv", "rows": 4, "sample_data": true}`

## Candidate Files Found

- None
