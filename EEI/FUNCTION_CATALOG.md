# 系统功能清单与导航架构

系统共有 **17 个正式功能板块**。默认进入 Watchlist 当前公司的商业版图；模型、数据库、对象范围、功能结构和开发治理均为正式导航能力。

v5 同步后，生产阻塞任务 T1300-T1309 已写入 `data/function_catalog.csv` 的相关功能映射。重点影响：商业版图/供应链/集团结构需要真实数据与生产 API；数据中心需要 PostgreSQL 迁移、真实采集和调度；模型中心需要事务性激活与原子刷新；已保存视图需要服务端冲突控制；系统治理需要规模、soak 和品牌清权证据。

| ID | 导航 | 功能 | 默认可视化 | 优先级 | 规格 | 原型 | 生产实现 |
|---|---|---|---|---|---|---|---|
| FUN-EXP-01 | 探索 | 商业版图 | 多层关系网络 + 语义缩放 + 时间变化 | P0 | DONE | DONE | NOT_STARTED |
| FUN-EXP-02 | 探索 | 全链供应链 | 分阶段流图 + Sankey + 关键路径 | P0 | DONE | DONE | NOT_STARTED |
| FUN-EXP-03 | 探索 | 集团业务与子板块 | 分层树图 + 组合矩阵 + 地域分布 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-EXP-04 | 探索 | 资金与并购 | 资金流 Sankey + 交易网络 + 时间轴 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-EXP-05 | 探索 | 所有权与控制 | 控制树 + 经济/投票双轴 + 穿透路径 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-EXP-06 | 探索 | 政策与政府 | 政策雷达 + 地域热图 + 合同/补贴流 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-EXP-07 | 探索 | 战略信号 | 信号轨迹 + 主题动量 + 反证面板 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-EXP-08 | 探索 | 行业地图 | 行业价值链地图 + 集中度矩阵 | P1 | DONE | PARTIAL | NOT_STARTED |
| FUN-RM-01 | 研究管理 | Watchlist | 对象列表 + 变化气泡 + 优先级条 | P0 | DONE | DONE | NOT_STARTED |
| FUN-RM-02 | 研究管理 | 重要变化 | 变化时间轴 + 前后差异图 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-RM-03 | 研究管理 | 已保存视图 | 场景缩略图 + 探索路径 | P0 | DONE | DONE | NOT_STARTED |
| FUN-DM-01 | 数据与模型 | 数据库与来源 | ERD + 数据血缘 + 来源健康矩阵 + 表详情 | P0 | DONE | DONE | NOT_STARTED |
| FUN-DM-02 | 数据与模型 | 模型与参数 | 公式图 + 权重图 + 阈值仪表 + 影响预览 | P0 | DONE | DONE | NOT_STARTED |
| FUN-DM-03 | 数据与模型 | 操作日志 | 审计时间轴 + 前后 diff + 影响范围 | P0 | DONE | DONE | NOT_STARTED |
| FUN-DM-04 | 数据与模型 | 双周校准 | 漂移雷达 + Top-N 稳定矩阵 + 建议 diff | P1 | DONE | PARTIAL | NOT_STARTED |
| FUN-SYS-01 | 系统治理 | 功能结构 | 四层架构图 + 功能矩阵 + 依赖流 | P0 | DONE | DONE | NOT_STARTED |
| FUN-SYS-02 | 系统治理 | 开发治理 | 状态看板 + 追踪链 + 风险矩阵 + 门禁进度 | P0 | DONE | DONE | NOT_STARTED |

完整输入输出、对象、表/API、任务、验收和风险见 `data/function_catalog.csv`。
