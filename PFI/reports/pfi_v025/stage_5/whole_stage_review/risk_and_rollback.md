# PFI v0.2.5 Stage 5 整阶段审查风险与回滚

- 唯一验收：`ACC-PFI-V025-STAGE5-WHOLE-REVIEW`。
- 风险等级：`T3_FINANCIAL_MODEL_UI_REPORT_PRIVACY`。
- 真实财务数据仅只读重放；四项金额只存在于内存和临时 browser document，tracked evidence 全部脱敏。
- `FORM-PFI-016`、`FORM-PFI-017`、`FORM-PFI-018`、`FORM-PFI-020` 中缺参数、缺证据链或缺 OOS 验证的输出继续 blocked，不以 Stage 5 整阶段通过替代模型验证。
- 浏览器验证仅使用 ephemeral local loopback；没有外部网络、Finder、push、App install 或 Stage 6 工作。

回滚：仅回滚本次 Stage 5 whole-review 本地提交；恢复 `read_model_status.py` 与 `shell.js` 到 `ec3e3af020cc37f5bddd39dba2e445895e015f9e`，并删除本 review 目录和对应治理增量。三笔 Phase 5.1–5.3 历史提交保持不变。
