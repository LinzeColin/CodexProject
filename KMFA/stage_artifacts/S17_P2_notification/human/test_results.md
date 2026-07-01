# KMFA S17-P2 Notification Test Results

generated_at: 2026-07-01T23:59:00+10:00

## TDD Red Evidence

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_notification_reminders.py
ModuleNotFoundError: No module named 'KMFA.tools.notification_reminders'
```

## Green Evidence

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tests/test_notification_reminders.py` | PASS: 6 tests |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/notification_reminders.py --check-only` | PASS: rules=3, events=3, dispatch_logs=3, email_reminder_only=true, full_report_body=false, metadata_logs=true, stage17_review=false, github_upload=false |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/notification_reminders.py --generated-at 2026-07-01T23:59:00+10:00` | PASS: generated S17-P2 notification artifacts |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 KMFA/tools/check_s17_p2_notifications.py` | PASS: rules=3, events=3, dispatch_logs=3, email_reminder_only=true, full_report_body=false, attachments=false, metadata_logs=true, stage17_review=false, github_upload=false |

## Final Gate Rerun

| Command | Result |
|---|---|
| `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s KMFA/tests -q` | PASS: 239 tests |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=512, tasks=162, v1.2_html=45+ |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_required_html.py` | PASS: html=45, core=7 |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_no_float_money.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/metadata_protocol_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/immutability_policy_check.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 KMFA/tools/check_report_grade_gate.py` | PASS |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors=0, warnings=0 |
| `PYTHONDONTWRITEBYTECODE=1 python3 scripts/validate_governance_sync.py --changed-only --enforce-sync` | PASS: errors=0, warnings=0 |
| JSON/JSONL/YAML/CSV parse checks for changed governance files | PASS |

## Boundary Result

- `stage17_review=false`
- `github_upload=false`
- `external_email_connector=false`
- `full_report_body=false`
- `report_attachment=false`
- `recipient_plaintext_address=false`
- `raw_business_data=false`
