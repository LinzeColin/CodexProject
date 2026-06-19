# PFIOS Codex Prompts

## Standard Implementation Prompt

Read `HANDOFF.md`, `AGENTS.md`, `README.md`, and the affected tests first.

Implement one low-risk, independently testable improvement.

Run focused tests, then run the full suite when the change touches shared behavior.

Report:

- What changed.
- Why it changed.
- Files affected.
- Validation commands and results.
- Residual risks.
- Rollback path.

## Research Boundary Prompt

PFI_OS is the master-system entry, displayed as PFI_OS. PFIOS is the embedded quantitative research subsystem and is research-only.

Do not add live-trading integrations, real order placement, account credential storage, or autonomous trading actions.

Downgrade unsupported conclusions to observation, watch, needs evidence, or reject.
