---
name: kmfa-dingtalk-attendance-skill
description: Use when operating, reviewing, migrating, or modifying KMFA S19 DingTalk attendance automation in LinzeColin/CodexProject.
---

# KMFA DingTalk Attendance Skill

## Use First

This skill is the portable, public-safe operating entry for KMFA S19 DingTalk attendance automation.
Use it only with a clone of `LinzeColin/CodexProject` and start from `main`.

Before acting, read:

1. `references/runbook.md`
2. `references/configuration.md`
3. `KMFA/HANDOFF.md`
4. `KMFA/metadata/dingtalk_attendance/README.md`
5. The exact source or test files you will touch

## Hard Boundaries

- Do not create branches, PRs, issues, or worktrees unless the user explicitly changes this rule.
- Do not commit `.env.local`, webhook URLs, signing keys, app secrets, token values, DWS resolved IDs, SQLite, raw JSON/JSONL/GZ, employee attendance plaintext, report bodies, or OneDrive raw archives.
- Do not run DWS live commands or send DingTalk messages without explicit user authorization in the current thread.
- Live DWS gate env: `KMFA_S19_ALLOW_DWS_COMMANDS`.
- Use `python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only` before any live consideration.
- If changing behavior, use tests first and keep the change narrowly scoped.

## Current Attendance Rules

- Automation name: `每日早晚钉钉考勤检查`.
- Timezone: `Asia/Shanghai`.
- Morning run: 08:35. Evening run: 18:15.
- DWS backend is live-only; no sample employees or fixture attendance records are allowed as production data.
- Known no-record people: `张霖泽`, `林全意`; only their own missing records are exempted.
- Rest reminder rule: `REST_REQUIRED_THRESHOLD_DAYS = 23`.
- Rest reminder excluded names: `丁春法`, `李永占`; they are excluded only from `需要休息` and private ledger `rest_required_snapshots`, while all other statuses are still counted normally.
- Effective attendance day: the same natural day has both morning and evening punches.
- Monthly notification rollups reset by natural month.
- For each status section, show everyone when count is 10 or less; otherwise show total count plus Top 10.
- SQLite ledger is a rebuildable private index, not payroll basis and not a wage calculation source.
- Private ledger path: `KMFA/metadata/dingtalk_attendance/private_runtime/attendance_ledger.sqlite`; never commit it.

## Portable Package

- Config templates: `templates/`
- Operating runbook: `references/runbook.md`
- Config map: `references/configuration.md`
- Skill conversion SWOT and downstream impact: `references/decision-impact.md`
- Local package validator: `tools/validate_skill_package.py`

Run the package validator from repo root:

```bash
python3 KMFA/kmfa-dingtalk-attendance-skill/tools/validate_skill_package.py
```
