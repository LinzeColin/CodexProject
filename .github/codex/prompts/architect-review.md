# Architect Review Prompt

This prompt documents the expected Architect Review shape. The workflow uses
`scripts/agent_loop/architect_review.py` to run this review when feasible.

Do not generate a new Task Pack. Review:

- approved Task Pack
- final diff
- validation result
- Codex review
- acceptance criteria

Return:

- `ARCHITECT_REVIEW=PASS`, `FAIL`, or `N/A`
- `Unresolved P0/P1: yes/no`
- scope drift assessment
- validation gaps
- security/privacy risks
- merge recommendation
