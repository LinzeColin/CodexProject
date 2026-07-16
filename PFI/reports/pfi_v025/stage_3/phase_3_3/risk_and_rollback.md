# Phase 3.3 风险与回滚

- 风险等级：`T3_FINANCIAL_RECONCILIATION_PRIVACY`。
- 输入边界：只读 immutable Git-object snapshot；未读取 worktree 财务文件，未修改真实源或数据库。
- 主要剩余风险：1,250 条转账缺少显式 link/account-role，249 条退款缺少 offset；均已进入 review queue，不能解释为已完成业务确认。
- 时间风险：来源只有日期粒度；标准化为 UTC 当日零点不代表真实交易时刻。
- 数据范围风险：余额、负债、持仓、市场价格和生产 FX 仍未加载，本 Phase 不支持净资产/现金余额/投资市值结论。
- 回滚：仅 revert 本 Phase 提交；Phase 3.1/3.2 合同和 Stage 2 immutable evidence 不变。无数据库或真实数据回滚动作。
- 停止条件：若需要真实源写入、来源名称推断、金额/时间近似挂链、fixture 替代真实输入或静默丢弃差异，则停止发布。
