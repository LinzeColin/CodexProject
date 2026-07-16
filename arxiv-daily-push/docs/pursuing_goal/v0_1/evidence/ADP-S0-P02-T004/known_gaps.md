# Known gaps · ADP-S0-P02-T004

- **截图 PNG 不入仓**：遵守 no-binary/low-token 契约。视觉状态以文字（截图内容描述）+ HTML 标记（fingerprints.json）+ headers 固化，可用 evidence/commands.log 中的只读命令复现。实测截图在本采集会话内完成，非二进制提交。
- **双域名严格一致性属 T006/FACT-014**：本任务只做公开面初判（归一化相似度 0.9973、headers 逐字一致、六主题/视频/仪表盘标记一致 → 初判同一 build），不下「每次部署后恒为同一 build」的最终结论；该结论需 build endpoint/Cloudflare 导出，是 T006 的私有基线工作。
- **`/search` 结果页**：本次仅采集空搜索页（无 `?q=`）状态 200；带查询参数的结果状态与内容未逐一采集，留作后续。
- **私有事实 FACT-011..015**（D1 行数/大小/延迟、R2、套餐/账单、私有分支）= `UNVERIFIED_PRIVATE`，由 T006 补齐；本任务未涉及。
- 独立验证：本报告以 `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` 结束，PASS/FAIL 由独立上下文判定，实现者不自签。
