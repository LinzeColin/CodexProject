# KMFA Agent Contract

本项目继承仓库根 `AGENTS.md` 与 `docs/governance/STANDARD.md`，本文件只追加 KMFA 专项约束，不弱化根规则。

## Scope

- 项目名: KMFA
- 中文名: 经营分析系统
- GitHub 目录: `LinzeColin/CodexProject/KMFA`
- 形态: 独立项目，稳定后再作为入口或模块接入 OpMe
- 当前 Stage: `S11｜前端基础界面与数据源检查板`
- 当前 Phase: `S11-P2｜数据源检查板｜本地验证完成`

## Execution Rules

- 每次 pursuing goal 只处理一个 Stage。
- 每次 run work 最多解决一个 Phase。
- 中间 Phase 完成不上传 GitHub。
- 只有整个 Stage 完成、Stage 复审完成、复审问题修复完成后，才允许整体上传 GitHub。
- 时间是资源参考，不是质量豁免；质量门禁通过可以提前交付，未通过不得交付。
- 后续开发基线必须读取 `KMFA/taskpack/v1_2/`；涉及 UI、报告、前端或验收时必须读取 `20_HTML_UIUX_报告预览/`。

## Data And Privacy

- 禁止提交原始敏感经营数据、银行流水、合同、工资、税务申报、账号密码、token、API key。
- 公开仓库只允许保存结构、hash、manifest、状态、证据索引、脱敏 fixture 和治理记录。
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

- 不扩展 S11-P2 以外的 UI；S11-P2 只允许 public-safe 数据源检查板。
- 不生成正式可信经营报告。
- 不关闭 S09-P3 pending owner/授权复核差异。
- 不在 S11-P2 完成后跳过 `S11-P3｜项目成本页面` 直接进入 Stage 11 review、S12 或正式报告。
- 不在未读取 v1.2 HTML/UIUX 样板前实现 S11 前端。
- 不接红圈、金蝶、WPS、银行、税务自动接口。
- 不做付款、报税、开票、工资或奖金审批执行。
