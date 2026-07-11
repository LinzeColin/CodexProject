# KMFA Agent Contract

本项目继承仓库根 `AGENTS.md` 与 `docs/governance/STANDARD.md`，本文件只追加 KMFA 专项约束，不弱化根规则。

## Scope

- 项目名: KMFA
- 中文名: 经营分析系统
- GitHub 目录: `LinzeColin/CodexProject/KMFA`
- 形态: 独立项目，稳定后再作为入口或模块接入 OpMe
- 当前 Stage: `v0.1.4 Stage 15 phase delivery`
- 当前 Phase: `V014_S15_P1_POST_REMEDIATION_PERFORMANCE_FACT_FIELDS 已按 Roadmap 定义开票金额、毛利率、结算速度、回款速度、审计偏差、客情费率 6 个字段，连接 6/6 项目成本与回款 public-safe 结构引用，并对 5 个只读 raw、48 个 XLSX 容器和 4,198 个可解析工作表执行双次候选探针。六字段候选为 9/1/2/4/2/2，覆盖 13 个唯一工作表且指纹不一致为 0；权威行/值绑定和绩效事实物化均为 0，6/6 字段保持人工复核。当前仍为 Q4 / D / NO_GO / 3-9-2-1，raw 前后、跨 Stage 14 review 与当前快照一致。下一步只能另起 run work 执行 S15-P2，不得执行 S15-P3、Stage 15 整体复审、工资奖金、薪资导出、GitHub upload、app reinstall、正式报告、差异关闭或业务执行。历史 Stage 12-18 产物仅作 legacy 证据，不是当前 active gate。`

## Execution Rules

- 每次 pursuing goal 只处理一个 Stage。
- 每次 run work 最多解决一个 Phase。
- 中间 Phase 完成不上传 GitHub。
- v1.3 本轮目标下，GitHub main upload 统一延期到 Stage 1-10 全部完成、整体复审通过并修复 findings 后一次性执行；不得按单个 Stage 做 GitHub upload gate。
- v1.4 本轮目标下，GitHub main upload 统一延期到 Stage 1-18 全部完成、整体复审通过并修复 findings 后一次性执行；不得按单个 Stage 做 GitHub upload gate。
- 时间是资源参考，不是质量豁免；质量门禁通过可以提前交付，未通过不得交付。
- 后续开发基线必须读取 `KMFA/taskpack/v1_4/`；涉及 UI、报告、前端或验收时必须读取 v1.4 HTML/UIUX 人类流程验收样板。

## Data And Privacy

- 禁止提交原始敏感经营数据、银行流水、合同、工资、税务申报、账号密码、token、API key。
- 公开仓库只允许保存结构、hash、manifest、状态、证据索引、脱敏 fixture 和治理记录。
- 本机 KMFA raw data inbox 固定为 `/Users/linzezhang/Downloads/KMFA_MetaData`；该目录属于用户原始财务数据，只读，不得修改、删除、移动、重命名、覆盖或写入生成文件。
- Codex 私有 inventory、schema/header diagnostic、mapping diagnostic、scratch files 或本地报告只能写入项目受控且 Git 忽略的位置，例如 `KMFA/.codex_private_runtime/`，或另一个明确加入 `.gitignore` 的额外工作目录。
- `90_用户原始上传数据_仅本地私有_禁止提交GitHub/` 只允许作为本地私有源包存在；公开仓库只保存其 SHA256 登记和禁止提交规则。
- metadata 只保存索引、hash、状态、证据，不保存明文敏感数据。
- 前端后续只允许写控制事件、字段映射规则、项目匹配确认、差异处理意见、人工确认记录、备注和报告发布审批。
- 前端和后端都不得修改原始上传文件、原始 hash、原始抽取值、已发布历史报告和已批准历史处理事件。

## Money And Report Gates

- 业务金额必须使用整数分或 Decimal，禁止使用 float。
- 任意 0.01 元差异必须失败或进入差异队列。
- 缺数据、过期数据、未处理差异不得伪装成完整经营报告。
- A/B/C/D 报告等级必须受 Q0-Q5 数据质量、零差异和人工确认约束。

## Current Non-Goals

- v0.1.4 S15-P1 本轮完成；下一轮只能单独执行 S15-P2。不得顺手执行 S15-P3、Stage 15 整体复审、工资计算、奖金审批、薪资导出、最终发放、GitHub upload、protected source matching、lineage full check、正式报告、差异关闭、live connector、app reinstall、OpMe 深度耦合、客户联络、催收、法务、发票开具、纳税申报、付款、银行、贷款管理或任何业务动作。
- 以下 Stage 15/16/17/18 final upload 相关表述是 legacy/Post-S18 历史证据，不是当前 v0.1.4 active gate。当前 v0.1.4 GitHub main upload 仍延期到 Stage 1-18 全部完成并整体复审修复后一次性执行；不得直接进入 lineage full check、正式报告、完整报告邮件正文、外部邮件连接器、live connector、OpMe 深度耦合、采购执行、付款审批、付款执行、银行操作、现场施工、安全签字、技术签字、开票、催收、法律决策、工资计算、奖金审批、薪资导出、最终发放或外部接口。
- 不生成正式可信经营报告。
- 不关闭 S09-P3 pending owner/授权复核差异。
- 不把 Stage 12 review 或历史 Stage 12 GitHub upload 视为当前 v1.4 GitHub upload gate、lineage full check、差异关闭、正式报告或业务 release。
- 不在未读取 v1.2 HTML/UIUX 样板前实现 S11 前端。
- 不接红圈、金蝶、WPS、银行、税务自动接口。
- 不做付款、报税、开票、工资或奖金审批执行。
