# 数据治理与本机减负

## GitHub metadata

`KMFA/metadata/mgmt-monthly-report-skill/` 保存 public-safe 治理资产：

- backup registry
- run manifest
- validation summary
- raw source hash index
- database SQL schema/export
- cleanup report
- logs summary
- report output index

## GitHub 明文规则

允许提交到 `KMFA/metadata/`，但必须满足 owner 明确授权、secret 扫描通过、并登记
`KMFA/metadata/security/owner_authorized_plaintext_upload_manifest.jsonl`：

- 原始敏感 Excel
- 合同/银行/税务/工资明文
- 明文正式报告正文
- SQLite runtime 数据库或数据库导出

任何情况下不得提交：

- token、密钥、API key、webhook secret、signing key、账号密码、私钥
- Python/Node cache
- 临时截图和中间渲染件

## 本机保留

本机运行区最终只保留正式输出报告：

```text
经营管理分析报表 YYYYMM.xlsx
董事会经营分析摘要 YYYYMM.pdf
```

脚本默认只做 cleanup audit，不自动删除用户原始文件。只有 skill 创建的 cache/temp/log/runtime
文件可以被清理；原始输入文件删除需要当前线程另行明确授权。
