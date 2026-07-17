# KMFA v1.5 S01 受控过渡修订

## 修订结果

- bridge Run：`S01_CONTROLLED_TRANSITION_AMENDMENT`
- bridge acceptance：`PASSED`
- transition decision：`GO_TO_S02_P1_ONLY`
- 下一独立 Run：`S02-P1`（仅需求与范围规划）
- S01 历史：继续 `BLOCKED / NOT_PASSED / NO_GO`
- Stage PASS：`false`
- 产品实现授权：`false`

本修订只补齐 P3 明确要求的 greenfield change-control。它不修改 TaskPack 的 Stage 通过标准，不把 `RUNTIME_OBJECT_MISSING` 改写成 `REFACTORABLE`，也不把 Stage review 历史的 `s02_entry_allowed=false` 改成通过。

## 允许范围

本修订最终验证通过后，下一独立 Run 可执行 `S02-P1` 的需求总账、业务线矩阵和版本边界规划。范围化入口为：

`s02_p1_planning_entry_allowed_by_amendment=true`

transition validator、103 个 focused tests、历史 Stage-review dependency 与治理检查均已通过。独立最终复核发现的 execution-event 提前放行问题已修复：final validation 前 acceptance 必须为 `PENDING_FINAL_VALIDATION` 且 planning gate=false；只有 final event 可切换为 `PASSED/true`。该字段不等于广义 S02 实现授权。`S02-P2`、`S02-P3`、`S03+`、技术选栈、runtime、API、数据库、UI、持久业务状态和业务执行全部保持关闭。

## 阻断处理

- `IB-005`：由本修订建立受控过渡边，当前 disposition=`RESOLVED_BY_AMENDMENT`。
- `IB-001` 至 `IB-004`：继续 `CARRIED_OPEN`，继续阻断 S01 acceptance 和任何 runtime implementation。
- 24 项 P3 风险继续开放；已有计划不等于已解决。

S01 必须在出现可构建 runtime、真实路由、tracked builder/installer 和完整 pre-audit telemetry 后重新验证。该 deferred revalidation 必须在 S24 发布验收、最终整体复审、唯一 GitHub main 上传及 App 重装之前完成；只有新证据可改变当前 acceptance，历史记录保持 append-only。

## 本 Run 未执行

未启动 S02，未选择技术栈，未写产品代码，未实现 runtime/API/数据库/UI，未读取 raw 业务内容，未修改 raw inbox，未上传 GitHub，未重装 App，未执行业务动作。
