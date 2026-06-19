# AGENTS.md

## Product truth

这是公开证据驱动、可递归聚焦的企业商业网络研究工具。v4.2 的批准 UI 是 Watchlist-first、visual-first、database-aware 和 model-transparent；不是行业卡片主页或 Agent 控制台。

## Read order

1. `GOVERNANCE_INDEX.md`
2. `CODEX_MASTER_TASK.md`
3. `FUNCTION_CATALOG.md`
4. `MODEL_MANAGEMENT.md`
5. `DOMAIN_DATA_CATALOG.md`
6. `DEVELOPMENT_STATUS.md`
7. `RISK_AND_ACCEPTANCE.md`
8. `docs/23-36`
9. contracts, catalogs and ledgers

## Mandatory governance

- 一次一个 Issue、一个目录、一个验收目标；先只读计划。
- 功能变更同步 function catalog、导航、任务、验收、风险和截图。
- 模型变更同步 model/formula/parameter 目录、配置、影响预览、版本、日志和回滚。
- 关系/公司/行业/供应链变化同步 taxonomy/catalog、来源和迁移规则。
- 规格完成、原型完成和生产实现必须分开报告。
- 每次提交运行 `python scripts/validate_task_pack.py`。

## UI invariants

- 默认进入 Watchlist 当前公司主图；首页可视化覆盖 >=90。
- 核心页面平均可视化覆盖 >=80；数据库、模型和治理页也必须可视化。
- 左上游、中主体、右下游；上资本/控制；下政策/风险。
- 选择只打开详情；明确操作才切换研究中心。
- 默认有图预算、渐进展开、语义缩放、等价列表和键盘路径。
- motion 使用统一 token 并尊重 reduced motion；触觉不是唯一反馈。

## Data/model invariants

证据、时间、金额、unknown、reported/derived/disputed/revoked 不得丢失。金额只在同语义、币种、期间下聚合。评分只用于研究排序，不是收益概率。模型版本不可变、可解释、可回滚；双周校准不自动激活。
