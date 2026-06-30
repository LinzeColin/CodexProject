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
- 新增 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_resolution_record.md` 和 machine manifest，记录 Excel 候选不能机器闭环为单一 A0 项目基准，仍需 owner 或授权私有映射决策。
- 新增 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/human/excel_owner_decision_packet.md` 和 machine packet，限定 Excel 候选后续只能走私有映射、降级为交叉来源支持或保持 pending 三类决策。
- 新增 `KMFA/tools/check_s05_p2_excel_owner_decision.py` 和 `KMFA/tests/test_s05_p2_excel_owner_decision.py`，验证 owner 决策包、fixture pending 状态、approval/control events 和 Q4/Q5 禁止状态一致。
- 新增 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/machine/excel_owner_decision_intake_contract.json`、`KMFA/tools/check_s05_p2_owner_decision_intake.py` 和 `KMFA/tests/test_s05_p2_owner_decision_intake.py`，限定后续 owner/授权决策记录的 public-safe schema、actor role、禁止明文键和 Q4/Q5 边界。

## 边界

- 未提交 `销售绩效考核.zip`、PDF、Excel 或任何原始业务文件。
- 未提交真实合同额、支出合计、毛利、毛利率、成本分类 raw value 或 normalized value。
- 本机提供的 `销售绩效考核.zip` 整包 hash/size 与登记 source package 不匹配；但过滤 macOS 隐藏文件后的 9 个真实业务成员 hash 与 Stage2 Ring4 registry 匹配。
- 当前 40 条 PDF 字段候选已记录 hash/source anchor，5 条 Excel 字段候选仍为 `pending_private_source_unavailable`；Excel 候选已完成机器复核但未人工决策。
- S05-P2 只生成字段级候选和 private refs；未执行 S05-P3 人工锁定、Q5 计算基准、zero-delta、事实层、报告生成或 UI。

## 结果

- `S5PBT01`: 已建立 5 个字段级黄金基准候选合同；8 个 PDF 候选的 40 条字段已 hash-only 回填，Excel 候选 5 条字段 pending。
- `S5PBT02`: 每条字段候选均绑定 `source_file_ref`、`page_ref`、`sheet_ref`、`cell_ref`、`raw_value_private_ref`、`normalized_value_private_ref` 和 pending/hash 状态；公开仓库不保存 raw/normalized 明文。
- `S5PBT03`: 已生成 A0 golden fixture 候选 JSONL，所有记录保持 `Q3` 机器候选、`q4_human_confirmed=false`、`q5_calculation_baseline_allowed=false`。
- Excel 候选待决策状态: `awaiting_owner_or_authorized_decision`，且 owner decision packet validator 与 owner decision intake validator 已通过。

## 风险

- 当前回填和 owner 决策包都不是正式 A0 golden fixture 锁定；仍有 5 条 Excel 字段 pending，且未做 Q4 人工确认。
- 后续必须补齐 Excel 候选字段或形成明确 owner/授权人工豁免、不适用或降级决策，再进入 S05-P3；公开仓库仍只允许保存 hash/ref/status，不允许保存真实字段值。
- 45 条字段候选不能用于正式报告或 zero-delta 通过声明。

## 回滚

- 删除 `KMFA/tools/a0_golden_fixture.py`
- 删除 `KMFA/tools/check_a0_golden_fixture.py`
- 删除 `KMFA/tests/test_a0_golden_fixture.py`
- 删除 `KMFA/metadata/baseline/a0_golden_fixture_manifest.json`
- 删除 `KMFA/metadata/baseline/a0_golden_fixture_candidates.jsonl`
- 删除 `KMFA/stage_artifacts/S05_P2_a0_golden_fixture/`
- 恢复 S05 stage status 和中文入口记录。
