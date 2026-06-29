# KMFA Model Spec

product_version: 0.1.0-s02p2

## Scope

当前模型说明覆盖 S01 已建立的治理边界、S02-P1 metadata 协议、S02-P2 不可污染原则和后续业务模型草案，不声明项目成本计算、zero-delta、lineage 完整检查或报告等级门禁已经实现。

## Active Model

### MOD-KMFA-GOV-001

- type: deterministic governance contract
- purpose: 控制 Stage/Phase 边界、GitHub 上传门禁、公开仓库隐私边界和质量优先规则。
- fact_level: EXTRACTED
- evidence: `KMFA/AGENTS.md`, `KMFA/docs/governance/model_registry.yaml`

### MOD-KMFA-METADATA-001

- type: deterministic metadata governance contract
- purpose: 定义 metadata 七类目录、核心标识符、公开仓库隐私边界和协议检查。
- fact_level: EXTRACTED
- evidence: `KMFA/docs/governance/METADATA_PROTOCOL.md`, `KMFA/metadata/protocol/metadata_protocol.yaml`, `KMFA/tools/metadata_protocol_check.py`

### MOD-KMFA-IMMUTABILITY-001

- type: deterministic immutability contract
- purpose: 定义 raw manifest 不可变字段、派生数据版本化、前端/人工控制事件写入边界，防止原始数据污染。
- fact_level: EXTRACTED
- evidence: `KMFA/docs/governance/IMMUTABILITY_POLICY.md`, `KMFA/metadata/imports/raw_manifest_policy.yaml`, `KMFA/tools/immutability_policy_check.py`

## Planned Business Model

### MOD-KMFA-COST-001

- status: planned
- purpose: 后续文件型项目成本分析 MVP。
- dependency: S04 金额工具、S05 A0 基准、S06 零差异、S09 成本计算、S10 报告等级。
- current limitation: no production data import, no official report generation.

## Counts

- active models: 3
- active formulas: 3
- active parameters: 8
- planned models: 1
- planned formulas: 1
- planned parameters: 4

## Stop Conditions

- 原始敏感经营数据进入公开仓库。
- 业务金额使用 float。
- 0.01 元差异被静默通过。
- 缺数据报告被伪装为完整报告。
- Stage 未完成复审修复即上传 GitHub。
