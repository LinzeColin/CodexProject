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

Private config belongs in OneDrive and must not be committed:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/private_runtime/
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
DWS_OUTPUT_ZIP
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

Only upstream input zip:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs.zip
```

Required group member prefixes inside the zip:

```text
付款请示群
生产管理群
```

A disk `/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/`
folder is normally absent and is not configurable input. Never probe, create,
materialize, copy, extract, or fall back to it. Stream required zip members in
place and do not automatically evict the zip after each run.

OneDrive routine-check output root:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check
```

Private local runtime:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/private_runtime
```

## Active Database Policy

Active SQLite stays in OneDrive private runtime so routine-check runs do not create ignored runtime files inside the Git package:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/private_runtime/daily_routine_check.sqlite
```

Append-only logs also go to OneDrive:

```text
/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/KMFA/daily_routine_check/YYYYMM/
```

## Config Philosophy

Do not hard-code names, group names, document keywords, thresholds, due times, or OCR classifier weights in Python. Load them from YAML/JSON templates so a non-developer can change behavior later.
