# KMFA S19 DingTalk Attendance

S19 adds the public-safe structure for `每日早晚钉钉考勤检查`.

The module is live-only and uses the local `dws` CLI as its current DingTalk attendance backend. It does not create sample employees, sample punches, or fixture attendance records. When DWS is unavailable, scripts return `DWS_UNAVAILABLE`.

The live DWS backend reads organization members through `dws contact dept list-children/list-members`, then calls `dws attendance record get` and `dws attendance summary`. Transient attendance errors are retried once with verbose output.

Notification config is loaded from the ignored local file `private_runtime/.env.local`. The current enabled notification path is DingTalk group robot markdown: each message is signed locally, includes `开明考勤`, and writes only send status to the private dispatch receipt.

Private runtime data belongs outside Git:

- local operational cache: `KMFA/metadata/dingtalk_attendance/private_runtime/`
- long-term private archive: `/Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/`

The OneDrive month folder stores raw JSONL gzip, management report, HR report, dispatch receipt, manifest, and cleanup audit directly under `YYYYMM`. `--send-latest-report-only` can resend the newest private reports without another DWS collection run.

Git may store only code, schema, policy, prompts, path references, aggregate validation evidence, and no employee attendance plaintext.
