# KMFA v1.5 S02-P3 测试结果

## TDD

- RED：首次运行 helper test 因 `KMFA.tools.v015_s02_p3_scope_gate` 不存在而得到 `ModuleNotFoundError`。
- GREEN：范围、禁止事项、变更控制 helper 与 mutation tests 完成；builder 可 byte-exact 重建 5 个核心公开安全产物。

## 覆盖

- 权威来源：TaskPack ZIP hash、24/72/216、21/21 内部文件、S02-P3 三个 Task 合同。
- 记账：103 个范围项、51 个禁止项、4 个审计域、5 类变更、36 个必填字段。
- 变异：范围缺失/重复/质量绕过/优先级漂移；禁止项缺失/内容漂移/override/merge fail-open；变更协议字段、scope integrity、audit contract、审批、回归与验证缺口。
- 边界：S02 Stage 未通过、S03 未开放、runtime/product/report/business/upload/reinstall/raw 均未执行。
- 兼容：S02-P1/P2 历史 strict validator、Roadmap successor、旧公式/参数/模型统计保持有效。

## 机器证据

最终命令、exit code 与 PASS 状态以同目录 `machine/validation_results.jsonl` 为机器收据；最终 strict validator 还会重建 5 个核心产物与 manifest，并核验治理、事件、公开安全、依赖 hash、Phase diff allowlist 与 committed blob。
