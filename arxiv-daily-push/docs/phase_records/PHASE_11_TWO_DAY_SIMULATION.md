# Phase 11 Two-Day Simulation

Generated: `2026-06-22T06:30:00+10:00`
Project: `arxiv-daily-push`
Version: `0.11.27`
Task: `ADP-PHASE11-TWO-DAY-SIMULATION-030`

## Objective

Satisfy the updated Phase 11 acceptance target by running a deterministic
two-day simulation instead of requiring 30 production days.

## Scope

- Add `adp-two-day-simulation-v1`.
- Add `adp run-two-day-simulation`.
- Simulate two consecutive Australia/Sydney daily runs:
  - `2026-06-22`;
  - `2026-06-23`.
- Reuse the scheduled daily execution path and trial ledger update path.
- Require two unique dates, source IDs, and publication IDs.

## Non-Scope

- No live arXiv network fetch.
- No real SMTP send.
- No real GitHub Release upload.
- No secret value read.
- No Codex auth read.
- No media/model/cache artifact retention.
- No production acceptance claim.

## Evidence

Actual command:

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX=/tmp/codex_adp_two_day_cli \
PYTHONPATH=arxiv-daily-push/src \
python3 -m arxiv_daily_push run-two-day-simulation \
  --path . \
  --generated-at 2026-06-22T06:30:00+10:00 \
  --start-date 2026-06-22 \
  --json
```

Saved report:

```text
/Users/linzezhang/Documents/Codex/2026-06-21/readme-first-md-01-execution-contract/outputs/arxiv_daily_push_two_day_simulation_20260622.json
```

Observed result:

- `status=pass`
- `two_day_simulation_ready=true`
- `observed_day_count=2`
- `accepted_for_production=false`
- `production_acceptance_claimed=false`
- no configured SMTP password value in the JSON report

## Verification

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX=/tmp/codex_adp_two_day_focus \
PYTHONPATH=arxiv-daily-push/src \
python3 -m unittest arxiv-daily-push/tests/test_simulation.py -q
```

Result: `3 tests OK`.

```bash
PYTHONDONTWRITEBYTECODE=1 \
PYTHONPYCACHEPREFIX=/tmp/codex_adp_two_day_arxiv1 \
PYTHONPATH=arxiv-daily-push/src \
python3 -m unittest discover -s arxiv-daily-push/tests -q
```

Result: `160 tests OK`.

## Decision

For the updated goal, the Phase 11 simulation acceptance path is satisfied when
the two-day simulation report passes. This does not prove real production
launch, real SMTP delivery, real Release upload, owner-provisioned GitHub
Secrets/Variables, or a 30-day production trial.

## Rollback

Remove `src/arxiv_daily_push/simulation.py`, the `run-two-day-simulation` CLI
command, `tests/test_simulation.py`, `MOD-ADP-031`, `FORM-ADP-033`,
`PARAM-ADP-167` through `PARAM-ADP-169`, this phase record, the run manifest,
and restore version `0.11.26`.
