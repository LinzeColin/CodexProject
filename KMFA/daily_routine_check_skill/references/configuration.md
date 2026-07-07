# KMFA Daily Routine Check Configuration

## Public Config And Metadata

These files are safe to read and commit:

```text
KMFA/metadata/daily_routine_check/README.md
KMFA/metadata/daily_routine_check/routine_rules.public.yaml
KMFA/metadata/daily_routine_check/cash_monitor.public.yaml
KMFA/metadata/daily_routine_check/database_manifest.json
KMFA/metadata/daily_routine_check/notification_policy.yaml
KMFA/metadata/daily_routine_check/onedrive_storage_manifest.yaml
KMFA/metadata/daily_routine_check/retention_policy.yaml
KMFA/metadata/daily_routine_check/codex_automation/install_or_update_skill.prompt.md
KMFA/metadata/daily_routine_check/codex_automation/daily_routine_check.prompt.md
KMFA/metadata/daily_routine_check/codex_automation/github_sync.prompt.md
```

## Private Config

Private config belongs here and must not be committed:

```text
KMFA/metadata/daily_routine_check/private_runtime/
```

Use templates from this package:

```text
KMFA/daily_routine_check_skill/templates/env.local.example
KMFA/daily_routine_check_skill/templates/notification_targets.local.example.json
```

Copying these templates into private runtime is a machine-local setup action and must not be committed.

## Environment Keys

Known local-only keys:

```text
DINGTALK_ROUTINE_ROBOT_URL
DINGTALK_ROUTINE_ROBOT_SIGNING_KEY
DINGTALK_BOSS_USER_ID
DINGTALK_BOSS_DISPLAY_NAME
OPENAI_API_KEY
CLOUD_OCR_PROVIDER
CLOUD_OCR_API_KEY
DWS_OUTPUT_ROOT
DAILY_ROUTINE_ONEDRIVE_ROOT
DAILY_ROUTINE_ALLOW_SEND
DAILY_ROUTINE_ALLOW_CLOUD_OCR
DAILY_ROUTINE_ALLOW_LLM
DAILY_ROUTINE_GIT_AUTOSYNC
```

Default gates:

```text
DAILY_ROUTINE_ALLOW_SEND=0
DAILY_ROUTINE_ALLOW_CLOUD_OCR=1
DAILY_ROUTINE_ALLOW_LLM=1
DAILY_ROUTINE_GIT_AUTOSYNC=0
```

The user authorized cloud OCR/LLM/agent for this use case. Sending notifications still needs local target setup.

## Canonical Paths

Input root:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs
```

Input groups:

```text
付款请示群
生产管理群
```

OneDrive routine-check output root:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check
```

Private local runtime:

```text
KMFA/metadata/daily_routine_check/private_runtime
```

## Active Database Policy

Active SQLite should stay in local private runtime to avoid OneDrive sync conflicts while writes are active:

```text
KMFA/metadata/daily_routine_check/private_runtime/daily_routine_check.sqlite
```

Daily durable copies and append-only logs go to OneDrive:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/YYYYMM/
```

## Config Philosophy

Do not hard-code names, group names, document keywords, thresholds, due times, or OCR classifier weights in Python. Load them from YAML/JSON templates so a non-developer can change behavior later.
