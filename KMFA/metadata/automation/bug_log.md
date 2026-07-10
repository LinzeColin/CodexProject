# KMFA Automation Bug Log

## 2026-07-11 `dws-auth-keepalive-2` False Keepalive And Login Fallback

Scope: only the DWS authentication keepalive automation. The original contract
required automatic renewal of refreshable access tokens.

Root causes:

- The live prompt mislabeled `dws auth login --yes --no-browser` as a
  non-interactive refresh. `--no-browser` only suppresses browser launch; login
  still starts a complete OAuth authorization and waits for user interaction.
- The actual refresh trigger is `dws auth status --format json`.
- DWS status can exit 0 with `authenticated=true` and
  `refresh_token_valid=true` after an access-token refresh failure while
  omitting `token_valid` and `refreshed`. Trusting exit 0 created false-green
  keepalive runs.
- The prompt wrote dedupe state to the retired `dws-auth-keepalive` memory while
  the active automation ID is `dws-auth-keepalive-2`, splitting the ledger.
- The old doctor command used `--format json`; doctor requires `--json`.

Repair:

- Added `KMFA/tools/automation/dws_auth_keepalive.py` and regression tests.
- The wrapper invokes only profile-pinned `auth status`; success requires a
  consistent success/authenticated/token/refresh/profile state, future parseable
  access and refresh expiries, and doctor with zero fails. It returns nonzero
  for every missing, contradictory, stale, malformed, or unavailable gate.
- DWS's inner HTTP timeout is 20 seconds and the parent process timeout is 25
  seconds, preventing the wrapper from killing the CLI before its own timeout.
- No failure path executes `auth login`; manual device authorization is only a
  reported next action.
- Added a Git-tracked prompt/contract and updated the live automation without
  changing its pure RRULE or adding a timezone.
- Pinned the expected organization in a machine-private 0600 config; status and
  doctor no longer depend on mutable `currentProfile`.
- Moved ledger and 24-hour/final-4-hour reminder dedupe into the deterministic
  wrapper. Active files are 0600 in a 0700 directory and contain no corp/user
  identity; the legacy identity-bearing ledger is retained private at 0600.
- Upgraded the official DWS CLI to v1.0.51 for current credential diagnostics;
  the upgrade itself is not treated as refresh proof.

Open acceptance gate:

- The current token pair cannot obtain a new access token even though the local
  refresh expiry metadata is still in the future. A one-time owner-authorized
  `dws auth login --device` is required. Long-term closure additionally requires
  a later natural scheduled run after access-token expiry to report
  `refreshed=true` and `token_valid=true` with a newer expiry.

## 2026-07-10 `kmfa-3` Owner-Fixed 20:00 Stability Repair

Scope: only the evening attendance automation `kmfa-3`. The owner fixed its
permanent trigger to the host's local wall-clock 20:00. This time must not be
converted from Beijing time, UTC offset, or daylight-saving state.

Root causes:

- The live automation had already been edited to 20:00, but the Git contract,
  prompt mirrors, S19 schedule constant, validator, and docs still encoded
  22:05 / 20:05. The central checker therefore reported `kmfa-3: rrule` drift.
- `run_attendance.py` printed failure payloads but always returned exit code 0,
  allowing DWS, partial collection, or notification failures to look green to
  the scheduler.
- The local scheduler literal was also reused as an `Asia/Shanghai` DWS summary
  cutoff. With Sydney 20:00 occurring at Beijing 18:00/17:00, that could query
  two or three hours into the future.
- The evening prompt did not lock the exact S19 command and could treat the
  advisory App Key-oriented runtime inspection as more authoritative than the
  current DWS PAT config-only healthcheck.

Permanent contract:

```text
RRULE:FREQ=WEEKLY;BYHOUR=20;BYMINUTE=0;BYDAY=SU,MO,TU,WE,TH,FR,SA
```

The live record contains no `DTSTART`, `TZID`, or explicit scheduler timezone.
The runner continues to use `Asia/Shanghai` only for business-date semantics;
that internal argument must never shift the scheduler's 20:00 wall-clock time.
Live summary queries now use the actual run datetime in the business-date
clock, while controlled historical reruns keep their explicit replay datetime.
The contract records `fixed_local_wall_clock=true` and
`offset_conversion_allowed=false` for `kmfa-3`.
The central live checker also locks the normalized evening prompt SHA-256 and
canonical project id, so a future stale prompt or wrong-project rebound fails
the same health gate even when the RRULE itself still looks correct.
CLI success is a positive whitelist: collection/send-only status and
`notification_status` must agree on `SENT`; contradictory payloads fail.

Runtime evidence already observed from the automation-created task on this
date: canonical cwd, real S19 DWS entry, 44/44 record calls, 44/44 summary
calls, zero command failures, private OneDrive artifacts, and both configured
notification targets `SENT`. This proves the execution and delivery chain, but
the 21:18 AEST start was a save-trigger/missed-trigger run rather than a natural
20:00 timing proof.

Remaining acceptance gate: observe the next natural `kmfa-3` trigger at 20:00
local wall clock and verify one task, canonical cwd, completed collection,
private archive, and successful configured-target delivery. Do not claim the
natural timing gate before that evidence exists.

## 2026-07-10 Pure-RRULE Scheduler Repair (Historical Pre-20:00 State)

Scope: remove scheduler timezone metadata from all five active KMFA-related
Codex Desktop automations and add a regression gate that reads the live app
records instead of validating only business-time constants.

Root cause and evidence:

- The live attendance and routine records used `DTSTART;TZID=Asia/Shanghai`
  while the Codex scheduler executed historical runs by the Mac's Sydney local
  wall clock. Prompt text saying `Asia/Shanghai` did not change scheduler time.
- Existing S19 and S20 tests validated business times and prompt/package files,
  but did not read `~/.codex/automations/*/automation.toml`; invalid live RRULEs
  therefore passed every repo validator.
- The S19 business runtime is currently healthy: config-only healthcheck is
  `READY`, DWS command safety is `READY`, and both the personal and group
  notification targets are available. The last successful manual personal run
  proves the runner, but not the natural scheduler.

Repair:

| ID | Pure scheduler rule | Business interpretation |
|---|---|---|
| `kmfa` | `RRULE:FREQ=DAILY;BYHOUR=12;BYMINUTE=35` | 10:35 Asia/Shanghai at current AEST offset |
| `kmfa-3` | `RRULE:FREQ=DAILY;BYHOUR=22;BYMINUTE=5` | 20:05 Asia/Shanghai at current AEST offset |
| `kmfa-4` | `RRULE:FREQ=DAILY;BYHOUR=13,19;BYMINUTE=5,35;BYSETPOS=2,3` | 11:35 and 17:05 Asia/Shanghai at current AEST offset |
| `kmfa-5` | `RRULE:FREQ=WEEKLY;BYDAY=MO,SA;BYHOUR=11;BYMINUTE=0` | Monday/Saturday 11:00 Sydney local |
| `kmfa-dws` | `RRULE:FREQ=DAILY;BYHOUR=11,19;BYMINUTE=0` | Daily 11:00 and 19:00 Sydney local |

All five records were saved through the official Codex automation update API.
No live TOML was edited directly. `kmfa-4` remains one automation: `BYSETPOS`
selects 13:35 and 19:05 without creating the unwanted 13:05/19:35 product.

Regression protection:

```text
KMFA/metadata/automation/codex_app_schedules.contract.toml
KMFA/tools/automation/check_kmfa_automation_schedules.py
KMFA/tests/test_automation_schedule_contract.py
```

The checker rejects `DTSTART`, `TZID`, explicit scheduler timezone fields,
multiline/multiple RRULEs, schedule drift, cwd drift, inactive state, model
drift, and reasoning-setting drift across the five live records.

Validation observed after the official update:

```text
CODEX_AUTOMATIONS_READY (5 automations, 0 mismatches)
3 scheduler regression tests OK
66 S19 attendance tests OK
19 S20 routine tests OK
attendance skill validator PASS
routine skill validator PASS
fund live automation checker CODEX_AUTOMATION_READY
```

The original 22:05 acceptance gate was superseded by the owner's permanent
local 20:00 correction documented above.

Known unrelated runtime issue: S20 routine-check config-only health reports its
OneDrive `DWS_Outputs.zip` as a dataless placeholder. That source blocker is not
caused by the scheduler repair and was not widened into this change.

Historical note: offset conversion applied to this earlier repair. It no longer
applies to `kmfa-3`, whose owner-fixed 20:00 scheduler time must never move.

## 2026-07-10 Diagnosis and Repair

Scope: diagnose why KMFA automations were visible but not reliable, and repair
the live Codex App automation records plus the tracked repo contracts.

Root causes:

| Issue | Impact | Fix | Validation |
|---|---|---|---|
| Two local projects were both named `CodexProject`. The KMFA automations were bound to project id `25bfcad9-f99d-40f9-9094-64a7045f80b0`, whose cwd is the old `/Users/linzezhang/Documents/Codex/2026-07-05/.../CodexProject` worktree. | Fixes made in canonical `/Users/linzezhang/CodexProject` were not used by scheduled runs, so the same bugs appeared to return. | Rebound `kmfa`, `kmfa-3`, `kmfa-4`, and `kmfa-5` to project id `40dd52a0-b6eb-4528-9577-0cb5f4f86e3e`, cwd `/Users/linzezhang/CodexProject`. | Live toml now shows all four KMFA/CodexProject automations with `cwds = ["/Users/linzezhang/CodexProject"]`. |
| Fund weekly automation checker did not treat old cwd drift as a failure, and runtime readiness compared `FREQ=...` while the tracked/live toml used `RRULE:FREQ=...`. | Quality gates could say ready in one place and blocked in another, or fail to catch the wrong workspace. | Added canonical cwd to `codex_app_automation.contract.toml` and `check_codex_app_automation.py`; aligned runtime/delivery expected RRULE strings. | `python3 KMFA/fund-weekly-analysis-skill/tools/check_codex_app_automation.py` returns `CODEX_AUTOMATION_READY` with cwd `/Users/linzezhang/CodexProject`. |
| Tracked prompt mirrors still referenced the old July 5 worktree or stale automation ids. | Future agents could recreate the same bad live configuration from stale repo docs. | Updated fund prompt, attendance SKILL/manifest/validator, and daily routine manifest to current ids and canonical cwd. | Attendance skill package, daily routine skill package, and fund taskpack validators pass. |
| Upstream DWS archive was separate but KMFA prompts previously described mixed cwd usage. | KMFA tasks could drift back into the DWS archive workspace and duplicate resource-heavy archive work. | KMFA prompts now state that KMFA automations run only from `/Users/linzezhang/CodexProject`; DWS archive remains separate producer automation. | Live `kmfa-dws` remains bound only to the DWS project cwd; KMFA tasks do not include that cwd. |

Current active KMFA automation set after repair:

| ID | Name | Project id | Cwd | Expected state |
|---|---|---|---|---|
| `kmfa` | `KMFA｜每日钉钉考勤检查｜晨报` | `40dd52a0-b6eb-4528-9577-0cb5f4f86e3e` | `/Users/linzezhang/CodexProject` | Active |
| `kmfa-3` | `KMFA｜每日钉钉考勤检查｜晚报` | `40dd52a0-b6eb-4528-9577-0cb5f4f86e3e` | `/Users/linzezhang/CodexProject` | Active |
| `kmfa-4` | `KMFA｜钉钉工作检查` | `40dd52a0-b6eb-4528-9577-0cb5f4f86e3e` | `/Users/linzezhang/CodexProject` | Active |
| `kmfa-5` | `KMFA｜资金周报自动化` | `40dd52a0-b6eb-4528-9577-0cb5f4f86e3e` | `/Users/linzezhang/CodexProject` | Active |
| `kmfa-dws` | `KMFA｜上游每日钉钉DWS归档` | `cbf3c45e-f4ad-47d7-b397-faf7e3dea35e` | `/Users/linzezhang/Documents/Codex/2026-07-04/392b1a986ba680338068ddc1c2a0fd0e-https-app-notion-com-p` | Active |

Validation commands run:

```text
python3 KMFA/fund-weekly-analysis-skill/tools/check_codex_app_automation.py
python3 KMFA/kmfa-dingtalk-attendance-skill/tools/validate_skill_package.py
python3 KMFA/daily_routine_check_skill/tools/validate_skill_package.py
python3 KMFA/fund-weekly-analysis-skill/tools/validate_taskpack.py
python3 -m unittest KMFA.tests.test_dingtalk_attendance -q
python3 -m unittest KMFA.tests.test_daily_routine_check -q
python3 KMFA/fund-weekly-analysis-skill/tools/check_source_readiness.py --repo-root /Users/linzezhang/CodexProject --timezone Australia/Sydney
dws doctor --format json
/usr/bin/python3 scripts/archive_dingtalk_all_files.py --plan-only --run-source codex_automation --automation-name 每日钉钉DWS归档
python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only
```

Observed validation result:

- Attendance tests: 66 tests passed.
- Daily routine tests: 19 tests passed.
- Fund source readiness: `READY`, file_count `292`, unreadable_count `0`.
- DWS doctor: 3 pass, 1 version warning, 0 fail.
- DWS archive plan-only: success, 9 groups planned.
- Attendance healthcheck: `READY`, DWS command safety ready, multi-target notification ready with 张霖泽 personal target available.

## 2026-07-09 Recovery

Scope: restore and verify the five KMFA-related Codex Desktop automations without
sending production group messages. Live attendance validation used the personal
DWS chat target for Zhang Linze only.

Current active KMFA automation set:

| ID | Name | Workspace | Expected state |
|---|---|---|---|
| `kmfa-dws` | `KMFA｜上游每日钉钉DWS归档` | DWS archive project | Active |
| `kmfa` | `KMFA｜每日钉钉考勤检查｜晨报` | CodexProject | Active |
| `kmfa-3` | `KMFA｜每日钉钉考勤检查｜晚报` | CodexProject | Active |
| `kmfa-4` | `KMFA｜钉钉工作检查` | CodexProject | Active |
| `kmfa-5` | `KMFA｜资金周报自动化` | CodexProject | Active |

Root causes and fixes:

| Issue | Impact | Fix | Validation |
|---|---|---|---|
| Raw edits and backup copies under `~/.codex/automations` caused Codex Desktop registry/card drift and orphaned old IDs. | KMFA cards disappeared or appeared under wrong workspaces. | Recovered the active cards with the official Codex automation update path; active KMFA cards are now bound only to CodexProject, while upstream DWS archive stays in the DWS project. | Current registry check shows `kmfa-dws`, `kmfa`, `kmfa-3`, `kmfa-4`, and `kmfa-5` active. |
| S19 personal notification target had public manifest metadata but missing private resolved runtime target. | Personal-only tests could not prove delivery without risking group sends. | Resolved the private Zhang Linze DWS personal target in ignored private runtime; production group robot config remains unused for the test. | Morning and evening personal-only reruns dispatched exactly one personal DWS chat target and no group target. |
| DWS `attendance record get` may return `AGENT_CODE_NOT_EXISTS` for one member while the summary endpoint succeeds. | A valid run was incorrectly marked `PARTIAL`. | Added summary-backed `record_detail_unavailable` classification; this does not count as a command failure. | `python3 -m unittest KMFA.tests.test_dingtalk_attendance -q` includes the regression. |
| DWS `attendance summary` may return `AGENT_CODE_NOT_EXISTS` while the daily record endpoint has complete on/off-duty evidence. | Evening run could remain `PARTIAL` even with usable daily record evidence. | Added record-backed `summary_detail_unavailable` classification; it only applies when record evidence is successful and complete. | Evening personal-only rerun completed with `command_failure_count=0`. |
| DWS department discovery may return a transient empty failure without a useful error code. | One temporary DWS response could abort the whole automation with an undiagnosable blank error. | Empty DWS failures are now retried, and final failures include a readable failure label. | Unit regression covers an empty first failure followed by success. |
| Sensitive scanner flagged public schema flags whose names contained a credential suffix. | Valid public manifests could fail safety validation. | Refined assignment-style credential detection to avoid underscore-prefixed schema fields while still catching bare credential assignments. | Sensitive scan passes for tracked KMFA files. |
| Fund automation source folder was missing after cleanup. | `kmfa-5` source readiness returned `SOURCE_MISSING`. | Materialized the fund source from the OneDrive DWS zip into the expected local hot folder. | Source readiness now returns `READY` with 298 files. |
| DWS archive automation tried to commit the raw `DWS_Outputs.zip` to GitHub. | The raw package is too large for normal GitHub commits and should not cross the public metadata boundary. | Changed the DWS backup contract and `kmfa-dws` prompt to commit manifest/hash/run summary only; raw zip remains in OneDrive. | `KMFA/metadata/dws_outputs_backup/latest/manifest.json` and `runs/20260709T215022.json` record size, SHA-256, file count, run summary, and validation status. |

Verification evidence:

| Area | Result |
|---|---|
| S19 morning personal-only live rerun | `COMPLETED`; DWS live; one personal DWS chat target; no group target; `command_failure_count=0`. |
| S19 evening personal-only live rerun | `COMPLETED`; DWS live; one personal DWS chat target; no group target; `command_failure_count=0`. |
| S20 daily routine dry-run | Morning and evening windows evaluated expected rules from the DWS zip input without sending notifications. |
| S21 fund automation readiness | Codex automation readiness passed; source readiness passed after materialization; wrapper smoke indexed 298 files with OCR disabled for low-resource validation. |
| Upstream DWS archive | Controlled run succeeded; output validation passed; OneDrive mirror file count 996; cold storage validation passed. |
| DWS auth keepalive | `dws doctor` reported login/network/cache pass and only a version-update warning. |

Validation commands run:

```text
python3 -m unittest KMFA.tests.test_dingtalk_attendance -q
python3 KMFA/tools/dingtalk_attendance/validate_no_sensitive_git.py
python3 KMFA/kmfa-dingtalk-attendance-skill/tools/validate_skill_package.py
python3 KMFA/daily_routine_check_skill/tools/validate_skill_package.py
python3 -m unittest KMFA.tests.test_daily_routine_check -q
python3 KMFA/fund-weekly-analysis-skill/tools/check_codex_app_automation.py
python3 KMFA/fund-weekly-analysis-skill/tools/validate_taskpack.py
python3 KMFA/fund-weekly-analysis-skill/tools/check_source_readiness.py
python3 scripts/validate_dws_output_structure.py --config config/target_groups.yaml --mirror /Users/linzezhang/onedrive/DWS_Outputs.zip --expect-downloads-deleted --summary-json reports/daily_summary.json --cold-root /Users/linzezhang/onedrive/DWS_Archive
```

Safety notes:

- No production DingTalk group notification was sent during the personal-only
  attendance tests.
- No private resolved DWS IDs, raw JSON/JSONL/GZ, SQLite ledgers, report
  bodies, robot URLs, signing keys, tokens, or cookies are committed by this log.
- GitHub backup for DWS output is metadata-only; raw archive files remain in
  OneDrive/private runtime.

## 2026-07-10 Registry Hot-Directory Cleanup

Scope: fix recurring Codex Desktop Scheduled visibility drift after the active
KMFA automations were already restored.

Observed state:

| Check | Result |
|---|---|
| Official Codex automation view | `kmfa-dws`, `kmfa`, `kmfa-3`, `kmfa-4`, and `kmfa-5` rendered successfully. |
| Active top-level KMFA IDs | Only the five expected KMFA automation IDs were active. |
| Old top-level active IDs | None of `dws`, `automation-5`, `automation-6`, `automation-7`, `kmfa-2`, or old keepalive IDs remained. |
| Residual registry clutter | Eight backup/orphan directories still lived directly under the hot `~/.codex/automations` namespace. |

Root cause:

- The repeated bug was not only stale active automation TOML. Backup and orphan
  directories were left inside the same hot registry namespace that Codex
  Desktop scans for scheduled cards. Even when active IDs were correct, this
  kept the registry surface noisy and made UI/cache drift easier to reproduce.

Fix:

- Moved the eight `_backup_*` and `_orphan_*` directories out of
  `~/.codex/automations` into:
  `/Users/linzezhang/.codex/automation_backups/registry_cleanup_20260710T105856`
- Active automation directories were not modified or deleted.
- Future fixes must not store backup copies directly inside
  `~/.codex/automations`; use `~/.codex/automation_backups/` or a repo-private
  evidence path instead.

## 2026-07-10 Fund Automation Entrypoint Recovery

Scope: fix `kmfa-5` so the scheduled entrypoint can recover from a missing
fund hot folder without bypassing the source-readiness gate.

Observed state:

| Check | Result |
|---|---|
| `kmfa-5` automation contract | Active, weekly Monday/Saturday 11:00 local Sydney time, CodexProject workspace. |
| Configured source folder | `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群` was missing before the entrypoint smoke. |
| Source zip candidates | `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip` and `/Users/linzezhang/onedrive/DWS_Outputs.zip` were readable. |
| First source readiness | `SOURCE_MISSING`; runner was not started. |

Root cause:

- The fund weekly skill already had a safe `materialize_fund_source.py` tool,
  and `check_source_readiness.py` could point at the DWS zip candidate, but the
  scheduled shell entrypoint did not perform the explicit materialization step.
  Any cleanup or OneDrive hot-folder loss could therefore make `kmfa-5`
  repeatedly unavailable even though the latest DWS zip was healthy.
- The runner and delivery-acceptance helpers still compared the schedule against
  the pre-normalized RRULE string without the `RRULE:` prefix. The live Codex
  automation and tracked contract had already moved to
  `RRULE:FREQ=WEEKLY;BYDAY=MO,SA;BYHOUR=11;BYMINUTE=0`, so generated run
  packages could incorrectly mark the automation schedule gate as mismatch even
  when the card was correct.

Fix:

- `tools/run_daily_local.sh` now handles only readiness exit `2`
  (`SOURCE_MISSING`) by explicitly materializing `付款请示群` from the configured
  DWS zip candidate, then rerunning `check_source_readiness.py`.
- The runner still starts only after the second readiness check returns
  `READY`; other readiness failures remain fail-closed and do not trigger
  materialization.
- `tools/run_fund_weekly_analysis.py` and `tools/check_delivery_acceptance.py`
  now use the same RRULE string as the tracked `kmfa-5` contract.
- Added a regression test covering this exact call order:
  readiness `SOURCE_MISSING` -> materialize zip -> readiness `READY` -> runner.

Validation:

| Evidence | Result |
|---|---|
| Focused regression tests | `Ran 3 tests ... OK`. |
| Full fund weekly tests | `Ran 71 tests ... OK`. |
| Real scheduled-entrypoint smoke | First smoke: readiness `SOURCE_MISSING`; materialized 292 `付款请示群` files from `DWS_Outputs.zip`; second readiness `READY`; runner reached `INDEXED_PENDING_EXTRACTION`. Post-fix smoke: readiness directly `READY`; runner reached `INDEXED_PENDING_EXTRACTION`. OCR engine intentionally set to `none`; Codex handoff intentionally skipped. |
| Hot source folder after smoke | 292 files present under the configured fund input folder. |
| Fund taskpack / automation / source checks | Taskpack static validation `PASS`; `check_codex_app_automation.py` returned `CODEX_AUTOMATION_READY`; source readiness returned `READY` with 292 files and 0 unreadable files. |

Safety notes:

- This is not silent fallback. The entrypoint logs the materialization action and
  still requires a fresh readiness pass before extraction.
- The materialization is group-scoped to `付款请示群`; other DWS groups are not
  copied into the fund input folder.
- No source files are overwritten by the materializer; conflicts remain
  fail-closed under the existing materialization contract.

## 2026-07-11 S20 Routine Check ZIP-only And Cache I/O Root Cause

Scope: `kmfa-4` / `Dingtalk-routine-check` only. This entry does not change the
separate S21 fund-folder materialization contract.

Observed state:

| Check | Result |
|---|---|
| Canonical S20 input | `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip` existed and was the actual latest run input. |
| ZIP disk state | Logical size `568878497` bytes; allocated `555548 KiB` (about 543 MiB); locally materialized, not dataless. |
| Alias duplication | `/Users/linzezhang/onedrive/DWS_Outputs.zip` had the same inode as the canonical path; it was not a second copy. |
| Direct folder state | `DWS_Outputs/` was absent under canonical OneDrive, the alias path, and Downloads; absence is normal for S20. |
| Extraction/cache scan | No DWS extraction copy was found. Routine private runtime was about 208 KiB; the old `/private/tmp/daily_routine_check_pkg` source package was about 156 KiB with no CSV/JSONL/SQLite/ZIP payloads. |
| Required ZIP payload | Four target CSV members totaled `267878` bytes uncompressed and `65374` bytes compressed inside a roughly 1006-entry archive. |

Root cause:

- Commit history had converted the workflow to ZIP-first but retained the old
  folder fallback across rules, healthcheck, reader, CLI output wording, docs,
  and the live prompt. This was an incomplete contract migration.
- Healthcheck still probed direct group paths, and the reader could switch to
  the folder branch. The prompt therefore continued teaching future agents that
  a folder might be expected even though the owner can only provide a ZIP.
- `inspect_group_sources()` read a group CSV and the main loop read the same CSV
  again. The scheduled command also requested SQLite VACUUM every run through
  cleanup flags. Neither behavior caused a DWS extraction folder, but both added
  avoidable I/O around an already large hydrated ZIP.

Repair state:

- ZIP-only reader/healthcheck/CLI and the single-read source snapshot are
  implemented. Manual cleanup now exits before ZIP/business loading. The owning
  run passed 25 routine tests, the skill validator,
  8 automation contract tests, a real-ZIP healthcheck, and both window dry-runs.
- Cleanup execution now requires the explicit maintenance gate
  `--cleanup --apply`; scheduled commands no longer carry those flags. Official
  live prompt/hash readback passed and all 5 KMFA automation contracts reported
  no drift. The next natural-trigger run remains the only runtime acceptance
  gate; no natural-run success is claimed by this entry.
- Auto-eviction of the ZIP is prohibited because it would force the next run to
  download the full archive again. A target-only small ZIP or reliable remote
  range reader would be a separate upstream design decision requiring owner
  authorization.
