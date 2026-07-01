# PFI v0.2.4 Stage 5 Phase 5.3 - Interaction States

## Scope

本轮只执行 `Stage 5 / Phase 5.3 - 交互状态`。

不执行 Stage 5 whole-stage review，不上传 GitHub main，不重装 app，不写入或补造用户财务数据。

## Deliverables

- `PFI/web/app/ux_state.js`：从 Phase 5.2 的 45 个二级业务页生成 `loading / success / error / empty` 四态。
- `PFI/web/app/shell.js`：在二级页面 surface 渲染四态卡片，并把 empty/error 等动作接到真实 route。
- `PFI/web/index.html` 与 `PFI/src/pfi_os/app/streamlit_app.py`：保证 `ux_state.js` 在 `stage5Subpages.js` 之后、`shell.js` 之前加载。
- `PFI/tests/test_v024_stage5_phase53_interaction_states.py`：锁定合同、可行动空态、history/back-forward 合同、bundle 加载和 evidence。
- `PFI/reports/pfi_v024/stage_5/phase_5_3/`：保存 validation、history、terminal、rollback 和 evidence。

## Contract

- 每个二级页面必须拥有四类状态：`loading`、`success`、`error`、`empty`。
- 空状态必须是中文可行动状态，按钮必须有 label、target workspace 和 route alias。
- 错误状态必须提供可重试动作，不能只显示说明文字。
- 后退/前进验收覆盖 route alias、`pushState`、`replaceState`、`hashchange`、`popstate` 和 route state preservation。
- 本轮继续继承 Phase 5.1 与 Phase 5.2，不进入整阶段复审。

## Validation

Phase 5.3 machine validation:

- `ux_state_validation.json`: pass, `total_page_count=45`
- `history_validation.json`: pass, `duplicate_route_aliases=[]`

Final command results are recorded in `PFI/reports/pfi_v024/stage_5/phase_5_3/terminal.log`.
