# MetaDatabase

`MetaDatabase/` 是 `LinzeColin/CodexProject` 的顶层原始数据保险库，用来保存用户上传、交付或授权导入的原始数据及其处理后索引。

## 当前范围

| 系统 | 数据域 | 路径 | 状态 |
| --- | --- | --- | --- |
| PFI | 支付宝日常账单 | `MetaDatabase/PFI/alipay_daily/raw/` | 已保存 4 个原始 CSV |
| PFI | 支付宝标准化导入结果 | `MetaDatabase/PFI/alipay_daily/processed/` | 已保存 manifest 和 8815 条标准化流水 |

## 使用规则

- 原始文件只追加、不覆盖；任何重新解析必须生成新的 processed 文件或 manifest。
- 业务系统读取这里的数据时必须保留 `source_id`、原始文件名、parser 版本和导入时间。
- PFI 不在这里写入交易指令、支付动作、券商下单或实盘自动化结果。
- 含个人财务数据，提交 GitHub 前必须确认用户授权；本轮按用户明确要求同步到 `LinzeColin/CodexProject/MetaDatabase`。
