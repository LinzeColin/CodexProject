# PFI v0.2.5 Stage 5 整阶段独立审查

## 结论

`ACC-PFI-V025-STAGE5-WHOLE-REVIEW`：`accepted_for_transition`。

Stage 5 的 12 个 Task 已绑定到三笔线性 Phase 提交，并完成初审、最小整改、复审和明确验收。四项财务指标现在由同一真实只读 snapshot payload 提供给正式主页、消费页和报告页；浏览器在确认真实数值可见后先脱敏，再写截图、trace 与 a11y 证据。

验收结果为 `pass_with_explicit_blocked_models`：Stage 5 可进入 Stage 6，但缺参数、缺证据链或缺 OOS 验证的模型仍保持 blocked。Stage 6 尚未开始，Production Acceptance 尚未开始。

## 初审与整改

- 初审：Critical 1、Important 4、Minor 1。
- Critical：Phase 5.3 的 actual UI/report binding 为 false，正式三页面没有消费四项指标。
- 整改：新增私有运行时四指标 payload，接入 read-model 与 formal shell；真实金额不进入 tracked evidence。
- 截图复核补充发现：file protocol 的 service-worker 审计遮罩会挡住真实 UI。最终 harness 使用 ephemeral loopback 和隔离 profile 的空 service-worker/cache adapter，并断言 release identity ready、冲突层隐藏、app shell 可见。
- 复审：Critical 0、Important 0、Minor 0。

## 证据边界

- 真实数据：8,815 条输入，6,879 条 published，1,936 条 review，0 条 silent drop；只读。
- Surface：`homepage`、`consumption_page`、`report`；同一 payload hash。
- 四项指标：消费总流出、生活消费、投资资金流出、投资域内配置；tracked screenshot 中统一显示 `CNY 已脱敏`。
- Browser：实际 formal shell，ephemeral local loopback；无外部网络。
- 禁止动作：Finder、GitHub push、PFI.app install、数据库写入、Stage 6 实施均未发生。

## 最小范围例外

Roadmap 的 Stage 5 Allowed Files 没有列出 formal Web/read-model consumer，但 Acceptance 明确要求主页、消费页和报告实际展示四项指标。本 review 仅为满足该验收触及 `read_model_status.py`、`shell.js` 与 browser review harness，不扩展产品范围。

## 下一步边界

下一轮最多执行 Stage 6 Phase 6.1（`S6-P1-T1`–`S6-P1-T4`）。不得在本轮开始 Stage 6。
