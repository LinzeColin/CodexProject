# Known gaps · ADP-S0-P01-T003

- 合同 hash 的价值在于**后续任务真正读取并校验**：本任务提供 `MACHINE_CONTRACT.sha256`（`shasum -c` 可验），但“每个任务开工前校验 hash”这一流程闭环要到 T004 起的任务证据里实际体现（在各 commands.log 记录 `shasum -c` 结果）。
- `baseline_commit` 记为 `76e80edf`（T002 后 main）；合同随 canonical 基线演进时应在新任务里更新并重算 hash，而非默默漂移。
- 私有 Cloudflare 事实 FACT-011..015 仍为 `UNVERIFIED_PRIVATE`，由 S0-P02（T004–T007）补齐；本任务未涉及。
- 独立验证：本报告以 `IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION` 结束，PASS/FAIL 由独立上下文判定，实现者不自签。
