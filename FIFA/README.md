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
- Legacy system: `legacy/fifa-analysis-system/` is read-only and not a default run path.
- Local ops material: `ops/` is operational reference only, not application source.
- Handoff: `docs/HANDOFF.md` and `docs/HANDOFF_DETAILED.md`
- Governance entry: `docs/governance/MODEL_SPEC.md`
- Current formal automation status: blocked.
- Research-only daily report status: available as candidate.
- Current executable new stake: `AUD 0`.

## S5PBT01 Structure Boundary

- Active pipeline and tests live under `tab-research-pipeline/`.
- Legacy implementation is isolated under `legacy/fifa-analysis-system/`; default commands do not import or execute it.
- Generated reports, backups, and public-safe latest artifacts live under `artifacts/`; Wave 2 archive candidates remain checksum-bound by the governance manifest before any future movement.
- Local launch and cleanup notes live under `ops/`; they are not product runtime source.
- Structure evidence: `docs/FIFA_structure_report.md` and `../governance/stage_gates/s5pb/fifa_structure_contract.yaml`.

## Governance Baseline

FIFA now maintains canonical governance files under `docs/governance/`:

- `MODEL_SPEC.md`
- `model_registry.yaml`
- `formula_registry.yaml`
- `parameter_registry.csv`
- `DEVELOPMENT_LEDGER.md`
- `development_events.jsonl`
- `DELIVERY_PLAN.md`
- `delivery_tasks.yaml`
- `VERSION_MATRIX.yaml`
- `TRACEABILITY_MATRIX.csv`

中文人类入口：`功能清单`、`开发记录`、`模型参数文件`。这三份文件必须直接保留
owner 可读的功能摘要、Roadmap/任务、模型/参数、证据状态、限制和下一步门禁；
它们不是跳转页，也不是第二套可编辑机器事实源。机器真相仍以
`docs/governance/` 下的 Lean v2 文件为准。

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
