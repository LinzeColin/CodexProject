# KMFA Daily Routine Check Skill Package

This folder packages public-safe operating instructions, configuration templates, validation checks, and Codex Desktop handoff material for the KMFA daily DingTalk routine check automation.

It intentionally excludes private runtime data, DingTalk credentials, DWS resolved identifiers, SQLite ledgers, raw DWS JSON/JSONL, raw OneDrive archives, OCR raw bodies, robot webhook URLs, and report bodies.

Start with `SKILL.md`, then read:

1. `references/runbook.md`
2. `references/configuration.md`
3. `references/rules.md`
4. `references/data_contract.md`
5. `references/database_governance.md`

## Purpose

The skill streams required members from the complete OneDrive `DWS_Outputs.zip` and checks whether required DingTalk work artifacts were sent on time. That zip is the only upstream input; a disk `DWS_Outputs/` folder is normally absent and must not be probed, created, materialized, extracted, or used as fallback. It also performs cash monitoring for Yang Ting's two separate daily finance artifacts:

- `资金账户明细表`
- `资金流水明细` / `资金明细`

The skill does not collect DingTalk messages by itself. It depends on an existing upstream DWS archive job that already writes into OneDrive.

## GitHub Policy

- Destination: `LinzeColin/CodexProject/KMFA/daily_routine_check_skill`
- Branch: `main` only
- No open branch
- No open PR
- No issue creation unless the owner explicitly asks
- Any local change to the skill/code/public metadata/tests must be validated, committed, pushed to `origin/main`, and verified.

## Automation Schedule

Create exactly one Codex Desktop automation:

```text
Dingtalk-routine-check / 钉钉工作检查
```

Business evaluation uses `Asia/Shanghai`. The existing timezone-free local scheduler has two daily trigger windows:

- `11:35` -> `--trigger-window morning_1135`
- `17:05` -> `--trigger-window evening_1705`

Do not create one automation per rule. Every run log records `run_at_beijing`, `check_date`, `trigger_window`, `rules_evaluated`, and `rules_skipped`.
Each trigger runs only its corresponding window once. Scheduled runs do not perform cleanup, copy/extract source members, or automatically evict the source zip.
