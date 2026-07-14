# Data Quality and Reconciliation Contract

## Quality grades

| Grade | Meaning | Entry requirement |
|---|---|---|
| Q0 | Raw acquired | Source responses archived and hashed. |
| Q1 | Raw valid | JSON/schema parse, endpoint metadata, batch hash, pagination completeness. |
| Q2 | Identity mapped | Every record maps to internal employee identity and employment status period. |
| Q3 | Attendance normalized | Work date, shift, check type, result, location evidence, and approval links normalized. |
| Q4 | Payroll baseline eligible | No unresolved P0/P1 exception, policy version locked, raw-to-derived reconciliation passed. |
| Q5 | Shadow payroll accepted | Five stage-2 evening runs are exact canonical-hash matches. |

## Exception priority

| Priority | Blocks stage-2 | Examples |
|---|---:|---|
| P0 | Yes | Identity collision, missing employee map, duplicate employee ID, wrong target month, raw batch corruption, database transaction failure. |
| P1 | Yes | Missing required punch detail, location evidence below threshold, unresolved absent/leave/correction, policy drift. |
| P2 | No by default | Formatting anomaly, non-payroll display issue, minor address normalization warning. |
| P3 | No | Informational note. |

## Reconciliation checks

1. Raw result count by employee/date/check type equals normalized result count after documented de-duplication.
2. Raw detail count equals detail fact count after documented de-duplication.
3. Each payroll-facing classification links to source event IDs and policy version.
4. Every day in target month has either a valid attendance state or a documented non-attendance reason.
5. Every location-sensitive punch has detail evidence or an explicit issue.
6. Every correction/approval reference is linked or explicitly missing.
7. Derived facts can be regenerated and produce the same canonical snapshot hash.

## Canonical snapshot rules

Canonical snapshot must include:

- target month
- policy version
- employee identity version
- source batch hashes
- normalized day facts
- normalized punch facts
- location evidence summary
- unresolved exception summary
- payroll baseline candidate rows

Canonical snapshot must exclude volatile fields:

- run ID
- acquired_at timestamp
- file system path
- local absolute path
- transient API token or request signature
- non-deterministic ordering

## Exact consensus rule

Stage-2 acceptance requires exact equality of the canonical hash across runs 1-5. Majority vote is not allowed. Fuzzy matching is not allowed. Manual override is not part of stage-2 acceptance.
