# SWOT Response Matrix

## Objective

把原 SWOT 中的优势、劣势、机会、威胁全部转成工程措施。你的优先级不是节省 token，而是准确性、鲁棒性、数据库化、工资标准化。

| SWOT 点 | 风险/机会 | 本任务包的解决方式 | 对应文件 |
|---|---|---|---|
| Strength: 新 agent 接手成本低 | 接手越稳定，月度流程越一致 | Skill 固定入口、路径、运行顺序、阶段二门禁 | `SKILL.md`, `operating_contract.md` |
| Strength: DWS/OneDrive/private_runtime 边界清晰 | 采集链路可重放 | raw payload + manifest + hash + DB batch | `source_of_truth_contract.md`, `postgres_schema.sql` |
| Strength: 减少遗漏 | 阶段二必须每次相同流程 | preflight -> inspect -> acquire -> DB -> canonical -> consensus | `automation_contract.md` |
| Weakness: 规则漂移 | 工资标准最大风险 | 明确规则优先级，漂移阻断 Q5 | `rule_drift_contract.md` |
| Weakness: 业务规则复制 | Skill 和 repo 可能冲突 | Skill 不作为唯一规则源；repo/DB policy version 优先 | `SKILL.md` |
| Opportunity: 工资前置治理 | 可变成工资标准 | Q0-Q5，Q5 后进入 payroll baseline | `payroll_baseline_contract.md` |
| Opportunity: 数据库化 | 后续可审计、可追溯、可对接 | PostgreSQL schema + views + stage2 tables | `database/postgres_schema.sql` |
| Threat: 自动 live/自动误发 | 数据污染会影响工资 | batch hash、transaction marker、stage2 exact hash | `dws_contract.md`, `stage2_consensus_gate.py` |
| Threat: 地点/轨迹缺失 | 严格考勤无法判定 | 强制 detail/location/trajectory evidence | `source_of_truth_contract.md` |
| Threat: 结果不稳定 | 工资依据不能摇摆 | 次月 1-5 夜间 5 次 canonical hash 完全一致 | `stage2_protocol.md` |

## Default decision

采用方案 B 的操作边界，但实现目标直接按 v0.3：

```text
Skill/operator framework
  + deterministic data pipeline
  + PostgreSQL schema
  + stage-2 exact consensus
  + payroll baseline certificate
```
