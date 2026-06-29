# KMFA S02-P1 Test Results

run_id: `KMFA-S02-P1-20260629`

## Commands

```bash
python3 KMFA/tools/metadata_protocol_check.py
python3 KMFA/tools/no_omission_check.py
python3 scripts/lean_governance.py validate --project KMFA
python3 scripts/validate_project_governance.py --project KMFA
git diff --check -- KMFA
```

## Results

| Command | Result |
|---|---|
| `python3 KMFA/tools/metadata_protocol_check.py` | PASS: dirs=8, files=16, identifiers=5 |
| `python3 KMFA/tools/no_omission_check.py` | PASS: requirements=20, P0=9, P1=8, status_records=234, tasks=162 |
| `python3 scripts/lean_governance.py validate --project KMFA` | PASS: errors 0 / warnings 0 |
| `python3 scripts/validate_project_governance.py --project KMFA` | PASS: errors 0 / warnings 0 |
| `git diff --check -- KMFA` | PASS |
| JSON/JSONL parse check | PASS: events=4, development_events=4, stage_status=234, S02-P1 protocol JSONL files parse |
| raw/sensitive file suffix scan | PASS: no forbidden raw file-like artifacts under `KMFA/` |
| secret pattern scan | PASS: no OpenAI/GitHub/AWS/private-key/Slack token patterns found |
| `python3 -m py_compile KMFA/tools/metadata_protocol_check.py KMFA/tools/no_omission_check.py` | PASS |

## Residual Risk

S02-P2 and S02-P3 are not complete. Stage 2 cannot be reviewed or uploaded to GitHub after S02-P1 alone.
