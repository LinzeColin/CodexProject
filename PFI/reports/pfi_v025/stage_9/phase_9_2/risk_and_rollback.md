# Phase 9.2 Risk and Rollback

- `net_worth`、`cash`、`investment` 的必要生产来源未 ready，继续 `blocked`；不得将缺失值解释为零。
- `consumption`、`cashflow` 仅为来源覆盖与非金额敏感性 `partial`，不等于完整财务结论。
- 历史/样本外模型验证缺 ground truth，继续 blocked；不声明预测有效性或准确率。
- 正式 UI 必须保持同一 data/read-model/formula/parameter/base-report hash，并保留 7 个可行动复核入口。
- 公开配置、截图、trace 与 Evidence 不得包含财务金额、私有路径、账户标识或 runtime token。
- Phase 9.3、Stage 9 whole-stage review、push、App install、自动交易和 production/final acceptance 均不属于本轮。

Rollback：按逆序 revert Phase 9.2 Evidence/治理提交和两笔产品提交；不改写 Phase 9.1 immutable reports，也不触碰 accepted input artifacts、数据库或真实财务数据。
