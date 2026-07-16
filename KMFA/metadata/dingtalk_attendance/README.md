# KMFA 钉钉考勤 skill

The KMFA 钉钉考勤 skill provides the public-safe structure for `每日早晚钉钉考勤检查`.

Current owner usability status is `AWAITING_NATURAL_GROUP_DELIVERY_EVIDENCE`. Morning and evening results remain temporary reminders. Scheduled delivery uses the frozen template and existing group target only after exact real-time integrity PASS, with zero sender calls on failure and a work-date/run-slot duplicate guard. Manual/latest-report resend remains disabled. A completed work date receives a separate official final reconciliation, and new monthly notification rollups use only canonical final archives.

Natural automations execute `$HOME/Library/Application Support/Codex/KMFA/attendance-production/current`. Local branch, HEAD, origin HEAD, and dirty paths are recorded as diagnostics only. They never block attendance and never change the active immutable release fingerprint.

The module is live-only and uses the local `dws` CLI as its current DingTalk attendance backend. It does not create sample employees, sample punches, or fixture attendance records. When DWS is unavailable, scripts return `DWS_UNAVAILABLE`.

The live DWS backend uses DingTalk attendance-group membership as the reporting scope. Morning/evening temporary reminders query every scoped member through current `dws attendance record get` and `dws attendance summary` data for the exact Beijing business date. Successful empty punch data remains complete coverage; a query failure, missed member, wrong date, or parse failure stops the reminder.

The final daily result remains separate: it requires an independently frozen official XLS/XLSX export and exact reconciliation of the 48 required fields. Final waiting or failure never changes a completed temporary reminder, and temporary data never substitutes for final evidence. DWS subprocesses explicitly receive `TZ=Asia/Shanghai` for business-date conversion; this does not add a timezone field to the Codex automation schedule.

The private R6 coordinator persists aggregate-only reminder integrity errors and coverage counts to `state.json` and the Chinese `运行状态.md`; it never writes employee detail into public GitHub state.

Official parity gates are fail closed:

- all required report columns must resolve by exact current name;
- every current attendance-group member must have exactly the target business-date report row;
- returned users and dates must match the request scope;
- every official status must be classifiable;
- any query, coverage, date, or status failure returns `OFFICIAL_ATTENDANCE_PARITY_FAILED` and sends no notification.
- morning/evening dispatch boundaries require their exact real-time reminder integrity fields; final retains independent official parity. Legacy manifests cannot be resent as current attendance truth.

Required official columns are `考勤结果`, `应出勤天数`, `出勤天数`, `休息天数`, `迟到次数`, `早退次数`, `上班缺卡次数`, `下班缺卡次数`, and `旷工天数`. Field IDs are dynamic and are never hard-coded. The DWS API permits up to 20 users per call; KMFA intentionally uses 5 per batch to reduce timeout risk.

Notification config is loaded from the ignored local file `private_runtime/.env.local`. The current enabled notification path is DingTalk group robot markdown: each message is signed locally, includes `开明考勤`, and writes only send status to the private dispatch receipt.

Private runtime data belongs outside Git:

- local operational cache: `KMFA/metadata/dingtalk_attendance/private_runtime/`
- long-term private archive: `/Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/`

The OneDrive month folder stores raw JSONL gzip, management report, HR report, dispatch receipt, manifest, and cleanup audit directly under `YYYYMM`. `--send-latest-report-only` can resend the newest private reports without another DWS collection run.

New monthly notification rollups read canonical `final` archives only. Legacy archives and canonical morning/evening temporary reminders are audit-only and never enter new monthly cumulative values. The private SQLite transition ledger retains its separate replay/audit role and is not the notification monthly source.

An existing v1 ledger is not considered valid after code upgrade. `--validate` reports `MIGRATION_REQUIRED`, and read-only month queries fail closed until `sync_attendance_ledger.py --all` has replayed every private raw manifest and marked every indexed run with schema v2 plus the shared parsed run sort key. This replay is required because an old SQLite row alone cannot distinguish an official-normal snapshot from a legacy-normal inference.

Git may store only code, schema, policy, prompts, path references, aggregate validation evidence, and no employee attendance plaintext.
