# Stage 10 - 报告、建议与复盘

版本：`v0.2.2 数据库治理`

本轮目标：把报告口径和行动建议从 Stage 5 的骨架升级为 v0.2.2 可追溯、可排序、可复盘的合同。Stage 10 不实现 Stage 11 测试与验证总门，不生成 Stage 12 最终交付包，不执行 Stage 13 后置触发复核，不修改 v0.2.1 主 Web Shell UIUX 基线，不新增真实交易、自动投资、支付或券商提交能力。

## Phase 10.1 - 报告口径

| Task ID | 交付物 | 验收标准 | 状态 |
| --- | --- | --- | --- |
| `S10-P1-T1` | 月报模板 | 同时显示消费总流出和生活消费 | 本轮完成 |
| `S10-P1-T2` | 投资报告 | 显示收益、成本、费用、汇率、交易频率、风格、现金拖累 | 本轮完成 |
| `S10-P1-T3` | 数据质量报告 | 显示未匹配转账、重复候选、低置信、标签变更、参数变更、hash diff | 本轮完成 |

### 月报双消费口径

| 指标 | 说明 | 公式/来源 |
| --- | --- | --- |
| 消费总流出 | 用于观察真实现金流出压力，包含生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用，并由退款抵消。 | Stage 7 消费总流出公式 |
| 生活消费 | 用于观察日常生活支出，只包含普通生活消费并由退款抵消。 | Stage 7 生活消费公式 |

停止条件检查：月报不再只显示一个消费口径。

### 投资报告成本和行为

投资报告必须包含：

- 收益
- 成本
- 费用
- 汇率
- 交易频率
- 风格
- 现金拖累

停止条件检查：投资报告不是只有收益。

### 数据质量报告 Interconnection 指标

数据质量报告必须包含：

- 未匹配转账
- 重复候选
- 低置信
- 标签变更
- 参数变更
- hash diff

停止条件检查：数据质量报告包含 Interconnection 和 Runtime Diff 关联指标。

## Phase 10.2 - 行动建议与复盘

| Task ID | 交付物 | 验收标准 | 状态 |
| --- | --- | --- | --- |
| `S10-P2-T1` | 参数文件 + 合同模型 | 将“推荐”定义为“行动建议与复盘”，明确不是自动投资建议，而是消费、投资、数据、现金流复盘任务 | 本轮完成 |
| `S10-P2-T2` | 参数文件 + 评分函数 | 建议评分包含影响金额、风险降低、紧急度、置信度、执行难度、学习价值，并保留可逆性与执行成本反比分 | 本轮完成 |
| `S10-P2-T3` | 生命周期数据结构 | 支持 `pending`、`accepted`、`rejected`、`snoozed`、`reviewed`、`effect_measured` | 本轮完成 |

### 行动建议类型

PFI 的“推荐”统一解释为“行动建议与复盘”。它不是自动买卖建议，不是券商下单，不是支付动作，也不是自动投资指令。

允许的任务类型：

- 数据修复建议
- 消费复盘建议
- 投资行为复盘建议
- 现金流风险建议
- 订阅优化建议
- 参数调整建议

### 行动建议评分

```text
行动建议评分 =
财务影响分 × 25%
+ 风险降低分 × 20%
+ 紧急程度分 × 15%
+ 置信度分 × 15%
+ 可逆性分 × 10%
+ 执行成本反比分 × 10%
+ 学习价值分 × 5%
```

其中“执行难度”以“执行成本反比分”表达：越容易执行，分数越高。

### 每条建议必备字段

- 证据来源
- 相关交易
- 相关参数
- 相关公式
- 预期影响金额 CNY
- 置信度
- 是否需要人工复核
- 用户决策状态
- 效果复盘状态

### 生命周期

| 状态 | 中文含义 |
| --- | --- |
| `pending` | 待处理 |
| `accepted` | 已接受 |
| `rejected` | 已拒绝 |
| `snoozed` | 已暂缓 |
| `reviewed` | 已复核 |
| `effect_measured` | 已完成效果复盘 |

## 交付文件

- `PFI/src/pfi_v02/stage_v022_report_advice_review.py`
- `PFI/src/pfi_v02/stage_v022_database_governance.py`
- `PFI/tests/test_v022_stage10_report_advice_review.py`
- `PFI/docs/pfi_v022/STAGE10_REPORT_ADVICE_REVIEW.md`
- `PFI/config/pfi_parameters.yaml`
- `PFI/config/parameter_changelog.md`
- `PFI/模型参数文件.md`
- `PFI/功能清单.md`
- `PFI/开发记录.md`
- `PFI/HANDOFF.md`
- `PFI/README.md`

## 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage10_report_advice_review.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py tests/test_v022_stage9_visualization_uiux.py tests/test_v022_stage10_report_advice_review.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests -q -p no:cacheprovider
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## 非目标

- Stage 11 测试与验证不在本轮实现。
- Stage 12 文档同步与最终交付不在本轮实现。
- Stage 13 后置触发型复核不在本轮实现。
- 不修改 v0.2.1 主 Web Shell UIUX 基线。
- 不新增真实交易、自动投资、支付或券商提交。
