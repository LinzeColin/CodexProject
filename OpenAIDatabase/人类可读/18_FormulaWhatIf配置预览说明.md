# 18 Formula What-if 配置预览说明

## 结论

S07 P3 已完成 Formula What-if 的最小配置预览。任务 ID 为 `MA-V12-S07P3`，
验收 ID 为 `ACC-MA-V12-S07P3`，状态为
`phase_s07_p3_formula_what_if_completed_pending_s07_review`。

本阶段没有实现运行时 UI，也没有修改 active formula config。它只生成可审计的
配置预览输出，帮助查看不同权重假设下 Personal Economic Proxy 会怎样变化。
下一步只允许进入 S07 Review。

## 文件

- 配置：`机器治理/参数与公式/formula_what_if_defaults.v1_2_s07_p3.json`
- 输出：`data/derived/economic_proxy/formula_what_if_preview.json`
- Builder：`scripts/build_memory_atlas_formula_what_if.py`
- Validator：`apps/memory-atlas/scripts/validate_memory_atlas_v1_2_s07_p3.cjs`
- Review：`docs/reviews/memory_atlas_v1_2_s07_p3_formula_what_if.md`

## 可调整权重

Formula What-if 预览支持查看这些权重组合：

- 时间节省：`time_saved_weight`
- 复用价值：`reuse_value_weight`
- 机会价值：`opportunity_value_weight`
- 长期复利：`skill_compounding_weight`
- 自动化增强：`automation_alignment_weight`
- 返工成本：`rework_cost_weight`
- 低价值循环惩罚：`low_value_loop_penalty_weight`

输出中的每个 scenario 都包含中文说明、公式来源、参数引用、加权 proxy 分数、
相对 baseline 的变化、主要参数影响和 `parameter_change_proposal`。

## 边界

- `active_config_write=false`。
- `proposal_required_before_apply=true`。
- 不接入外部经济数据库。
- 不是精确收入预测。
- 不是财务建议。
- 不修改 raw。
- 不修改运行时 UI。
- No GitHub main upload in this phase。

## 如何查看

可使用：

```bash
python scripts/atlasctl.py analyze --stage formula-what-if --dry-run
python scripts/atlasctl.py audit --check formula-what-if
```

`--dry-run` 只返回预览，不写文件。正式生成的派生输出为
`data/derived/economic_proxy/formula_what_if_preview.json`。

## 下一步

下一步只允许进入 S07 Review。S07 Review 应复审 S07 P1 Personal Economic Proxy、
S07 P2 Information ROI 与 Visual ROI Gate、S07 P3 Formula What-if 配置预览是否
解释一致、边界一致、validator 可复跑，并继续保持 No GitHub main upload in this phase。
