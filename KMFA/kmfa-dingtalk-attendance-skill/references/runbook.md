# KMFA 钉钉考勤 skill Runbook

## 1. Repo Entry

Canonical GitHub destination:

- Repository: `LinzeColin/CodexProject`
- Local root on this machine: `/Users/linzezhang/CodexProject`
- Project root in repo: `KMFA/`
- Attendance module: `KMFA/tools/dingtalk_attendance/`
- Public metadata: `KMFA/metadata/dingtalk_attendance/`

Development publication policy:

- Work on `main`.
- Do not create PRs, issues, branches, or worktrees unless the user explicitly asks.
- Build approved changes from the latest GitHub `main` snapshot in isolated staging; do not mutate the owner's checkout to make it match.
- Natural production runs never require local `HEAD == origin/main`, a clean attendance scope, or a clean repository. Branch, HEAD, origin HEAD, and dirty paths are diagnostics only.

## 2. First Files To Read

Read only the minimum current context first:

```text
KMFA/HANDOFF.md
KMFA/metadata/dingtalk_attendance/README.md
KMFA/metadata/dingtalk_attendance/attendance_database_manifest.json
KMFA/metadata/dingtalk_attendance/notification_targets_manifest.json
KMFA/tools/dingtalk_attendance/notification_template.py
KMFA/tools/dingtalk_attendance/run_attendance.py
KMFA/tools/dingtalk_attendance/dws_auth_guard.py
KMFA/tests/test_dingtalk_attendance.py
```

## 3. Safety Boundaries

Never commit:

- `.env.local`
- Webhook URLs or signing keys
- app secrets, token values, passwords, DWS credential material
- DWS `open_dingtalk_id`, group conversation IDs, or resolved private channel values
- SQLite, raw JSON, raw JSONL, raw JSONL.gz
- employee attendance plaintext
- management or HR report bodies
- OneDrive private raw archives

Allowed in Git:

- Code
- Tests
- Public-safe manifests
- Public-safe prompts
- Paths and aggregate validation evidence
- Config templates with placeholders only

## 4. Current Business Rules

Source of truth is the current code and tests, but the expected rules are:

- `REST_REQUIRED_THRESHOLD_DAYS = 23`.
- `REST_REQUIRED_EXCLUDED_NAMES = {"丁春法", "李永占"}`.
- 丁春法 and 李永占 are excluded only from the `需要休息` section and private `rest_required_snapshots`; attendance anomalies, pending actions, summaries, and other status counts still include them normally when applicable.
- 张霖泽 and 林全意 are known no-record people; they are not hidden globally and only their own no-record condition is exempted.
- `NOTIFICATION_HIDDEN_NAMES` should remain empty unless the user explicitly authorizes a display-only hiding rule.
- All status rollups are natural-month rollups.
- Effective attendance day means both morning and evening punches exist on the same natural day.
- Morning/evening `今日异常 / 无考勤` is a temporary snapshot driven by current per-member `record get + summary` reads for every attendance-group member. A successful empty punch result is valid coverage; failed/missed/wrong-date/unparseable reads fail closed.
- Current-month cumulative counts are annotations for people already shown because they hit today's status. They must never create a today no-record/anomaly row by themselves.
- Empty notification sections render nothing: no title and no `无`.
- If collection is complete and there is no same-day anomaly, the notification says `本次 N 人全部考勤正常`.
- The user-visible `待审批 / 待补卡 / 待核查` section is removed; pending/internal diagnostics stay in manifest, receipt, or machine state only.
- Notification display rule: 10 or fewer people shows all names; over 10 shows total plus Top 10.
- Top 10 ordering: monthly count or days descending, latest date descending, then stable name sort.
- DWS collection logic must not be changed when only notification wording or ledger indexing is requested.
- Morning/evening use the scoped per-member current-data collector. Final alone uses the independent official XLS/XLSX and 48-required-field strict reconciliation; final waiting or failure cannot block a current reminder.
- Morning and evening outputs are temporary reminders. The later official final reconciliation is the only daily result eligible for new monthly notification rollups.
- Legacy, morning, and evening archives remain audit-only for monthly notification values.
- Scheduled morning/evening group delivery is owner-enabled only after exact real-time integrity PASS and is protected by work-date/run-slot deduplication. Manual/latest-report resend remains owner-disabled.
- Scheduled runs execute only `$HOME/Library/Application Support/Codex/KMFA/attendance-production/current`. The production entry verifies the immutable manifest/fingerprint and live prompt before DWS begins.
- A new attendance runtime is built as a candidate, fully validated, and atomically activated. Candidate failure leaves the previous `current` release unchanged.

## 5. Safe Offline Commands

Run from repo root unless noted.

```bash
python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only
python3 KMFA/tools/dingtalk_attendance/sync_attendance_ledger.py --validate
python3 KMFA/tools/dingtalk_attendance/query_attendance_ledger.py --month 202607 --summary
python3 KMFA/tools/dingtalk_attendance/validate_no_sensitive_git.py
python3 KMFA/tools/dingtalk_attendance/check_dingtalk_attendance.py
python -m py_compile KMFA/tools/dingtalk_attendance/*.py
python3 -m unittest KMFA.tests.test_dingtalk_attendance -q
python3 KMFA/kmfa-dingtalk-attendance-skill/tools/validate_skill_package.py
git diff --check
git status --porcelain
```

`sync_attendance_ledger.py --all` reads OneDrive private archives and writes a private SQLite index under ignored `private_runtime/`. It is local/private, not Git output, `salary_basis_allowed=false`, and not payroll basis.

## 6. Live Commands Need Current Authorization

Do not run these unless the user explicitly authorizes live DingTalk/DWS work in the current thread:

```bash
python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type morning --timezone Asia/Shanghai
python3 KMFA/tools/dingtalk_attendance/run_attendance.py --run-type evening --timezone Asia/Shanghai
python3 KMFA/tools/dingtalk_attendance/send_latest_report.py --channel auto --targets all
python3 KMFA/tools/dingtalk_attendance/notification_probe.py --all-targets
dws ...
```

Before a live run, perform the read-only guard:

```bash
pgrep -af 'run_attendance|dingtalk_attendance|(^|/)dws( |$)|open-dev\.dingtalk|personalAuthorization'
python3 KMFA/tools/dingtalk_attendance/healthcheck.py --config-only
```

Live DWS collection also requires:

- `KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS=1`
- DWS browser policy file present
- policy `default.openBrowser=false`
- no stale DWS or attendance process still running

Do not close Chrome automatically. If an authorization tab appears, ask the user to handle it or explicitly authorize a narrow cleanup action.

## 7. Output And Archive Shape

Private long-term archive:

```text
/Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/
```

The month folder directly stores original run files. Do not add deeper date folders by default.

Private runtime:

```text
KMFA/metadata/dingtalk_attendance/private_runtime/
```

Expected private runtime files are local-only and ignored:

- `.env.local`
- `notification_targets.local.json`
- `notification_targets_resolved.json`
- `notification_channel_resolved.json` for legacy compatibility
- `notification_probe_diagnostic.json`
- `attendance_ledger.sqlite`

## 8. Development Rule

For behavior changes, add or update tests first. Watch the targeted test fail, implement the minimal change, then rerun focused tests and the public-safe validators.

For documentation-only changes, run at least:

```bash
python3 KMFA/kmfa-dingtalk-attendance-skill/tools/validate_skill_package.py
python3 KMFA/tools/dingtalk_attendance/validate_no_sensitive_git.py
git diff --check
```

## 9. Completion Standard

Do not claim completion without:

- exact files changed
- validation commands and outcomes
- git commit hash
- push result
- post-push GitHub `main` contains the intended commit; local checkout parity is diagnostic only

## 10. Reminder Collection Timeout

- The total realtime reminder collection deadline is 330 seconds by default, based on the 285-second slowest successful 2026-07-15 natural collection plus 45 seconds of headroom.
- Each DWS command starts in a dedicated process group. A per-command timeout, total collection timeout, interrupt, or cancellation terminates the entire group.
- Total timeout must persist `failed_operation=reminder_collection`, `error_code=REMINDER_COLLECTION_TIMEOUT`, elapsed seconds, `notification_status=NOT_SENT`, and zero message/target/sender calls.
- `ABORTED_TIMEOUT` is terminal for that date and slot: do not probe artifacts, recover, resend, or send late.
- `--collection-probe-only` is the authorized read-only validation entry. It runs the same bounded live collection and integrity gate but writes no archive and invokes no notification target.
