# KMFA Daily Routine Check Runbook

## 1. Repo Entry

Canonical GitHub destination:

```text
Repository: LinzeColin/CodexProject
Local root: /Users/linzezhang/CodexProject
Project root: KMFA/
Skill folder: KMFA/daily_routine_check_skill/
Automation module: KMFA/tools/daily_routine_check/
Public metadata: KMFA/metadata/daily_routine_check/
```

Default branch policy:

- Work on `main`.
- Do not create PRs, issues, branches, or worktrees unless the user explicitly asks.
- Before changing files, confirm:

```bash
git branch --show-current
git fetch origin main
git rev-parse HEAD
git rev-parse origin/main
```

If local `HEAD` is not `origin/main`, stop and resolve with the owner or do `git pull --ff-only origin main` when safe.

## 2. What This Automation Does

This skill powers one automation only:

```text
Dingtalk-routine-check / 钉钉工作检查
```

It does not create, replace, or operate the upstream DWS archive job. It reads the existing complete OneDrive zip package as its only upstream input:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip
```

The checker streams required CSV members from the zip without copying or extracting it. A disk `DWS_Outputs/` folder is normally absent and must never be probed, created, materialized, or used as fallback. The zip must contain these members, with or without a top-level `DWS_Outputs/` prefix:

```text
DWS_Outputs/付款请示群/chat_records/chat_records.csv
DWS_Outputs/付款请示群/_manifest/manifest.csv
DWS_Outputs/生产管理群/chat_records/chat_records.csv
DWS_Outputs/生产管理群/_manifest/manifest.csv
```

If healthcheck reports `ZIP_INPUT_MISSING` or `ZIP_INPUT_UNREADABLE`, hydrate or replace the sole OneDrive zip and fail closed. Do not search for a directory alternative, copy/extract members into local scratch, or automatically evict the zip after the run.

The automation performs:

1. Load DWS group manifests and chat records.
2. Normalize messages and file references.
3. Match routine deliverable rules.
4. Identify missing/late/unreliable items.
5. Run OCR/LLM classification for image-only documents when needed.
6. Separately classify `资金账户明细表` and `资金流水明细/资金明细`.
7. Extract cash-account summary and cash-flow entries into structured tables.
8. Evaluate cash threshold risk: P0/P1/P2.
9. Append logs and update SQLite ledger.
10. Notify 张霖泽 for missing, late, P0, P1, and review-needed events.

Current offline implementation does not call an external OCR provider. It uses
DWS message text plus configured amount markers first; image/file-only cash
candidates become `NEEDS_REVIEW` until private OCR credentials and targets are
explicitly configured.

## 3. First Files To Read

```text
KMFA/daily_routine_check_skill/SKILL.md
KMFA/daily_routine_check_skill/references/configuration.md
KMFA/daily_routine_check_skill/references/rules.md
KMFA/daily_routine_check_skill/references/data_contract.md
KMFA/daily_routine_check_skill/references/database_governance.md
KMFA/metadata/daily_routine_check/README.md
KMFA/metadata/daily_routine_check/routine_rules.public.yaml
KMFA/metadata/daily_routine_check/cash_monitor.public.yaml
KMFA/tools/daily_routine_check/main.py
KMFA/tests/test_daily_routine_check.py
```

## 4. Safe Offline Commands

Run from repo root:

```bash
python3 KMFA/tools/daily_routine_check/healthcheck.py --config-only --input-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip
python3 KMFA/daily_routine_check_skill/tools/validate_skill_package.py
python3 -m py_compile KMFA/tools/daily_routine_check/*.py
python3 -m unittest KMFA.tests.test_daily_routine_check -q
git diff --check
git status --porcelain
```

## 5. Live Run Commands

Live notification requires explicit current authorization and local notification config.

Dry run:

```bash
python3 -m KMFA.tools.daily_routine_check.main \
  --date today \
  --timezone Asia/Shanghai \
  --trigger-window morning_1135 \
  --input-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip \
  --dry-run
```

Send notifications:

```bash
python3 -m KMFA.tools.daily_routine_check.main \
  --date today \
  --timezone Asia/Shanghai \
  --trigger-window evening_1705 \
  --input-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip \
  --send
```

Do not send live notifications unless the user confirms that notification targets are configured.
Each scheduled trigger must execute exactly one matching window command once.
Never run both commands in one task. Scheduled commands must not include
`--cleanup` or `--apply`; cleanup remains a separate manual maintenance action.

## 6. Codex Desktop Automation Schedule

Business date evaluation uses Beijing time / `Asia/Shanghai`. The Codex
Desktop scheduler itself uses the host local wall clock with no explicit
timezone field.

Create exactly one local Codex Desktop automation:

```text
Dingtalk-routine-check / 钉钉工作检查
```

The automation has two daily business trigger windows only:

```text
11:35 Asia/Shanghai -> --trigger-window morning_1135
17:05 Asia/Shanghai -> --trigger-window evening_1705
```

At the current Australia/Sydney AEST offset (UTC+10), save one pure local
scheduler rule:

```text
RRULE:FREQ=DAILY;BYHOUR=13,19;BYMINUTE=5,35;BYSETPOS=2,3
```

`BYSETPOS=2,3` selects 13:35 and 19:05 from the four hour/minute candidates.
Do not add `DTSTART`, `TZID`, an explicit scheduler timezone field, or multiple
RRULE lines. Recalculate the local hours when the host UTC offset changes.

Do not create one automation per rule. `due_time` remains in YAML as business reference, but rule evaluation is controlled by the trigger window.

Every run log must include:

```text
run_at_beijing
check_date
trigger_window
rules_evaluated
rules_skipped
```

If upstream OneDrive DWS output is missing or stale, record `SOURCE_MISSING` or `SOURCE_STALE` and notify 张霖泽 according to the notification policy.
Rules for a source-blocked group must appear in `rules_blocked_by_source` and must not be emitted as routine `MISSING`; stale payment source also suppresses `CASH_NO_DATA` to avoid false cash-risk alerts.

## 7. GitHub Sync Rule

After any change to the skill/code/public metadata/tests:

```bash
python3 KMFA/daily_routine_check_skill/tools/validate_skill_package.py
python3 -m unittest KMFA.tests.test_daily_routine_check -q
git diff --check
git status --porcelain
git add KMFA/daily_routine_check_skill KMFA/metadata/daily_routine_check KMFA/tools/daily_routine_check KMFA/tests/test_daily_routine_check.py
git commit -m "daily-routine-check: update skill"
git pull --ff-only origin main
git push origin main
git fetch origin main
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
```

The helper script `KMFA/tools/daily_routine_check/git_autosync.py` can automate this, but it must fail closed if validators fail or blocked files are staged.

## 8. Completion Standard

Do not claim completion without:

- exact files changed
- validation commands and outcomes
- commit hash
- push result
- post-push `HEAD == origin/main`
- runtime dry-run result when behavior changed
