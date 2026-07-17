# 经营管理月报 Metadata

该目录只保存 `mgmt-monthly-report-skill` 的 public-safe 数据治理资产。任何角色、
任何授权状态均不得把原始敏感明文、报告正文或 private/source 派生指纹放入
`KMFA/metadata/`。

允许提交：

- public-safe v2 schema
- 脱敏 run manifest
- backup registry
- validation summary
- cleanup report
- SQL schema/export
- 脱敏日志摘要
- 版本化、非派生 opaque ref
- 状态与聚合计数

不允许提交：

- token、API key、webhook secret、signing key、账号密码、私钥
- raw/source/private 文件名、路径、大小、扩展名、sheet 名或其派生指纹
- 非 tracked public artifact 的任何 digest；tracked public artifact digest 必须绑定可验证 blob
- 客户、人员、项目、金额、账号、税务或报告明细
- 任何敏感明文文件（owner 授权不构成例外）
