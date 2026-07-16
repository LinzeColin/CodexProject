# Phase 9.1 风险与回滚

- 最大风险是假完整：缺账户、负债、持仓、价格、FX、economic-event adapter 或 Phase 9.2 分析实现时，财务报告不得是 `complete`。
- `partial` 只允许明确 scope 的来源覆盖结论；不得输出金额、建议、模型有效性或确定性财务结论。
- data/read_model/formula/parameter 任一 hash 漂移即 fail closed，不允许页面或后续导出旁路。
- Evidence 只允许 aggregate metadata 和 hash；禁止账户标识、raw row、私密路径与财务数值。
- 本 Phase 不读写数据库、不修改真实数据、不修改公式/参数值，不 push、不安装、不进入 Phase 9.2。
- 回滚方式：回滚本地 Phase 9.1 commit；所有 Stage 2/4/7 accepted inputs 和既有报告保持原样。
