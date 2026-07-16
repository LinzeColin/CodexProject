# Known gaps · ADP-S5-P04-T067

- **provenance 5 项由条目携带**：`add_to_library` 要求条目已带 `source_url / version / fetched_at / claim_evidence / license`——这些由**上游摄取/证据管线**提供（URL 来自源、version 来自 T026 content_hash/版本号、fetched_at 来自抓取时间戳、claim_evidence 来自 Evidence Locator[T018]、license 来自源注册表/许可映射）。本任务专注「已带 provenance → 存入并导出且不丢失/不脱证据」；缺任一项**拒存并拒导**（None/[]/空白串=缺，真值如 0 算有）。
- **许可提示为文本字段**：`license` 是**人类可读的许可提示文本**（如「arXiv 非独占许可，注明来源」）。真实的许可合规判定（可否再分发/商用）由**法务 + 源注册表许可映射**负责；本任务保证导出**始终携带**该提示、不静默丢弃，不做许可裁决。
- **导出为库层字符串**：`export_markdown/csv/json` 返回**字符串**（确定性、可测）；落盘/下载/编码头/BOM 由部署阶段的导出视图负责。CSV 用 `csv` 模块正确引用（逗号/引号/换行无损）；Markdown 为逐条 labeled block（多行值在 block 内按行展示）。
- **无时钟**：不读 wall-clock；抓取时间来自条目 `fetched_at`（确定性、可重放）。
- **NOT_DEPLOYED**：不接 worker/cron/D1/R2，不改生产数据。实时无回归（live build_id b189d3cc0703 == T040）。S5-P04（资料与知识有效性）：本任务后接 T068（Knowledge Validity + 131 项收益对齐回归，S5-P04 收尾）。
