# PFI_OS Thread Handshake Manifest

Last updated: 2026-06-15 Australia/Sydney

This file records read-only handshakes with the three source-system Codex threads that must feed the PFI_OS migration, GitHub backup, and local slimming work. Treat it as a routing manifest, not as proof that the referenced local files still exist. Re-verify paths before moving, deleting, or uploading data.

## Source Threads

| Source thread | Thread id | Original cwd | PFI_OS target | Current migration status |
| --- | --- | --- | --- | --- |
| Consumption Analysis Original | `019e8d22-4ad0-7760-a31c-d61b090bef20` | `/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-20250604` | `systems/finance_ledger` | source/tests/docs migrated |
| Government Document Interpretation | `019e8c9e-6816-7320-8d6b-c6f215378abd` | `/Users/linzezhang/Documents/Codex/2026-06-03/sop-skill-pursuing-goal-diff-step` | `systems/policy_intelligence` | source/tests/docs migrated |
| Industry Research and Trading Strategy Advice | `019e8b29-5726-7ff0-a044-dbfc6a15e460` | `/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-codex` | `systems/industry_research` | source/tests/docs migrated |

## Finance Ledger / Consumption Analysis

Current root:

```text
/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-20250604
```

Migrated into PFI_OS:

```text
systems/finance_ledger/source
systems/finance_ledger/samples
systems/finance_ledger/SYSTEM_MANIFEST.json
```

Keep private and do not upload:

```text
data/finance_ledger/
outputs/finance_ledger_20220605_20260603/data/
outputs/finance_ledger_20220605_20260603/audit/
*.sqlite
raw Alipay/WeChat bills
transaction-level HTML reports
```

Known remaining issues:

- Goal completion audit drift was reported as `8/9` with `goal_complete=false`.
- Manual review queue had 92 rows at handoff time.
- WeChat intake contract existed, but the live SQLite table was not confirmed in the source handoff.

Next PFI_OS step:

- Build a ResearchBus adapter that publishes summarized ledger metrics only. Never publish raw transaction rows.

## Policy Intelligence / Government Documents

Current policy system root:

```text
/Users/linzezhang/Documents/Codex/2026-06-03/sop-skill-pursuing-goal-diff-step/outputs/source-authority-registry
```

Migrated into PFI_OS:

```text
systems/policy_intelligence/source
systems/policy_intelligence/source/data/sample
systems/policy_intelligence/SYSTEM_MANIFEST.json
```

Important local runtime data:

```text
data/source_registry.sqlite
data/policy_documents.sqlite
data/automation/scheduler.json
data/monitor/latest_status.json
reports/handoff_package_20260615/
reports/政策智能系统_交付评审包_20260615.zip
```

Keep private and do not upload:

```text
/Users/linzezhang/.policy-intelligence
/Users/linzezhang/.codex/automations/automation
/Users/linzezhang/Library/Application Support/Google/Chrome/Default
policy-search-secrets.json
policy-platform-auth.json
cookies, sessions, browser profiles, API keys, raw HTML dumps, debug logs
```

Known remaining issues:

- Latest monitor status was `attention`.
- Automation freshness was stale relative to 2026-06-15.
- Latest report quality gates were not production clean: external references `1/5`, external platforms `1/2`.
- It should not be marketed as unlimited whole-web crawling; use compliant-source coverage language.

Next PFI_OS step:

- Build a ResearchBus adapter that publishes policy readiness, queue status, external-reference gaps, and quality-gate summaries without raw document text, cookies, API keys, or local auth paths.

## Industry Research / Trading Strategy Advice

Current source root:

```text
/Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-codex/outputs/AI-Research-System
```

Migrated into PFI_OS:

```text
systems/industry_research/source
systems/industry_research/SYSTEM_MANIFEST.json
```

External report output:

```text
/Users/linzezhang/Downloads/行研报告
```

Keep private and do not upload:

```text
data/private/
data/private/alipay/
data/report_artifacts/
/Users/linzezhang/Library/Containers/com.moomoo.mm-mac/
/Users/linzezhang/.codex/
/Users/linzezhang/Downloads/支付宝*
/Users/linzezhang/Downloads/*交易明细*
real holdings, account data, cookies, API keys, moomoo local databases, runtime logs
```

Known remaining issues at source handoff time:

- Automation health was `fail`.
- Main blockers: automation model gate mismatch, stale quote snapshot, Alipay not updated, missing policy bridge, and missing 2026-06-15 reports.
- The separate source handoff package path was reported as `/Users/linzezhang/Downloads/AI行研系统交接包_15062026.zip`.

Current PFI_OS migration evidence:

- Full migrated suite passed locally: `198 passed, 9 subtests passed`.
- Root smoke includes compile, focused industry tests, and CLI help.
- Runtime output and private account artifacts remain excluded.

Next PFI_OS step:

- Build a ResearchBus adapter that publishes report readiness, evidence gaps, validation tasks, and strategy scan summaries without private holdings or account data.

## Slimming Rules

Back up to GitHub before deleting only when files are public-safe:

```text
old handoff docs
public-safe report samples
public-safe fixture CSVs
README/HANDOFF/docs/tests/source code
```

Delete locally without GitHub backup only when files are reproducible caches:

```text
__pycache__/
.pytest_cache/
.DS_Store
temporary preview caches
```

Keep local/private unless a separate private storage plan exists:

```text
SQLite runtime databases
raw bills
holdings
broker-adjacent data
browser profiles
API credentials
automation local state
generated report artifacts containing account or source traces
```
