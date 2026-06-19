# Task Pack 最终验证报告

**基线版本**：v4.2.0  
**基线日期**：2026-06-19  
**发布判定**：`READY FOR CODEX G0 READ-ONLY PLAN`  
**产品真实性边界**：本报告验证需求、治理目录、机器契约、高保真 fixture 原型、PDF、GitHub 模板、自动校验和 ZIP 完整性；**不代表生产数据库、真实企业关系、真实资金流、生产评分服务、实时更新或投资预测已经实现**。

## 1. 最终交付基线

| 治理对象 | 数量 | 人类可读入口 | 机器单一事实来源 |
|---|---:|---|---|
| 功能板块 | 17 | `FUNCTION_CATALOG.md` | `data/function_catalog.csv` |
| 模型 / 公式 | 11 / 11 | `MODEL_MANAGEMENT.md` | `data/model_registry.csv`、`data/formula_registry.csv` |
| 参数 / 阈值 | 60 / 17 | `docs/24_MODEL_FORMULA_PARAMETER_THRESHOLD_CENTER.md` | `data/parameter_catalog.csv`、`data/threshold_registry.csv` |
| 关系家族 / 关系类型 | 10 / 52 | `DOMAIN_DATA_CATALOG.md` | `data/relationship_family_catalog.csv`、`data/relationship_taxonomy.csv` |
| 供应链阶段 / 上下游角色 | 16 / 24 | `docs/17_SUPPLY_CHAIN_RESEARCH_AND_EXPANSION_RULES.md` | 对应 taxonomy/catalog CSV |
| 行业 / 用户入口板块 | 26 / 13 | `docs/35_DATA_CATALOGS_AND_TAXONOMIES.md` | `data/industry_taxonomy.csv`、`data/sector_taxonomy.csv` |
| 业务板块 / 资本对象 / 领域对象 | 20 / 30 / 32 | `docs/31_DOMAIN_OBJECT_SCOPE_CATALOG.md` | 对应 taxonomy/catalog CSV |
| 公司与外部研究对象 | 140 | `docs/12_RESEARCH_UNIVERSE_SOURCE_METRICS_SCREENING.md` | `data/company_catalog.csv`、`data/research_universe.csv` |
| 来源类别 / 指标 | 34 / 54 | `docs/05_DATA_SOURCES_AND_PROVENANCE.md` | `data/source_registry_extended.csv`、`data/metric_catalog.csv` |
| 开发任务 / 验收标准 | 120 / 200 | `DEVELOPMENT_STATUS.md` | `data/task_backlog.csv`、`data/acceptance_matrix.csv` |
| 风险 / 发布 Gate | 53 / 10 | `RISK_AND_ACCEPTANCE.md` | `data/risk_register.csv`、`data/release_gate_catalog.csv` |
| 验收追踪关系 | 212 | `docs/33_RISK_CONTROL_ACCEPTANCE_TRACEABILITY.md` | `data/acceptance_traceability.csv` |

`GOVERNANCE_INDEX.md` 提供用户要求到 Markdown、CSV/JSON/YAML 与 GitHub 变更入口的完整映射。

## 2. 静态目录、模型和契约验证

| 检查 | 结果 | 说明 |
|---|---|---|
| 目录数量与 ID 唯一性 | PASS | 功能、模型、公式、参数、阈值、关系、行业、任务、验收和风险均符合基线数量 |
| 交叉引用 | PASS | 模型→公式、阈值→参数、任务→依赖/验收、P0 功能→验收追踪均有效 |
| 高风险治理 | PASS | High/Critical 风险均具有 control、trigger、owner 与 release gate |
| 权重约束 | PASS | 默认顶层权重总和为 `1.0 ± 0.0001` |
| JSON / YAML | PASS | 模型注册表、公式注册表、配置、Issue Forms 与 GitHub Workflow 可解析 |
| SQL / OpenAPI / Schema | PASS | 数据模型与 API/事件/配置契约已纳入 Task Pack |
| JavaScript / shell | PASS | `prototype/app.js` 与执行脚本语法通过 |
| 原型双入口一致性 | PASS | `prototype/index.html` 与 `prototype/standalone.html` 字节一致 |
| PDF 结构 | PASS | 16 页、A4 横向、未加密 |

最终执行命令：

```bash
python scripts/compile_model_runtime_defaults.py --dry-run
python scripts/validate_catalog_integrity.py
python scripts/validate_governance.py
python scripts/validate_task_pack.py
node --check prototype/app.js
bash -n scripts/preflight.sh scripts/run_codex_autonomous.sh
```

原始证据：`artifacts/static_validation.txt`。

## 3. 浏览器交互冒烟测试

使用 Chromium、Playwright、1440×900 视口和离线 `set_content()` 验证：

- 默认进入 Watchlist-first 商业版图，默认主体为 NVIDIA。
- 图谱节点、关系与 fixture 声明正常显示。
- 单击 TSMC 打开详情抽屉；选择“以它为中心”后递归重绘为 TSMC 主体。
- 数据资产、模型与参数、对象与范围、开发状态、开发治理等导航可达。
- 修改模型参数并保持权重总和后，可提交变更原因、显示全局刷新进度、生成新模型版本并进入“已生效”状态。
- 页面异常 `0`；控制台 warning/error `0`。

原始证据：`artifacts/prototype_smoke_test.txt`。视觉回归截图位于 `prototype/screenshots/`。

## 4. 可视化覆盖自动验收

在 1440×900、1280×800、1024×768 三种视口下运行：

```bash
python scripts/validate_visual_coverage.py
```

| 指标 | 门槛 | 结果 |
|---|---:|---:|
| 首页可视化覆盖 | `>= 0.90` | `1.000` |
| 核心系统平均可视化覆盖 | `>= 0.80` | `1.000` |
| 页面 / 控制台错误 | `0` | `0` |

该结果衡量已标记的信息工作区和可视化表面在有效内容区域中的覆盖，不等同于真实用户可用性研究、生产性能或图谱大数据量压力测试。真实可用性、动效流畅度、触觉适配、可访问性与性能仍须在生产 Build/QA 阶段按 `docs/22_...`、`docs/27_...` 和 `docs/28_...` 完成。

原始证据：`artifacts/visual_coverage_validation.txt`。

## 5. PDF 质量验证

- 文件：`US_Corporate_Power_Map_Governance_Blueprint_v4.2.pdf`
- 规格：16 页，A4 横向，未加密。
- 16/16 页以 130 DPI 成功渲染。
- 已检查完整联系表和重点页面：系统架构、默认可视化工作台、数据库/数据血缘、模型参数中心、公式阈值、任务状态、风险 Gate 和 GitHub 治理。
- 未观察到标题截断、正文重叠、乱码、意外空白页、黑色渲染块、卡片越界或页脚冲突。
- 可复现 HTML 源保存在 `artifacts/governance_blueprint_v42_source.html`；生成脚本为 `scripts/generate_governance_pdf.py`。

原始证据：`artifacts/pdf_contact_sheet.png`、`artifacts/pdf_visual_inspection.txt`。

## 6. GitHub 开发治理与备份验证

已包含：

- `CODEOWNERS`、PR 模板、Feature / Model Change / Data Scope / Relationship / Risk / Bug Issue Forms。
- `governance-validation` 工作流：校验目录数量、ID、引用、模型配置、JSON/YAML、PDF、shell、checksums 与多视口视觉覆盖。
- `data/github_document_registry.csv`：对仓库文件进行分类、标记 canonical 状态、变更触发器、owner 和备份策略。
- 三层一致性规则：人类可读 Markdown、机器可读 CSV/JSON/YAML、GitHub 自动校验必须同步。

任一功能、模型、关系类型、行业/板块、公司范围、任务状态、风险或验收发生变化，都必须通过同一 PR 更新相关目录；否则校验失败。

## 7. ZIP 与干净环境复验

最终 ZIP 已执行：

- ZIP 结构完整性测试；
- 解压到全新目录后的 catalog、governance、Task Pack 验证；
- 原型双入口一致性检查；
- `CHECKSUMS.sha256` 全文件校验；
- 干净目录中的浏览器视觉覆盖复验。

判定：`PASS`。目录树见 `DIRECTORY_TREE.txt`，纯路径清单见 `manifest.txt`，文件校验见 `CHECKSUMS.sha256`。

## 8. 执行主机前置条件

`bash scripts/preflight.sh` 返回成功，但当前打包主机提示：Codex CLI、Docker/Compose 与 pnpm 未安装，且目录尚未初始化为 Git 仓库。这些是后续 Build/Release 的执行环境前置条件，不是 Task Pack 文件缺陷。

建议顺序：

```bash
git init
git add .
git commit -m "chore: add Atlas v4.2 governance baseline"

bash scripts/preflight.sh
codex exec --sandbox read-only - \
  < prompts/01_PLAN_ONLY.md \
  | tee artifacts/01_plan_output.txt
```

只有 G0 只读计划明确列出文件范围、测试、迁移、风险、回滚与验收映射并通过人工审查后，才进入 workspace-write。

## 9. 生产实现状态

| 层级 | 当前状态 |
|---|---|
| 需求、架构、目录、模型、任务、风险和验收基线 | `SPECIFIED` |
| 高保真交互原型 | `PROTOTYPED`（fixture） |
| GitHub 治理模板与自动校验 | `PACKAGED`，待仓库启用 |
| 生产数据库、图查询、采集管道、真实数据核验 | `NOT STARTED` |
| 生产评分服务、全局即时刷新、后台任务和告警 | `NOT STARTED` |
| 生产前端、性能、可访问性和真实用户测试 | `NOT STARTED` |

原型数据不得作为公司事实、资金事实或投资建议。任何真实关系进入生产图谱前，必须具有来源、事实状态、方向、时间、证据和核验记录。
