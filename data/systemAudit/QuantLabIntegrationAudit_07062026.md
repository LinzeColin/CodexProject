# QuantLab Integration Audit

- Status: `Pass`
- As Of: `2026-06-07`
- Generated At: `2026-06-07T11:28:28`

| Layer | Status | Summary | Next Action |
| --- | --- | --- | --- |
| DataTrust | Pass | Data Trust status=Pass; records=145. | 继续保持只读审计和证据链记录。 |
| EntityRegistry | Pass | Entity Registry schema=QuantLabEntityRegistryV1; records=28. | 确认 ProxyMapped 和 MissingSymbol 的报告口径。 |
| WorkflowInputs | Pass | Workflow inputs are queryable; rows=3. | 新报告应引用 workflow_input_id 或明确标注 ManualOrLocalOnly。 |
| ReportEvidence | Pass | RunMetadata files=31; report_evidence=1. | 旧报告可保留；新报告必须包含 QuantLabReportEvidenceV1。 |
| ResearchBusInterop | Pass | ResearchBus interoperability status=Pass. | 继续保持跨系统同步审计。 |
| NoLiveTradingBoundary | Pass | No live order code was found; policy boundary is documented. | 保持研究-only 边界。 |
