# Codex Desktop Prompt｜Install or Update daily_routine_check_skill

You are working locally in Codex Desktop, not Codex Cloud.

Repository:

```text
/Users/linzezhang/CodexProject
```

Target branch policy:

```text
main only
no branch
no PR
no issue
no worktree
push directly to origin/main after validation
```

Task:

1. Read `KMFA/AGENTS.md` and current `KMFA/kmfa-dingtalk-attendance-skill/SKILL.md` to mirror governance style.
2. Create/update `KMFA/daily_routine_check_skill/`.
3. Create/update `KMFA/metadata/daily_routine_check/`.
4. Create/update `KMFA/tools/daily_routine_check/`.
5. Create/update `KMFA/tests/test_daily_routine_check.py`.
6. Do not modify the existing DWS archive automation.
7. Do not create any Automation 1. This skill only reads existing OneDrive DWS outputs.
8. Input must default to `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip`, with `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs` only as a compatibility fallback.
9. Implement independent checks for `资金账户明细表` and `资金流水明细/资金明细`.
10. Do not generate summary Excel. Implement SQLite + JSONL logs.
11. Keep exactly one `Dingtalk-routine-check / 钉钉工作检查` automation with two Beijing triggers: `11:35 -> morning_1135` and `17:05 -> evening_1705`.
12. Do not create one automation per rule.
13. Ensure every run log records `run_at_beijing`, `check_date`, `trigger_window`, `rules_evaluated`, and `rules_skipped`.
14. Record `SOURCE_MISSING` or `SOURCE_STALE` when upstream DWS output is missing or stale.
15. Implement local Git autosync guard so any future change under this skill/code/metadata/tests can be validated, committed, pushed, and verified on main.

Validation required:

```bash
python3 KMFA/daily_routine_check_skill/tools/validate_skill_package.py
python3 -m py_compile KMFA/tools/daily_routine_check/*.py
python3 -m unittest KMFA.tests.test_daily_routine_check -q
git diff --check
git status --porcelain
```

Push requirements:

```bash
git add KMFA/daily_routine_check_skill KMFA/metadata/daily_routine_check KMFA/tools/daily_routine_check KMFA/tests/test_daily_routine_check.py
git commit -m "daily-routine-check: add skill and local automation contract"
git pull --ff-only origin main
git push origin main
git fetch origin main
test "$(git rev-parse HEAD)" = "$(git rev-parse origin/main)"
```

Return to the user:

- files changed
- validation results
- commit hash
- push result
- post-push parity check
