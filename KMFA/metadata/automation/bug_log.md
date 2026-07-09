# KMFA Automation Bug Log

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
