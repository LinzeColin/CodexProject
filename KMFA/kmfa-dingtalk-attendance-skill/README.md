# KMFA DingTalk Attendance Skill Package

Canonical path:

```text
KMFA/kmfa-dingtalk-attendance-skill/
```

This folder packages the public-safe operating instructions, automation prompts, configuration templates, validators, PostgreSQL schema, stage-2 consensus protocol, and handoff rules for KMFA 钉钉考勤 skill.

It intentionally excludes private runtime data, DingTalk credentials, DWS resolved identifiers, SQLite, raw OneDrive archives, and report bodies.

Start with `SKILL.md`, then read:

```text
references/runbook.md
references/configuration.md
references/operating_contract.md
references/source_of_truth_contract.md
references/stage2_shadow_payroll_acceptance.md
docs/codex_task_pack.md
docs/acceptance_criteria.md
```

The public metadata/config source is `KMFA/metadata/`; real private attendance payloads remain in ignored private runtime or OneDrive unless explicitly exported in public-safe form.

Local Codex automation state is mirrored in `automation/`. Any change to this skill package or automation prompts must be committed and pushed to GitHub `main`.
