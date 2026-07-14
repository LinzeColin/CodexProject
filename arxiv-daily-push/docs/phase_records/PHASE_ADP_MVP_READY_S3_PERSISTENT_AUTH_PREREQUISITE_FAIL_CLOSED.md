# PHASE ADP MVP Ready S3 Persistent Authorization Prerequisite Fail Closed

更新时间：2026-07-10 21:50:12 Australia/Sydney

## 任务合同

- Task ID: `ADP-MVP-READY-S3-PERSISTENT-AUTH-PREREQUISITE-FAIL-CLOSED`
- Iteration: `ITER-20260710-ADP-MVP-READY-S3-PERSISTENT-AUTH-PREREQUISITE-FAIL-CLOSED`
- Roadmap context: `S2PMT07`
- Gate: `PERSISTENT_DAILY_OPERATION_AUTHORIZATION_PREREQUISITE_FAIL_CLOSED_NO_RUNTIME_ENABLEMENT`
- Acceptance: `ACC-S2PMT07-FINAL-REVIEW`
- Risk tier: `T2`

## 根因与修复

历史 builder 只用 live authorization artifact 的存在与格式有效性派生 `persistent_daily_operation_authorized`，没有把 owner-decision 和 controlled-run 的 `failed_checks` 纳入最终授权判定；validator 又信任输出布尔值，因此接受 `PASS + failed_checks`。缺失 owner decision 时，`None` 还会直接进入 `.get()` 并抛出 `AttributeError`。

修复后的固定判定顺序为：

1. artifact 缺失：`blocked_persistent_daily_operation_authorization_missing`。
2. artifact 存在但无效：`blocked_persistent_daily_operation_authorization_invalid`。
3. artifact 有效但任一非 artifact 前置条件失败：`blocked_persistent_daily_operation_authorization_prerequisites_failed`。
4. 全部 checks 通过：`pass_persistent_daily_operation_authorization_recorded_no_runtime_enablement`。

`persistent_daily_operation_authorized`、`owner_daily_operation_authorization_recorded` 和 `daily_operation_enablement_allowed_by_this_artifact` 只有在全部 checks 通过时才为 true。缺失 JSON mapping 标准化为空 mapping 并失败关闭；validator 独立从 checks 重算授权，不接受自相矛盾状态。

## TDD 证据

- RED：核心授权测试出现 2 failures + 1 error；空 controlled-run 被错误判为 PASS，缺失 owner decision 抛 `AttributeError`，validator 接受 PASS + failed checks。
- RED：从 PASS state 删除一个必需 prerequisite check key 后，validator 曾错误返回无错误。
- RED：临时根目录中的有效授权 artifact 配合空 controlled-run 时，readiness 与 enablement preflight 均错误 exit 0 / PASS。
- GREEN：9 个 persistent-authorization 聚焦测试通过；2 个 readiness/preflight prerequisite 端到端测试通过；validator 还要求 checks key 集合精确匹配 12 个必需前置项。
- FULL：`unittest discover` 完整 ADP suite 共 890 项，全部通过。
- 临时授权文件只存在于 `TemporaryDirectory`；真实仓库没有创建 `FINAL_ACCEPTANCE_BUNDLE/daily_operation_persistent_enablement_authorization.json`。

## 模型与版本

- Model: 沿用 `MOD-ADP-100`，版本保持 `adp-s2pmt07-final-gate-precheck-v1`。
- Formula: 沿用 `FORM-ADP-102`；行为规则和实现 AST 指纹更新。
- Parameters: `NOT_APPLICABLE`，没有参数数值或 profile 变化。
- Product version: runtime/release `0.23.0` 不变；governance provisional `0.23.1` 不变。

## 生产边界

本任务不创建 owner 持久授权，不进入 S3/DAILY_OPERATION，不发送 SMTP，不启用 scheduler/LaunchAgents、Release 或 restore，不改 CURRENT/V7、public schema、DB、source、ranking 或 queue。真实仓库当前仍因 `persistent_daily_operation_authorization_missing` 阻断；本任务只保证未来 artifact 即使有效也不能绕过失败前置条件。

## 回滚

只回退本任务对授权 builder/validator、回归测试、`FORM-ADP-102` 指纹和治理/owner-facing 同步记录的修改；保留此前本地 MVP 准备补丁，不触碰任何 runtime 或生产状态。
