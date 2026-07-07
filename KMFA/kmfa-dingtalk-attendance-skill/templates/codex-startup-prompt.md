# KMFA DingTalk Attendance Startup Prompt

You are taking over KMFA S19 DingTalk attendance automation in `LinzeColin/CodexProject`.

Work from repo root and stay on `main`. Do not create branches, PRs, issues, or worktrees.

Read first:

1. `KMFA/kmfa-dingtalk-attendance-skill/SKILL.md`
2. `KMFA/kmfa-dingtalk-attendance-skill/references/runbook.md`
3. `KMFA/HANDOFF.md`
4. `KMFA/metadata/dingtalk_attendance/README.md`

Do not commit private runtime data, DWS resolved identifiers, SQLite, raw JSON/JSONL/GZ, employee attendance plaintext, or report bodies.

Do not run DWS live commands or send DingTalk messages unless the user explicitly authorizes that live action in the current thread.

Current critical rules:

- rest reminder threshold is 23 effective attendance days
- 丁春法 and 李永占 are excluded only from rest-required outputs
- all other statuses still count normally
- SQLite is private/rebuildable and not salary basis

Run safe validation before claiming completion:

```bash
python3 KMFA/kmfa-dingtalk-attendance-skill/tools/validate_skill_package.py
python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only
python3 KMFA/tools/dingtalk_attendance/validate_no_sensitive_git.py
python3 KMFA/tools/dingtalk_attendance/check_s19_dingtalk_attendance.py
python -m py_compile KMFA/tools/dingtalk_attendance/*.py
python3 -m unittest KMFA.tests.test_dingtalk_attendance -q
git diff --check
```
