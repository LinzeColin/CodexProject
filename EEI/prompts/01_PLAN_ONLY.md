# G0 - v4.2 只读计划：产品、模型、数据与开发治理

本阶段严格只读。不要全仓扫描，不要创建产品代码，不要修改目录、数据、配置或原型。

## 必读顺序

1. `AGENTS.md`、`CODEX_MASTER_TASK.md`、`GOVERNANCE_INDEX.md`。
2. 六份根目录治理文件：`FUNCTION_CATALOG.md`、`MODEL_MANAGEMENT.md`、`DOMAIN_DATA_CATALOG.md`、`DEVELOPMENT_STATUS.md`、`RISK_AND_ACCEPTANCE.md`、`GITHUB_REPOSITORY_BACKUP_INDEX.md`。
3. `docs/23_SYSTEM_FUNCTION_MODULE_ARCHITECTURE.md` 至 `docs/36_RELEASE_GATES_AND_DEFINITION_OF_DONE.md`。
4. 仅按本轮 Issue 读取 `data/content_inventory.csv` 指向的相关机器目录、`specs/` 合同、`config/` 配置及 `prototype/` 参考实现。

## 必须输出

1. **唯一工作单元**：本轮只处理一个 Issue、一个目录或一个最小跨目录切片、一个明确验收目标。
2. **现状差距**：分别报告规格、原型、生产实现和验证状态；不得把 fixture 原型写成已接入真实数据库。
3. **精确文件范围**：列出将读取、创建、修改和明确不修改的文件。
4. **追踪链**：Function ID -> Model/Formula/Parameter/Threshold ID -> Domain Catalog ID -> Task ID -> Acceptance ID -> Risk ID -> Gate。
5. **实现设计**：数据表/迁移、API/事件、计算与缓存、前端状态、视觉与交互、日志、错误与补偿机制。
6. **模型变更设计**：默认值、允许范围、缺失值语义、影响预览、不可变版本、原子激活、全局刷新、回滚和 14 天校准。
7. **测试命令**：单元、合同、集成、E2E、视觉、可访问性、性能、数据语义和失败模式；不得以“后续补测”替代 P0 验收。
8. **风险与停止条件**：列出触发器、预防/检测/补偿控制、回滚路径和本轮明确不解决的问题。
9. **Gate 计划**：一次只推进一个 Gate；完成后更新开发状态、验收证据和剩余风险。

## UI/UX 不变量

- 默认首页直接进入 Watchlist 当前公司的可视化商业版图；不得恢复行业卡片式首页。
- 首页可视化表面积目标 `>=90%`，核心系统页面平均 `>=80%`。
- 数据库、模型、功能结构和开发治理均须有正式导航和可视化工作台。
- 选择节点只打开详情；只有明确操作才切换研究中心。
- 图谱必须受节点/边预算约束，支持渐进展开、语义缩放、等价列表、键盘路径和 reduced motion。
