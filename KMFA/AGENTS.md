# KMFA Agent Contract

本项目继承仓库根 `AGENTS.md` 与 `docs/governance/STANDARD.md`，本文件只追加 KMFA 专项约束，不弱化根规则。

## Scope

- 项目名: KMFA
- 中文名: 经营分析系统
- GitHub 目录: `LinzeColin/CodexProject/KMFA`
- 形态: 独立项目，稳定后再作为入口或模块接入 OpMe
- 当前 Stage: `v0.1.4 Stage 1-18 complete, final overall review complete, one-time code upload pending`
- 当前 Phase: `V014_FINAL_OVERALL_REVIEW 已复跑 18/18 current Stage validators，并使用 bundled Python 完成全量回归。复审修复 S10 checker、S17 test 与 S18 review checker/test 的 active-phase 时态耦合、S14 generator-backed tests 固定公共证据污染、system runtime 无效验收基线及历史 tracked raw 文件名引用；raw-name remediation 同时保持 development events append-only 并完整登记 files_changed。14 findings=6 fixed / 8 passed / 0 open，raw 前后与跨 S18 review 快照一致，actual raw filename tracked hits=0。业务仍为 Q4 / D / NO_GO / 3-9-2-1，lineage full=false。下一步只能另起 run work 执行一次性 public-safe GitHub main upload；本轮未执行 upload，不得执行 App 重装、正式报告、差异关闭、真实连接器、凭据处理、持久业务写入或业务执行。历史 overall review/upload 产物仅作 legacy 证据，不是当前 active gate。`

## Execution Rules

- 每次 pursuing goal 只处理一个 Stage。
- 每次 run work 最多解决一个 Phase。
- 中间 Phase 完成不上传 GitHub。
- v1.3 本轮目标下，GitHub main upload 统一延期到 Stage 1-10 全部完成、整体复审通过并修复 findings 后一次性执行；不得按单个 Stage 做 GitHub upload gate。
- v1.4 本轮目标下，GitHub main upload 统一延期到 Stage 1-18 全部完成、整体复审通过并修复 findings 后一次性执行；不得按单个 Stage 做 GitHub upload gate。
- 时间是资源参考，不是质量豁免；质量门禁通过可以提前交付，未通过不得交付。
- 后续开发基线必须读取 `KMFA/taskpack/v1_4/`；涉及 UI、报告、前端或验收时必须读取 v1.4 HTML/UIUX 人类流程验收样板。

## Data And Privacy

- 经 owner 在当前线程或签名上传 manifest 明确授权后，原始敏感经营文件、银行流水、合同、工资、税务申报、SQLite/数据库导出、明文报告正文等非凭据类敏感材料允许以明文提交到 GitHub，但必须放在 `KMFA/metadata/` 下并登记到 `KMFA/metadata/security/owner_authorized_plaintext_upload_manifest.jsonl`。
- 账号密码、token、API key、webhook secret、signing key、私钥等 credential/secret 仍禁止提交 GitHub；如原始文件内含 credential/secret，必须先移除或更换源文件。
- 未经 owner 明确授权和 manifest 登记的敏感材料仍按历史规则处理：公开仓库只保存结构、hash、manifest、状态、证据索引、脱敏 fixture 和治理记录。
- 本机 KMFA raw data inbox 固定为 `/Users/linzezhang/Downloads/KMFA_MetaData`；该目录属于用户原始财务数据，只读，不得修改、删除、移动、重命名、覆盖或写入生成文件。
- Codex 私有 inventory、schema/header diagnostic、mapping diagnostic、scratch files 或本地报告只能写入项目受控且 Git 忽略的位置，例如 `KMFA/.codex_private_runtime/`，或另一个明确加入 `.gitignore` 的额外工作目录。
- `90_用户原始上传数据_仅本地私有_禁止提交GitHub/` 属于历史任务包命名；新规则下只有完成 owner 授权、secret 扫描和 upload manifest 登记后，才可把对应明文副本放入 `KMFA/metadata/`。
- metadata 默认保存索引、hash、状态、证据；经 owner 授权的明文敏感文件例外必须集中放入 `KMFA/metadata/`，不得散落到项目代码、测试或 stage artifact 目录。
- 前端后续只允许写控制事件、字段映射规则、项目匹配确认、差异处理意见、人工确认记录、备注和报告发布审批。
- 前端和后端都不得修改原始上传文件、原始 hash、原始抽取值、已发布历史报告和已批准历史处理事件。

## Money And Report Gates

- 业务金额必须使用整数分或 Decimal，禁止使用 float。
- 任意 0.01 元差异必须失败或进入差异队列。
- 缺数据、过期数据、未处理差异不得伪装成完整经营报告。
- A/B/C/D 报告等级必须受 Q0-Q5 数据质量、零差异和人工确认约束。

## Current Non-Goals

- v0.1.4 `V014_FINAL_OVERALL_REVIEW` 本轮完成；下一轮只能单独执行一次性 public-safe GitHub main upload。不得顺手执行 App 重装、生产恢复、raw 复制或备份、真实通知、真实连接器、凭据处理、客户联络、催收、法务、施工、签署、开票、采购执行、支付审批、支付执行、银行、工资计算、奖金审批、薪资导出、最终发放、protected source matching、lineage full check completion、正式报告、差异关闭、纳税申报、贷款管理或任何业务动作。
- 以下 Stage 15/16/17/18 final upload 相关表述是 legacy/Post-S18 历史证据，不是当前 v0.1.4 active gate。当前 v0.1.4 GitHub main upload 仍延期到 Stage 1-18 全部完成并整体复审修复后一次性执行；不得直接进入 lineage full check、正式报告、完整报告邮件正文、外部邮件连接器、live connector、OpMe 深度耦合、采购执行、付款审批、付款执行、银行操作、现场施工、安全签字、技术签字、开票、催收、法律决策、工资计算、奖金审批、薪资导出、最终发放或外部接口。
- 不生成正式可信经营报告。
- 不关闭 S09-P3 pending owner/授权复核差异。
- 不把 Stage 12 review 或历史 Stage 12 GitHub upload 视为当前 v1.4 GitHub upload gate、lineage full check、差异关闭、正式报告或业务 release。
- 不在未读取 v1.2 HTML/UIUX 样板前实现 S11 前端。
- 不接红圈、金蝶、WPS、银行、税务自动接口。
- 不做付款、报税、开票、工资或奖金审批执行。
