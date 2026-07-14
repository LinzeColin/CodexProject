# Codex Desktop Setup Notes

## Objective

Use Codex Desktop locally, not Codex Cloud, to install and maintain the `daily_routine_check_skill` under:

```text
/Users/linzezhang/CodexProject/KMFA/daily_routine_check_skill
```

## What Codex Must Do

1. Clone or open `/Users/linzezhang/CodexProject`.
2. Confirm current branch is `main`.
3. Confirm `HEAD == origin/main` or fast-forward pull.
4. Create/update:

```text
KMFA/daily_routine_check_skill/
KMFA/metadata/daily_routine_check/
KMFA/tools/daily_routine_check/
KMFA/tests/test_daily_routine_check.py
```

5. Do not create branch/PR/issue/worktree.
6. Preserve the governance style used by `kmfa-dingtalk-attendance-skill`.
7. Configure exactly one local scheduler/automation named `Dingtalk-routine-check / 钉钉工作检查`.
8. Set only two daily Beijing triggers: `11:35 -> morning_1135` and `17:05 -> evening_1705`.
9. Invoke the skill, not duplicate DWS scanning or create one automation per rule.
10. Configure local Git autosync guard so validated changes push to `origin/main`.

## OneDrive Input

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip
```

The automation must treat this complete zip as the only read-only upstream input and stream only required members. A disk `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/` folder is normally absent: never probe, create, materialize, copy, extract, or use it as fallback. Do not automatically evict the zip after each run.

## Recommended Automation Commands

11:35 Beijing:

```bash
cd /Users/linzezhang/CodexProject
python3 -m KMFA.tools.daily_routine_check.main --date today --timezone Asia/Shanghai --trigger-window morning_1135 --input-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip --send
```

17:05 Beijing:

```bash
cd /Users/linzezhang/CodexProject
python3 -m KMFA.tools.daily_routine_check.main --date today --timezone Asia/Shanghai --trigger-window evening_1705 --input-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip --send
```

For setup verification:

```bash
python3 -m KMFA.tools.daily_routine_check.main --date today --timezone Asia/Shanghai --trigger-window morning_1135 --input-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip --dry-run
python3 -m KMFA.tools.daily_routine_check.main --date today --timezone Asia/Shanghai --trigger-window evening_1705 --input-zip /Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip --dry-run
```

Each scheduled trigger executes only its corresponding command once. Never run
both commands in one task, and never add `--cleanup` or `--apply` to scheduled
commands. Cleanup remains a separate manual maintenance action.

## Git Autosync Command

```bash
cd /Users/linzezhang/CodexProject
python3 KMFA/tools/daily_routine_check/git_autosync.py --once
```

Optional continuous local watcher:

```bash
python3 KMFA/tools/daily_routine_check/git_autosync.py --watch --interval-seconds 60
```

The watcher must fail closed if tests or sensitive-data scans fail.
