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
cutoffs remain Beijing time inside the runner; they do not shift the owner's
fixed scheduler wall-clock time.

The `kmfa-3` owner-set 20:00 wall-clock time is permanent. Do not convert it
when the host UTC offset or daylight-saving state changes.

| Local id | Name | Business/run time | Scheduler rule | Execution | Prompt mirror |
| --- | --- | --- | --- | --- | --- |
| `kmfa` | `KMFA｜每日钉钉考勤检查｜晨报` | Daily 10:35 | `RRULE:FREQ=DAILY;BYHOUR=12;BYMINUTE=35` | local, `gpt-5.3-codex-spark`, `xhigh` | `automation/morning_prompt.md` |
| `kmfa-3` | `KMFA｜每日钉钉考勤检查｜晚报` | Daily local wall-clock 20:00 | `RRULE:FREQ=WEEKLY;BYHOUR=20;BYMINUTE=0;BYDAY=SU,MO,TU,WE,TH,FR,SA` | local, `gpt-5.3-codex-spark`, `xhigh` | `automation/evening_prompt.md` |

Current local Codex cwd list for both automations:

```text
/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa
```

Run KMFA git, skill, tests, and scripts from `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/kmfa`.
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
