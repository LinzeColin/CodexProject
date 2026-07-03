# KMFA Agent Contract

本项目继承仓库根 `AGENTS.md` 与 `docs/governance/STANDARD.md`，本文件只追加 KMFA 专项约束，不弱化根规则。

## Scope

- 项目名: KMFA
- 中文名: 经营分析系统
- GitHub 目录: `LinzeColin/CodexProject/KMFA`
- 形态: 独立项目，稳定后再作为入口或模块接入 OpMe
- 当前 Stage: `v0.1.4 Stage 6`
- 当前 Phase: `S06-P3 validation evidence 已完成本地验证；S06-P1/S06-P2 public-safe evidence 已输出 sanitized validation evidence 并写入 metadata/quality；Q5 allowed=0，report grade A allowed=0；不执行 Stage 6 review、GitHub upload、raw value matching、lineage full check 或正式报告`

## Execution Rules

- 每次 pursuing goal 只处理一个 Stage。
- 每次 run work 最多解决一个 Phase。
- 中间 Phase 完成不上传 GitHub。
- v1.3 本轮目标下，GitHub main upload 统一延期到 Stage 1-10 全部完成、整体复审通过并修复 findings 后一次性执行；不得按单个 Stage 做 GitHub upload gate。
- v1.4 本轮目标下，GitHub main upload 统一延期到 Stage 1-18 全部完成、整体复审通过并修复 findings 后一次性执行；不得按单个 Stage 做 GitHub upload gate。
- 时间是资源参考，不是质量豁免；质量门禁通过可以提前交付，未通过不得交付。
- 后续开发基线必须读取 `KMFA/taskpack/v1_2/`；涉及 UI、报告、前端或验收时必须读取 `20_HTML_UIUX_报告预览/`。

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

- v0.1.4 S06-P3 validation evidence 已完成；下一轮只能在用户明确开启后执行 `Stage 6 整体复审`。不得直接执行 GitHub upload、S07-P1、raw value matching、lineage full check、正式报告、live connector、OpMe 深度耦合或任何业务动作。
- Stage 15 已完成 S15-P1/S15-P2/S15-P3、整体复审和 final GitHub upload；S16-P1/S16-P2/S16-P3、Stage 16 整体复审和 final GitHub upload 已完成；S17-P1/S17-P2/S17-P3、Stage 17 整体复审和 final GitHub upload 已完成；S18-P1 精度与压力测试、S18-P2 全量回归验收、S18-P3 后续接入准备、Stage 18 整体复审和 Stage 18 final GitHub upload 均已完成。Stage 18 review-level Go/No-Go 仍为 `NO_GO`；不得直接进入 lineage full check、正式报告、完整报告邮件正文、外部邮件连接器、live connector、OpMe 深度耦合、采购执行、付款审批、付款执行、银行操作、现场施工、安全签字、技术签字、开票、催收、法律决策、工资计算、奖金审批、薪资导出、最终发放或外部接口。
- 不生成正式可信经营报告。
- 不关闭 S09-P3 pending owner/授权复核差异。
- 不把 Stage 12 GitHub upload 视为 lineage full check、差异关闭、正式报告或业务 release。
- 不在未读取 v1.2 HTML/UIUX 样板前实现 S11 前端。
- 不接红圈、金蝶、WPS、银行、税务自动接口。
- 不做付款、报税、开票、工资或奖金审批执行。
