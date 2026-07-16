# Known gaps · ADP-S1-P02-T012

- **只定义 schema，不迁移真实来源**：把现有 YAML/worker/D1/UI 的多份来源真相迁进 Registry 属 **T013**；本任务只提供 schema + validator + 合法样例。
- **sample 的省/市来源为占位示例**（example.gov.cn）：真实 A1/A2 官方源清单由后续来源真相任务按 DIR-002（覆盖中央/省级/重点城市/重要区）填充。
- **authority_kind 枚举可扩展**：当前 7 类（china_official/intl_official/journal/preprint/media/search/aggregator）；如需新增须同步更新 schema + validator。
- **official_evidence 语义**：true 仅限 official/journal/preprint 主源；media/search/aggregator 强制 false（schema+硬规则）；journal/preprint 若被误标可在 T013 迁移时逐条核。
- 独立验证：以 IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION 结束，实现者不自签。
