# Skill Conversion Decision Impact

## SWOT

Strengths:

- Gives any future agent one public-safe entrypoint for KMFA 钉钉考勤 skill work.
- Reduces repeated context loading by pointing to exact files and commands.
- Captures live-run guardrails, DWS browser policy, OneDrive private archive shape, and notification rules in one place.
- Keeps private data out of Git while still preserving enough setup templates for a new machine.

Weaknesses:

- The skill cannot include secrets, resolved DingTalk IDs, SQLite, raw attendance files, or report bodies, so a new machine still needs private runtime provisioning.
- Any duplicated operational facts can drift from code; agents must verify against `KMFA/HANDOFF.md` and current source before changes.
- It does not replace tests or live health checks.

Opportunities:

- Can be installed into Codex/agent skill folders or read directly from the repo.
- Makes future database, RAG, or reporting work safer because boundaries are explicit.
- Provides a controlled basis for later salary-interface design without turning attendance data into payroll input prematurely.

Threats:

- If an agent treats the skill as a substitute for current code, it may miss changed rules.
- If private runtime files are copied into the skill folder, Git could leak credentials or employee data.
- Live DWS or notification commands can still trigger external effects if run without the authorization gate.

## Token And Context Impact

Positive impact:

- Future agents should read this package first, then only the specific KMFA files needed.
- Avoid pasting raw reports or long handoffs into chat.
- Prefer manifests, validators, and focused source files over broad directory scans.

Risk:

- Overloading the skill with historical narrative would increase token cost and reduce actionability.

Control:

- Keep `SKILL.md` short.
- Put details in `references/`.
- Use `tools/validate_skill_package.py` after edits.

## Data Quality Impact

The skill does not alter source collection. It documents current behavior and guardrails.

Quality-sensitive rules:

- Rest reminder begins on natural-month effective attendance day 23.
- 丁春法 and 李永占 are excluded only from rest-required outputs.
- Other statuses still count normally.
- Known no-record exemptions are narrow and person-specific.
- DWS failures must be visible as pending/system issues, not converted to all-clear.

## Database Impact

The private SQLite ledger remains:

- reconstructable from OneDrive raw archives
- local/private
- ignored by Git
- validation and query layer only

The skill should improve database maintainability by documenting schema intent and rebuild commands, but it must not include the SQLite file or raw source rows.

## Salary And Payroll Impact

Current status:

- `salary_basis_allowed=false`
- no wage calculation
- no payroll export
- no final attendance approval workflow

Future payroll connection requires:

- separate scope and owner approval
- explicit data quality threshold
- manual review path for anomalies and DWS failures
- stable export contract
- no direct dependency on private report prose or raw DWS payloads
