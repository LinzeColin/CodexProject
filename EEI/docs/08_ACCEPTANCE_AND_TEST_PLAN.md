# 08 - Acceptance and Test Plan

## 1. Release rule

`make verify` 必须汇总 lint、typecheck、unit、integration、E2E、data checks、benchmark、a11y/security 和 migration rollback。任何 required suite skipped/failed 返回非零。

机器可读矩阵：`data/acceptance_matrix.csv`。

## 2. Critical E2E journeys

### E2E-01 Home to focus

- 打开首页；
- 选择半导体行业；
- 打开 NVIDIA fixture；
- 看到人类摘要、八层导航、coverage、As-of 和 profile。

### E2E-02 Three reroots

- NVIDIA -> synthetic foundry -> synthetic equipment -> synthetic materials；
- 每一步 breadcrumb/URL/back/forward 正确；
- layers/time/filters/profile 继承；
- graph budget 未超限；
- 每条边可开 evidence。

### E2E-03 Cross-industry

- AI infrastructure -> data center -> utility -> equipment；
- 显示行业切换，不阻断继续探索。

### E2E-04 Custom model

- 克隆 Balanced；
- 调高 supply-chain weight；
- 非法总和被拒绝；
- preview 不写正式结果；
- save/activate/rollback；
- score explanation 显示 contributions/missing/evidence/version。

### E2E-05 Audit and calibration

- profile 修改后查询 operation log；
- 运行 snapshot A 校准；
- fixture clock +14 天运行 snapshot B；
- 查看 drift/proposal；
- reject 后 active profile 不变；
- 所有动作有日志。

## 3. Data tests

- 30 P0 seeds；140 research universe；
- 10 relationship families；
- 正式边/事件 evidence coverage 100%；
- unknown 不等于 0；
- amount 语义完整；
- supply-chain stage/tier/materiality 校验；
- model/profile version 唯一；
- weight sum 和范围；
- calibration cadence =14；
- operation log append-only；
- reroot history sequence 一致。

## 4. API contract tests

- OpenAPI parse/validation；
- `/v1/home`, `/v1/industries`, `/v1/explore`, `/v1/explore/reroot`, `/v1/explore/expand`；
- entity empire/supply-chain/capital/policy/strategy；
- paths budget；
- watchlists；
- scoring profile/preview/explain/activate/rollback；
- audit logs；
- calibrations；
- export/provenance。

## 5. Performance

Recorded environment must be attached to benchmark results.

| Case | Target |
|---|---:|
| 300 nodes/1000 edges first usable render | <=2s |
| Common filter | <=250ms |
| Fixture reroot API p95 | <=250ms excluding client layout |
| Incremental expand 40 nodes | <=500ms API target |
| Score preview Top-100 | <=1s |
| Audit log query last 100 | <=250ms |

## 6. Accessibility

- Home and focus core path keyboard reachable；
- graph has table alternative；
- evidence and node actions accessible；
- focus/selection announced；
- charts not color-only；
- touch actions explicit；
- non-canvas AA target。

## 7. Failure injection

- source 429/503；
- parser error；
- DB failure mid-ingest；
- score run failure；
- calibration failure；
- invalid/over-budget graph query；
- stale profile version conflict；
- migration downgrade；
- evidence URL sanitization。

Expected: no partial publish, active profile preserved, failures visible, retry bounded, rollback documented.

## 8. Clean-room release

A new operator must clone/unzip, run README commands, seed fixtures, open home, complete demo journey and run `make verify` without undocumented manual edits.
