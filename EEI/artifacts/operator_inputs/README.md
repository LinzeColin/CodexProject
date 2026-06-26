# EEI Operator Inputs

This directory is reserved for signed, operator-supplied release evidence.
Files placed here are not accepted automatically; they must pass the matching
fail-closed validator before any release preflight can become ready.

Expected MVP input paths:

- `a202/signed-release-decision-intake.json`
  - Acceptance: A202
  - Validator: `make generate-a202-signed-intake-preflight validate-a202-signed-intake-preflight`
- `a210/signed-brand-clearance.json`
  - Acceptance: A210
  - Validator: `make generate-brand-clearance-artifact validate-brand-clearance`
- `a026_a027/production-gold-labels.json`
  - Acceptance: A026 and A027
  - Validator: `make generate-gold-quality-evaluation-artifacts validate-gold-quality-evaluation`
- `a209/promoted-operator-soak-finalization.json`
  - Acceptance: A209
  - Validator: `make generate-operator-soak-finalization-preflight validate-operator-soak-finalization-preflight`
- `a209/clean-rerun-authorization.json`
  - Acceptance: A209
  - Validator: `make generate-operator-soak-recovery-authorization-packet validate-operator-soak-recovery-authorization-packet`
  - Purpose: operator authorization for a fresh 24h rerun after failed evidence is preserved

Do not place source text, secrets, API keys, private credentials, or unsigned
drafts here. Templates, fixtures, screenshots, partial A209 checkpoints, and
unchecked market/legal research do not count as clearance evidence.
