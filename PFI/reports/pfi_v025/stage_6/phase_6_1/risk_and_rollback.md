# Phase 6.1 Risk and Rollback

## Risks

- 旧 v0.2.3/v0.2.4 tests 仍断言 `/home`、`/sources-upload`、旧 strategy-lab alias 与两套 desktop/mobile primary nodes；它们与 v0.2.5 Appendix A 冲突，作为 superseded non-gate signal 保留。
- Phase 6.1 只锁定导航 ownership 与 alias normalization，不证明页面内容唯一性、完整 history、键盘/a11y 或 no-JS 运行行为。
- release source hash 已更新，但本轮不安装 canonical App，也不 push；磁盘源码与已安装 App 的 parity 仍留到 Stage 12 final transaction。
- Stage 5 模型残余继续 blocked；导航通过不能提升财务数据、估值或 production readiness。

## Controls

- Python contract 同时审计 registry、alias matrix、HTML DOM 与 candidate boundary。
- desktop/mobile browser 使用相同正式 shell，逐个点击 10 个入口并验证 7 个 alias、single-active 与 release identity。
- 截图通过持续 redaction 处理；外部网络、Finder、数据库、真实财务数据、push 和 install 全部禁止。
- 治理明确把 Phase 6.2/6.3 与 whole-stage review 保持 `not_started`。

## Rollback

回滚只需 revert 本 Phase 本地提交，恢复 `routes.js`、`shell.js`、`index.html` 与 release manifest 的前一状态，并移除本 Phase 新增合同、测试、浏览器 harness、证据和治理事件。不得 reset/rewrite 历史，不触碰 Stage 5 evidence、数据库、真实来源、远端或已安装 App。
