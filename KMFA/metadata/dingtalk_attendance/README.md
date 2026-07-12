# KMFA 钉钉考勤 skill

The KMFA 钉钉考勤 skill provides the public-safe structure for `每日早晚钉钉考勤检查`.

Current owner usability status is `UNAVAILABLE`. Morning and evening results are temporary reminders. A completed work date receives a separate official final reconciliation, and new monthly notification rollups use only canonical final archives. Legacy and temporary-reminder archives remain audit-only. Attendance delivery is owner-disabled.

The module is live-only and uses the local `dws` CLI as its current DingTalk attendance backend. It does not create sample employees, sample punches, or fixture attendance records. When DWS is unavailable, scripts return `DWS_UNAVAILABLE`.

The live DWS backend uses DingTalk attendance-group membership as the reporting scope. It resolves the current official report column IDs with `dws attendance report columns`, then reads the target Beijing business date with `dws attendance report query-data` in batches of 5 users. The exact official `考勤结果` and official count columns are the only source for user-visible attendance totals and anomaly classification.

`dws attendance record get` and `dws attendance summary` remain private diagnostic evidence only. Their record count, two-punch heuristic, and monthly-summary labels must never override the official report result. The scheduled official collector intentionally skips this per-member legacy sweep after exact parity, preventing 42 users × 2 endpoints × retries from blocking production. Explicit legacy/replay diagnostics remain available outside the scheduled production path. DWS subprocesses explicitly receive `TZ=Asia/Shanghai` because those legacy endpoints convert dates through the process-local timezone; this does not add a timezone field to the Codex automation schedule.

After exact official parity succeeds, an isolated permission or call failure from either diagnostic endpoint is archived as a diagnostic failure only; it cannot block or alter the official attendance notification. The older legacy collector keeps its original PAT fail-fast behavior.

Official parity gates are fail closed:

- all required report columns must resolve by exact current name;
- every current attendance-group member must have exactly the target business-date report row;
- returned users and dates must match the request scope;
- every official status must be classifiable;
- any query, coverage, date, or status failure returns `OFFICIAL_ATTENDANCE_PARITY_FAILED` and sends no notification.
- live runs, resend commands, and every attendance dispatch boundary require the same exact official parity fields before target probing or sender invocation; legacy manifests cannot be resent as current attendance truth.

Required official columns are `考勤结果`, `应出勤天数`, `出勤天数`, `休息天数`, `迟到次数`, `早退次数`, `上班缺卡次数`, `下班缺卡次数`, and `旷工天数`. Field IDs are dynamic and are never hard-coded. The DWS API permits up to 20 users per call; KMFA intentionally uses 5 per batch to reduce timeout risk.

Notification config is loaded from the ignored local file `private_runtime/.env.local`. The current enabled notification path is DingTalk group robot markdown: each message is signed locally, includes `开明考勤`, and writes only send status to the private dispatch receipt.

Private runtime data belongs outside Git:

- local operational cache: `KMFA/metadata/dingtalk_attendance/private_runtime/`
- long-term private archive: `/Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/`

The OneDrive month folder stores raw JSONL gzip, management report, HR report, dispatch receipt, manifest, and cleanup audit directly under `YYYYMM`. `--send-latest-report-only` can resend the newest private reports without another DWS collection run.

New monthly notification rollups read canonical `final` archives only. Legacy archives and canonical morning/evening temporary reminders are audit-only and never enter new monthly cumulative values. The private SQLite transition ledger retains its separate replay/audit role and is not the notification monthly source.

An existing v1 ledger is not considered valid after code upgrade. `--validate` reports `MIGRATION_REQUIRED`, and read-only month queries fail closed until `sync_attendance_ledger.py --all` has replayed every private raw manifest and marked every indexed run with schema v2 plus the shared parsed run sort key. This replay is required because an old SQLite row alone cannot distinguish an official-normal snapshot from a legacy-normal inference.

Git may store only code, schema, policy, prompts, path references, aggregate validation evidence, and no employee attendance plaintext.
