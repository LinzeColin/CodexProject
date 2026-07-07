# KMFA S19 Local Configuration Policy

Do not commit DingTalk credentials, robot endpoint values, signing keys, local environment files, raw API responses, report bodies, or database files.

Allowed local configuration surfaces:

- macOS user keychain
- `KMFA/.env.local`
- environment variables in the local Codex automation process

Required live configuration names:

- `DINGTALK_APP_KEY`
- `DINGTALK_APP_CREDENTIAL`
- `DINGTALK_CORP_ID`
- `DINGTALK_AGENT_ID`

Optional notification configuration names:

- `DINGTALK_ROBOT_URL`
- `DINGTALK_ROBOT_SIGNING_KEY`
- `DINGTALK_BOSS_USER_ID`
- `DINGTALK_CONVERSATION_ID`

When configuration is missing, S19 must return `CONFIG_MISSING` or `NOTIFIER_CONFIG_MISSING`; it must not create sample attendance data.
