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

Codex Desktop scheduler rules use the host's local wall clock and must be a
single pure `RRULE:` string. Do not add `DTSTART`, `TZID`, an explicit
scheduler timezone field, or multiple RRULE lines. Business dates and report
cutoffs remain Beijing time.

Current host clock snapshot: Australia/Sydney AEST (UTC+10). Recalculate the
local wall-clock hours whenever the host UTC offset changes.

| Local id | Name | Beijing business time | Current AEST scheduler rule | Execution | Prompt mirror |
| --- | --- | --- | --- | --- | --- |
| `kmfa` | `KMFA｜每日钉钉考勤检查｜晨报` | Daily 10:35 | `RRULE:FREQ=DAILY;BYHOUR=12;BYMINUTE=35` | local, `gpt-5.3-codex-spark`, `xhigh` | `automation/morning_prompt.md` |
| `kmfa-3` | `KMFA｜每日钉钉考勤检查｜晚报` | Daily 20:05 | `RRULE:FREQ=DAILY;BYHOUR=22;BYMINUTE=5` | local, `gpt-5.3-codex-spark`, `xhigh` | `automation/evening_prompt.md` |

Current local Codex cwd list for both automations:

```text
/Users/linzezhang/CodexProject
```

Run KMFA git, skill, tests, and scripts from `/Users/linzezhang/CodexProject`.
The upstream DWS archive has its own separate automation and is not part of the
KMFA attendance automation cwd list.

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
