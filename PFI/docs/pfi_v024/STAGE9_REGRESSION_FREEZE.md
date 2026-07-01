# PFI v0.2.4 Stage 9 Regression Freeze

本轮只执行：`Stage 9 / Phase 9.3 - 用户验收`。
本轮只准备人工验收清单、reply protocol 和等待用户回复的 evidence；不写验收通过、不执行 Stage 9 whole-stage review、不上传 GitHub main、不进入未来版本、不重装 app bundle、不修改 launcher C/Info.plist、不写入、清理、删除、补造或改写真实财务数据。

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

## Phase 9.2 Scope

Phase 9.2 只生成候选交付冻结包，覆盖 roadmap 中的四个任务：

- `T9.2.1` 生成最终 evidence index。
- `T9.2.2` README 写候选状态。
- `T9.2.3` 列出未做事项。
- `T9.2.4` 列出后续风险。

当前候选冻结明确等待 Phase 9.3 用户验收，不声明 Stage 9 已完成最终交付。

## Phase 9.2 Evidence

- `PFI/reports/pfi_v024/stage_9/phase_9_2/final_evidence_index.json`
- `PFI/reports/pfi_v024/stage_9/phase_9_2/closeout_candidate.md`
- `PFI/reports/pfi_v024/stage_9/phase_9_2/evidence.json`
- `PFI/reports/pfi_v024/stage_9/phase_9_2/terminal.log`
- `PFI/reports/pfi_v024/stage_9/phase_9_2/changed_files.txt`
- `PFI/reports/pfi_v024/stage_9/phase_9_2/risk_and_rollback.md`

## Phase 9.3 Scope

Phase 9.3 只输出用户验收材料并停止等待用户回复，覆盖 roadmap 中的三个任务：

- `T9.3.1` 输出人工验收清单。
- `T9.3.2` 停止等待用户验收。
- `T9.3.3` 不自动进入未来版本。

当前状态是 `waiting_for_user_acceptance`。本 phase 不把用户确认写成事实，不执行整阶段复审，不执行 GitHub main upload。

## Phase 9.3 Evidence

- `PFI/reports/pfi_v024/stage_9/phase_9_3/manual_acceptance.md`
- `PFI/reports/pfi_v024/stage_9/phase_9_3/reply_protocol.md`
- `PFI/reports/pfi_v024/stage_9/phase_9_3/evidence.json`
- `PFI/reports/pfi_v024/stage_9/phase_9_3/terminal.log`
- `PFI/reports/pfi_v024/stage_9/phase_9_3/changed_files.txt`
- `PFI/reports/pfi_v024/stage_9/phase_9_3/risk_and_rollback.md`

## Non Goals

- 不写验收通过。
- 不把 Phase 9.3 等待状态写成 Stage 9 最终 closeout。
- 不执行 Stage 9 whole-stage review。
- 不上传 GitHub main。
- 不进入未来版本。
- 不修改 app bundle、launcher 或真实财务数据。

## Stop Condition

停止在 `Stage 9 / Phase 9.3 - 用户验收材料已准备，等待用户回复`。Stage 9 whole-stage review 必须下一轮再进入，且必须有用户明确验收或明确指令。
