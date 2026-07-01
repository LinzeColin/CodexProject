# PFI v0.2.4 Stage 9 Phase 9.3 Manual Acceptance

状态：等待用户验收。用户尚未确认交付冻结。

本清单只用于人工确认 v0.2.4 修补包是否可作为后续开发基线；不自动进入 Stage 9 whole-stage review，不自动上传 GitHub main，不自动进入未来版本。

## 请人工确认

- [ ] PFI 当前正式一级入口仍为 10 个正式一级入口：首页总览、账户与资产、账本流水、投资管理、消费管理、数据源与上传、建议与复盘、报告与洞察、市场与研究、设置。
- [ ] app/浏览器 E2E 证据可接受：Stage 8.1 自动验收、Stage 8.2 截图验收、Stage 8.3 人工验收来源、Stage 8 whole-stage review 与 Stage 8 GitHub main upload 已形成证据链。
- [ ] 回归防线可接受：Stage 9.1 覆盖旧 UI、假零、入口堆叠、mock/sample/demo/synthetic/fixture/fake 财务数据、机械文案和暗色控制台默认风格。
- [ ] 交付冻结候选可接受：Stage 9.2 `final_evidence_index.json`、`closeout_candidate.md`、terminal 和截图索引可审计。
- [ ] README 没有声明验收通过；当前状态是等待用户验收。
- [ ] 未加载、缺失、过期、解析失败或权限失败的数据不会用财务 0 冒充真实结果。
- [ ] 正式财务指标、报告、图表、首页、投资、消费、资产、现金流验收没有使用 mock/sample/demo/synthetic/fixture/fake 数据。
- [ ] 历史 9 入口约束、禁止市场与研究一级入口、暗色 AI 控制台方向均未恢复为正式要求。
- [ ] app bundle、launcher C/Info.plist 和真实财务数据未在本 phase 被修改。
- [ ] 不自动进入未来版本；后续只能在用户明确验收或明确指令后继续。

## 当前停止点

- Phase 9.3 验收材料已准备。
- 用户确认结果：等待用户回复。
- Stage 9 whole-stage review：未开始。
- Stage 9 GitHub main upload：未执行。
- 未来版本开发：未开始。
