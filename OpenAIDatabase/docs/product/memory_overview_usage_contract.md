# Memory Atlas 记忆总览与系统使用说明合同

适用版本：Memory Atlas v1.1.6 Stage 1 Phase 1

状态：contract-only，本 phase 不修改运行时 UI、CSS、路由、数据生成、写回逻辑或长期记忆。

## 1. 目标

Stage 1 的目标是让用户打开 Memory Atlas 后先看懂系统当前状态、可采取动作和各入口用途。记忆总览不是欢迎页，也不是普通指标面板；它必须成为默认的操作中枢，回答：

1. 今天这套长期记忆系统处于什么状态。
2. 哪些主题、资产、机会或低价值循环最值得关注。
3. 下一步建议动作是什么，为什么值得做。
4. 记忆星系、记忆时间河、Inspector、Proposal、搜索和复盘分别用于什么场景。
5. 用户如何在不直接写长期记忆的前提下提出调整。

## 2. 输入边界

记忆总览只能消费 redacted derived data、Universe State Snapshot、共享状态层和本地公开配置。它不得读取或渲染：

- raw transcript。
- cookies、sessions、browser state。
- plaintext secrets、private keys、`.env`。
- 本地绝对私有路径。
- 未脱敏 GitHub 不应公开的数据。

所有调整入口必须保持 proposal-only。前端不得直接修改 active memory、偏好文件、GitHub 数据或长期记忆数据库。

## 3. 首页必备信息结构

记忆总览第一屏必须按“状态 -> 原因 -> 行动 -> 深入入口”的顺序组织。以下模块都必须可见或有清晰入口：

| 模块 | 必须回答的问题 | 默认层级 |
|---|---|---|
| 今日状态 | 今天整体记忆系统是否稳定、集中、分散、升温或需要复盘 | 首页主区 |
| Memory Weather | 当前认知天气是什么，主要驱动因素是什么 | 首页主区 |
| 建议动作 | 现在最应该继续、复盘、整合、探索或暂缓什么 | 首页主区 |
| 低价值循环 | 哪些重复消耗、冲突或低 ROI 模式正在形成黑洞 | 首页摘要 + Inspector |
| 新生机会 | 哪些 proto-star 机会、主题或项目值得验证 | 首页摘要 + Inspector |
| 层级资产摘要 | 核心画像、项目、决策、工作流、知识和机会的分布如何 | 首页摘要 |
| 主题分类摘要 | 当前主导主题、上升主题、衰退主题和置信度如何 | 首页摘要 |
| Mini 记忆星系 | 当前主题引力源、机会和风险的大致空间关系 | 首页视觉预览 |
| 记忆时间河脉冲 | 最近主题、决策和机会随时间如何变化 | 首页视觉预览 |
| 系统使用说明 | 用户接下来应该点哪里、如何判断和如何调整 | 首页辅助层 |

长解释不得塞进表格或卡片正文。超过两行的解释必须进入展开层、Inspector 或后续明细工作台。

## 4. 系统使用说明

系统使用说明必须短、可操作、中文可读，不能变成产品营销文案。它至少覆盖以下路径：

1. 打开系统后先读今日状态和 Memory Weather。
2. 查看建议动作，先处理高 ROI 且低 effort 的动作。
3. 展开层级资产摘要，判断核心画像、项目、决策、工作流、知识和机会是否失衡。
4. 展开主题分类摘要，判断主题增强、衰退、新增或低置信。
5. 点击建议动作进入 Inspector，看原因、证据、ROI、努力成本和下一步。
6. 跳到记忆星系，看该动作属于哪个主题引力源或机会云。
7. 跳到记忆时间河，看该动作如何随时间形成。
8. 判断系统建议不准时，通过 proposal-only 调整 importance、priority、topic 或 action status。
9. 进入搜索、复盘、总结与迭代时，把总览里的 focus、time range 和 source scope 带过去。

## 5. Presentation 与 Analysis 模式说明

记忆总览必须解释两种模式的用途，但不能把用户推入 debug UI：

| 模式 | 面向用户 | 必须显示 | 不应默认显示 |
|---|---|---|---|
| Presentation | 快速理解当前状态和行动 | 今日状态、天气、建议动作、摘要、视觉预览 | 内部字段名、公式长表、debug JSON |
| Analysis | 解释系统为什么这么判断 | 证据、公式摘要、参数、置信度、来源范围 | raw/private 文本、secret、不可公开路径 |

模式切换不得改变底层数据，不得自动写入 proposal，也不得清空用户当前选择。

## 6. Inspector 与 Proposal 说明

首页必须让用户理解 Inspector 和 Proposal 的边界：

- Inspector 用于解释原因、证据、公式、来源范围、更新时间和可审计引用。
- Proposal 用于提出调整建议，不直接写长期记忆。
- Proposal 必须显示 old value、proposed value、reason、parent snapshot、rollback hint。
- 任何 apply 都必须由 agent/human 在前端之外重新读库、冲突检查、写 history 并保留 rollback。

## 7. 与后续 Stage 的边界

本 phase 只建立 Stage 1 Phase 1 合同和验收。以下内容进入后续 phase 或 stage：

- Stage 2：建议动作、层级资产和主题分类的可展开明细工作台。
- Stage 3：proposal-only 调整工作区的字段、JSON schema 和安全验收。
- Stage 4：Search 2.0、复盘、总结与迭代工作流。
- Stage 5：Data Map 2.0 四层导图。
- 后续实现 phase：浏览器截图、Playwright、真实 UI 改造和视觉回归。

## 8. 验收

Stage 1 Phase 1 通过条件：

1. 合同明确记忆总览是默认系统入口，不是欢迎页或普通 dashboard。
2. 合同包含今日状态、Memory Weather、建议动作、低价值循环、新生机会、层级资产摘要、主题分类摘要、Mini 记忆星系和记忆时间河脉冲。
3. 合同解释系统使用路径、Presentation / Analysis 模式、Inspector 和 Proposal。
4. 合同明确 proposal-only，不直接写长期记忆。
5. 合同明确不读取 raw/private/cookie/session/secret 数据。
6. 验收文件提供可复查清单、失败条件和后续截图入口。
7. 记录文件登记目标、范围、风险、验收和回滚。

## 9. 回滚

删除本合同、对应验收文件、validator、package script 和记录增量即可回滚。本 phase 不改变运行时，因此不需要 UI 或数据回滚。
