# PFI v0.2.4 Stage 9 Regression Freeze

本轮只执行：`Stage 9 / Phase 9.1 - 回归规则`。
本轮不执行 Phase 9.2 交付冻结、不执行 Phase 9.3 用户验收、不执行 Stage 9 whole-stage review、不上传 GitHub main、不重装 app bundle、不修改 launcher C/Info.plist、不写入、清理、删除、补造或改写真实财务数据。

## Phase 9.1 Scope

Phase 9.1 建立防复发规则，覆盖 roadmap 中的四个任务：

- `T9.1.1` 旧 UI signature 测试。
- `T9.1.2` 入口堆叠测试。
- `T9.1.3` 假零测试。
- `T9.1.4` mock 财务数据测试。

同时把 Stage 9 acceptance 中的机械文案和暗色控制台默认风格列为 guardrail 定义，供后续 Phase 9.2/9.3 与整阶段复审继承。

## Guardrails

| Guardrail | 当前规则 | 当前结果 |
| --- | --- | --- |
| 旧 UI signature | 扫描 `web/index.html` 和 `web/app/shell.js`，禁止 `功能面板`、`PFI 功能入口`、`功能已准备`、`进入操作面板`、`系统能力面板`、`Task Pack`、`Prototype`、`AI console`、`运行边界`、`验收边界`、`安全边界` 等旧 UI signature 作为 runtime 文案回归。 | pass |
| 入口堆叠 | 解析桌面与移动正式一级入口，必须均为 10 个固定入口；`首页`、`市场`、`研究`、`持仓`、`策略实验室`、`数据与系统` 只能作为兼容 alias/command，不得成为同层一级入口。 | pass |
| 假零 | 复用 Stage 4 数据状态机：非 `ready` / `confirmed_zero` 状态不得渲染 `CNY 0.00`；`confirmed_zero` 必须携带 source、record_count、as_of、formula、confidence 证据链。 | pass |
| mock 财务数据 | 复用 Stage 4 forbidden financial data scanner，扫描正式财务 runtime payload `web/app/data_state.js`，禁止 mock/sample/synthetic/fixture/demo/fake 财务数据进入正式验收。 | pass |
| 机械文案 | Phase 9.1 固定 scoped guardrail；报告和设置可有人类可读公式、参数、依据，但旧默认机械功能面板不得回归。 | defined |
| 暗色控制台默认风格 | Phase 9.1 固定 dark console default guardrail；默认正式 UI 继续继承亮色高质感方向。 | defined |

## Evidence

- `PFI/reports/pfi_v024/stage_9/phase_9_1/evidence.json`
- `PFI/reports/pfi_v024/stage_9/phase_9_1/regression_guardrails.json`
- `PFI/reports/pfi_v024/stage_9/phase_9_1/terminal.log`
- `PFI/reports/pfi_v024/stage_9/phase_9_1/changed_files.txt`
- `PFI/reports/pfi_v024/stage_9/phase_9_1/risk_and_rollback.md`

## Non Goals

- 不生成最终 `final_evidence_index.json`。
- 不写 `closeout_candidate.md`。
- 不声明用户已验收或交付冻结已确认。
- 不执行 Stage 9 whole-stage review。
- 不上传 GitHub main。
- 不修改 app bundle、launcher 或真实财务数据。

## Stop Condition

停止在 `Stage 9 / Phase 9.1 - 回归规则 candidate pass`。Phase 9.2 必须下一轮再进入。
