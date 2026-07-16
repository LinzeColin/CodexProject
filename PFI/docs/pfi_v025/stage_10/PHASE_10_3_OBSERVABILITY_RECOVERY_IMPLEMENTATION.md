# PFI v0.2.5 Stage 10 Phase 10.3：可观测性与故障恢复

## Run contract

- Phase：`V025-S10-P10.3`
- Tasks：`S10-P3-T1..T4`
- Acceptance：`ACC-PFI-V025-STAGE10-WHOLE-REVIEW`
- 风险路由：`T2_RUNTIME_OBSERVABILITY_RECOVERY_PRIVACY`
- 实施基线：`9800d202d7eab7ab8b5fed4d0336327d4c4bd12e`
- 产品提交：`9d2a8eb9f7b3e91492cdabffa9965339cd3bba2e`
- 当前结论：Phase `candidate_pass`；Stage 10 phase tasks=`12/12 candidate_complete`；整阶段审查与用户阶段验收仍为 `not_started`。

本轮只实现 trace/span、结构化脱敏日志、durable runtime supervisor/API/UI 与 failure matrix。未进入 Stage 10 whole-stage review、Stage 11、canonical 私有 PFI DB 迁移、push、PFI.app 安装或 production/final acceptance。

## 实现真值

### 1. Trace、span 与结构化日志

- 每个 job 固定一个 32-hex `trace_id`，每个持久 revision 固定一个 16-hex `span_id`；queued、claim、lease recovery、progress 和 terminal event 均可按同一 trace 关联。
- `durable_job_trace_contexts` 保存不可变 trace context；`durable_job_spans` 与 `durable_job_logs` append-only，并用 SQLite trigger 拒绝 update/delete。
- 日志记录 stage timing、error code/message、impact scope、retry count、cache fallback、external-network count 与六类 hash dimension；不保存 job payload、lease token 或财务值。
- 路径、email、token/secret、敏感字段和金额形态在持久化前替换为显式 redaction token；日志自身形成 SHA-256 chain。

Schemas：

- `PFIV025DurableJobTraceV1`
- `PFIV025DurableJobSpanV1`
- `PFIV025DurableJobStructuredLogV1`
- migration：`v025_stage10_job_observability_v1`

### 2. Durable supervisor 与正式 UI

- `RuntimeJobSupervisor` 以 SQLite job/event/checkpoint 为唯一状态源，执行三项真实单位：dependency snapshot、runtime diff、cache runtime ready。
- `/api/jobs`、`/api/jobs/{id}` 与 `/api/jobs/cache-refresh` 只返回持久投影；正式 UI 只映射 backend 的七种状态、revision、trace、retry、error、result、cache fallback 与 `completed_units/total_units`。
- 页面 timer 只调度下一次 API 读取，不改变 job 状态或百分比；无持久单位时不显示合成进度。
- 页面离开后重新载入，从 SQLite 列表恢复同一 job；过期 lease 先显式追加 `lease_expired_requeued`，再由新 worker 继续 checkpoint。

### 3. Failure matrix

- Offline：本地 cache refresh 完成 3/3 单位，外网调用为 0。
- Timeout：进入显式 `failed`，错误码 `LOCAL_TIMEOUT`，progress percent 保持 null，`cache_fallback_used=true`。
- Unsafe network policy：在任何 runtime work 前 fail closed，completed units=0，实际 external calls=0。
- Restart：过期 lease 进入 retry，保留 1/3 checkpoint，第二次 attempt 完成 3/3。
- Real kill：测试子进程持久化 checkpoint 后收到真实 `SIGKILL`；新进程恢复同一 SQLite job，最终 succeeded，attempt=2、retry=1、integrity pass。
- Browser leave/restart：正式 Shell 离页 10,503ms 后恢复同一 job，UI/API/DB status/revision/trace/progress 一致，外部请求为 0。

## 验证结果

- Phase 10.3 专项：`14 passed`。
- 最终产品合并回归：`121 passed`，仅 2 条 upstream protobuf deprecation warnings，无失败。
- 正式无头浏览器：`browser_status=pass`、`database_status=pass`、`trace_privacy_status=pass`、`external_network_calls=0`。
- SQLite：1 job / 8 events / 8 spans / 8 logs，revision=7、attempt=2、retry=1、progress=3/3；integrity/FK pass，journal=`DELETE`，WAL=false。
- Sanitized Playwright trace：不含 runtime token、private value 或 absolute local path；截图已纯工具目视复核。

完整命令与产物见 `PFI/reports/pfi_v025/stage_10/phase_10_3/`。

## 风险与回滚

- 本 Phase 只验证隔离 SQLite 与本机 loopback，不接受 canonical 私有 PFI DB、生产并发规模或 Stage 11 的迁移/备份恢复要求。
- trace/log 证明执行关联，不证明财务事实正确；财务输出仍受既有 source/model/human-review gates 约束。
- 新敏感字段类型进入 log context 前必须增加 redaction test；未知外网声明继续 preflight fail closed。
- 回滚顺序：先 revert Phase 10.3 证据/治理提交，再 revert 产品提交 `9d2a8eb9f7b3e91492cdabffa9965339cd3bba2e`。本 Phase 未触碰 canonical 私有 DB 或安装，无需生产数据回滚。

## Stop point

本轮严格停止在 Phase 10.3 candidate。下一唯一任务是新 run 的 `STAGE10-WHOLE-REVIEW`；完成独立整阶段审查、必要整改、复审和 transition acceptance 前，不进入 Stage 11。
