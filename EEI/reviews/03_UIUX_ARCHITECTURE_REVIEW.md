# 独立审查 C：页面、UI、交互、功能连接与架构

> 审查口径：本文件由一个独立审查单元形成，不引用其他审查单元的结论作为证据。严重度按 CRITICAL/HIGH/MEDIUM/LOW；“阻塞合并”区分本 Task Pack 基线与未来生产发布。

## 结论

首页的 visual-first 方向正确，但原包仍存在“像生产数据库、实际是 fixture”的认知错位，且多个控件仅显示 toast。v5 先修复品牌、真实性和数据集隔离，保留简洁商务工作台；生产阶段必须以真实 WorkspaceContext、路由、查询和证据状态替换演示联动。

## 推荐界面架构

```text
全局 Shell
├─ Watchlist / 行业 / 搜索 / 最近路径
├─ WorkspaceContext（主体、时间、筛选、模型版本、数据快照）
├─ 主画布（商业全景 / 供应链 / 资本 / 控制 / 政策 / 变化）
├─ 证据与对象详情抽屉
├─ 数据资产与血缘工作台
├─ 模型/公式/参数/阈值中心
└─ 运行、审计、开发状态与治理
```

## 发现明细

| ID | 严重度 | 状态 | 发现 | 是否阻塞生产 | 建议/处理 |
|---|---|---|---|---|---|
| UX-001 | HIGH | FIXED_IN_V5 | Atlas 与同类供应链平台直接冲突且品牌未清权 | YES | 统一中性工作名和“品牌待定”，加入品牌 Gate |
| UX-002 | HIGH | FIXED_IN_V5 | 数据库与运行页视觉上像生产系统，但没有生产底座 | YES | 所有指标标注 fixture/设计态/生产待实现 |
| UX-003 | MEDIUM | OPEN_PRODUCTION | 若干导航别名聚合到同一页面，用户会误认为独立功能已实现 | YES | 生产版使用真实路由；未实现入口禁用或标注“规划中” |
| UX-004 | MEDIUM | PARTIAL_V5 | 已有 hover/选中/过渡/触觉，但缺少全链路 loading/error/empty/partial 状态系统 | YES | 建立统一 async state、toast/inline error、skeleton、retry、undo tokens |
| UX-005 | MEDIUM | PARTIAL_V5 | 计时器动画已防竞态并尊重 reduced motion，但尚无真实图布局连续性与性能预算 | YES | 主体切换使用 shared-position/FLIP，动效 120–280ms，支持中断 |
| UX-006 | LOW | PARTIAL_V5 | Vibration API 支持有限，桌面端不能依赖“触觉” | NO | 视觉、声音可选、触觉仅增强；不得作为唯一反馈 |
| UX-007 | MEDIUM | OPEN_PRODUCTION | 模型/数据/治理页信息密度高，缺少用户任务优先级和渐进披露实测 | YES | 首屏保留决策信息；高级字段抽屉/二级页；可保存布局 |
| UX-008 | HIGH | OPEN_PRODUCTION | 真实大图下固定坐标和首屏覆盖指标可能形成“毛线团”或被装饰性元素游戏化 | YES | 服务器子图、关系预算、聚合节点、语义缩放、等价列表 |
| UX-009 | HIGH | OPEN_PRODUCTION | 筛选、深度、地区、比较、固定、展开等控件多为 toast-only | YES | 实现真实状态/查询/API；未完成前禁用并标注 |
| UX-010 | HIGH | OPEN_PRODUCTION | 原型的关系证据摘要仍是 fixture，缺少原文片段、冲突证据和来源版本 | YES | 证据抽屉包含来源、片段、时间、解析器、置信度、反证和审核状态 |
| UX-011 | HIGH | OPEN_PRODUCTION | UI 状态、图查询、模型配置、数据版本尚未形成单一上下文契约 | YES | 定义 WorkspaceContext: focus/filter/time/config/data snapshot/path |
| UX-012 | MEDIUM | OPEN_PRODUCTION | 单文件原型不可直接作为生产组件架构 | YES | 拆分 shell、graph、inspector、model center、data workbench、state/query 层 |
| BRAND-001 | HIGH | FIXED_IN_V5 | 命名研究此前缺乏同类成熟产品对照和法律 Gate | YES | 新增 49 个代表性产品矩阵、冲突登记、品牌策略和验证脚本 |

## 合并判断

- **v5 规格/原型：可合并**，因为品牌和 fixture 真相已明确。
- **产品功能合并：逐 Issue 判定**。任何 toast-only 控件不得计入“已实现”；任何页面必须有 loading/error/empty/partial/success 状态和可回退路径。
