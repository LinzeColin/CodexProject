# KMFA v1.5 S01-P3 无副作用核验

## 结论

`UNEXPECTED_LOCAL_GIT_TRACKING_REF_CHANGE_DETECTED_WITH_UNVERIFIED_ATTRIBUTION`

T03 执行完成，但验收为 `NOT_PASSED`。这不是单一 telemetry 缺口，而是三个必须同时保留的事实：

1. 审计窗口内确实发生了预期的审计支持代码、baseline metadata、governance/status append 和 Stage evidence 写入；因此 TaskPack T03 的字面“未改代码、metadata”条件不成立，即使这些写入都在受控 allowlist 内且不是产品运行副作用。
2. 审计开始前缺少 raw 递归指纹和持续历史进程监控，terminal finding 保持 `INSUFFICIENT_PREAUDIT_TELEMETRY`；当前点时证据不足以证明审计窗口内绝对无副作用。
3. `refs/remotes/origin/main` reflog 在 `2026-07-13T10:51:52+10:00` 记录 `fetch origin main: fast-forward`，本地 tracking ref 在 P3 窗口内由 `d6f379ad…` 变为 `d0a098b7…`。共享仓库下无法把这次 Git 写操作可靠归因给当前任务或并发进程，因此状态为 `UNVERIFIED_CONCURRENT_SHARED_REPOSITORY_CHANGE`，不能声称“本任务未 fetch”。

GitHub remote main 漂移与本地 tracking ref 变化均已披露；前者是外部状态，后者是本地 Git 状态变化且归因未验证。

## 已证明的事实

- v0.1.4 base 到 P3 前 HEAD 共 41 个 tracked 路径变化，全部属于预期审计/治理写入：
  - Stage artifacts 17
  - governance docs 12
  - audit metadata 3
  - audit validator/tests 4
  - 顶层交付记录 5
  - unexpected/product runtime/database 0
- App：13 files / 830331 bytes / aggregate SHA-256 `848521287dfaafd93f64872ce96cec6cc9996becddfc31df15ff8bbff8877779`，签名、0.1.4、build 20260713.4 与 P1 一致；未重装。
- raw root：device/inode/mode/size/mtime 的浅层 sentinel 与 P1 一致。
- 当前 KMFA App 常驻进程和监听均为 0。
- tracked 数据库变化为 0；未发现绑定 KMFA runtime database。
- ignored private runtime 至少有 16 项预期审计证据写入：P1-T01=5、P1-T02=10、one-shot launch receipt=1。
- GitHub remote main 与本地 `origin/main` tracking ref 均已从历史基线 `d6f379ad…` 移动到 `d0a098b7…`；reflog 证明发生过 fetch fast-forward，但归因未验证。当前 P3 结果未 push，最终合并前必须重新审查。

## P3 当前 29 个 tracked 路径

P3 本身当前有 29 个预期路径变化，不能被“unexpected=0”掩盖为“没有写入”：

- Stage artifacts：8，包括本报告、风险/测试报告和 4 个 machine evidence。
- governance docs：12，均为当前 Phase 的治理同步。
- audit metadata：2，包括新增 P3 baseline JSON 和 append `KMFA/metadata/stage_status.jsonl`。
- audit validator/tests：2，包括新增 P3 validator 和 focused test；它们是代码写入，但不是产品/runtime 源码。
- 顶层交付记录：5，包括 `CHANGELOG.md`、`HANDOFF.md`、功能清单、开发记录和模型参数文件。
- unexpected/product runtime/database：0。

因此 P3 的准确表述是“29 个预期审计/治理路径变化，0 个非预期路径变化”，不是“0 个路径变化”。

## 必须披露的预期变化

不能声称“零代码变化”或“metadata 未改”：

- P1/P2 新增了 2 个审计 validator 和 2 个测试。
- P1/P2 新增 2 个 audit baseline JSON，并 append stage status。
- P3 本身继续新增 1 个 validator、1 个 focused test、1 个 baseline JSON，并 append stage status；同时同步治理文件、中文入口和 Stage evidence。
- 上述均为执行 TaskPack 所需的受控审计写入，但仍属于真实发生的 code/metadata 变化，不能用“都是预期的”将其改写为“没有发生”。
- P1-T02 曾按计划 one-shot 启动 App；不能声称没有启动任何进程。

## 未证明的范围

- 审计开始前没有 raw 递归指纹，因此 `raw_recursive_integrity=UNVERIFIED`。
- 只有 one-shot receipt 和点时进程/监听快照，没有持续历史进程监控，状态为 `PARTIAL_RECEIPT_ONLY`。
- 外部数据库完整性为 `UNVERIFIED_OR_NOT_APPLICABLE`。
- remote main 漂移后的 KMFA 差异尚未在 P3 merge；本 Phase 不扩大到远端集成。本地 tracking ref 变化分类固定为 `CONCURRENT_SHARED_REPOSITORY_CHANGE_ATTRIBUTION_UNVERIFIED`。

因此不得使用 `NO_SIDE_EFFECTS_PROVEN`、`RAW_UNCHANGED_PROVEN`、`NO_PROCESS_STARTED`、`ZERO_CODE_CHANGES` 或 `ZERO_METADATA_CHANGES`。

## 后续处理

本负面结论必须进入 Stage 01 整体复审。复审必须同时保留“预期 code/metadata 写入已发生”“pre-audit telemetry 不足”“本地 tracking ref 变化且归因未验证”三项依据；不得只保留其中一项。不得在 P3 内补做产品实现，也不得通过当前点时快照反向伪造审计开始前的递归/持续监控证据。
