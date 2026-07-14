# S05-P2 字段级黄金基准候选与部分回填记录

## 范围

- Stage/Phase: `S05-P2`
- Task: `S5PBT01-S5PBT03`
- 目标: 建立 A0 字段级黄金基准候选结构，为合同额、支出合计、毛利、毛利率、成本分类提供 source/value binding contract，并对可验证私有来源执行 hash-only 回填。

## 已完成

- 新增 `KMFA/tools/a0_golden_fixture.py`，从 S05-P1 A0 文件清单和项目候选清单生成字段级黄金基准候选 metadata。
- 新增 `KMFA/tools/check_a0_golden_fixture.py`，验证字段合同、候选数量、source binding、private value ref、Q3/Q4/Q5 状态和公开仓库安全边界。
- 新增 `KMFA/metadata/baseline/a0_golden_fixture_manifest.json`，登记 5 个 S05-P2 必需字段合同：合同额、支出合计、毛利、毛利率、成本分类。
- 新增 `KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl`，为 9 个 A0 项目候选生成 45 条字段级候选记录。
- 新增 `KMFA/tests/test_a0_golden_fixture.py`，覆盖无私有源时 pending 输出、合成私有 CSV 的 hash-only 输出、禁止公开 raw/normalized 明文键。
- 使用仓库外私有 CSV 对 8 个 PDF A0 候选执行 hash-only 回填，共 40 条字段候选记录 private value hash 和 source anchor。
- 新增 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/private_backfill_record.md` 和 machine manifest，记录公开安全的私有输入审计与部分回填结果。
- 新增 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_resolution_record.md` 和 machine manifest，记录 Excel 候选不能机器闭环为单一 A0 项目基准；后续 active owner/授权决策已将其降级为 cross-source support only。
- 新增 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_owner_decision_packet.md` 和 machine packet，限定 Excel 候选后续只能走私有映射、降级为交叉来源支持或保持 pending 三类决策。
- 新增 `KMFA/tools/check_s05_p2_excel_owner_decision.py` 和 `KMFA/tests/test_s05_p2_excel_owner_decision.py`，验证 owner 决策包、fixture pending 状态、approval/control events 和 Q4/Q5 禁止状态一致。
- 新增 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_intake_contract.json`、`KMFA/tools/check_s05_p2_owner_decision_intake.py` 和 `KMFA/tests/test_s05_p2_owner_decision_intake.py`，限定后续 owner/授权决策记录的 public-safe schema、actor role、禁止明文键和 Q4/Q5 边界。
- 新增 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_templates/`、`KMFA/tools/check_s05_p2_owner_decision_templates.py` 和 `KMFA/tests/test_s05_p2_owner_decision_templates.py`，为三种允许决策提供 public-safe 非决策模板，并验证模板不能被误当成 active owner 决策。
- 新增 `KMFA/tools/check_s05_p2_completion_gate.py` 和 `KMFA/tests/test_s05_p2_completion_gate.py`，验证 S05-P2 只有在 45/45 hash/source anchor 完整或存在 resolving active owner/授权决策时才可关闭；当前默认 gate 返回 `BLOCKED`，`--expect-blocked` 验证通过。
- 新增 `KMFA/tools/preview_s05_p2_owner_decision_application.py`、`KMFA/tests/test_s05_p2_owner_decision_application.py` 和 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/no_owner_decision_application_preview.json`，验证 owner/授权决策如何 public-safe 预览为私有 hash 映射、降级为 cross-source support 或继续 pending；no-decision 路径按预期 blocked，active downgrade decision 路径已验证 ready。
- 新增 active owner/授权决策记录 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/excel_owner_resolution_decision.json` 和 human record，按 owner 指示只读复核私有 `PRIVATE_RAW_SOURCE_005.zip`、`PRIVATE_RAW_SOURCE_004.zip` 后，将 Excel candidate 降级为 `cross_source_support_only`；application preview 和 completion gate 已验证 ready。

## 边界

- 未提交 `PRIVATE_RAW_SOURCE_005.zip`、PDF、Excel 或任何原始业务文件。
- 未提交真实合同额、支出合计、毛利、毛利率、成本分类 raw value 或 normalized value。
- 本机提供的 `PRIVATE_RAW_SOURCE_005.zip` 整包 hash/size 与登记 source package 不匹配；但过滤 macOS 隐藏文件后的 9 个真实业务成员 hash 与 Stage2 Ring4 registry 匹配。
- 当前 40 条 PDF 字段候选已记录 hash/source anchor，5 条 Excel 字段候选不写入 A0 baseline；Excel 候选已通过 owner/授权降级决策处理为 `cross_source_support_only`。
- S05-P2 只生成字段级候选和 private refs；未执行 S05-P3 人工锁定、Q5 计算基准、zero-delta、事实层、报告生成或 UI。

## 结果

- `S5PBT01`: 已建立 5 个字段级黄金基准候选合同；8 个 PDF 候选的 40 条字段已 hash-only 回填，Excel candidate 已 owner/授权降级为 cross-source support only。
- `S5PBT02`: 每条字段候选均绑定 `source_file_ref`、`page_ref`、`sheet_ref`、`cell_ref`、`raw_value_private_ref`、`normalized_value_private_ref` 和 pending/hash 状态；公开仓库不保存 raw/normalized 明文。
- `S5PBT03`: 已生成 A0 golden fixture 候选 JSONL，所有记录保持 `Q3` 机器候选、`q4_human_confirmed=false`、`q5_calculation_baseline_allowed=false`。
- Excel 候选已形成 resolving owner/授权决策: `downgrade_to_cross_source_support`，且 owner decision packet、intake、template、application preview 和 completion gate validators 已通过；该 Excel candidate 不进入 Q4/Q5 A0 baseline。

## 风险

- 当前回填、owner 决策包、owner 决策模板和 completion gate 都不是正式 Q4/Q5 A0 golden fixture 锁定；5 条 Excel 字段仍不写入 hash 明文映射，但已通过 owner/授权降级决策从 A0 baseline 中排除。
- Owner decision application preview 已证明 active decision 可被 deterministic/public-safe 地应用，不提交 raw values、不声明 Q4/Q5。
- 后续进入 S05-P3 前，公开仓库仍只允许保存 hash/ref/status，不允许保存真实字段值。
- 45 条字段候选不能用于正式报告或 zero-delta 通过声明。

## 回滚

- 删除 `KMFA/tools/a0_golden_fixture.py`
- 删除 `KMFA/tools/check_a0_golden_fixture.py`
- 删除 `KMFA/tests/test_a0_golden_fixture.py`
- 删除 `KMFA/tools/preview_s05_p2_owner_decision_application.py`
- 删除 `KMFA/tests/test_s05_p2_owner_decision_application.py`
- 删除 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/owner_decision_records/`
- 删除 `KMFA/metadata/baseline/a0_golden_fixture_manifest.json`
- 删除 `KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl`
- 删除 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/`
- 恢复 S05 stage status 和中文入口记录。
