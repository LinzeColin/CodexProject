# Codex Desktop Automation Prompt｜GitHub Autosync Governance

Run locally from:

```text
/Users/linzezhang/CodexProject
```

Use:

```bash
python3 KMFA/tools/daily_routine_check/git_autosync.py --once
```

Or continuous local watcher:

```bash
python3 KMFA/tools/daily_routine_check/git_autosync.py --watch --interval-seconds 60
```

Allowed paths:

```text
KMFA/daily_routine_check_skill/
KMFA/metadata/daily_routine_check/
KMFA/tools/daily_routine_check/
KMFA/tests/test_daily_routine_check.py
```

Blocked content:

```text
.env.local
.sqlite
.db
.jsonl
.jsonl.gz
webhook
token
secret
open_conversation_id actual values
raw_messages actual private files
DWS_Outputs raw archives
screenshots
OCR raw response bodies
```

Before push, autosync must run validators/tests and fail closed on any issue.
