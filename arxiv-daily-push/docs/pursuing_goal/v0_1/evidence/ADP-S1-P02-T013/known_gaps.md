# Known gaps · ADP-S1-P02-T013

- **board3 尚无真 A0-A2 政府官方源**：本迁移把现有 board3 四家媒体（人民网/中新网/新浪）纠正为 media/official_evidence=false（EXC-1）；真正的国务院/部委/省级/重点城市 A0-A2 源尚未加入，属后续来源真相任务（DIR-002）。
- **config/boards_v0_3.yaml 未对齐**（EXC-2）：config board3 定义与 worker 线上不同；本任务以 worker 为准迁移，未改 config；对齐由后续任务处理。
- **worker/D1/UI 仍各自持源**：本任务只产出权威 Registry（数据），尚未让 worker/D1/UI 从 Registry 编译生成——那是 **T014 Registry 编译器**（runtime/UI/seed SQL 由一个源生成）。故「消除多份真相」在 T013 完成登记、在 T014 完成机制。
- **platform/website 字段迁移时留空**：为聚焦 id/board/authority/feed 的等价性，platform/website 未逐条回填（可后续从 worker 补全）；不影响 fixture 等价与 schema 合法。
- **未重查 D1**：源数以 T006 快照（cn_sources=33）与 worker（33）一致为据，未再连 D1（0 D1 读）。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
