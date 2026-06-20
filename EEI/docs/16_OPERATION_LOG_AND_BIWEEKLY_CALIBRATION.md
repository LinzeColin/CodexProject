# 16 - 操作日志与每两周校准机制

## 1. 范围

MVP 不建设复杂权限管理。默认只有一个本地用户命名空间，但必须保留可审计操作日志和每 14 天一次的校准机制。

## 2. 操作日志

### 必须记录的操作

- 创建、修改、激活、停用、回滚评分 profile；
- 修改权重、阈值、半衰期、缺失值策略和归一化方法；
- 手工确认/驳回实体解析和关系候选；
- 加入/移除 Watchlist；
- 手工触发采集、重算或校准；
- 接受/拒绝校准建议；
- 修改来源启用状态或重要配置；
- 导出研究集。

### 最小字段

- `id`
- `occurred_at`
- `actor`（MVP 默认 `local_user` 或 `system`）
- `action_type`
- `object_type`, `object_id`
- `old_value`, `new_value`, `diff`
- `reason`
- `request_id`, `session_id`
- `model_version`, `profile_version`
- `result_status`, `error`

日志追加写入，不提供直接修改接口；敏感密钥和原始认证信息不得进入日志。

## 3. 校准频率

- 固定 cadence：每 14 天。
- 支持手工立即运行。
- 计划时间按部署时区配置；默认 Australia/Sydney 周一 06:00。
- 失败重试最多 2 次，指数退避；失败进入 Change Feed。
- 校准不是数据抓取替代品；它基于最近成功数据快照。

## 4. 校准检查项

### 数据覆盖

- P0/P1 实体覆盖；
- 关系证据覆盖；
- unknown/disputed/stale 比例；
- 来源失败率和披露滞后；
- 行业与供应链阶段空洞。

### 分数稳定性

- 各组件分布和分位数漂移；
- Top-10/Top-50 排名稳定性；
- 分数大幅变化的对象及原因；
- profile 间敏感性；
- 缺失值重归一化影响。

### 质量抽检

- Top-N 关系人工 gold sample precision；
- 实体解析准确率；
- 关系方向、时间和金额语义错误；
- 供应链 Tier 和材料性误标；
- 冲突未显式化。

### 用户行为反馈

- 用户经常手工调整的维度；
- 被忽略或反复展开的关系层；
- 用户覆盖默认排序的次数；
- Watchlist 中高优先级但低覆盖对象。

## 5. 校准输出

每次生成：

1. 校准元数据和输入快照；
2. 通过/警告/失败项；
3. 数据覆盖与漂移报告；
4. 模型敏感性和 Top-N 变化；
5. 错误样本与待复核队列；
6. 建议参数变更及预览；
7. 与上一轮对比；
8. 风险与回滚方案。

建议默认状态为 `proposed`，不得自动激活。用户接受后生成新 profile/version 并写操作日志。

## 6. 校准门槛示例

| 检查 | 通过 | 警告 | 失败/阻断 |
|---|---:|---:|---:|
| 正式关系证据覆盖 | 100% | 不适用 | <100% |
| P0 数据 stale | <=10% | 10-20% | >20% |
| 实体解析 precision | >=95% | 92-95% | <92% |
| 关系 precision | >=90% | 85-90% | <85% |
| Top-20 两周无解释变动 | <=30% | 30-50% | >50% |
| 来源批次失败率 | <5% | 5-15% | >15% |
| profile 结果可重现 | 100% | 不适用 | <100% |

阈值是默认参数，可在校准配置中调整并版本化。

## 7. 防止过拟合与确认偏差

- 不以短期价格表现优化权重；
- 不自动把用户偏好当作正确答案；
- 校准报告同时展示支持和反证；
- 参数建议必须说明受影响对象和副作用；
- 至少保留一个冻结的默认基准 profile；
- 每次变更可回滚到上一已知良好版本；
- 重大公式变化需单独 ADR。

## 8. API 与任务

- `GET /v1/audit-logs`
- `GET /v1/calibrations`
- `POST /v1/calibrations/run`
- `GET /v1/calibrations/{id}`
- `POST /v1/calibrations/{id}/accept-proposal`
- `POST /v1/calibrations/{id}/reject-proposal`
- scheduler job: `calibration_run` via `scripts/job_scheduler.py run-once --job-type calibration_run`
- scheduler output: coverage metrics, score-result coverage, drift warnings, `proposal_status=none`, `calibration.run.completed` outbox event

## 9. 验收

- 修改 profile 后 1 秒内可查询对应日志；
- 日志包含 old/new diff 和 reason；
- 同一日志不得被 API 修改或删除；
- 校准 scheduler 以 14 天 cadence 注册；
- fixture 模式可模拟两轮校准并比较；
- 建议不会自动激活；
- 接受/拒绝均写日志；
- 校准失败不覆盖当前 active profile；
- 任何 score result 能追溯到数据快照、model、profile 和 calibration run。
