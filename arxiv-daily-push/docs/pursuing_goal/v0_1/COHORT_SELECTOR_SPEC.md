# A0 Backfill Cohort Selector Spec · ADP-S4-P02-T045

**按用户价值**选高价值**中央/国家级** A0 源做回填 cohort——**不按 Registry 顺序盲目全开**。
工具：`tools/cohort_selector.py`。**NOT_DEPLOYED**。Wave-1 cohort 是 **Owner S4 cohort 门（SCALE/HOLD/STOP）** 的提案；执行是 T046。

## Priority model（用户价值打分）

`value_score(c) = 0.4·domain_value + 0.3·coverage_gap + 0.3·stability`。候选 = S3-P02 已证明的 A0 源
（gov-cn-policy/gov-cn-fagui/stats-gov/ndrc-gov/cac-gov/nda-gov）。**排序高价值优先，非 registry 顺序**。

## Cohort manifest（每源必含 4 项）

`select_cohort` → 每 member：
- **authority_role**（A0/A1/A2）；
- **history_start**（历史起点，如 2016-01；nda-gov 2023-10 该局成立后）；
- **expected_doc_types**（预期文档类型，如 通知/规定/办法）；
- **stop_rule**（`until_month` 回填至历史起点 + `stop_when` 每月 shard done + guardrail：realtime P95>基线+20% 自动暂停[T042]）；
- **expected_benefit**（coverage_gain + authoritativeness）。

## 验收（`test-results/cohort_tests.txt`，PASS）

- **每 source 有权威角色/历史起点/预期文档类型/停止规则**（+expected_benefit）：5 个 member 全齐。
- **按价值非 registry 顺序**：members 按 value 降序 [gov-cn-policy 1.0 > gov-cn-fagui 0.965 > stats-gov 0.9 > cac-gov 0.88 > ndrc-gov 0.865]；top = 最高价值中央源。
- **不盲开**：live 受阻的 `nda-gov` **deferred**（needs browser/RSS），不入 Wave 1。
- priority model + cohort manifest + expected benefit 齐备。

## Owner cohort 门（下一步）

Wave-1 cohort（5 源）须交 **Owner S4 cohort 门决策 SCALE/HOLD/STOP** 后才进 **T046 执行 A0 2016+ Wave 1（SHADOW）**。
本任务只给提案 + 价值/停止规则，不自签晋级、不执行回填。
