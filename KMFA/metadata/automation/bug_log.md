# KMFA Automation Bug Log

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
