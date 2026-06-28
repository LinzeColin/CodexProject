# PFI v0.2.2 Stage 1 复审

复审日期：2026-06-28  
复审阶段：第一阶段逐 Stage 复审并解决问题，本轮只复审解决 Stage 1，不复审 Stage 2-13，不做整体项目复审，不重装 app 入口。  
复审结论：通过  
上线阻塞项：0

## 复审范围

| 范围 | 结论 |
| --- | --- |
| Stage | Stage 1：模型参数文件重构 |
| Phase | Phase 1.1 建立中文参数总目录；Phase 1.2 参数中文化 |
| Task | `S1-P1-T1`、`S1-P1-T2`、`S1-P1-T3`、`S1-P2-T1`、`S1-P2-T2`、`S1-P2-T3` |
| 非目标 | 不复审 Stage 2-13；不改 v0.2.1 Web Shell UIUX；不新增真实交易、支付、券商提交、自动投资；不重装 app 入口 |

## 证据来源

| 证据 | 用途 | 当前判断 |
| --- | --- | --- |
| `PFI/模型参数文件.md` | 用户可读中文参数目录、公式解释、阈值说明、变量字典 | 可证明 Stage 1 中文化要求 |
| `PFI/config/pfi_parameters.yaml` | 机器可读 canonical 参数源 | 可证明 YAML/Markdown 对齐 |
| `PFI/config/pfi_v022_parameters.yaml` | v0.2.2 参数交付镜像 | 已声明不是 canonical，避免漂移 |
| `PFI/tests/test_pfi_parameters_consistency.py` | 参数一致性测试 | 可证明 Markdown/YAML/前端核心阈值一致 |
| `PFI/src/pfi_v02/stage_v022_database_governance.py` | `build_v022_stage1_contract()` 和 `load_v022_parameter_catalog()` | 可证明 Stage 1 合同和参数读取入口 |
| `PFI/docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md` | Stage 1 原始交付验收报告 | 可证明早期 Stage 1 closeout |
| `PFI/tests/test_v022_review_stage1.py` | 本轮复审合同测试 | 可证明本轮不是只复用旧完成说明 |

## Task 复审矩阵

| Task ID | Roadmap 验收标准 | 当前证据 | 复审结论 |
| --- | --- | --- | --- |
| `S1-P1-T1` | 中文参数目录包含：货币、汇率、时间、数据源、账户角色、事件类型、Interconnection、消费分类、标签、置信度、消费模型、投资模型、现金流、可视化、测试 | `PFI/模型参数文件.md` 的 Stage 1 参数域目录和 `PFI/config/pfi_parameters.yaml` 的 `domains` | 通过 |
| `S1-P1-T2` | `PFI/config/pfi_parameters.yaml` 与 Markdown 参数含义一致；字段中文说明可在 Markdown 查到 | `load_v022_parameter_catalog()` 可读取 YAML；一致性测试检查 domain label/description、核心参数和 Markdown 文本 | 通过 |
| `S1-P1-T3` | `tests/test_pfi_parameters_consistency.py` 能确认 Markdown/YAML/前端显示的核心阈值一致 | 测试覆盖 `AUD/CNY`、`06:00`、`70 分`、`CNY 2000`、`AUD 500`、现金流窗口和集中度阈值 | 通过 |
| `S1-P2-T1` | 每个公式必须有中文名称、用途、输入、输出、计算逻辑、示例 | `PFI/config/pfi_parameters.yaml` 的 `formulas` 每项含 `name_zh`、`purpose_zh`、`inputs`、`outputs`、`logic_zh`、`example_zh` | 通过 |
| `S1-P2-T2` | 每个阈值必须有当前值、为什么存在、触发后影响哪些页面、能否用户修改 | `threshold_index` 每项含 `current_value`、`why_zh`、`impact_surfaces`、`user_editable` | 通过 |
| `S1-P2-T3` | 公式变量建立中文别名，例如 `gross_consumption_cny = 消费总流出金额` | `formulas[*].variable_aliases` 和 `PFI/模型参数文件.md` 的变量字典 | 通过 |

## 停止条件复核

| 停止条件 | 当前证据 | 是否触发 |
| --- | --- | --- |
| 参数仍散落在代码和文档中时停止 | Stage 1 参数域已有统一目录；机器 canonical 源是 `PFI/config/pfi_parameters.yaml` | 未触发 |
| Markdown 和 YAML 不一致时停止 | `tests/test_pfi_parameters_consistency.py` 与本轮 `tests/test_v022_review_stage1.py` 检查一致性 | 未触发 |
| 核心阈值多处不一致时停止 | 核心阈值在 Markdown、YAML 和前端显示中有测试覆盖 | 未触发 |
| 只有英文变量或代码名时停止 | 公式均有中文名称、用途、逻辑、示例和中文别名 | 未触发 |
| 阈值无解释时停止 | 阈值说明表含当前值、原因、影响页面、是否可修改 | 未触发 |
| 用户看不懂变量含义时停止 | 变量字典含 `gross_consumption_cny = 消费总流出金额`、`future_cash_balance = 未来现金余额` 等 | 未触发 |

## 参数域覆盖

- 货币
- 汇率
- 时间
- 数据源
- 账户角色
- 事件类型
- Interconnection
- 消费分类
- 标签
- 置信度
- 消费模型
- 投资模型
- 现金流
- 可视化
- 测试

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_review_stage1.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_pfi_parameters_consistency.py tests/test_v022_stage0_database_governance.py tests/test_v022_review_stage1.py -q -p no:cacheprovider
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前验证结果：

- 初始 RED：`tests/test_v022_review_stage1.py` 失败，原因是复审报告缺失，并发现 `threshold_index` 中 3 个阈值/开关键未出现在 `PFI/模型参数文件.md`。
- 修复：补齐 3 个阈值/开关键说明，分别是 `confidence.source_layered_thresholds_allowed`、`consumption_model.subscription_score_threshold`、`cashflow.reserve_months_default` 的中文阈值说明。
- Stage 1 复审目标测试：`3 passed`。
- Stage 0/1 轻量回归：初次 `21 passed`；历史词条修复后关键范围回归 `26 passed`。
- 完整 PFI 测试：`258 passed`。
- Web shell 语法检查：`node --check web/app/shell.js` 通过。
- 项目治理：`errors 0 / warnings 0`。
- `git diff --check -- PFI`：通过。
- macOS app 入口轻量验收：`29 pass / 0 fail / 2 info`；8501 健康。

## 剩余风险

- Stage 1 只证明参数治理和中文解释链路已复审并解决本轮发现的问题；不证明 Stage 2-13 或整体项目复审完成。
- Stage 1 不重装 app 入口；整体 pursuing goal 完成后再执行 app 入口重装。
- Stage 1 不改变金融公式数值，不新增模型参数，不修改正式 UI。
