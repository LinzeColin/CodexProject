# Acceptance Criteria

## Skill installation acceptance

- [ ] `KMFA/KMFA/kmfa-dingtalk-attendance-skill/SKILL.md` exists.
- [ ] Codex can explicitly invoke `$kmfa-dingtalk-attendance-skill`.
- [ ] Skill description includes KMFA, DingTalk attendance, stage2, payroll baseline, database, location/trajectory terms.
- [ ] `preflight.sh`, `inspect_runtime.sh`, `validate_offline.sh`, `month_gate.py`, and `stage2_consensus_gate.py` are executable.

## Data acquisition acceptance

- [ ] Attendance result records are collected.
- [ ] Attendance detail records are collected.
- [ ] Location fields are stored when present.
- [ ] Trajectory evidence points are stored.
- [ ] Raw JSON is stored unchanged.
- [ ] Raw batch hash exists.
- [ ] Pagination/retry status is recorded.

## Database acceptance

- [ ] PostgreSQL schema applies cleanly.
- [ ] Raw tables are idempotent.
- [ ] Detail table supports latitude/longitude/address/base fields.
- [ ] Trajectory table supports one or more points per punch.
- [ ] Derived facts link to raw IDs.
- [ ] Policy version and rule config snapshot are present.
- [ ] Stage-2 tables exist.
- [ ] Payroll baseline table/view exists.
- [ ] Private DB landing bundle includes policy_version, accepted stage-2 certificate, day facts, payroll baseline rows, and a generated load plan before any database mutation.
- [ ] Generated PostgreSQL load plan passes static validation before any non-production execution.
- [ ] PostgreSQL load plan execution fail-closes unless `--execute`, explicit acknowledgement, non-production target env, and approved DSN are all present.

## Stage-2 acceptance

- [ ] Stage-2 is skipped in morning automation.
- [ ] Stage-2 is skipped outside days 1-5.
- [ ] Stage-2 target month is previous natural month.
- [ ] Day 1 evening writes run_01.
- [ ] Day 2 evening writes run_02.
- [ ] Day 3 evening writes run_03.
- [ ] Day 4 evening writes run_04.
- [ ] Day 5 evening writes run_05.
- [ ] Day 5 compares all five canonical hashes.
- [ ] Q5 is assigned only if all five hashes match exactly and P0/P1 are zero.

## Payroll baseline acceptance

- [ ] Payroll baseline candidate rows are generated from accepted Q5 target month.
- [ ] Each row links to day_fact, stage2 certificate, canonical hash, and policy version.
- [ ] Active baseline view returns only accepted certificate rows.
- [ ] Post-acceptance correction supersedes prior version rather than overwriting evidence.
