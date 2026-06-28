# Stage 8 - 本地运行 Diff 与 Impacted Metrics

版本：`PFI v0.2.2`

本阶段目标：每次本地运行先生成依赖 hash 快照，只在依赖发生变化时重算受影响指标；无 diff 不联网、不生成 Codex ticket、不触发 LLM；重要业务冲突只生成本地中文 `Codex Review Ticket`，不自动调用外部服务。

## Phase 8.1 本地一致性刷新

| Task ID | 交付物 | 验收标准 | 停止条件 |
| --- | --- | --- | --- |
| `S8-P1-T1` | run snapshot | 至少包含原始数据、标准化交易、账本事件、interconnection、参数、分类、标签、汇率快照 hash。 | 无法判断数据是否变化时停止。 |
| `S8-P1-T2` | 运行策略 | 无 diff 不联网、不生成 Codex ticket、不触发 LLM。 | 无 diff 仍触发 agent 时停止。 |
| `S8-P1-T3` | 依赖图 | 有 diff 时只重算受影响指标，不全量重算所有板块。 | 小 diff 导致全局重算时停止。 |

依赖 hash 键固定为：

```text
raw_data_hash
normalized_transactions_hash
ledger_events_hash
interconnection_hash
parameter_hash
category_hash
tag_hash
fx_snapshot_hash
```

## 真实输入来源

Stage 8 运行差异输入必须来自真实本地来源或真实空态，不得使用 demo/sample/synthetic/fixture/mock/fake/测试样例财务记录。

| 依赖 | 当前来源 |
| --- | --- |
| 原始数据 | `MetaDatabase/PFI/alipay_daily/raw`，当前真实 raw 文件数 `4` |
| 标准化交易 | `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`，当前真实记录数 `8815` |
| 账本事件 | 由真实标准化支付宝流水派生 |
| interconnection | 暂无真实分组文件时使用中文真实空态，不生成模拟分组 |
| 参数 | `PFI/config/pfi_parameters.yaml` |
| 分类 | `PFI/docs/pfi_v02/LEDGER_CLASSIFICATION_STANDARD.md` 与 Stage 5 分类/事件类型表 |
| 标签 | Stage 6 默认标签与标签规则 |
| 汇率快照 | `PFI/data/fx_snapshots/AUD_CNY/2026-06-28.json` |

当前真实空态文案：`暂无真实 Interconnection 分组文件，使用真实空态，不生成模拟分组。`

## Phase 8.2 收紧 Impacted Metrics

### P0 核心指标

P0 核心指标仅包括：

```text
净资产
生活现金
投资资产
消费总流出
生活消费
投资收益
现金流窗口
待复核数量
Interconnection 异常数量
```

这些指标只有在真实金额、核心口径、现金流窗口、待复核数量或 Interconnection 异常发生实质变化时才进入 impacted metrics。

### P1 分析指标

P1 分析指标包括：

```text
分类占比
标签视图
订阅
夜间
大额
商户集中度
投资风格
交易频率
费用拖累
现金拖累
```

P1 不得与 P0 核心金额混在一起。分类或标签变化可以影响分析视图，但不能自动改变净资产、投资收益或现金流窗口。

### P2 展示指标

P2 展示指标包括：

```text
图表排序
趋势图
辅助说明
tooltip
参数中心展示
```

P2 属于展示层。展示变化被误判为财务核心变化时停止。

### 不应受影响指标

每个 diff report 必须标记“不应受影响指标”。示例：

| diff 类型 | 可影响 | 不应影响 |
| --- | --- | --- |
| 仅标签显示名变化 | 标签视图、辅助说明、tooltip | 净资产、投资收益、现金流窗口 |
| 仅图表排序变化 | 图表排序 | 任何金额 |
| 仅刷新本地缓存 | 缓存状态 | ledger_event_hash |
| 仅参数说明文本变化 | 辅助说明、参数中心展示 | 模型参数 hash、核心金额 |

## Phase 8.3 ChatGPT / Codex / LLM 触发条件

允许触发本地复审票据的原因只包括：

```text
业务语义变化
公式逻辑变化
分类冲突
标签冲突
跨板块不一致
测试无法解释
```

无需 LLM 的场景：

```text
无 diff
只刷新缓存
只重绘图表
汇率快照未变
参数未变
普通本地重算
```

`S8-P3-T2` 的交付物是 `PFI/review_queue/CODEX_REVIEW_TICKET_TEMPLATE.md`。票据必须包含触发原因、影响指标、涉及文件、期望检查、禁止事项、中文业务解释。

## 本轮非目标

- Stage 9 可视化与 UI/UX 不在本轮实现。
- 不修改 v0.2.1 HTML Web Shell UIUX 基线。
- 不联网、不调用外部 LLM、不生成真实 agent 任务。
- 不新增真实交易、自动投资、支付或券商提交。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage8_runtime_diff.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage8_runtime_diff.py tests/test_v022_review_stage8.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests/test_v022_stage0_database_governance.py tests/test_pfi_parameters_consistency.py tests/test_v022_fx_effective_date.py tests/test_v022_stage3_source_account_profiles.py tests/test_v022_interconnection_no_double_count.py tests/test_v022_consumption_investment_outflow.py tests/test_v022_stage5_ledger_taxonomy.py tests/test_v022_stage6_tags_views.py tests/test_v022_stage7_formula_scoring.py tests/test_v022_stage8_runtime_diff.py -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pytest tests -q -p no:cacheprovider
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```
