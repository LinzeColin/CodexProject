# Stage-2 Protocol

## Definition

阶段二是“完整自然月结束后，次月 1-5 日夜间 automation 对上月数据连续做 5 次独立验证，5 次 canonical 结果完全一致后，目标月达到 Q5”。

## Calendar rule

使用考勤业务时区，默认 `Asia/Shanghai`。

```text
2026-07-01 至 2026-07-31 = 目标自然月 202607
2026-08-01 晚上 = stage2 run_01 for 202607
2026-08-02 晚上 = stage2 run_02 for 202607
2026-08-03 晚上 = stage2 run_03 for 202607
2026-08-04 晚上 = stage2 run_04 for 202607
2026-08-05 晚上 = stage2 run_05 for 202607 + consensus gate
```

## Run artifact layout

```text
private_runtime/stage2/YYYYMM/run_01/
private_runtime/stage2/YYYYMM/run_02/
private_runtime/stage2/YYYYMM/run_03/
private_runtime/stage2/YYYYMM/run_04/
private_runtime/stage2/YYYYMM/run_05/
```

Each run writes:

```text
run_manifest.json
raw_batch_hashes.json
normalized_counts.json
canonical_snapshot.json
canonical_snapshot.sha256
quality_report.json
exception_report.json
payroll_baseline_candidate.json
```

Day 5 writes:

```text
stage2_hash_matrix.csv
stage2_consensus_certificate.json
stage2_consensus_certificate.md
```

If mismatch:

```text
stage2_divergence_report.md
```

## Acceptance truth table

| Condition | Required value |
|---|---|
| target month ended | true |
| run dates | next month days 1-5 |
| run slot | evening |
| run count | 5 |
| canonical hashes | all identical |
| per-run quality | Q4 or higher |
| final quality | Q5 |
| unresolved P0 | 0 |
| unresolved P1 | 0 |
| location evidence | pass |
| trajectory evidence | pass |
| rule drift | none |

## Failure cases

| Failure | Result |
|---|---|
| day 1 missing | stage2 failed |
| morning run tries stage2 | ignored / not eligible |
| any P0/P1 unresolved | stage2 failed |
| canonical hash mismatch | stage2 failed |
| location evidence below threshold | stage2 failed |
| raw-to-derived count mismatch | stage2 failed |
