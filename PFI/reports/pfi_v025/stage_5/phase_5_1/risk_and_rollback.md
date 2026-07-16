# Phase 5.1 风险与回滚

- 活动公式版本内容若改变，历史报告可能无法重放；runtime 对 same-version mutation fail closed，变更只能发布新 version。
- AUD/CNY 若倒置会造成金额方向错误；只接受 `AUD_TO_CNY` 与 `CNY/AUD`，不自动取倒数。
- `4.81` 是单元测试示例，生产默认固定为 `null`；真实 production FX 仍 not_loaded。
- 记录分类 100 分不得掩盖 coverage、reconciliation、valuation、model validation 或 report completeness；六维 schema 禁止额外 overall score。
- Phase 5.2/5.3 与 whole-stage review 未执行，不能将本 Phase 写成 Stage 5 pass 或 production acceptance。
- 回滚：revert 本 Phase 本地原子提交；不涉及 raw、ledger、SQLite、真实财务行、网络、GitHub push 或 PFI.app 安装。
