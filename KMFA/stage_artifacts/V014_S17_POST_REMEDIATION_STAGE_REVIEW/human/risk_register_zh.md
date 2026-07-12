# Stage 17 整体复审风险登记

| 风险 | 控制 | 状态 |
|---|---|---|
| 非 canonical 角色绕过 P1 权限 | P3 owner 已统一并由 cross-phase matrix fail-closed | 已修复 |
| 手册审计要求未绑定 P1 action | 4 个 runbook 显式映射 action 与 7 字段 | 已修复 |
| 通知契约保留过期时态 | delivery scope 改为永久中性只记录不投递 | 已修复 |
| P2 测试要求自己永久 active | profile 永久校验，HANDOFF 仅在 active 时校验 | 已修复 |
| P2 checker 要求状态文档永久保留 P2 active | OWNER/STATUS 仅在 P2 active 时校验 | 已修复 |
| P3 测试要求自己永久 active | profile 永久校验，HANDOFF 仅在 P3 active 时校验 | 已修复 |
| review 治理记录引用不存在的证据文件 | manifest/report 引用统一到实际生成路径并由 validator 校验 | 已修复 |
| metadata 提醒被误读为真实投递 | delivery/full body/attachment/address/connector 均为 0 | 已控制 |
| 合成恢复被误读为生产恢复 | raw copy 与 production restore 均为 0 | 已控制 |
| 历史 review 污染当前状态 | 历史动态状态明确 non-authoritative | 已控制 |
