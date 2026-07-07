# KMFA S19 DingTalk Attendance Configuration

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
KMFA/metadata/dingtalk_attendance/codex_automation/morning_0835.prompt.md
KMFA/metadata/dingtalk_attendance/codex_automation/evening_1815.prompt.md
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
KMFA_S19_ALLOW_DWS_COMMANDS
KMFA_S19_DWS_BROWSER_POLICY_PATH
```

Default live gate:

```text
KMFA_S19_ALLOW_DWS_COMMANDS=0
```

Only set it to `1` for a user-authorized live run after healthcheck and process checks.

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

- `KMFA_S19_ALLOW_DWS_COMMANDS=1`
- browser policy is ready
- `default.openBrowser=false`

The policy check reads `KMFA_S19_DWS_BROWSER_POLICY_PATH` or defaults to:

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
