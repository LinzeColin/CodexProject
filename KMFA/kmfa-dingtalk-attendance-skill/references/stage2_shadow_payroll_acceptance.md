# Stage-2 Shadow Payroll Acceptance

## Objective

After a natural month has completed, run five independent evening validations during the following month's days 1-5. The five results must converge to the same canonical monthly state before that month can be promoted to Q5.

## Eligibility gate

Stage-2 is eligible only when all are true:

1. Local attendance timezone date is day 1, 2, 3, 4, or 5.
2. Run slot is `evening`.
3. Target month is the previous natural month.
4. Target month end date is strictly before local run date.
5. The target month's policy version is locked.
6. The stage-2 run index equals the local day-of-month.

## Run index mapping

| Local date | Target month | Run index |
|---|---|---:|
| Next month day 1 evening | previous month | 1 |
| Next month day 2 evening | previous month | 2 |
| Next month day 3 evening | previous month | 3 |
| Next month day 4 evening | previous month | 4 |
| Next month day 5 evening | previous month | 5 |

## Per-run required artifacts

```text
private_runtime/stage2/YYYYMM/run_0N/
  run_manifest.json
  raw_batch_hashes.json
  normalized_counts.json
  canonical_snapshot.json
  canonical_snapshot.sha256
  quality_report.json
  exception_report.json
  payroll_baseline_candidate.json
```

## Day-5 consensus artifacts

```text
private_runtime/stage2/YYYYMM/
  stage2_consensus_certificate.json
  stage2_consensus_certificate.md
  stage2_hash_matrix.csv
  stage2_divergence_report.md   # only when mismatch exists
```

## Acceptance condition

Accept only when:

```text
run_01 canonical hash
= run_02 canonical hash
= run_03 canonical hash
= run_04 canonical hash
= run_05 canonical hash
```

and each run has:

- quality grade at least Q4
- P0 unresolved count = 0
- P1 unresolved count = 0
- required location evidence thresholds passed
- raw-to-derived reconciliation passed
- database transaction committed and verified

## Failure behavior

If any condition fails:

1. Mark `stage2_status = failed`.
2. Generate divergence report.
3. Do not emit accepted consensus certificate.
4. Keep all five run artifacts for forensic comparison.
5. Next action is issue-specific remediation, then a new controlled re-run window or manual reconciliation protocol.
