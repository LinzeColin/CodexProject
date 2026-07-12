# S11-P3 风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 历史 12 pending 回流 | 当前 S09/S10/S11-P2 状态覆盖，历史动态值禁止复用 | controlled |
| 把全局差异平均分到四个项目 | 项目级计数保持 null，页面明确未公开归属 | controlled |
| 受限预览被误认为正式报告 | D级、NO_GO 和内部复核限制在页面及 iframe 外持续显示 | controlled |
| raw/private/secret 泄漏 | public-safe validator、Git ignore 和候选提交扫描阻断 | controlled |
| 历史 phase validator 比较全局最新状态后报 drift | 当前 phase 依赖冻结 public-safe manifest；Stage 11 整体复审单独修复跨 phase 时态耦合 | open_for_stage_review |
