# Known gaps · ADP-S1-P03-T018

- **L2 深度层需模型、provisional 未生成**：按 Owner 2026-07-16 决策，L2 深度解释（区分事实/解释/推断）须模型生成，未接模型前 status=provisional_pending_model、text=null（不捧造）。board prompts 已备好；接入模型属后续（需模型路由/成本 Gate）。
- **render payload 未接入 worker 渲染**：本任务产出的是给 UI 的数据契约与样例，worker 尚未改为渲染 L0-L3（现仍显示英文摘要）；切换渲染属后续部署任务（须保六主题 + 部署验证 + 用 T017 defect baseline 做 before/after）。
- **英文标题仍显示为标题**：L1 的「标题」字段保留原标题（可能英文），因其是标题非「大段英文」；如需中文标题须模型翻译（同 L2，provisional）。
- **样本 200 条**：契约在 200 真实样本上验证；全量 682 可后续扩展。
- **provisional_machine**：L0/L1 事实层为确定性抽取，标 provisional 待 Owner 抽查。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
