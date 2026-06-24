# Task Card：S2PAT02 V7 合同写入仓库

## 唯一目标

把 Owner 已确认的 V7 结构写成机器合同、中文人类总纲、决策记录和需求追踪，并建立版本/哈希。

## 主要修改

- `docs/governance/product_contract.yaml`
- `docs/governance/decision_log.yaml`
- `docs/governance/requirements.yaml`
- `00_用户中心/05_系统总纲开发要求与验收标准.md`
- 相关 Schema/生成器/测试

## 非目标

不改连接器、不改邮件模板、不搬迁整个仓库。

## Stop Gate

`ACC-S2PAT02-CONTRACT`：每项 Owner 要求有 ID、Task、Acceptance、人类视图和防漂移测试。

## Stop Conditions

`TRACE-FAIL`、`G-DRIFT`、产生第二套可编辑事实源。
