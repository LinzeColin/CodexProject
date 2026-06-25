# Agent Continuity Instructions

Default language for user-facing responses: Chinese.

## Mission

Continue development of the TAB FIFA research-only reporting system with high accuracy, high traceability, and low context waste.

## First Files To Read

1. `docs/HANDOFF.md`
2. `docs/DEVELOPMENT_STATUS.md`
3. `docs/FILE_RETENTION_POLICY.md`
4. `tab-research-pipeline/README.md`
5. `tab-research-pipeline/tests/test_pipeline.py`

## Non-Negotiable Safety Rules

- Do not automate betting.
- Do not click odds.
- Do not add selections to Bet Slip.
- Do not submit or mutate wagering tickets.
- Do not bypass TAB access controls.
- Treat TAB public raw AI controlled access rejection as fail-closed.
- Do not upload private My Bets raw text, Chrome profiles, cookies, credentials, OTP, account identifiers, or private stake details.

## Current Access Policy

Public raw and Live discovery are blocked by access policy:

- blocker code: `ai_controlled_access_rejected`
- allowed recovery: official/authorized feed, user export/import, research-only from existing fresh partial raw
- forbidden recovery: headed fallback, CAPTCHA bypass, fingerprint spoofing, stealth browser

`TAB_FIFA_HEADLESS=0` is allowed only for user-authorized private My Bets read-only bootstrap.

## Development Standard

- Keep changes focused and test-backed.
- Update `docs/HANDOFF.md` after meaningful state changes.
- Update `docs/DEVELOPMENT_STATUS.md` when a milestone or blocker changes.
- Keep `artifacts/latest/` public-safe.
- Keep local cache, virtualenv, private profiles, and generated bulk outputs out of Git unless explicitly approved and sanitized.

## S5PBT01 Structure Boundary

- Active source and tests stay in `tab-research-pipeline/`.
- `legacy/fifa-analysis-system/` is read-only historical code and must not become a default run path.
- `artifacts/` is generated-output territory; use the Wave 2 manifest before any archive movement.
- `ops/` is local operational reference, not application source.

## Verification

Preferred checks:

```bash
cd tab-research-pipeline
python3 -m py_compile run_daily_report.py scripts/tab_fifa_app_server.py tests/test_pipeline.py
bash -n scripts/run_tab_fifa_daily_automation.sh scripts/tab_real_refresh_smoke.sh
node --check scripts/refresh_tab_readonly.mjs
node --check scripts/discover_tab_live_boards.mjs
python3 -m unittest tests.test_pipeline
```

Record actual command results. Do not claim a test passed if it was not run.

