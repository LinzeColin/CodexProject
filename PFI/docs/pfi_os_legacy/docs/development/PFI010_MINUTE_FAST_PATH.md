# PFI-010 Minute Fast Path

Status: local deterministic Gate 4 evidence complete.

As of: 2026-06-20 Australia/Sydney

## Scope

PFI-010 adds a minute-level fast path acceptance layer for Gate 4. It proves a
local, legal, three-source refresh path can update independently of the UI page,
stay within the 60-second p95 budget, recover from a transient failure, and
publish a Web Shell runtime dashboard.

This slice is deterministic and does not sleep for real-time soak windows. The
final Gate 7 release package can replay a wall-clock soak if release policy
requires elapsed 1h/24h evidence.

## Implemented

- `src/pfi_os/application/pfi010_minute_fast_path.py`
  - `PFI010MinuteFastPathContractV1`
  - `PFI010MinuteFastPathAcceptanceV1`
  - `PFI010MinuteFastPathReadModelV1`
- Three legal local sources:
  - market public sample
  - policy reviewed local input
  - report manifest local source
- Durable worker proof through existing `DurableJobStore` and `job_records`.
- Incremental cursor movement for every source.
- Page-closed proof with `ui_session_active=false` and completed worker jobs.
- Failure injection with retry recovery.
- Latency dashboard with p95 <= 60 seconds.
- Deterministic logical 1h and 24h soak summaries.
- Operational Store source/evidence/task records.
- Web Shell runtime exposure through `workflow_runtime.minute_fast_path`.

## Verification

```bash
python -m pytest tests/contract/test_pfi010_minute_fast_path.py -q
scripts/pfi010MinuteFastPathAcceptance.sh --summary-json
```

Observed:

- PFI-010 contract: 6 passed.
- Acceptance script:
  - `status=Pass`
  - `pass=11`
  - `fail=0`
  - `source_count=3`
  - `sample_count=15`
  - `p95_seconds=44.0`
  - `page_closed_updates=true`
  - `failure_injection_status=Pass`
  - `logical_1h_soak=Pass`
  - `logical_24h_soak=Pass`

## Boundaries

- No provider fetch.
- No broker calls.
- No LLM calls.
- No network dependency.
- No live trading.
- No order execution.
- No payment or betting execution.
- Human review remains required.

## Remaining Release Work

- Re-run PFI-010 in final Gate 7 release packaging.
- If final policy requires elapsed soak rather than deterministic logical soak,
  run a wall-clock 1h/24h soak and attach that evidence to the final package.
