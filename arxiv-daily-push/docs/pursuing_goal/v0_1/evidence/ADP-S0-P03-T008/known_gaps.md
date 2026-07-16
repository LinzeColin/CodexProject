# Known gaps · ADP-S0-P03-T008

- **静态校验，非语义校验**：工具校验证据**结构/依赖/DAG**，不判断业务内容是否正确 —— 这正是「实现者不自签、由独立上下文判 PASS/FAIL」的设计意图。
- **status 不自动回写**：TASK_INDEX.csv 的 `status` 列不由工具自动更新；任务完成状态以 development_events.jsonl + git 历史为准，工具只做就绪校验。
- **依赖就绪 = 证据 READY**：task_runner 以「依赖有通过 validate_evidence 的证据包」判定依赖就绪，不校验依赖是否已被独立复核 PASS（独立复核发生在框架之外）。
- **validate_evidence 的自签检测是启发式**：匹配常见自签模式（`Verifier: PASS` 等）；刻意规避的措辞可能漏检 —— 独立复核仍是最终防线。
- FACT-013 / FACT-015 仍 UNVERIFIED，交 S0 Exit Owner；本任务未涉及。
- 独立验证：本报告以 `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` 结束，PASS/FAIL 由独立上下文判定，实现者不自签。
