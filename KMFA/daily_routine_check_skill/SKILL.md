---
name: daily_routine_check_skill
description: Use when operating, reviewing, migrating, or modifying KMFA DingTalk daily routine check automation for payments, production management, routine deliverables, and Yang Ting cash OCR monitoring.
---

# KMFA Daily Routine Check Skill

## Use First

This skill is the portable, public-safe operating entry for the KMFA DingTalk daily routine check automation.

Use it only with a clone of:

```text
LinzeColin/CodexProject
```

Work from:

```text
/Users/linzezhang/CodexProject
```

Project root:

```text
KMFA/
```

Skill package:

```text
KMFA/daily_routine_check_skill/
```

Before acting, read:

1. `KMFA/daily_routine_check_skill/references/runbook.md`
2. `KMFA/daily_routine_check_skill/references/configuration.md`
3. `KMFA/daily_routine_check_skill/references/rules.md`
4. `KMFA/daily_routine_check_skill/references/data_contract.md`
5. `KMFA/daily_routine_check_skill/references/database_governance.md`
6. `KMFA/metadata/daily_routine_check/README.md`
7. The exact source or test files you will touch

## Scope

Automation name:

```text
Dingtalk-routine-check
```

Chinese name:

```text
钉钉工作检查
```

Timezone:

```text
Asia/Shanghai
```

Automation schedule:

```text
one automation only: Dingtalk-routine-check / 钉钉工作检查
daily 11:35 Asia/Shanghai -> trigger_window=morning_1135
daily 17:05 Asia/Shanghai -> trigger_window=evening_1705
```

Do not create one automation per rule. `due_time` may remain in YAML as a business reference, but actual evaluation is controlled by the two trigger windows.

Canonical primary input:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip
```

The reader streams required CSV entries from the zip and does not extract the package to local disk. Direct group folders remain a compatibility fallback:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/
```

This skill must not create or manage the upstream DWS archive automation. The upstream archive already exists and is treated as a producer.

## Hard Boundaries

- Do not create branches, PRs, issues, or worktrees unless the user explicitly changes this rule.
- Work on `main` only.
- Push directly to `origin/main` only after validation passes.
- Do not commit `.env.local`, webhook URLs, signing keys, app secrets, token values, DWS resolved IDs, SQLite, raw JSON, raw JSONL, raw JSONL.gz, raw OCR bodies, raw screenshots, DWS output archives, robot response bodies, or OneDrive private archives.
- Do not run live DingTalk/DWS send commands without explicit current-thread authorization.
- Do not change the user's existing DWS archive automation unless the owner explicitly asks.
- Do not create multiple routine-check automations for individual rules.
- Do not merge `资金账户明细表` and `资金流水明细`; they are two separate required artifacts.
- Treat `资金流水明细` and `资金明细` as the same document family.
- Do not hard-code OCR/classification keywords in Python; load them from YAML configuration.

## Current Business Rules

### 付款请示群

Daily:

- 杨婷：资金账户明细表
- 杨婷：资金流水明细 / 资金明细

Weekly Monday:

- 杨婷：现存票据
- 杨婷：保证金回款表
- 杨婷：回款明细表

Monthly:

- 吴云霞：纳税申报表
- 吴云霞：汇算清缴
- Due by the Friday of the third week of each natural month.

### 生产管理群

Daily:

- 黄婷 or 李权智：每日人员表

Weekly Thursday:

- 黄婷 or 李权智：资金计划

Weekly Friday:

- 黄婷：工人工时表
- 黄婷：应付表

### Cash Monitoring

- Sender: 杨婷
- Group: 付款请示群
- Cash account document: `资金账户明细表`
- Cash flow document: `资金流水明细` / `资金明细`
- Hard threshold: 500000 RMB
- Soft threshold: 1000000 RMB
- P0 red: total available cash below hard threshold
- P1 yellow: total available cash below soft threshold but not below hard threshold
- P2 green: normal; log only, do not disturb
- Missing/late/low-confidence/OCR conflict: notify 张霖泽

## Data and Storage

Private input:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip
```

Private OneDrive routine-check archive:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/
```

Private local runtime:

```text
KMFA/metadata/daily_routine_check/private_runtime/
```

Active SQLite ledger is local-private and ignored by Git. Daily snapshots, append-only JSONL logs, OCR cache references, and cleanup reports may be stored in OneDrive.

Every run log must include `run_at_beijing`, `check_date`, `trigger_window`, `rules_evaluated`, and `rules_skipped`. Missing or stale upstream DWS output must be recorded as `SOURCE_MISSING` or `SOURCE_STALE` and surfaced to 张霖泽 through the notification policy.

## Portable Package

- Public configuration: `KMFA/metadata/daily_routine_check/`
- Templates: `KMFA/daily_routine_check_skill/templates/`
- Operating runbook: `KMFA/daily_routine_check_skill/references/runbook.md`
- Rule list: `KMFA/daily_routine_check_skill/references/rules.md`
- Data contract: `KMFA/daily_routine_check_skill/references/data_contract.md`
- Database governance: `KMFA/daily_routine_check_skill/references/database_governance.md`
- Validator: `KMFA/daily_routine_check_skill/tools/validate_skill_package.py`

Run package validation from repo root:

```bash
python3 KMFA/daily_routine_check_skill/tools/validate_skill_package.py
```

Completion standard:

- Exact files changed
- Validation commands and outcomes
- Git commit hash
- Push result
- Post-push `HEAD == origin/main`
