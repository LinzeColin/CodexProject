# KMFA v0.1.3 S01-P2 非范围与停止线

## 本轮非范围

- S01-P3。
- Stage 1 review。
- GitHub upload。
- lineage full check。
- pending reconciliation closure。
- report grade upgrade。
- formal report release。
- business decision basis。
- live connector。
- OpMe deep coupling。
- business execution。

## 禁止提交材料

- raw business data。
- zip。
- Excel workbook。
- PDF。
- private CSV。
- sqlite/db。
- credentials。
- 银行流水。
- 合同全文。
- 薪资明细。
- 税务申报材料。

## 停止线

如果后续动作需要读取或提交原始业务文件、关闭 12 条 pending reconciliation、生成 actual lineage rows、提升 D 级报告、发布正式报告、上传 GitHub、连接外部系统或执行业务动作，必须停止当前 phase，另开明确 phase/owner 授权和验收。

## 本机 raw 目录操作边界

`/Users/linzezhang/Downloads/KMFA_MetaData` 是用户指定的 KMFA 财务原始数据目录。Codex 对该目录只有按任务需要的只读权限，不得在该目录内创建、修改、删除、移动或重命名文件。所有临时处理必须放在 `KMFA/.codex_private_runtime/` 或后续明确指定的 Codex-owned 私有目录，并保持 GitHub 禁入。

## 质量门禁

本 phase 只有在 S01-P2 validator、unit test、治理 validator、changed-only governance sync、raw/private scan、secret scan 和 diff check 全部通过后，才能本地 commit。即使全部通过，也不代表 delivery、release、formal report 或 business execution 被授权。
