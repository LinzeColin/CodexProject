# FIFA TAB Research System

This repository is the continuity home for the local TAB FIFA betting-research system.

## Purpose

Build and maintain a research-only FIFA World Cup betting market analysis system:

- read and normalize authorized/public-safe market snapshots;
- generate Chinese professional betting-research reports;
- track research cadence, missing reports, and model/market diagnostics;
- monitor private My Bets positions only after local user authorization;
- support daily report automation readiness;
- never place bets, click odds, mutate Bet Slip, or bypass TAB access controls.

## Current Status

- Local app entry: `http://127.0.0.1:8767/`
- Local app bundle: `/Users/linzezhang/Downloads/TAB FIFA盘口研究系统.app`
- Primary code: `tab-research-pipeline/`
- Latest public artifacts: `artifacts/latest/`
- Handoff: `docs/HANDOFF.md` and `docs/HANDOFF_DETAILED.md`
- Current formal automation status: blocked.
- Research-only daily report status: available as candidate.
- Current executable new stake: `AUD 0`.

## Hard Boundary

TAB public raw / Live discovery access is currently treated as `ai_controlled_access_rejected`.

The system must fail closed and must not use:

- headed fallback for public raw;
- CAPTCHA bypass;
- fingerprint spoofing;
- stealth browser;
- automatic odds clicks;
- Bet Slip mutation;
- unattended betting.

Allowed recovery paths:

- official or authorized odds/data feed;
- user-exported public raw snapshot imported into the pipeline;
- existing fresh partial raw for research-only diagnostics;
- private My Bets read-only import after user-authorized local login.

## Quick Start

```bash
cd tab-research-pipeline
python3 -m unittest tests.test_pipeline
python3 run_daily_report.py
python3 scripts/tab_fifa_app_server.py --port 8767
```

For current status and next steps, read:

- `docs/DEVELOPMENT_STATUS.md`
- `docs/FILE_RETENTION_POLICY.md`
- `docs/HANDOFF.md`
