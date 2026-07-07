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

## 禁止提交

不得提交：

- 原始敏感 Excel
- 合同/银行/税务/工资明文
- token、密钥、webhook
- SQLite runtime 数据库
- Python/Node cache
- 临时截图和中间渲染件
- 未脱敏正式报告正文

## 本机保留

本机运行区最终只保留正式输出报告：

```text
经营管理分析报表 YYYYMM.xlsx
董事会经营分析摘要 YYYYMM.pdf
```

脚本默认只做 cleanup audit，不自动删除用户原始文件。只有 skill 创建的 cache/temp/log/runtime
文件可以被清理；原始输入文件删除需要当前线程另行明确授权。

