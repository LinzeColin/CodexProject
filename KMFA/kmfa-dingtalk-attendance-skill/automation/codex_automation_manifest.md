# Codex Automation Manifest

This file mirrors the local Codex automation state that must stay aligned with
GitHub. Local automation records are not portable by themselves; these prompt
files are the portable source for another agent or computer.

## Canonical Repo

- Repository: `LinzeColin/CodexProject`
- Branch: `main`
- Skill path: `KMFA/kmfa-dingtalk-attendance-skill/`
- Public metadata/config path: `KMFA/metadata/`

## Local Automations

| Local id | Name | Beijing schedule | Prompt mirror |
| --- | --- | --- | --- |
| `automation-3` | `每日早晚钉钉考勤检查｜晨报` | Daily 10:35 | `automation/morning_prompt.md` |
| `automation-4` | `每日早晚钉钉考勤检查｜晚报` | Daily 20:05 | `automation/evening_prompt.md` |

## Sync Rule

Any change to `SKILL.md`, `automation/*.md`, automation schedule, automation
cwd/model/reasoning setting, or related validator/config must be validated,
committed, and pushed to GitHub `main` in the same run before claiming the
workflow is portable.

## Runtime Rule

Automation prompts must call `$kmfa-dingtalk-attendance-skill`. If a Codex
agent cannot resolve repo-scoped skill names, it must read
`KMFA/kmfa-dingtalk-attendance-skill/SKILL.md` from the repo clone and follow
the same rules.

Private runtime, raw DingTalk payloads, SQLite, report bodies, credentials, and
resolved DWS identifiers must stay out of Git.
