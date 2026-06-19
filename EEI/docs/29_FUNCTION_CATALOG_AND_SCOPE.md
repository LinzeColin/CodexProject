# 29 - 功能清单、导航板块与系统范围

## 结论

`data/function_catalog.csv` 是功能单一事实来源。系统当前定义 **17 个正式功能板块**；每个板块都明确用户问题、主可视化、输入、输出、操作、领域对象、数据表、API、任务、验收和风险。规格完成、原型完成与生产实现必须分别记录。

## 功能总表

| ID | 导航组 | 功能板块 | 优先级 | 规格 | 原型 | 生产实现 |
|---|---|---|---|---|---|---|
| FUN-EXP-01 | 探索 | 商业版图 | P0 | DONE | DONE | NOT_STARTED |
| FUN-EXP-02 | 探索 | 全链供应链 | P0 | DONE | DONE | NOT_STARTED |
| FUN-EXP-03 | 探索 | 集团业务与子板块 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-EXP-04 | 探索 | 资金与并购 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-EXP-05 | 探索 | 所有权与控制 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-EXP-06 | 探索 | 政策与政府 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-EXP-07 | 探索 | 战略信号 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-EXP-08 | 探索 | 行业地图 | P1 | DONE | PARTIAL | NOT_STARTED |
| FUN-RM-01 | 研究管理 | Watchlist | P0 | DONE | DONE | NOT_STARTED |
| FUN-RM-02 | 研究管理 | 重要变化 | P0 | DONE | PARTIAL | NOT_STARTED |
| FUN-RM-03 | 研究管理 | 已保存视图 | P0 | DONE | DONE | NOT_STARTED |
| FUN-DM-01 | 数据与模型 | 数据库与来源 | P0 | DONE | DONE | NOT_STARTED |
| FUN-DM-02 | 数据与模型 | 模型与参数 | P0 | DONE | DONE | NOT_STARTED |
| FUN-DM-03 | 数据与模型 | 操作日志 | P0 | DONE | DONE | NOT_STARTED |
| FUN-DM-04 | 数据与模型 | 双周校准 | P1 | DONE | PARTIAL | NOT_STARTED |
| FUN-SYS-01 | 系统治理 | 功能结构 | P0 | DONE | DONE | NOT_STARTED |
| FUN-SYS-02 | 系统治理 | 开发治理 | P0 | DONE | DONE | NOT_STARTED |

## 正式导航

- **研究**：商业版图、全链供应链、集团业务与子板块、资金与并购、所有权与控制、政策与政府、战略信号、行业地图。
- **研究管理**：Watchlist、重要变化、已保存视图。
- **数据与模型**：数据库与来源、模型与参数、操作日志、双周校准。
- **系统治理**：功能结构、开发治理。

首页默认打开 Watchlist 当前公司的商业版图。所有板块共享主体、时间、数据快照、模型版本、筛选、探索路径和选中对象。

## 生产完成定义

P0 功能只有在主可视化、等价列表、数据/API、空/加载/冲突/错误状态、键盘路径、性能预算、测试证据、风险控制和回滚全部通过后，才可标记 `DONE`。
