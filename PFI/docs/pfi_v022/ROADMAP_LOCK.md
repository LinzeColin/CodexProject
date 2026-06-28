# PFI v0.2.2 Roadmap Lock

版本：`v0.2.2 数据库治理 / E2E 逻辑优化`

Roadmap 形态：`Stage -> Phase -> Task`

权威任务包：`PFI_v0.2.2_Stage_Phase_Task_Roadmap_zh.md`

追求目标：

```text
建立一个以 CNY 为主口径、以统一账本为事实层、以 Interconnection 为核心关联机制、以参数文件为模型治理中心、以中文可视化为人工验收入口的个人金融 E2E 逻辑系统。
```

## Stage 顺序

| Stage | 名称 | 本轮状态 | 说明 |
| --- | --- | --- | --- |
| Stage 0 | 任务锁定与文件定位 | 已补做复核 | 完成 `S0-P1-T1..S0-P2-T2`；独立复核文件为 `docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`。 |
| Stage 1 | 模型参数文件重构 | 本轮完成 | 中文参数总目录、机器可读 YAML、一致性测试。 |
| Stage 2 | CNY 基准与汇率规则 | 本轮完成 | CNY 主显示、原币辅助、06:00 有效汇率日、本地快照读取。 |
| Stage 3 | 数据源、账户角色与可扩展结构 | 待 owner 开启 | Source Profile、capabilities、账户角色重叠和生效期。 |
| Stage 4 | Economic Event 与 Interconnection 逻辑 | 待 owner 开启 | economic_event_id、interconnection_group_id、Matrix。 |
| Stage 5 | 统一账本事件、消费双口径与分类体系 | 待 owner 开启 | event type、双消费口径、12 大类 / 50 中类。 |
| Stage 6 | 标签系统与自定义视图 | 待 owner 开启 | 标签注册、赋值、规则、变更历史和视图。 |
| Stage 7 | 模型公式、阈值与评分标准 | 待 owner 开启 | 置信度、消费、投资、现金流公式。 |
| Stage 8 | 本地运行 Diff 与 Impacted Metrics | 待 owner 开启 | dependency hash、diff 收紧、LLM 触发规则。 |
| Stage 9 | 可视化与 UI/UX | 待 owner 开启 | 参数中心、Interconnection 可视化、现金流和 drilldown。 |
| Stage 10 | 报告、建议与复盘 | 待 owner 开启 | 双消费口径报告、投资成本行为、建议评分生命周期。 |
| Stage 11 | 测试与验证 | 待 owner 开启 | 金融逻辑、跨板块一致性、可视化一致性测试。 |
| Stage 12 | 文档同步与交付 | 待 owner 开启 | 三基、审查 HTML、总结报告。 |
| Stage 13 | 后置触发型复核 | 非默认执行 | 仅在 diff/test/owner 指定触发时执行。 |

## Stage 0 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S0-P1-T1` | Phase 0.1 | `PFI/开发记录.md` 新增 `PFI v0.2.2 E2E 逻辑优化` 任务章节 | 本轮补做 |
| `S0-P1-T2` | Phase 0.1 | 文件清单，覆盖三基、参数 YAML、前端 HTML、测试文件 | 本轮补做 |
| `S0-P1-T3` | Phase 0.1 | 非目标清单：不做真实交易、自动投资、隐私私有化重构、每次运行联网抓汇率 | 本轮补做 |
| `S0-P2-T1` | Phase 0.2 | `PFI/模型参数文件.md` metadata 新增 `task_name` 和 `parameter_version` | 本轮补做 |
| `S0-P2-T2` | Phase 0.2 | `PFI/config/parameter_changelog.md` | 本轮补做 |

## Stage 0 Acceptance Criteria

- 已列出现有参数与硬编码阈值。
- 已列出现有消费、投资、现金流、建议模块的计算口径。
- 已标记哪些逻辑与 v0.2.2 要求冲突。
- 已确认不会破坏已有 v0.2 Stage 6 基础。
- 已锁定 HTML 模板只是未来逻辑审查参考，不是本轮 UI 修改要求。
- 已按 Stage -> Phase -> Task roadmap 补做 Stage 0，不再只保留 milestone 摘要。
- 已创建参数变更记录文件 `PFI/config/parameter_changelog.md`。
- 已在 `PFI/模型参数文件.md` 记录 `task_name=PFI v0.2.2 E2E 逻辑优化` 和 `parameter_version=v0.2.2`。

## Stage 0 Stop Condition

- 无法定位现有模型参数文件。
- 无法定位现有前端入口。
- 无法判断现有测试框架。
- Stage 0 改动触碰 v0.2.1 正式前端显示。

当前检查结论：以上停止条件均未触发。

独立补做验收：`docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`，用于 GitHub 单独检查 Stage 0。

## Stage 0 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## Stage 1 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S1-P1-T1` | Phase 1.1 | `PFI/模型参数文件.md` 中文参数目录 | 本轮完成 |
| `S1-P1-T2` | Phase 1.1 | `PFI/config/pfi_parameters.yaml` | 本轮完成 |
| `S1-P1-T3` | Phase 1.1 | `PFI/tests/test_pfi_parameters_consistency.py` | 本轮完成 |
| `S1-P2-T1` | Phase 1.2 | 公式中文解释 | 本轮完成 |
| `S1-P2-T2` | Phase 1.2 | 阈值说明表 | 本轮完成 |
| `S1-P2-T3` | Phase 1.2 | 公式变量中文别名 | 本轮完成 |

## Stage 1 Acceptance Criteria

- `模型参数文件.md` 已包含货币、汇率、时间、数据源、账户角色、事件类型、Interconnection、消费分类、标签、置信度、消费模型、投资模型、现金流、可视化、测试。
- 已新增机器可读参数文件 `PFI/config/pfi_parameters.yaml`。
- `pfi_parameters.yaml` 与 Markdown 参数含义一致，字段中文说明可在 Markdown 查到。
- 已新增 `PFI/tests/test_pfi_parameters_consistency.py`。
- 测试能确认 Markdown、YAML、前端合同和 HTML 显示中的核心参数一致。
- 每个核心公式有中文名称、用途、输入、输出、计算逻辑和示例。
- 每个核心阈值有当前值、为什么存在、触发后影响哪些页面、能否用户修改。
- 公式变量有中文别名，例如 `gross_consumption_cny = 消费总流出金额`。

## Stage 1 Stop Condition

- 参数仍散落在代码和文档中且没有统一目录。
- Markdown 和 YAML 核心参数不一致。
- 核心阈值多处不一致且没有明确标记为后续阶段差异。
- 公式只有英文变量或代码名，用户无法理解。

当前检查结论：以上停止条件均未触发。

## Stage 1 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_pfi_parameters_consistency -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## Stage 2 Task Lock

| Task ID | Phase | 交付物 | 状态 |
| --- | --- | --- | --- |
| `S2-P1-T1` | Phase 2.1 | 首页、投资、消费、现金流、报告主显示以 `CNY` 为基准 | 本轮完成 |
| `S2-P1-T2` | Phase 2.1 | 原币辅助显示，例如 `CNY 2,343.70 / 原币 AUD 500.00 / AUD/CNY=4.6874` | 本轮完成 |
| `S2-P1-T3` | Phase 2.1 | 账本金额字段：`原始金额`、`原始币种`、`CNY金额`、`汇率快照ID` | 本轮完成 |
| `S2-P2-T1` | Phase 2.2 | 06:00 Australia/Sydney 有效汇率日规则 | 本轮完成 |
| `S2-P2-T2` | Phase 2.2 | 普通本地运行只读快照，不默认联网刷新 | 本轮完成 |
| `S2-P2-T3` | Phase 2.2 | `PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json` 含来源、读取时间、pair、hash | 本轮完成 |

## Stage 2 Acceptance Criteria

- 系统主口径为 `CNY`，Web Shell 首页和动态金额标签不再以 `AUD` 作为主显示。
- 原币信息保留为辅助展示，不覆盖 CNY 主口径。
- 账本金额字段可生成 `原始金额`、`原始币种`、`CNY金额`、`汇率快照ID`。
- 06:00 之前使用前一自然日快照，06:00 及之后使用当天快照。
- 普通运行不得自动访问网络；只有显式 `--allow-network` 刷新才调用外部汇率 API。
- `data/fx_snapshots/AUD_CNY/2026-06-28.json` 是真实读取快照，包含 `source_provider`、`source_url`、`fetched_at`、`pair_base`、`pair_quote`、`hash`。
- 当有效快照缺失时返回 `汇率数据待更新`，不得编造实时汇率，也不得强制刷新网络。

## Stage 2 Stop Condition

- CNY 主显示仍被 AUD 主显示覆盖。
- 原始金额、原始币种、CNY 金额或快照 ID 任一字段缺失。
- 普通运行会默认联网抓取汇率。
- 快照缺少来源、读取时间、pair 或 hash。
- 06:00 有效日边界不可测试。

当前检查结论：以上停止条件均未触发。

## Stage 2 Validation

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_fx_effective_date -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v022_stage0_database_governance PFI.tests.test_pfi_parameters_consistency PFI.tests.test_v022_fx_effective_date -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m pfi_v02.stage_v022_fx read
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest discover -s PFI/tests -q
node --check PFI/web/app/shell.js
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```
