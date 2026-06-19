# Serenity Production Action Queue

- Generated: 2026-06-13T08:03:29+08:00
- Status: watch
- Production ready: False
- Row count: 4
- Priority counts: {'P2': 4}
- Blocker counts: {'benchmark_source_priority': 2, 'benchmark_history': 2}

## Boundary

- No-New-Order is enforced.
- This queue does not place trades.
- This queue does not send email.
- This queue does not unlock production; it only lists the evidence required before promotion and preflight can pass.

## Recommended Order

1. Keep the Serenity baseline candidate and fund-rule evidence fresh.
2. Upgrade P2 benchmark evidence from public aggregation fallback to MooMoo or official index/exchange evidence when available.
3. Rerun validation and completion audit after any evidence refresh.

```bash
python -m app.cli source-evidence-audit --pack-dir outputs/intake_pack --require-pass --json
python -m app.cli promote-intake-pack --json
python -m app.cli promote-intake-pack --apply --json
python -m app.cli validate-intake --scan-path ~/Downloads --scan-path ~/Documents --require-production --json
python -m app.cli production-unlock-check --apply --scan-path ~/Downloads --scan-path ~/Documents --require-production --json
```

## P0 Queue

| Priority | Blocker | Asset | Weight | Target field | Evidence |
|---|---|---|---|---|---|
| - | - | - | - | - | - |

## Files

- `markdown`: `outputs/preflight/production_action_queue_latest.md`
- `csv`: `outputs/preflight/production_action_queue_latest.csv`
- `json`: `outputs/preflight/production_action_queue_latest.json`
