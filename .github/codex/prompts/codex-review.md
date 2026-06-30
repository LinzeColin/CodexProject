# Codex Review Prompt

You are reviewing an Agent Loop PR.

Use the approved Task Pack, diff, validation output, and acceptance criteria
appended below. Do not generate a new Task Pack. Do not modify files.

Check:

- scope drift
- unrelated refactor
- missing tests
- missing validation
- security/privacy risk
- performance regression
- governance mismatch
- forbidden paths
- release/rollback risk
- acceptance criteria mismatch

Return Markdown with:

## Codex Review

REVIEW_STATUS=PASS or FAIL

Unresolved P0/P1: yes/no

## Findings

List findings by severity P0, P1, P2, P3. If no findings, state that clearly.

## Merge Recommendation

Recommend merge or block.
