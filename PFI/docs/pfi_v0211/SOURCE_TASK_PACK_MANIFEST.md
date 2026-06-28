# PFI v0.2.1.1 来源资料清单

更新时间：2026-06-29

本文件用于 Stage 0 准备轮。它只记录 v0.2.1.1 Product UI Recovery 的输入资料，不声明前端已重建。

| 来源 | 路径 | 用途 | Stage 0 结论 |
| --- | --- | --- | --- |
| 用户 RTF 纠偏稿 | `/Users/linzezhang/Downloads/v0.2.1.1.rtf` | 最新产品判断、失败原因、反 AI 演示壳要求、正常财务软件路径 | 作为 v0.2.1.1 的最新用户口径 |
| Markdown Task Pack/Roadmap | `/Users/linzezhang/Downloads/pfi_v0.2.1_controlled_ui_rebuild_task_pack_roadmap.md` | 受控重构范围、禁止项、验收条件、第一关提示词 | 作为验收清单和禁止事项来源 |

## 已识别冲突

| 冲突 | Markdown | RTF | Stage 0 默认处理 |
| --- | --- | --- | --- |
| 正式主导航数量 | 9 个入口，不含市场与研究 | 10 个入口，包含市场与研究 | 后续 Stage 1 默认按 RTF 最新稿执行 10 个入口；如用户要求 9 个，Stage 1 前更新合同 |
| 策略实验室归属 | 投资管理 > 策略实验室 | 市场与研究 > 策略实验室 | 后续 Stage 1 默认按 RTF 最新稿执行，旧入口只做跳转别名，不生成第二个页面 |
| 执行层级 | Phase - Stage - Task | 用户明确说 Stage/Phase 母子关系搞反 | v0.2.1.1 以 Stage 为每轮 pursuing goal 的顶层 run gate |
| 图表与持久化顺序 | 图表在持久化前 | 先真实操作和持久化，最后图表 | 后续按用户最新纠偏：操作流 -> 持久化 -> 图表与最终验收 |

## Stage 0 禁做

- 不修改 `PFI/web/index.html`。
- 不修改 `PFI/web/app/shell.js`。
- 不修改 `PFI/src/pfi_os/app/streamlit_app.py`。
- 不刷新 app 入口。
- 不声明 v0.2.1.1 已完成。
- 不提前执行 Stage 1-5。
