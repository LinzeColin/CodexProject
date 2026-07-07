# KMFA S19 DingTalk Attendance

S19 adds the public-safe structure for `每日早晚钉钉考勤检查`.

The module is live-only. It does not create sample employees, sample punches, or fixture attendance records. When live DingTalk configuration is missing, scripts return `CONFIG_MISSING`.

Private runtime data belongs outside Git:

- local operational cache: `KMFA/metadata/dingtalk_attendance/private_runtime/`
- long-term private archive: `/Users/linzezhang/OneDrive/dingtalk_attendance/YYYYMM/`

Git may store only code, schema, policy, prompts, path references, and validation evidence.
