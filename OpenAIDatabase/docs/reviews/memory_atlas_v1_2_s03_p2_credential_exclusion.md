# Memory Atlas v1.2 S03 P2 Credential Exclusion

Task ID: `MA-V12-S03P2`.

Acceptance ID: `ACC-MA-V12-S03P2`.

Status: `phase_s03_p2_credential_exclusion_completed_pending_s03_p3`.

Validator: `validate:v1.2-s03-p2`.

## Result

S03 P2 implements the credential is not memory boundary for Memory Atlas v1.2.

The implemented boundary is `credentials_not_transcript`: ordinary transcript is memory,
but credentials are not memory and must fail the gate before public backup or commit.

## Files

- `机器治理/同步与备份/credential_exclusion_policy.v1_2_s03_p2.json`
- `scripts/privacy_guard.py`
- `scripts/sync_codex_memory_data.py`
- `人类可读/07_凭证排除说明.md`
- `apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s03_p2.cjs`

## Acceptance Coverage

- Credential categories covered: cookies, session tokens, passwords, api keys,
  private keys, oauth tokens and browser credential store.
- Ordinary transcript is not blocked when it only discusses token budgets,
  API-key policy or credential-management concepts.
- The shared privacy guard exposes scanner, assertion and redaction functions.
- Codex sync uses the shared redaction entry and records the `credentials_not_transcript`
  credential boundary.
- Repo audit uses the same credential exclusion scanner.

## Boundaries

- No complex UI.
- No S03 P3 manifest generation.
- No connector implementation.
- No real transcript ingestion in this phase.
- No public raw file mutation in this phase.
- No GitHub main upload in this phase.

Next gate: pending S03 P3.
