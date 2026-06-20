# PFI-012 MVP Release Gate

Status: strict release gate implemented; final external Gate 7 evidence is
fail-closed and must be replayed for the current branch head before closeout.

As of: 2026-06-20 Australia/Sydney

## Scope

PFI-012 turns the accumulated PFI-001 through PFI-011 evidence into a
machine-readable MVP release gate. It is not allowed to silently claim final
GitHub CI, rollback tag, or manual user signoff when those artifacts have not
been attached.

## Implemented

- `src/pfi_os/application/pfi012_mvp_release_gate.py`
  - `PFI012MVPReleaseGateContractV1`
  - `PFI012MVPReleaseGateAcceptanceV1`
  - `PFI012ReleaseChecksumManifestV1`
- `scripts/pfi012MVPReleaseGate.sh`
  - writes `data/systemAudit/PFI012MVPReleaseGate_*.json`
  - writes `data/systemAudit/PFI012MVPReleaseGate_latest.json`
  - supports `--summary-json`, `--json`, `--ci-status`, `--ci-url`,
    `--rollback-ref`, `--user-uat-status`, and
    `--require-external-release-evidence`
- `tests/contract/test_pfi012_mvp_release_gate.py`
  - local release matrix covers PFI-001 through PFI-012 and Gate 1 through
    Gate 7
  - P0 open count is zero in the release disposition ledger
  - every P1 has a release disposition
  - latest UAT/vertical/gate artifacts are required for local release candidate
  - privacy audit rejects private/runtime/secrets in the release manifest
  - legacy freeze rejects active visible remnants from the retired identity and
    value layer, raw provider/debug labels, and old English placeholders
  - checksum manifest is signed by canonical SHA-256 over the manifest body
  - external CI and rollback evidence fail closed when explicitly required

## Gate Policy

PFI-012 has two distinct statuses:

- `local_release_candidate_status`: proves local repo, tests, UAT artifacts,
  privacy audit, legacy freeze, and checksum manifest.
- `external_release_evidence.overall_status`: records GitHub CI URL and
  rollback ref evidence. It is `PendingExternal` unless those artifacts are
  supplied and verified.

The normal script mode can pass local release-candidate evidence while keeping
external Gate 7 evidence explicit. The strict mode
`--require-external-release-evidence` fails closed unless both CI and rollback
evidence are present.

For the current release scope, closeout uses:

- GitHub Actions workflow: `PFI_OS Smoke` on the branch-head commit.
- Rollback ref: `pfi-os-rollback-20260620-redo-final`.
- Strict command:
  `PFI012_CI_STATUS=Pass PFI012_CI_URL=<github-run-url> PFI012_ROLLBACK_REF=pfi-os-rollback-20260620-redo-final scripts/pfi012MVPReleaseGate.sh --summary-json --require-external-release-evidence`.

If another branch-head commit is added, the CI URL, rollback ref target, and
strict PFI-012 replay must be refreshed before claiming Gate 7 complete.

## Verification

```bash
python -m pytest tests/contract/test_pfi012_mvp_release_gate.py -q
scripts/pfi012MVPReleaseGate.sh --summary-json
PFI012_CI_STATUS=Pass PFI012_CI_URL=<github-run-url> PFI012_ROLLBACK_REF=<tag-or-commit> scripts/pfi012MVPReleaseGate.sh --summary-json --require-external-release-evidence
```

## Boundaries

- Does not start services.
- Does not run network calls by default.
- Does not create Git tags.
- Does not mutate holdings, orders, accounts, bank/payment state, or broker
  state.
- Does not commit private runtime data, SQLite, logs, model cache, holdings,
  credentials, cookies, or secrets.
- Treats final manual UAT, GitHub CI pass URL, and rollback ref as explicit
  release evidence rather than assumptions.
