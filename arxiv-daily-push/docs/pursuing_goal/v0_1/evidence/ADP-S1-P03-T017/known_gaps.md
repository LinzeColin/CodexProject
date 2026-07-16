# Known gaps · ADP-S1-P03-T017

- **缺陷判据为启发式 provisional**：english_direct_output 用 ASCII 字母比≥0.85 且长度≥40；board_pollution 用 board3 无政策关键词；templating 用近空 summary。这些是可回溯的机器判据，标 provisional_machine，待 Owner 抽查升为 human_verified。
- **样本为近 200 条**（board2 86/board3 85/board4 29，board1 此窗口少）；全量 682 条基线可后续扩展。
- **duplication 仅 batch 内**：跨天/跨批的重复未覆盖；本 batch 内无重复标题（duplication 计数 0）。
- **no_evidence=0**：因所有样本 published_at 有值（date 非 null）；接入真政策源（带文号）后此判据更有区分度。
- **不改内容、不修复**：本任务只建 before 基线；修复（L0-L3 人话版）是 T018。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
