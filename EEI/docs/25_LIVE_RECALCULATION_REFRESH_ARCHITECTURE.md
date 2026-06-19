# 25 - 参数即时重算、全视图刷新与一致性架构

## 1. 目标

用户修改权重、阈值、时间半衰期或图谱预算时，不应逐页刷新。系统以统一 `AnalysisContext` 驱动全部视图，并通过预览计算、版本化重算、事件推送和原子快照切换保证“快”和“可信”同时成立。

## 2. 三层刷新

### A. 浏览器即时预览

- 输入变化经 120ms debounce；
- Web Worker 对当前已加载事实重算；
- 图、Sankey、矩阵、时间轴和右侧解释共享同一结果；
- 不写数据库；
- p95 < 250ms；
- UI 显示“草稿预览”，禁止伪装成已发布结果。

### B. 会话级应用

- 参数写入 session context；
- 统一失效当前主体所有模块的 query keys；
- 重新请求缺失投影；
- p95 < 700ms；
- 页面和 URL 可恢复，但不改变系统默认。

### C. 持久化激活

```text
POST activate profile
  -> transaction: profile version + operation log + outbox event
  -> worker computes affected entities/edges
  -> write new score_snapshot_id
  -> validate counts/checksum/coverage
  -> atomic activate snapshot
  -> SSE broadcasts score_snapshot.activated
  -> clients invalidate and cross-fade to new snapshot
```

大范围重算期间继续读取上一个成功快照；失败时不切换。

## 3. 事件类型

| 事件 | 触发 | 前端动作 |
|---|---|---|
| `analysis.preview.changed` | 本地参数变化 | 当前视图立即重绘 |
| `analysis.session.applied` | 会话应用 | 失效当前主体所有模块 |
| `model.profile.activated` | 配置版本激活 | 显示重算进度 |
| `score.snapshot.activated` | 新分数快照就绪 | 原子切换并全视图刷新 |
| `data.snapshot.activated` | 新数据快照就绪 | 刷新实体、边、事件与来源状态 |
| `source.health.changed` | 来源状态变化 | 更新数据状态与警告 |
| `calibration.completed` | 双周校准完成 | 显示校准报告，不自动改参数 |

## 4. 数据一致性

每个 API 响应必须携带：

```json
{
  "data_snapshot_id": "...",
  "score_snapshot_id": "...",
  "model_version": "...",
  "profile_version": "...",
  "as_of": "...",
  "generated_at": "..."
}
```

同一屏内不得混用不同 `data_snapshot_id` 或 `score_snapshot_id`。如果后台出现新快照，先显示“可更新”，再一次性切换，禁止图、右侧分数和表格处于不同版本。

## 5. PostgreSQL 事件策略

- `transactional_outbox` 是持久事件源；
- `LISTEN/NOTIFY` 只用于唤醒 worker/SSE gateway，不承担可靠队列；
- worker 按 outbox id 幂等消费；
- 成功后记录 processed_at；
- 失败按指数退避并写 operation log；
- materialized projections 通过新快照表或 concurrent refresh 更新；
- 激活通过单行指针/配置表事务切换。

## 6. 前端刷新合同

- 所有模块读取统一 `analysisContextKey`；
- query key 至少包含主体、时间、筛选、profile version 和 snapshot id；
- 参数预览只改变 presentation score，不修改原始事实；
- 图形更新使用稳定 object id，使图形可 morph 而不是整屏闪烁；
- 旧数据退出 160-220ms，新数据进入 220-360ms；
- reroot 使用 320-420ms 空间过渡；
- 支持 `prefers-reduced-motion`，精简模式改为淡入/直接替换。

## 7. 失败与回滚

| 失败 | 行为 |
|---|---|
| 本地预览计算失败 | 恢复上一个草稿值并提示具体参数 |
| 保存失败 | 不创建版本，不清空草稿 |
| 重算失败 | active snapshot 不变，显示失败和重试 |
| SSE 断开 | 退化为带退避的轮询 |
| 新快照校验失败 | 不激活；记录校验差异 |
| 页面刷新 | 从 URL + session + active version 恢复 |

## 8. 验收

- 调整任一 P0 参数后，当前已加载的六类核心研究视图在 250ms 内开始更新；
- 预览状态有明确标识；
- 激活后所有连接客户端收到同一 snapshot id；
- 任一失败不破坏上一个成功快照；
- Playwright 测试验证图、详情、排名、告警计数使用同一版本。
