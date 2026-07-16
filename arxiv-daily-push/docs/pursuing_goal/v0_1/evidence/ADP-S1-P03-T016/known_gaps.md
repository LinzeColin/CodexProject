# Known gaps · ADP-S1-P03-T016

- **人工基准 = provisional machine（待 Owner 抽查）**：按 Owner 2026-07-16 决策，200 样本 P0 字段用确定性机器抽取作 provisional 基准（baseline_status=provisional_machine），非人工标签；Owner 后续抽查一小部分即可将其升为 human_verified。不捧造人工标签。
- **board1 未在近 200 样本**：近 200 条 first_seen 排序里为 board2(86)/board3(85)/board4(29)；board1（arxiv/biorxiv/medrxiv）预印本此窗口内较少。DOI 抽取器已支持，board1 样本充足时同样适用。
- **board3 文号覆盖低（2/85）**：因 board3 现为媒体源（人民网/中新网/新浪，DRIFT-FACT-006），非带文号的政策原文；待后续接入真 A0-A2 政策源后文号覆盖会上升。如实反映，不强凑。
- **agency 抽取未实现**：board3/board4 的发文/发布机关抽取留占位（null）；后续可加机构词典。
- **只读 D1 200 行**：抽样为近 200 条；全量 682 条的基准可在需要时扩展（成本=更多只读 D1 读）。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
