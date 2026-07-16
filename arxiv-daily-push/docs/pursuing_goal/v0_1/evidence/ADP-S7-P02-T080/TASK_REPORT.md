# TASK_REPORT · ADP-S7-P02-T080｜补齐组件状态、Undo 与跨主题状态保持

- **Iteration**: ITER-20260716-ADP-V01-FINAL-EXECUTION
- **Task**: ADP-S7-P02-T080（Stage S7 UI/UX, Motion & Performance / S7-P02 移动端、组件状态与状态保持，size S）
- **release_mode**: NOT_DEPLOYED（改 worker 源 + 重算 BUILD `9690390a9fc8`→`40a46aa2baee`，不部署；live 仍 `b189d3cc0703`）
- **Depends**: ADP-S7-P01-T078（Visual/Motion Regression CI 门）

## 6 个前置问题
1. **哪些组件缺状态？** — base `button{}` 无 `:active`/`:disabled`/加载/成功/错误/聚焦；grade/run fetch 无 error 处理（失败即挂起）；无 Undo。
2. **怎样「点击 100ms 内反馈」？** — `button:active`（浏览器 pointerdown 即触发 <16ms）+ `transition:transform .08s`（80ms<100ms）；点击后 picked 类 + 撤销控件**同步**出现（Node 行为测试证）。
3. **Undo 怎么做到「不改写既有生产数据」？** — 乐观 Undo 窗：点击不立即写，起 4s 可取消倒计时（`_pend`），`/api/grade` POST 只在**延迟的 gradeCommit** 里发；`gradeUndo` 清计时器且**不 fetch** → 撤销**零写入**。
4. **怎样「切主题不丢状态」？** — `applyTheme` 只 setAttribute(data-theme…)+同步 hero/gauge，**不 reload/navigate/innerHTML 重建** → 阅读位置/答案/筛选/展开**天然保持**（属性交换不重置 DOM）。
5. **NOT_DEPLOYED？** — 改 worker 源 + 重算 build_id，不部署；live 不变。
6. **不破坏高级视觉？** — 只改 base CSS + 页面体 grade/run JS（非合同哈希）；6 主题 + 11 动效元素字节不变；走 T078 approved-change。

## 交付物
- **组件状态矩阵**（base CSS）：`button:active`/`:disabled`+`[aria-disabled]`/`[aria-busy]`/`:focus-visible`/`[data-state=ok|err]`/`button.undo` + `button{transition:transform .08s …}`；不新增 @keyframes（不动 motion 哈希）。
- **乐观 Undo 窗**：两处 grade() 客户端流程重写（studyPage 内联 + graderHTML）——点击 → picked + 撤销 + 4s 倒计时；撤销取消（零写入）；窗口结束 → gradeCommit 写一次；commit 加 `aria-busy` 加载态 + try/catch → `[data-state=err]` 错误态。run() 同样加 try/catch + aria-busy + 错误态。
- **工具** `tools/component_state_audit.py`：state_matrix/feedback_within_100ms/undo_defers_write/error_states_wired/applytheme_preserves_state/preserves_advanced_visual，均判别性（pre-fix 负控制）。
- **行为证明** `test-results/undo_behavior_test.js`（Node，跑**真实抽取**的 grade 客户端码，stub DOM/fetch/timer）：点击 0 写、撤销 0 写、窗口结束恰 1 写。
- **浏览器证明** `browser_measurements.json`（内置 Chromium）：6 主题切换全保 scroll/reveal/filter/details；状态 CSS 全计算（success/loading/disabled/:active/transition）。
- **known_gaps.md**（含延迟写权衡）、**pre_fix_worker.js/pre_fix_baseline.json**（T079 基线，负控制）、**独立对抗复核** `adversarial_review.md`。

## 验收（PASS，verifier 独立重算，exit 0）
证据：`test-results/component_state_tests.txt`（ACCEPTANCE = PASS）。

1. **点击 100ms 内反馈** — 状态矩阵 7/7；`:active` 原生 + transform 过渡 0.08s ≤100ms；点击同步出 picked+撤销（Node 测试）。**负控制**：pre-fix CSS 状态 0/7。
2. **切主题不丢状态** — applyTheme 仅 setAttribute+同步（无 reload/navigate/innerHTML）；**负控制**：注入 location.reload 的 applyTheme 被检出。**浏览器**：6 主题切换全保 scroll(600)/reveal/filter(量子纠错)/details(open)。
3. **Undo 不改写数据** — 点击不写、撤销不写、窗口结束恰 1 写（真实码 Node 测试 11/11）；**负控制**：pre-fix undo 属性 0/5。
4. **高级视觉保持** — specific 变化只 `base_css`；6 主题 + 11 动效元素字节相同；门 BLOCK 无 approval / PASS_APPROVED 带 approval。

## 实时未回归
NOT_DEPLOYED：改源 + 重算 build_id(40a46aa2baee)，不部署。live `/build.json`=b189d3cc0703（六主题+动效不变）。1 次只读 GET。

## 成本（unknown 不填 0）
生产 new_requests 0；D1 0；R2 0；model 0；cloud 0；只读 GET 1；in-app 浏览器渲染 1；Node 测试 1；人工=状态矩阵 CSS + 两处 grade 重写 + run 错误处理 + 审计工具 + 行为/浏览器测试 + 验证器 + 复核撰写。

## 独立验证
实现者**不自签 PASS**。交独立 Agent 复核（见 adversarial_review.md）。
IMPLEMENTATION_READY_FOR_INDEPENDENT_VERIFICATION
