# Phase 2.2 风险与回滚

- DST 风险：evaluation instant 必须带 offset，再转换到 Australia/Sydney；naive datetime fail-closed。
- 假日风险：只接受 source 显式 closed dates，不自行推断地区假日；当前 production calendar 未加载，因此 FX 保持 blocked。
- 旧快照风险：旧 snapshot 只记录 path alias 与 SHA-256，明确 reference-only，不加载为 production rate。
- stale 风险：有效业务日早于预期日即 stale；未来日期、方向或 hash 不一致均 fail-closed。
- 网络风险：v0.2.5 module 无网络 import/call，普通运行 network flag 为 false。
- 隐私风险：Evidence 只含 aggregate coverage、状态和 hash，不含财务明细、账户标识或真实汇率值。

回滚只撤销本 Phase 的 policy/schema/code/docs/tests/evidence/governance 变更；不触碰 source 或数据库。
