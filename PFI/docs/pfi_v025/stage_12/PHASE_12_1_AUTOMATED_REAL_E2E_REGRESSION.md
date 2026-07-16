# PFI v0.2.5 Stage 12 Phase 12.1：自动化真实 E2E 与回归

## 唯一目标

对当前 v0.2.5 candidate 执行 release identity、真实数据、正式 Web Shell、路由、报告、accessibility、performance 与 visual regression；关闭所有 P0/P1 后停在 Phase 12.2 之前。

## Acceptance target

- Acceptance ID：`ACC-PFI-V025-S12-P121-AUTOMATED-REAL-E2E`
- Tasks：`S12-P1-T1`、`S12-P1-T2`、`S12-P1-T3`、`S12-P1-T4`
- 结果上限：`candidate_pass`
- 仍需：Stage 12 后续 Phase、整阶段 review 与最终绑定 release 的人类验收

## 真实数据边界

- 交易输入直接读取当前 Git commit 中 4 个 immutable Alipay raw CSV objects；复制到临时 0600 snapshots 后走正式 upload/import/review/ledger service。
- canonical source、canonical operational SQLite 均不写；E2E 数据库只存在于临时 0700 root，并在 run 结束删除。
- `SRC-HOLDINGS` 当前为 `not_loaded`。持仓真实流程必须记录为 `not_run`，仅“正确阻断且无假零”门禁可以通过；不得使用 sentinel、mock、sample、demo、synthetic、fixture 或 fallback 冒充真实持仓。
- Evidence 只保留 hash、计数、状态、覆盖和门禁结果；trace 移除 resource bodies、request bodies、token、绝对路径和财务文本，截图在写入前脱敏。

## 自动化矩阵

1. 四方 release identity 与 frontend/backend asset hash 一致。
2. 4 个真实 Git objects → preview → confirm → idempotent replay → isolated SQLite integrity/FK。
3. 持仓缺源 truthful block；5 份报告保持 3 blocked / 2 partial，且不显示财务假零。
4. 10 个 canonical 一级路由与 10 个差异化二级页；旧 alias 不进入一级导航或 AX tree。
5. 当前内容 20 routes 的 deterministic WCAG 2.2 AA、keyboard、Chrome CDP AX 与 40 screenshots visual regression。
6. release identity/data/route/workflow/quality/report/resilience focused pytest matrix。

## 已关闭回归

真实 GB18030 CSV 的固定 64 KiB probe 可能在末尾切断多字节字符。旧实现对该 incomplete suffix 进行 final strict decode，导致 4 个真实 objects 中 2 个被误判为 `unsupported_source`。修复使用 strict incremental decoder：错误字节仍 fail closed，边界 incomplete suffix 仅被 decoder 缓冲。Stage 12 回归测试直接读取全部 4 个 Git objects 锁定此行为。

首次 post-evidence 自检还发现 scanner 输出字段名 `account_identifiers=0` 会被自身的敏感标识符正则命中。该项不代表真实泄露，但会形成错误的封装通过；字段已改为不自触发的 `sensitive_identifier_findings=0`，并由最终 evidence self-scan 回归锁定。

## 历史测试处置

6 个旧测试把 Stage 2/3 当时的 progress、Phase 3.1/3.2 current status、next gate、HEAD 或外部私有环境精确快照当作永久当前事实。它们已被 immutable historical Evidence 哈希绑定，不能通过改写旧 Evidence“修绿”。Phase 12 将其列为非发布阻断的 P2 test debt，并用当前 inventory safety、immutable artifact consistency、canonical governance 与 current release gates 取代；不把这 6 项诊断失败解释成产品 P0/P1。

## 明确不做

- 不进入 Phase 12.2；不进行 Finder、LaunchServices 或任何 GUI 文件操作。
- 不安装或替换 `PFI.app`，不做目标 Mac lifecycle、sleep/wake、disk pressure 或人类 UAT。
- 不进入 Phase 12.3，不统一最终 VERSION/README/HANDOFF，不生成最终 human acceptance，不冻结 release。
- 不 push，不声明 production accepted / final human acceptance，不开始 v0.2.6。

## Rollback

回滚 bounded import-probe 修复与对应 release identity hash 同步；删除本 Phase 新增 harness、测试和 Evidence。临时 source snapshots 与 isolated SQLite 由 harness 自动删除，不涉及 canonical 数据恢复。
