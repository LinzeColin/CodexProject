# KMFA S01-P1 Risk Register

更新时间: 2026-06-29

## 1. 风险等级

总体风险等级: T3

原因: 涉及经营数据、项目成本、财务金额、税务证据、隐私与原始数据不可污染。当前阶段虽只读，但后续实现必须保持 fail-closed。

## 2. 风险清单

| ID | 风险 | 等级 | 当前状态 | 管控 |
|---|---|---:|---|---|
| R-S01P1-001 | 本地未发现 `LinzeColin/CodexProject/KMFA` checkout，路径可能误落到临时空仓库 | High | OPEN | S01-P2 前确认 canonical checkout；不要中途上传 GitHub |
| R-S01P1-002 | 根 `AGENTS.md` 和 `docs/governance/STANDARD.md` 未找到 | High | OPEN | S01-P2 前在正确 `CodexProject` 根读取；不能伪造治理规则 |
| R-S01P1-003 | 公开仓库误提交原始敏感数据 | Critical | CONTROLLED | 本轮不复制原始经营数据；后续只保存 hash、manifest、状态、证据索引 |
| R-S01P1-004 | 越界进入 S01-P2/P3 或业务实现 | Medium | CONTROLLED | 本轮仅写 S01-P1 计划/证据文件 |
| R-S01P1-005 | 将参考脚本 PASS 误写为正式项目工具 PASS | High | CONTROLLED | 明确区分 zip 参考脚本和未来 `KMFA/tools/*` |
| R-S01P1-006 | 金额计算使用 float 或忽略 0.01 元差异 | Critical | NOT STARTED | 后续实现必须整数分或 Decimal；S04/S06/S18 专门验证 |
| R-S01P1-007 | 前端或报告层直接改事实数据 | Critical | NOT STARTED | 后续前端只能写控制事件、映射规则、处理意见和审批记录 |
| R-S01P1-008 | 报告绕过 Q0-Q5 / A-D 等级门禁 | High | NOT STARTED | S02/S10/S18 必须建立并验证报告等级门禁 |

## 3. 当前可接受残余风险

S01-P1 可以接受以下残余风险:

- 正式 `KMFA/` 目录尚未创建。
- 正式治理工具尚未存在。
- 正式 `KMFA/tools/*` 尚未存在。
- GitHub remote 尚未配置。

这些风险必须在 S01-P2/S01-P3 或 Stage 1 复审中关闭，不能带入 Stage 2。
