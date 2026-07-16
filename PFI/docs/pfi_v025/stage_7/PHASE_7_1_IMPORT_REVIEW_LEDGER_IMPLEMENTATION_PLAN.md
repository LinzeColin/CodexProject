# v0.2.5 Stage 7 Phase 7.1：上传、复核与统一账本

## 执行合同

- 唯一范围：`S7-P1-T1..T4`。
- 唯一 Acceptance：`ACC-PFI-V025-S7-P71-IMPORT-REVIEW-LEDGER`（项目治理分配；源 Roadmap/Task Pack 未提供 Phase 级 ACC-*）。
- 目标：真实 CSV/ZIP 字节上传后完成来源/hash/parser 识别、真实解析预览、原子确认入账、可撤销复核、幂等、补偿回滚与重试。
- 非范围：Phase 7.2 持仓/设置持久化、Phase 7.3 参数中心/Interconnection/指标下钻、Stage 7 整阶段审查、push、App install、production/final acceptance。

## 实现

正式 Shell 只保留一条流程：文件选择调用 preview API；preview 只写隔离 private raw store 与 staged rows，统一账本保持为 0；用户点击确认后，SQLite `BEGIN IMMEDIATE` transaction 才写 `ledger_entries` 与 `import_review_queue`。复核决定和撤销均调用本机 API 持久化，不使用 localStorage/sessionStorage/IndexedDB 代替数据库。

新增 additive migration 管理 `import_batches`、`import_files`、`import_staged_transactions`、`ledger_entries`、`import_review_queue` 与 `import_audit_events`。批次 fingerprint 和唯一约束防止重复导入；回滚删除该批账本/复核写入但保留 staged/raw hash，重试从私有 raw store 重新解析。

## 真实源与隐私边界

真实支付宝 CSV/ZIP 只读源复制到 `/tmp` 后执行。canonical 文件前后 SHA-256 一致；SQLite 与 private raw store 也只存在于 `/tmp`。tracked evidence 只保留 hash、字节数、记录数、日期范围、状态和脱敏截图，不保留原始字节、交易对方、说明或金额。包含真实上传请求正文的 raw Playwright trace 明确不持久化，改存 sanitized trace metadata。

## 验证结果

- 聚焦合同：`6 passed`。
- 正式 Shell cached Playwright/local Chrome：20 项检查全部通过；console/page/HTTP/external-network errors=0。
- 真实源：1571 条标准流水、74 条待复核；preview ledger=0，confirm ledger=1571。
- 人工复核保存后 pending 减 1，撤销后恢复；重复上传仍为 1571；回滚为 0；重试预览后再确认恢复 1571。
- 失败 CSV：`status=failed`、transaction=0、该失败批 ledger=0；既有已确认账本不变。
- SQLite：`PRAGMA foreign_key_check` 无问题，`integrity_check=ok`。
- Release/Stage 6 Python 回归：60 passed；Stage 1 Node identity/cache：28 passed。

## 风险、回滚与停止条件

风险集中在真实字节泄漏、非原子写入、重复账本、失败伪预览和旧 MetaDatabase 写路径。回滚方式是 revert 本 Phase commit；additive migration 不删除历史表，批次补偿 API 可按 batch 撤销账本写入。任何 canonical 财务源写入、外网请求、证据出现私有值、preview 阶段账本非 0、重复导入增加 ledger、FK/integrity 失败或进入 Phase 7.2 都必须停止。

## 当前结论

`ACC-PFI-V025-S7-P71-IMPORT-REVIEW-LEDGER` 为 `candidate_pass`。v0.2.5 进度 `88/156 = 56.41%`；Stage 7 为 `in_progress`，Phase 7.2/7.3 和 whole-stage review 均 `not_started`。
