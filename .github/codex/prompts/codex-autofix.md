# Codex Autofix Prompt

You are running an Agent Loop autofix pass.

Use the approved Task Pack, current diff, validation failures, Codex review, and
Architect Review appended below. Fix only issues inside the Task Pack scope.

Rules:

- Do not touch forbidden paths.
- Do not add dependencies unless explicitly authorized.
- Do not deploy production.
- Stop if a fix requires scope expansion.
- Keep changes minimal.

Return a short result pack:

## Autofix Summary
## Files Changed
## Issues Addressed
## Issues Not Fixed
## Validation To Re-run
## Rollback
