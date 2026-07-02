# KMFA Raw Data Boundary

更新时间: 2026-07-02

## 本机原始数据入口

- local_raw_data_inbox: `/Users/linzezhang/Downloads/KMFA_MetaData`
- classification: `raw_private_business_data`
- owner_rule: 用户后续提供给 KMFA 的本机财务原始数据默认放入该目录。
- codex_access: 只读；仅在当前 phase 明确需要 raw-source inspection、aggregate readiness 或 private diagnostic 时读取。
- codex_write_allowed: `false`
- codex_mutation_allowed: `false`
- github_commit_allowed: `false`

## 操作边界

Codex 不得修改、删除、移动、重命名、覆盖、就地标准化或向 `/Users/linzezhang/Downloads/KMFA_MetaData` 写入任何生成文件。

Codex 需要生成的私有 inventory、schema/header diagnostic、mapping diagnostic、scratch files 或本地报告，必须写入项目受控且 Git 忽略的位置，例如 `KMFA/.codex_private_runtime/`，或另一个明确加入 `.gitignore` 的额外工作目录。

## 公开仓库边界

GitHub 只能保存 public-safe 结构、聚合计数、状态、hash/ref、证据索引、validator 结果和治理记录。

GitHub 不得保存 raw business data、zip、Excel、PDF、private CSV、sqlite/db、字段或表头明文、sheet 名、raw 文件名、raw 文件 hash、row values、业务金额、银行流水、合同、工资、税务申报、账号密码、token 或 API key。

## 当前授权状态

本文件只记录目录级治理边界，不授权正式报告、经营决策依据、raw value matching、lineage full check、外部接口、付款、银行、开票、催收、工资或税务执行。
