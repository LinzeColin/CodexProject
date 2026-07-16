# KMFA 钉钉考勤 skill Configuration

## Public Config And Metadata

These files are safe to read and commit:

```text
KMFA/metadata/dingtalk_attendance/README.md
KMFA/metadata/dingtalk_attendance/attendance_database_manifest.json
KMFA/metadata/dingtalk_attendance/notification_targets_manifest.json
KMFA/metadata/dingtalk_attendance/notification_channel_manifest.json
KMFA/metadata/dingtalk_attendance/notification_policy.yaml
KMFA/metadata/dingtalk_attendance/onedrive_storage_manifest.yaml
KMFA/metadata/dingtalk_attendance/retention_policy.yaml
KMFA/metadata/dingtalk_attendance/codex_automation/morning_1035.prompt.md
KMFA/metadata/dingtalk_attendance/codex_automation/evening_2000.prompt.md
KMFA/metadata/dingtalk_attendance/codex_automation/manual_rerun.prompt.md
```

## Private Config

Private config belongs here and must not be committed:

```text
KMFA/metadata/dingtalk_attendance/private_runtime/
```

Use templates from this package:

```text
KMFA/kmfa-dingtalk-attendance-skill/templates/env.local.example
KMFA/kmfa-dingtalk-attendance-skill/templates/notification_targets.local.example.json
```

Copying these templates into private runtime is a machine-local setup action and should not be committed.

## Environment Keys

Known local-only keys:

```text
DINGTALK_ROBOT_URL
DINGTALK_ROBOT_SIGNING_KEY
DINGTALK_BOSS_USER_ID
DINGTALK_APP_KEY
DINGTALK_APP_CREDENTIAL
DINGTALK_CORP_ID
DINGTALK_AGENT_ID
DWS_BIN
KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS
KMFA_DINGTALK_ATTENDANCE_DWS_BROWSER_POLICY_PATH
KMFA_DINGTALK_ATTENDANCE_REMINDER_COLLECTION_DEADLINE_SECONDS
KMFA_ATTENDANCE_PRODUCTION_FINGERPRINT
KMFA_ATTENDANCE_PRODUCTION_SOURCE_COMMIT
KMFA_ATTENDANCE_PRODUCTION_RELEASE_ROOT
KMFA_ATTENDANCE_LOCAL_KMFA_ROOT
KMFA_WORK_DATE_OVERRIDE
KMFA_TODAY_OVERRIDE
```

Default live gate:

```text
KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS=0
```

Only set it to `1` for a user-authorized live run after healthcheck and process checks.

The full morning/evening reminder collection has one wall-clock deadline. Its default is 330 seconds: the slowest successful 2026-07-15 natural collection took 285 seconds, so the default preserves 45 seconds of headroom while stopping before the outer automation ceiling. An authorized machine-local override may use `KMFA_DINGTALK_ATTENDANCE_REMINDER_COLLECTION_DEADLINE_SECONDS`; it must be positive. Deadline expiry is terminal for that work date and slot, kills the active DWS process group, records `ABORTED_TIMEOUT / NOT_SENT`, and forbids recovery or late sending.

Production release location:

```text
$HOME/Library/Application Support/Codex/KMFA/attendance-production/current
```

The three `KMFA_ATTENDANCE_PRODUCTION_*` keys and `KMFA_ATTENDANCE_LOCAL_KMFA_ROOT` are set only by the verified production entry after manifest, fingerprint, and live-prompt readback succeed. The local-root key keeps secrets, state, and SQLite in the owner checkout rather than copying them into the immutable release. They are not user configuration and must not bypass release verification. Repository branch, HEAD, origin HEAD, and dirty paths are recorded privately as diagnostics only.

## Notification Targets

Public manifest currently records only labels, target types, resolved channel names, probe status, timestamps, and `sensitive_values_committed=false`.

Private target config may include:

- personal target with `preferred_channel: dws_open_dingtalk_id_chat`
- group target with `preferred_channel: dingtalk_group_robot_env`
- environment-key references such as `webhook_env_key` and `secret_env_key`

Never copy actual webhook URLs, signing keys, `open_dingtalk_id`, or group conversation IDs into Git.

## DWS Setup

DWS is a local CLI dependency. The automation assumes the user has already authenticated and that DWS can reach the correct DingTalk organization.

Live collection commands fail closed unless:

- `KMFA_DINGTALK_ATTENDANCE_ALLOW_DWS_COMMANDS=1`
- browser policy is ready
- `default.openBrowser=false`

The policy check reads `KMFA_DINGTALK_ATTENDANCE_DWS_BROWSER_POLICY_PATH` or defaults to:

```text
~/.dws/pat_policy.json
```

## Database And Payroll Boundary

The private SQLite ledger is a rebuildable index:

```text
KMFA/metadata/dingtalk_attendance/private_runtime/attendance_ledger.sqlite
```

It is not committed, not a payroll basis, and not a wage calculation source.
Explicit boundary: `salary_basis_allowed=false`.

Future payroll or salary integration must use a separate reviewed contract, explicit owner approval, and public-safe exported facts. Do not connect salary workflows directly to raw DWS output, dispatch receipts, or private SQLite without a new approved scope.
