# KMFA v1.5 S02-P2 测试结果

## TDD

- RED：中央 builder import 缺失，focused test 以 `ModuleNotFoundError` 失败。
- GREEN：需求、lineage、公式 helper 及中央 builder/validator 已实现。

## 最终验证

最终命令、exit code 与 PASS 状态以同目录 `machine/validation_results.jsonl` 为唯一机器证据。最终 strict validator 必须同时重建 7 个 core artifacts、核验 S02-P1 dependency、治理状态、事件、完整性和公开安全边界。

S02 Stage Review/Fix 已把 governance sync 从无覆盖力的 `--base-ref HEAD` 修正为 Phase base `1de399f35d1c0d2b7ee1ea6451c2be8d1c49a861`，并把误名的 `structured_public_diff_checks` 更正为真实 `exact_core_rebuild_check`。

## 已锁门禁

- 134 bindings、55/55 requirements、97/97 requirement-stage pairs。
- actual lineage=0；full/report/business/product=false。
- formula/model=22、parameter controls=38、runtime enabled=0、unknown defaults=0。
- raw/S02-P3/S03+/upload/reinstall/business execution=false。
