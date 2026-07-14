# KMFA Quality Gate Policy

product_version: `0.1.4-s02p3-quality-gate`
stage_phase: `S02-P3`
fact_level: `EXTRACTED`

## Scope

S02-P3 defines data quality grades, report trust grades, and the release gate between them. It is a protocol phase only: it does not import files, calculate money, run real zero-delta checks, complete lineage verification, or generate formal reports.

v0.1.4 locks the same public-safe protocol for the HUMAN_FLOW_VERIFIED repair package. This phase does not read, list, inventory, modify, or write `/Users/linzezhang/Downloads/KMFA_MetaData`; it only commits policy, validator, evidence index, and governance records.

## Data Quality Grades

| Grade | Meaning | Report Permission |
|---|---|---|
| `Q0` | 未导入或无法读取 | No report |
| `Q1` | 已登记但未解析 | No report |
| `Q2` | 已解析但字段不完整 | No report |
| `Q3` | 机器候选结构化 | Preview only |
| `Q4` | 人工确认黄金字段 | Internal review report |
| `Q5` | 零差异验证通过并完成追溯 | Formal internal report |

## Report Trust Grades

| Grade | Required Conditions | Permission |
|---|---|---|
| `A` | `Q5` data, zero-delta passed, critical differences closed, human confirmation completed | Formal internal report |
| `B` | `Q4+` data, critical differences explainable, report limitations explicit | Internal review report |
| `C` | `Q3` data | Preview and review only |
| `D` | Critical data missing, stale, or unresolved differences exist | Not for business decisions |

## Release Gate

- `Q0`, `Q1`, and `Q2` cannot generate internal reports.
- `Q3` can only produce previews and review material.
- `Q4` can support internal review reports with explicit limitations.
- `Q5` is required for formal internal reports.
- `A` reports require `Q5`, zero-delta pass, closed critical differences, and human confirmation.
- Unresolved critical differences, stale inputs, missing lineage, or failed zero-delta block promotion.
- Any missing gate evidence is treated as blocked, not as passed.
- GitHub main upload remains deferred until v1.4 Stage 1-18 are complete, overall-reviewed, and review findings are fixed.

## S02-P3 Non-goals

- No raw file import.
- No business amount parsing or normalization.
- No formal zero-delta implementation.
- No lineage completeness checker.
- No HTML/CSV report generation.
- No Stage 2 review.
- No GitHub upload.
