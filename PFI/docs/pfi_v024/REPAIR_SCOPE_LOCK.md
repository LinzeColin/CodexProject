# PFI v0.2.4 Stage 0 Phase 0.1 Repair Scope Lock

## Run Boundary

本轮只执行 `PFI v0.2.4 Stage 0 / Phase 0.1 - 需求合同冻结`。

来源包仍命名为 `v0.2.3-repair`，但用户当前目标版本是 `v0.2.4`，因此仓库内
正式交付物使用 `pfi_v024` 和 `v0.2.4` 命名。

本轮不执行：

- Stage 0 Phase 0.2 历史约束废弃完整政策；
- Stage 0 Phase 0.3 测试与 Stage 0 总证据；
- Stage 0 whole-stage review；
- Stage 1 或后续功能开发；
- 业务 UI、app bundle、launcher 或数据逻辑修改。

Stage 0 未完成。完成 Phase 0.1 后必须停止，等待用户验收或明确指令进入
Phase 0.2。

## Product Contract

v0.2.4 修补包继承 v0.2.3 closeout 后的正式产品合同：

- 一级入口固定 10 个；
- `市场与研究` 是正式一级入口；
- 历史 9 入口约束不得恢复；
- 默认体验方向是亮色、高质感、人类任务流；
- 每次 run work 最多只完成一个 phase；
- 未经用户验收或明确指令，不得自动进入下一 phase/stage。

正式一级入口顺序：

1. 首页总览
2. 账户与资产
3. 账本流水
4. 投资管理
5. 消费管理
6. 数据源与上传
7. 建议与复盘
8. 报告与洞察
9. 市场与研究
10. 设置

## Data Trust Contract

正式 UI、报告、首页摘要、图表、建议和验收不得使用
`mock`、`sample`、`demo`、`synthetic`、`fixture`、`fake`
财务数据作为真实财务结论。

核心指标必须区分：

- `confirmed_zero`
- `not_loaded`
- `source_missing`
- `path_error`
- `parse_failed`
- `outdated_snapshot`
- `permission_denied`
- `calculation_failed`
- `filtered_empty`
- `ready`

未加载、路径错误、解析失败、权限失败、计算失败或筛选为空时，不得把财务金额
显示成全局真实 0。

## Phase 0.1 Task Mapping

| Task | Status | Evidence |
| --- | --- | --- |
| T0.1.1 写 repair 定位 | done | 本文件 |
| T0.1.2 写 10 入口机器合同 | done | `PFI/src/pfi_v02/stage_v024_repair_contract.py` |
| T0.1.3 写真实数据禁令 | done | 本文件与机器合同 |
| T0.1.4 写一轮一 Stage/Phase 规则 | done | 本文件与机器合同 |

