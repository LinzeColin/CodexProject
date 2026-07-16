# Phase 9.3 Risk and Rollback

- 两个建议对象都只能驱动数据/报告复核；不得解释为确定性财务建议、买卖信号、订单或交易授权。
- 人工 `accepted` 只追加复核事件，不执行动作；任何 trade execution capability 都使本 Phase fail closed。
- net worth、cash、investment 继续 blocked；consumption、cashflow 继续 partial，缺失输入不得解释为零。
- counter evidence、invalidation conditions、source/model versions、human review history 缺一即不通过。
- HTML/PDF/CSV/Markdown 必须绑定同一 export snapshot；任一文件 hash、size、metadata 或 snapshot 不一致即不通过。
- PDF 必须可解析、内嵌 CJK 字体且 Poppler 实际渲染可读；空白、乱码、裁切或重叠即不通过。
- Stage 9 whole-stage review、Stage 10、push、PFI.app install、production/final acceptance 均不属于本轮。

Rollback：按逆序 revert Phase 9.3 Evidence/治理提交、release identity 提交和实现提交；不修改 Phase 9.1/9.2 immutable snapshots、数据库或真实财务数据。
