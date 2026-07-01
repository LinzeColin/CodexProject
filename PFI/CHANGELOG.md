# CHANGELOG

## v0.2.4 Repair Pack Stage 7 Phase 7.3 - 2026-07-01

- 完成 `Stage 7 / Phase 7.3 - 验收`：验收报告中心 6 类报告、数据不足报告、公式/参数/样本量/数据范围可见性和反单段 AI 文本退化。
- `PFI/web/app/pages/reports.js` 新增 `PFI-V024-STAGE7-PHASE73-ACCEPTANCE` 合同和 report acceptance gate。
- 新增 `PFI/scripts/validate_v024_stage7_phase73_report_acceptance.js`，生成浏览器验收、数据质量 HTML 和 `formula_visibility.png`。
- 新增 `PFI/tests/test_v024_stage7_phase73_report_acceptance.py` 和 `PFI/reports/pfi_v024/stage_7/phase_7_3/` evidence。
- 本轮不执行 Stage 7 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 7 Phase 7.2 - 2026-07-01

- 完成 `Stage 7 / Phase 7.2 - 页面展示`：报告中心页面接入 Phase 7.1 报告结构，展示净资产、现金、投资、消费、现金流、数据质量 6 份报告。
- `PFI/web/app/pages/reports.js` 新增 `PFI-V024-STAGE7-PHASE72-PAGE-DISPLAY` 合同、report center view model 和页面显示验证。
- `PFI/web/app/shell.js` 通过 `PFI_V024_STAGE7_REPORTS` 把结论、公式、参数、样本量、数据范围、置信度、缺口和复核入口映射到 `报告与洞察`。
- `PFI/web/index.html` 与 `PFI/src/pfi_os/app/streamlit_app.py` 同步加载/内联 `reports.js` 和 Phase 7.1 `report_schema.json`，防止 app bundle 漂移。
- 新增 `PFI/tests/test_v024_stage7_phase72_report_page_display.py` 和 `PFI/reports/pfi_v024/stage_7/phase_7_2/` evidence。
- 本轮不执行 Phase 7.3 验收、Stage 7 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 7 Phase 7.1 - 2026-07-01

- 完成 `Stage 7 / Phase 7.1 - 报告结构`：建立 v0.2.4 报告 schema、6 类报告类型、数据不足阻断规则和导出字段。
- 新增 `PFI/src/pfi_v02/stage_v024_stage7_report_analysis.py`、`PFI/tests/test_v024_stage7_phase71_report_schema.py`、`PFI/docs/pfi_v024/STAGE7_REPORT_ANALYSIS.md` 和 `PFI/reports/pfi_v024/stage_7/phase_7_1/` evidence。
- 报告结构读取 Stage 4 真实 read model status：`MetaDatabase/PFI` ready，`8815` 条记录，`4` 个原始文件，as of `2026-06-03`；净资产/现金/投资/现金流缺少输入时保持 blocked。
- 本轮不执行 Phase 7.2 页面展示、Phase 7.3 验收、Stage 7 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 6 GitHub Main Upload - 2026-07-01

- 完成 `Stage 6 GitHub main upload gate`：将 Stage 6 Phase 6.1、Phase 6.2、Phase 6.3 和 whole-stage review package rebase 到当前 `origin/main` 后上传。
- 新增 `PFI/src/pfi_v02/stage_v024_stage6_experience.py`、`PFI/docs/pfi_v024/STAGE6_GITHUB_MAIN_UPLOAD.md`、`PFI/tests/test_v024_stage6_github_upload_contract.py` 和 `PFI/reports/pfi_v024/stage_6/github_main_upload/evidence.json`。
- 上传 gate 重新验证 Stage 6 upload contract、whole-stage review、Phase 6.1/6.2/6.3 回归、Stage 5 相邻回归、browser validation、JS syntax、JSON evidence 和 diff。
- 本轮不执行 Stage 7，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## v0.2.4 Repair Pack Stage 6 Whole-Stage Review - 2026-07-01

- 完成 `Stage 6 whole-stage review - 复审并解决暴露问题`，复审 Phase 6.1 设计系统、Phase 6.2 动效反馈、Phase 6.3 触感与设置隔离。
- 新增 `PFI/tests/test_v024_stage6_whole_review_contract.py`、`PFI/docs/pfi_v024/STAGE6_WHOLE_STAGE_REVIEW.md` 和 `PFI/reports/pfi_v024/stage_6/whole_stage_review/` evidence。
- 新增 `PFI/scripts/validate_v024_stage6_whole_review_browser.js`，生成 `desktop_light_home.png`、`mobile_responsive.png` 和 `settings_feedback_isolation.png`。
- 修复复审暴露的亮色 fallback 问题：v0.2.4 body 增加实体 `background-color`，并让趋势图读取 body scoped token，避免旧 root token 造成深色图表槽。
- 复审发现 4 项均已 fixed；本轮不执行 GitHub main upload，不进入 Stage 7，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 6 Phase 6.3 - 2026-07-01

- 完成 `Stage 6 / Phase 6.3 - 触感与设置隔离`：新增 haptics capability detection、设置页反馈偏好模型和不支持设备的静默视觉降级。
- `PFI/web/app/feedback.js` 新增 v0.2.4 Phase 6.3 haptics contract、runtime capability detection 和 haptics settings model。
- `PFI/web/app/pages/settings.js` 新增反馈设置 view model，明确触感、声音、动效控制只在设置页管理。
- `PFI/web/app/shell.js` 写入 `data-v024-haptic-capability`、`data-v024-haptic-degraded` 和 `data-v024-feedback-setting` 运行态标记，并保持业务页面无反馈控制台。
- 新增 `PFI/tests/test_v024_stage6_phase63_haptics_settings.py`、`PFI/docs/pfi_v024/STAGE6_HAPTICS_SETTINGS.md` 和 `PFI/reports/pfi_v024/stage_6/phase_6_3/` evidence。
- 本轮不执行 Stage 6 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 6 Phase 6.2 - 2026-07-01

- 完成 `Stage 6 / Phase 6.2 - 动效反馈`：新增页面切换、加载骨架、成功/失败/阻断反馈和报告生成进度的轻量动效。
- `PFI/web/app/feedback.js` 新增 v0.2.4 Phase 6.2 motion contract、feedback model 和 report progress model。
- `PFI/web/app/shell.js` 写入 `data-v024-route-transition`、`data-v024-motion-state`、`data-v024-report-progress` 等运行态标记。
- `PFI/web/styles.css` 新增 `PFI v0.2.4 Stage 6 Phase 6.2 motion feedback` 样式块，并支持 reduced motion。
- 新增 `PFI/tests/test_v024_stage6_phase62_motion_feedback.py`、`PFI/docs/pfi_v024/STAGE6_MOTION_FEEDBACK.md` 和 `PFI/reports/pfi_v024/stage_6/phase_6_2/` evidence。
- 本轮不执行 Phase 6.3、Stage 6 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 6 Phase 6.1 - 2026-07-01

- 完成 `Stage 6 / Phase 6.1 - 设计系统`：建立 v0.2.4 默认浅色 token、状态色、卡片/表格/图表槽和响应式布局覆盖层。
- `PFI/web/index.html` 锁定 `color-scheme=light`，并新增 `data-v024-stage6-design-system="phase_6_1"`。
- `PFI/web/styles.css` 新增 `body[data-pfi-target-version="v0.2.4"]` 作用域 token，不进入动效或触感实现。
- 新增 `PFI/tests/test_v024_stage6_phase61_design_system.py`、`PFI/docs/pfi_v024/STAGE6_DESIGN_SYSTEM.md` 和 `PFI/reports/pfi_v024/stage_6/phase_6_1/` evidence。
- 本轮不执行 Phase 6.2、Phase 6.3、Stage 6 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 5 GitHub Main Upload - 2026-07-01

- 准备 `Stage 5 GitHub main upload gate`：将 Stage 5 Phase 5.1、Phase 5.2、Phase 5.3 和 whole-stage review package 上传到 GitHub main。
- 新增 `PFI/src/pfi_v02/stage_v024_stage5_experience.py`、`PFI/docs/pfi_v024/STAGE5_GITHUB_MAIN_UPLOAD.md`、`PFI/tests/test_v024_stage5_github_upload_contract.py` 和 `PFI/reports/pfi_v024/stage_5/github_main_upload/evidence.json`。
- 上传 gate 重新验证 Stage 5 upload contract、whole-stage review、Phase 5.1/5.2/5.3 回归、Stage 3/4 相邻回归、JS syntax、JSON evidence 和 diff。
- 本轮不执行 Stage 6，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## v0.2.4 Repair Pack Stage 5 Whole-Stage Review - 2026-07-01

- 完成 `Stage 5 whole-stage review - 复审并解决暴露问题`，复审 Phase 5.1 首页、Phase 5.2 二级页面差异化、Phase 5.3 交互状态。
- 新增 `PFI/tests/test_v024_stage5_whole_review_contract.py`、`PFI/docs/pfi_v024/STAGE5_WHOLE_STAGE_REVIEW.md` 和 `PFI/reports/pfi_v024/stage_5/whole_stage_review/` evidence。
- 新增 `PFI/scripts/validate_v024_stage5_whole_review_browser.js`，生成 10 个一级入口和 10 个核心二级页面截图，browser validation 为 pass。
- 修复静态浏览器验收中可选 `/api/read-model-status` 404：`index.html` 关闭静态可选 fetch，Streamlit runtime 显式启用 `readModelStatusApi`。
- 复审发现 3 项均已 fixed：缺少 whole-stage review gate、缺少截图覆盖、静态 runtime 可选 endpoint 404。
- 本轮不执行 GitHub main upload，不进入 Stage 6，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 5 Phase 5.3 - 2026-07-01

- 完成 `Stage 5 / Phase 5.3 - 交互状态`：45 个二级业务页面均有 `loading / success / error / empty` 四态。
- 新增 `PFI/web/app/ux_state.js`，暴露 `PFI_V024_STAGE5_UX_STATE`、Phase 5.3 合同、页面状态模型、UX validation 和 history acceptance。
- `PFI/web/app/shell.js` 在二级页面 surface 渲染四态卡片，并把 empty/error 动作接到真实 route，不只显示说明或 toast。
- `PFI/web/index.html` 与 `PFI/src/pfi_os/app/streamlit_app.py` 同步加载/内联 `ux_state.js`，防止 app bundle 漂移。
- 新增 `PFI/tests/test_v024_stage5_phase53_interaction_states.py`、`PFI/docs/pfi_v024/STAGE5_INTERACTION_STATES.md` 和 `PFI/reports/pfi_v024/stage_5/phase_5_3/` evidence。
- 本轮不执行 Stage 5 whole-stage review 或 GitHub main upload；不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 5 Phase 5.2 - 2026-07-01

- 完成 `Stage 5 / Phase 5.2 - 二级页面差异化`：10 个正式一级入口共 45 个二级页面，最少每个入口 4 个。
- 新增 `PFI/web/app/pages/stage5Subpages.js`，暴露 `PFI_V024_STAGE5_PAGES`、Phase 5.2 合同、catalog flatten 和 route validation。
- `PFI/web/app/shell.js` 优先读取 v0.2.4 Stage 5 页面目录，并给二级页 DOM 标记 `data-stage5-state-key` 和 `data-stage5-data-object`。
- `PFI/web/index.html` 与 `PFI/src/pfi_os/app/streamlit_app.py` 同步加载/内联 `stage5Subpages.js`，防止 app bundle 漂移。
- 新增 `PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py`、`PFI/docs/pfi_v024/STAGE5_SUBPAGE_DIFFERENTIATION.md` 和 `PFI/reports/pfi_v024/stage_5/phase_5_2/route_validation.json`。
- 本轮不执行 Phase 5.3、Stage 5 whole-stage review 或 GitHub main upload；不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 5 Phase 5.1 - 2026-07-01

- 完成 `Stage 5 / Phase 5.1 - 首页重建`：首页新增“钱、位置、变化、问题、下一步、依据”六问结构。
- 新增 `PFI_V024_STAGE5_HOME`、`buildV024Stage5Phase51Contract()` 和 `buildV024Stage5Phase51HomeViewModel()`，读取 Stage 4 `read_model_status` 生成首页数据状态卡与下一步任务流。
- `PFI/web/index.html` 移除默认 `功能面板 / PFI 功能入口 / 功能已准备 / 进入操作面板` 机械层文案，并加载 `./app/pages/home.js`。
- `PFI/web/app/shell.js` 优先使用 v0.2.4 首页 API，把 `#pfi-read-model-status` 传给首页模型。
- 新增 `PFI/tests/test_v024_stage5_phase51_home_rebuild.py`、`PFI/docs/pfi_v024/STAGE5_HOME_REBUILD.md` 和 `PFI/reports/pfi_v024/stage_5/phase_5_1/evidence.json`。
- 本轮不执行 Phase 5.2、Phase 5.3、Stage 5 whole-stage review 或 GitHub main upload；不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 4 GitHub Main Upload - 2026-07-01

- 完成 `Stage 4 GitHub main upload gate`：将 Stage 4 Phase 4.1、Phase 4.2、Phase 4.3 和 whole-stage review package rebase 到当前 `origin/main` 后上传。
- 新增 `PFI/docs/pfi_v024/STAGE4_GITHUB_MAIN_UPLOAD.md`、`PFI/tests/test_v024_stage4_github_upload_contract.py` 和 `PFI/reports/pfi_v024/stage_4/github_main_upload/evidence.json`。
- 上传 gate 重新验证 Stage 4 非假零、read model 挂链、whole-stage review、JS syntax、JSON evidence 和 diff。
- 本轮不执行 Stage 5，不重装 app bundle，不修改 launcher C/Info.plist，不写入、清理、删除、补造或改写真实财务数据。

## v0.2.4 Repair Pack Stage 4 Whole-Stage Review - 2026-07-01

- 完成 `Stage 4 whole-stage review - 复审并解决暴露问题`，复审 Phase 4.1 状态机、Phase 4.2 read model 挂链、Phase 4.3 非假零验收。
- 新增 `PFI/docs/pfi_v024/STAGE4_WHOLE_STAGE_REVIEW.md`、`PFI/tests/test_v024_stage4_whole_review_contract.py` 和 `PFI/reports/pfi_v024/stage_4/whole_stage_review/evidence.json`。
- 复审发现 3 项均已 fixed：缺少 whole-stage review gate、顶层状态仍停在 Phase 4.3、Phase 4.3 浏览器证据需纳入整阶段验收。
- 重新验证 Stage 4 四个测试文件，`21 passed`；JS check、JSON evidence check 和截图 size 证据通过。
- 本轮不执行 GitHub main upload，不重装 app bundle，不修改真实财务数据源，不进入 Stage 5。

## v0.2.4 Repair Pack Stage 4 Phase 4.3 - 2026-07-01

- 完成 `Stage 4 / Phase 4.3 - 验收`：用测试和 Chrome headless 截图验证缺失数据不显示财务 0、真零必须携带证据链。
- 新增 `PFI/tests/test_v024_stage4_phase43_acceptance.py`，覆盖 blocked 指标不渲染 `CNY 0.00`、`confirmed_zero` 缺证据报错、前端 null `record_count/confidence` 不得变成 0。
- 新增 `PFI/scripts/validate_v024_stage4_phase43_chrome.py`，生成 Phase 4.3 browser validation、两张截图和 evidence pack。
- 修复 `PFI/web/app/data_state.js` 与 `PFI/web/app/shell.js`：`record_count=null` 和 `confidence=null` 保持未知，不再显示成 `0 条记录`。
- 当前真实数据状态仍为 `MetaDatabase/PFI` ready，`8815` 条记录、`4` 个原始文件、as of `2026-06-03`；真实生产指标中 `confirmed_zero` 数量为 `0`。
- 本轮不执行 Stage 4 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 4 Phase 4.2 - 2026-07-01

- 完成 `Stage 4 / Phase 4.2 - read model 挂链`：新增 shared read model status，把 Phase 4.1 数据状态机接入首页、账户、投资、消费和报告卡片状态。
- 新增 `PFI/src/pfi_os/application/read_model_status.py`，输出 `data_source_scan`、`read_model_status`、`core_metric_states` 和五个 surface 的共享状态。
- `PFI/src/pfi_v02/stage_v021_runtime_api.py` 新增 `/api/read-model-status`；`PFI/src/pfi_os/app/streamlit_app.py` 同步嵌入 `#pfi-read-model-status`。
- `PFI/web/app/data_state.js` 新增 shared surface view model；`PFI/web/app/shell.js` 读取 `/api/read-model-status` 并覆盖首页/账户/投资/消费/报告核心卡片，缺失状态不显示 `CNY 0.00`。
- 当前真实数据状态：`MetaDatabase/PFI` ready，`8815` 条记录、`4` 个原始文件、as of `2026-06-03`；净资产、现金余额和投资市值仍为 `source_missing`，消费总流出为 `ready`。
- 本轮不执行 Phase 4.3 验收、Stage 4 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 4 Phase 4.1 - 2026-07-01

- 完成 `Stage 4 / Phase 4.1 - 状态机定义`：冻结核心财务指标数据状态枚举、指标状态 schema、中文阻断原因和禁止假零规则。
- 新增 `PFI/src/pfi_v02/stage_v024_stage4_data_state.py`，提供 `PFI-V024-STAGE4-PHASE41-DATA-STATE` 合同、metric state builder、渲染守卫和运行时禁用词扫描。
- 新增 `PFI/web/app/data_state.js`，供后续 Phase 4.2/4.3 前端挂链复用；非 ready 状态返回中文原因，不渲染 `CNY 0.00`。
- 新增 `PFI/docs/pfi_v024/STAGE4_DATA_STATE_MACHINE.md`、`PFI/tests/test_v024_stage4_phase41_data_state_contract.py`、`PFI/tests/test_v024_stage4_no_mock_financial_data.py` 和 `PFI/reports/pfi_v024/stage_4/phase_4_1/evidence.json`。
- 本轮不执行 Phase 4.2 read model 挂链、Phase 4.3 验收、Stage 4 whole-stage review 或 GitHub main upload；不重装 app bundle，不修改真实财务数据源。

## v0.2.4 Repair Pack Stage 3 GitHub Main Upload - 2026-07-01

- 完成 `Stage 3 GitHub main upload gate`：将 Stage 3 Phase 3.1、Phase 3.2、Phase 3.3 和 whole-stage review package rebase 到当前 `origin/main` 后上传。
- 新增 `PFI/docs/pfi_v024/STAGE3_GITHUB_MAIN_UPLOAD.md`、`PFI/tests/test_v024_stage3_github_upload_contract.py` 和 `PFI/reports/pfi_v024/stage_3/github_main_upload/evidence.json`。
- 上传 gate 重新验证 Stage 3 浏览器导航、v0.2.4 回归、v0.2.3 Stage 3 兼容、JSON 和 diff。
- 本轮不执行 Stage 4、不重装 app bundle、不修改 launcher C/Info.plist、不修改真实数据逻辑。

## v0.2.4 Repair Pack Stage 3 Whole-Stage Review - 2026-07-01

- 完成 `Stage 3 whole-stage review - 复审并解决暴露问题`，复审 Phase 3.1、Phase 3.2 和 Phase 3.3 的合同、route、DOM、browser history 和 evidence。
- 新增 `PFI/docs/pfi_v024/STAGE3_WHOLE_STAGE_REVIEW.md`、`PFI/tests/test_v024_stage3_whole_review_contract.py` 和 `PFI/reports/pfi_v024/stage_3/whole_stage_review/evidence.json`。
- 修复复审发现的 3 个 Stage 3 范围问题：缺少 whole-stage review gate、顶层状态仍停在 Phase 3.3、Phase 3.3 浏览器证据需要 review-time refresh。
- 重新运行 Node Playwright 验收，刷新 `phase_3_3/browser_validation.json`、`legacy_routes_validation.json` 和截图证据。
- Stage 3 本地整阶段复审完成；本轮未执行 GitHub main upload、Stage 4、app bundle reinstall、真实数据逻辑修改。

## v0.2.4 Repair Pack Stage 3 Phase 3.3 - 2026-07-01

- 完成 `Stage 3 / Phase 3.3 - 导航验收`：真实浏览器验证 desktop/mobile 各 10 个一级入口，`市场与研究` 保持第 9 个正式一级入口。
- 新增 `PFI/scripts/validate_v024_stage3_phase33_browser.js`，用 Node Playwright 启动本地静态 HTTP server，实际加载 `PFI/web/index.html` 验证点击导航、direct URL alias 和 browser back/forward。
- 新增 `PFI/tests/test_v024_stage3_phase33_navigation_acceptance.py`，锁定 Phase 3.3 contract、browser validation JSON、legacy route JSON、截图和 evidence pack。
- 扩展 `PFI/src/pfi_v02/stage_v024_stage3_navigation.py`，新增 Phase 3.3 navigation acceptance contract。
- 新增 `PFI/reports/pfi_v024/stage_3/phase_3_3/` evidence，包括 `browser_validation.json`、`legacy_routes_validation.json`、`desktop_nav.png` 和 `browser_back_after_forward.png`。
- 本轮未执行 Stage 3 whole-stage review、app bundle reinstall、真实数据逻辑修改或 GitHub main upload。

## v0.2.4 Repair Pack Stage 3 Phase 3.2 - 2026-07-01

- 完成 `Stage 3 / Phase 3.2 - 路由实现`：`PFI/web/app/routes.js` 暴露 `window.PFI_V024_STAGE3_ROUTES`，可解析一级 route、二级 route 和 v0.1 alias redirect。
- 新增 `PFI/tests/test_v024_stage3_phase32_route_implementation.py`，用 Node 调用真实 route API 验证 10 个一级 route、45 个二级 route 和 6 个旧入口 redirect。
- `PFI/web/app/shell.js` 优先调用 `PFI_V024_STAGE3_ROUTES.resolveRouteAlias()`，再进入旧 fallback；保留 hash、`pushState`、`replaceState`、`hashchange` 和 `popstate` runtime 声明。
- 扩展 `PFI/src/pfi_v02/stage_v024_stage3_navigation.py`，新增 Phase 3.2 route contract。
- 新增 `PFI/reports/pfi_v024/stage_3/phase_3_2/evidence.json`。
- 本轮未执行 Phase 3.3 浏览器历史验收、Stage 3 whole-stage review、app bundle reinstall、真实数据逻辑修改或 GitHub main upload。

## v0.2.4 Repair Pack Stage 3 Phase 3.1 - 2026-06-30

- 完成 `Stage 3 / Phase 3.1 - 导航合同`：正式一级入口固定 10 个，`市场与研究` 保持第 9 个正式一级入口。
- 新增 `PFI/web/app/navigation.js` 和 `PFI/src/pfi_v02/stage_v024_stage3_navigation.py`，将 v0.2.4 Stage 3 导航合同独立为前端和 Python 可验证资源。
- `首页`、`市场`、`研究`、`持仓`、`策略实验室`、`数据与系统` 保留为 v0.1 alias/command，不作为同级一级入口。
- `PFI/web/index.html` 加载 `navigation.js` 后再加载 `routes.js`；`PFI/src/pfi_os/app/streamlit_app.py` 同步内联该脚本，避免 app/localhost bundle 漂移。
- 新增 `PFI/tests/test_v024_stage3_phase31_navigation_contract.py`、`PFI/docs/pfi_v024/STAGE3_NAVIGATION_ROUTING.md` 和 `PFI/reports/pfi_v024/stage_3/phase_3_1/evidence.json`。
- 本轮未执行 Phase 3.2、Phase 3.3、Stage 3 whole-stage review、app bundle reinstall、真实数据逻辑修改或 GitHub main upload。

## v0.2.4 Repair Pack Stage 2 Whole-Stage Review - 2026-06-30

- 完成 `Stage 2 whole-stage review - 复审并解决暴露问题`，复审 Phase 2.1、Phase 2.2、Phase 2.3 的入口链路、版本链路、真实浏览器验收和 evidence。
- 新增 `PFI/docs/pfi_v024/STAGE2_WHOLE_STAGE_REVIEW.md`、`PFI/tests/test_v024_stage2_whole_review_contract.py` 和 `PFI/reports/pfi_v024/stage_2/whole_stage_review/evidence.json`。
- 修复复审发现的证据漂移：重新运行 Phase 2.3 真实浏览器验收，使 `phase_2_3/evidence.json` 记录当前 Stage 2 review baseline。
- Stage 2 本地整阶段复审完成；本轮未进入 Stage 3、未重装 app bundle、未修改 launcher C/Info.plist、未修改真实财务数据逻辑、未上传 GitHub main。

## v0.2.4 Repair Pack Stage 2 Phase 2.3 - 2026-06-30

- 完成 `Stage 2 / Phase 2.3 - 实机验收`：localhost、app、清缓存浏览器上下文、新 Profile 四条路径均读取同一 Stage 2 build id 和 bundle hash。
- 新增 `PFI/scripts/validate_v024_stage2_phase23_entry.js`，生成 `browser_validation.json` 和四张真实浏览器截图。
- 修复 Phase 2.3 暴露的同路径旧服务复用问题：`PFI/StartPFI.command` 和 `PFI/scripts/startPFI.sh` 只复用带当前 build/UI contract marker 的 Streamlit 服务。
- 当前真实验收服务为 `http://127.0.0.1:8502`；旧 `8501` 同路径服务不再作为当前 build 入口复用。
- 本轮未执行 Stage 2 whole-stage review、未进入 Stage 3、未重装 app bundle、未修改 launcher C/Info.plist、未修改真实财务数据逻辑、未上传 GitHub main。

## v0.2.4 Repair Pack Stage 2 Phase 2.2 - 2026-06-30

- 完成 `Stage 2 / Phase 2.2 - 版本链路实现`：页面可见 `PFI v0.2.3 Repair`、build id、bundle version、bundle hash 和 UI contract version。
- 新增 `PFI/web/app/entry_audit.js`，提供 `window.PFI_READ_STAGE2_ENTRY_AUDIT` 给 Phase 2.3 真实 app/local/browser 验收读取。
- `PFI/web/app/version.js` 升级为 Stage 2 entry version metadata，同时保留 Stage 1 shell integrity compatibility fields。
- `PFI/web/app/shell.js` 会把 Streamlit 注入的动态 runtime metadata 写入 body dataset 和入口身份条。
- `PFI/web/styles/tokens.css` 为入口身份条提供稳定 top-bar 布局，并纳入 Stage 2 bundle hash。
- `PFI/StartPFI.command` 和 `PFI/scripts/startPFI.sh` 的 versioned URL 改为 `pfi-v024-stage2-phase22` / `PFI-V024-STAGE2-ENTRY-CONSISTENCY`。
- 本轮未执行 Phase 2.3 实机验收、未重装 app bundle、未修改 launcher C/Info.plist、未修改真实财务数据逻辑、未上传 GitHub main。

## v0.2.4 Repair Pack Stage 2 Phase 2.1 - 2026-06-30

- 完成 `Stage 2 / Phase 2.1 - 入口链路映射`：定位 macOS app、StartPFI、Streamlit、静态 HTML、shell runtime 和 version runtime 的当前链路。
- 新增 `src/pfi_v02/stage_v024_stage2_entry_consistency.py`、`tests/test_v024_stage2_phase21_entry_mapping.py` 和 `reports/pfi_v024/stage_2/phase_2_1/evidence.json`。
- 新增 `entry_map.md`、`old_ui_signatures.json` 和 `build_hash_display_spec.md`，记录旧 v0.2.3 Stage 1 入口签名并指定 Phase 2.2 的 build/hash 展示位置。
- 本轮未实现 Phase 2.2、未执行 Phase 2.3 实机验收、未修改 app bundle/launcher/业务 UI/真实数据逻辑、未上传 GitHub main。

## v0.2.4 Repair Pack Stage 1 Whole-Stage Review - 2026-06-30

- 完成 `Stage 1 whole-stage review - 复审并解决暴露问题`，复审 Phase 1.1、Phase 1.2、Phase 1.3 的合同、证据、测试和状态文件。
- 修复复审发现的两个 Stage 1 范围问题：缺少整体复审合同/evidence，以及顶层 run/status 文件仍停留在 Phase 1.3。
- 新增 `docs/pfi_v024/STAGE1_WHOLE_STAGE_REVIEW.md`、`tests/test_v024_stage1_whole_review_contract.py` 和 `reports/pfi_v024/stage_1/whole_stage_review/evidence.json`。
- Stage 1 已本地整体复审完成；Stage 2 和 GitHub main upload 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher 或真实指标计算。

## v0.2.4 Repair Pack Stage 1 Phase 1.3 - 2026-06-30

- 完成 `Stage 1 / Phase 1.3 - 验证`：记录 `node --check`、pytest 合同测试和 changed files audit。
- 新增 `tests/test_v024_stage1_phase13_validation_closeout.py` 和 `reports/pfi_v024/stage_1/phase_1_3/evidence.json`。
- Stage 1 当前为 candidate complete；whole-stage review、复审问题修复和 GitHub main upload 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher、`shell.js` 或真实指标计算。

## v0.2.4 Repair Pack Stage 1 Phase 1.2 - 2026-06-30

- 完成 `Stage 1 / Phase 1.2 - 最小恢复`：在 `shell.js` 中新增 `window.PFI_STAGE1_SHELL`，暴露 version、initialize、mountRoute 和 errorBoundary。
- 新增 `PFI/web/app/version.js`，提供 `window.PFI_STAGE1_VERSION` 和 `window.PFI_READ_STAGE1_VERSION` 版本读取接口。
- 新增 `tests/test_v024_stage1_phase12_shell_repair.py` 和 `reports/pfi_v024/stage_1/phase_1_2/evidence.json`。
- 本轮只做 shell integrity 最小恢复；Phase 1.3 和 Stage 1 whole-stage review 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher 或真实指标计算。

## v0.2.4 Repair Pack Stage 1 Phase 1.1 - 2026-06-30

- 完成 `Stage 1 / Phase 1.1 - 现状定位`：保存当前 `PFI/web/app/shell.js` 快照，记录语法检查结果，并定位当前残缺片段范围。
- 新增 `src/pfi_v02/stage_v024_stage1_shell_integrity.py`、`tests/test_v024_stage1_phase11_shell_diagnosis.py` 和 `reports/pfi_v024/stage_1/phase_1_1/evidence.json`。
- 当前 `shell.js` 在 Codex bundled Node 下语法检查通过；未发现 merge marker 或 syntax-fragment range。
- Phase 1.1 不修改 `shell.js`；Phase 1.2 仍需最小 shell integrity repair，Phase 1.3 和 Stage 1 whole-stage review 尚未执行。
- 本轮未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Whole-Stage Review - 2026-06-30

- 完成 `Stage 0 whole-stage review - 复审并解决暴露问题`，复审 Phase 0.1、0.2、0.3 的合同、证据、测试和状态文件。
- 修复复审发现的两个 Stage 0 范围问题：缺少整体复审合同/evidence，以及顶层 run/status 文件仍停留在 Phase 0.3。
- 新增 `docs/pfi_v024/STAGE0_WHOLE_STAGE_REVIEW.md`、`tests/test_v024_stage0_whole_review_contract.py` 和 `reports/pfi_v024/stage_0/whole_stage_review/evidence.json`。
- Stage 0 已整体复审完成；Stage 1 尚未开始，仍需用户验收或明确指令。
- 本轮未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Phase 0.3 - 2026-06-30

- 完成 `Stage 0 / Phase 0.3 - Stage 0 测试与证据`，用合同测试覆盖 10 个正式一级入口、`市场与研究` 一级入口、禁止假财务数据和 evidence pack 完整性。
- 新增 `tests/test_v024_stage0_phase03_contract.py` 和 `reports/pfi_v024/stage_0/phase_0_3/evidence.json`。
- 扩展 `src/pfi_v02/stage_v024_repair_contract.py`，记录 Phase 0.3 机器合同和 Stage 0 candidate complete 状态。
- 本轮未执行 Stage 0 whole-stage review、Stage 1 或后续阶段，未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Phase 0.2 - 2026-06-30

- 完成 `Stage 0 / Phase 0.2 - 历史约束废弃`，明确历史 9 入口约束、市场与研究一级入口禁令、暗色 AI 控制台方向和样例财务数据验收均已作废。
- 新增 `docs/pfi_v024/HISTORY_DEPRECATION_POLICY.md`、`tests/test_v024_stage0_phase02_contract.py` 和 `reports/pfi_v024/stage_0/phase_0_2/evidence.json`。
- 扩展 `src/pfi_v02/stage_v024_repair_contract.py`，记录废弃约束和仍保留的历史参考原则。
- 本轮未执行 Phase 0.3 或 Stage 0 whole-stage review，未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Stage 0 Phase 0.1 - 2026-06-30

- 完成 `Stage 0 / Phase 0.1 - 需求合同冻结`，记录 v0.2.4 修补包定位、10 个正式一级入口、真实数据禁令和每轮最多一个 phase 的执行规则。
- 新增 `docs/pfi_v024/REPAIR_SCOPE_LOCK.md`、`src/pfi_v02/stage_v024_repair_contract.py`、`tests/test_v024_stage0_phase01_contract.py` 和 `reports/pfi_v024/stage_0/phase_0_1/evidence.json`。
- 本轮未执行 Phase 0.2、Phase 0.3 或 Stage 0 whole-stage review，未修改业务 UI、app bundle、launcher 或数据逻辑。

## v0.2.4 Repair Pack Pre Stage 0 - 2026-06-30

- 建立 `v0.2.4` 修补包 pre stage 0；用户提供的 `v0.2.3-repair` roadmap/taskpack 作为来源输入，但当前 repo artifact 使用 `pfi_v024` 命名空间。
- 重新核验当前 GitHub main：`PFI/docs/pfi_v023` 和 v0.2.3 tests 已存在，`PFI/web/app/shell.js` 通过 `node --check`，TaskPack 内旧 GitHub audit 对当前 checkout 已过时。
- 新增 `docs/pfi_v024/PRE_STAGE0_CONTEXT_LOCK.md`、`SOURCE_TASK_PACK_MANIFEST.md`、`RUN_CONTRACT.md`、`src/pfi_v02/stage_v024_pre_stage0_contract.py` 和 `tests/test_v024_pre_stage0_contract.py`。
- 本轮未执行 Stage 0，未修改业务 UI、app bundle、launcher 或数据逻辑；停止等待用户验收或明确指令进入 Stage 0。

## v0.2.1.1 Product UI Recovery Stage 5/6 - 2026-06-29

- 完成 `v0.2.1.1 Stage 5` 真实图表与最终验收合同：账户、投资、消费趋势统一读取 `/api/trends`，来源限定为 SQLite operational DB 和 `MetaDatabase/PFI/alipay_daily`。
- 删除正式 Web Shell 的硬编码数字趋势回退；运行 API 不可用时只显示中文空状态。
- 隔离旧项目验收功能面板中的合成验收和测试数据路径，正式页面不再暴露 `fixture` 或合成验收入口。
- 新增 `docs/pfi_v0211/STAGE5_REAL_CHARTS_FINAL_ACCEPTANCE.md`、`docs/pfi_v0211/STAGE6_PROJECT_REVIEW_CLOSEOUT.md` 和 `tests/test_v0211_stage5_6_final_acceptance_contract.py`。
- Stage 6 项目级复审验收作为用户口径的第二阶段 closeout，覆盖跨板块复审、GitHub main 同步、本机 app 入口刷新和非必要缓存清理。

## v0.2.1.1 Product UI Recovery Stage 4 - 2026-06-29

- 完成 `S4 持久化与同步`，把 `投资管理 > 持仓` 保存路径接到本机 SQLite operational DB。
- 新增 `docs/pfi_v0211/STAGE4_PERSISTENCE_SYNC.md`、`tests/test_v0211_stage4_persistence_sync_contract.py`，并扩展 `src/pfi_v02/stage_v0211_ui_recovery.py` 的 Stage 4 合同。
- `src/pfi_v02/stage_v021_runtime_api.py` 新增 `/api/read-model` 和 `/api/reports/holdings`，让首页、投资管理和报告与洞察读取同一持仓读模型。
- 持仓编辑字段补齐账户、更新时间和备注；备注写入 SQLite snapshot 的 `metadata.note`。
- `web/app/shell.js` 保存持仓后刷新后端读模型，并同步更新首页、投资和报告卡片；生产保存不调用浏览器缓存。
- 正式库无真实持仓时继续显示中文空状态，不生成模拟收益或模拟持仓。

## v0.2.1.1 Product UI Recovery Stage 3 - 2026-06-29

- 完成 `S3 真实操作流`，把 Stage 2 页面骨架推进为可点击、可反馈、可复核的上传、账本、持仓和设置操作路径。
- 新增 `docs/pfi_v0211/STAGE3_REAL_OPERATION_FLOWS.md`、`tests/test_v0211_stage3_real_operation_flow_contract.py`，并扩展 `src/pfi_v02/stage_v0211_ui_recovery.py` 的 Stage 3 合同。
- `数据源与上传` 增加解析预览、字段映射、确认入库状态和待复核队列反馈；未选择真实文件时只提示中文空状态，不制造记录数。
- `账本流水` 增加筛选、分类选择、保存复核和导出流水；无真实流水时只导出空表头，不生成虚构流水。
- `投资管理 > 持仓` 保留未提交草稿标识，生产保存路径继续调用本机 `/api/holdings`，不把浏览器缓存作为生产保存来源。
- `设置` 增加保存设置、恢复默认和状态反馈；反馈控制台仍只在设置页显示。
- 本轮不声明 Stage 4 持久化与同步完成，不声明 Stage 5 真实图表与最终验收完成，不新增测试数据、样例流水、模拟持仓或虚构财务事实。

## v0.2.1.1 Product UI Recovery Stage 2 - 2026-06-29

- 完成 `S2 页面骨架与去 AI 化`，为 10 个正式一级入口建立中文页面骨架和二级入口。
- 新增 `docs/pfi_v0211/STAGE2_PAGE_SKELETON_CLEANUP.md`、`tests/test_v0211_stage2_page_skeleton_contract.py`，并扩展 `src/pfi_v02/stage_v0211_ui_recovery.py` 的 Stage 2 合同。
- Web Shell 默认首页改为用户任务语言：净资产、现金余额、投资市值、本月支出、待复核交易、数据源状态。
- 清理正式 UI 中运行边界、Task Pack、Demo、Prototype、手机预览、运行反馈控制台、多模态交互反馈、证据抽屉、运行证据、任务中心等污染词。
- `数据源与上传` 二级入口固定包含 `上传中心` 和 `导入中心`；`设置` 独立承接反馈、主题、语言、备份恢复等设置项。
- 本轮不做数据库 migration、上传入库闭环、持仓 SQLite 闭环、真实图表数据接入，也不声明 v0.2.1.1 整体完成。

## v0.2.1.1 Product UI Recovery Stage 0 - 2026-06-29

- 建立 v0.2.1.1 前端 UIUX 逻辑优化准备轮，明确当前 v0.2.1 前端优化不再作为正式 UI 完成状态，后续不得继续在旧 AI 化 Web Shell 上补丁式修补。
- 新增 `PRODUCT.md`、`docs/pfi_v0211/SOURCE_TASK_PACK_MANIFEST.md`、`docs/pfi_v0211/ROADMAP_LOCK.md`、`docs/pfi_v0211/STAGE0_PREPARATION.md`、`src/pfi_v02/stage_v0211_ui_recovery.py` 和 `tests/test_v0211_stage0_preparation_contract.py`。
- 将用户纠偏后的执行层级锁定为 6 个 Stage：S0 准备轮、S1 产品壳与路由、S2 页面骨架与去 AI 化、S3 真实操作流、S4 持久化与同步、S5 真实图表与最终验收；每次 run work 最多完成 1 个 Stage。
- 记录 Markdown roadmap 与 RTF 的来源差异：Stage 1 默认采用 RTF 最新稿的 10 个正式主导航入口，并把策略实验室唯一位置默认归到 `市场与研究 > 策略实验室`。
- 本轮不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`、`PFI/src/pfi_os/app/streamlit_app.py`，不刷新 app 入口，不清理缓存，不提前实现后续 Stage。

## v0.2.1 复审退回修复 - 2026-06-28

- 正式 Web Shell 删除运行边界/使用限制/隐私边界/只读/实盘/交易密码等用户可见边界类文案；约束保留在合同、测试和文档中。
- 新增 `src/pfi_v02/stage_v021_runtime_api.py`，提供本机 `GET/POST /api/holdings` 和 `GET /api/trends`。
- 持仓编辑保存路径改为 Web Shell -> 本机 API -> `V021HoldingsPersistenceService` -> SQLite operational database；浏览器缓存只保存明确标注的未提交草稿。
- 账户与资产、投资管理、消费管理趋势图改为从 SQLite 运行读模型派生；真实数据不足时显示中文空状态，不使用硬编码 demo 数组。
- 一级入口“策略实验室”和投资管理内部“策略实验室”统一进入 `/investment/strategy-lab`，复用同一功能面板、路由和状态。
- 新增 `tests/test_v021_review_rework_contract.py`，把复审失败项固化为回归测试，并扩展 Stage 2 合同禁词集合。

## v0.2.2 数据库治理 Stage 4 - 2026-06-28

- 完成 Stage 4 `Economic Event 与 Interconnection 逻辑`，覆盖 `S4-P1-T1..S4-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_interconnection.py`，建立 `economic_event_id`、`interconnection_group_id`、event type affects flags、Interconnection Matrix、Metric Dependency Graph 和 no-double-count 聚合函数。
- 新增 `docs/pfi_v022/STAGE4_INTERCONNECTION.md`、`docs/pfi_v02/INTERCONNECTION_MATRIX.md`、`tests/test_v022_interconnection_no_double_count.py` 和 `tests/test_v022_consumption_investment_outflow.py`，把 Stage 4 acceptance criteria、stop condition 和 validation 固化为可重复验证合同。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage4`，新增 `interconnection.event_type_policies`、`matrix_fields` 和 `metric_dependency_graph`。
- 双消费口径已锁定：投资入金、基金申购、黄金申购、投资买入进入消费总流出但不进入生活消费；退款抵消原消费；信用卡还款不重复计入生活消费。
- 本轮不实现 Stage 5 分类 taxonomy，不修改 v0.2.1 Web Shell UIUX 基线，不提交真实交易、支付、券商下单或自动投资能力。

## v0.2.2 数据库治理 Stage 3 - 2026-06-28

- 完成 Stage 3 `数据源、账户角色与可扩展结构`，覆盖 `S3-P1-T1..S3-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_source_profile.py`，建立 source profile schema、capabilities、`other_source_template`、账户多角色、角色生效期和 role-aware 计算合同。
- 新增 `docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md` 与 `tests/test_v022_stage3_source_account_profiles.py`，把 Stage 3 acceptance criteria、stop condition 和 validation 固化为可重复验证合同。
- `config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage3`，新增 `source_profile_schema`、`capability_labels_zh`、`other_source_template`、`account_role_schema` 和 `role_event_calculation_policy`。
- 本轮不实现 Stage 4 Interconnection Matrix，不修改 v0.2.1 Web Shell 交互架构，不提交真实交易、支付、券商下单或自动投资能力。

## v0.2.2 数据库治理 Stage 0 补做复核 - 2026-06-28

- 新增 `docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`，把 Stage 0 的 `S0-P1-T1..S0-P2-T2`、Milestone 0 acceptance criteria、stop condition、Agent 1/3 自检和验证命令整理为独立中文验收入口。
- 更新 `docs/pfi_v022/ROADMAP_LOCK.md`、`docs/pfi_v022/README.md`、`STAGE0_BASELINE_REPORT.md`、三基文件和 `HANDOFF.md`，明确 Stage 0 已补做复核且后续仍从 Stage 3 开始。
- 本轮不回滚 Stage 1/2，不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`、`PFI/web/styles/tokens.css`，不新增逻辑审查 HTML，也不做真实交易、自动投资或默认联网抓汇率。

## v0.2.2 数据库治理 Stage 2 - 2026-06-28

- 完成 Stage 2 `CNY 基准与汇率规则`，覆盖 `S2-P1-T1..S2-P2-T3`。
- 新增 `src/pfi_v02/stage_v022_fx.py`，实现 06:00 Australia/Sydney 有效汇率日、普通运行本地快照读取、显式联网刷新、快照 hash 校验、金额转 CNY 和账本金额字段生成。
- 新增真实快照 `data/fx_snapshots/AUD_CNY/2026-06-28.json`：`fx_AUD_CNY_20260628`，`1 AUD = 4.6874 CNY`，来源 `Frankfurter v2 public API`。
- Web Shell 顶部汇率徽标从旧 CNY/AUD 口径更新为当前 `AUD/CNY=4.69（YYYY/MM/DD HH:MM）`，主页等主金额显示以 `CNY` 为主。
- `config/pfi_parameters.yaml`、`模型参数文件.md`、`功能清单.md`、`开发记录.md` 和 `config/parameter_changelog.md` 补齐 Stage 2 汇率、快照、原币辅助、缺失状态和非目标边界。
- 新增 `docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md` 与 `tests/test_v022_fx_effective_date.py`，把 Stage 2 acceptance criteria、stop condition 和 validation 固化为可重复验证合同。
- 本轮不实现 Stage 3 数据源结构，不新增参数中心页面，不提交真实交易、支付、券商下单或自动投资能力。

## v0.2.2 数据库治理 Stage 1 - 2026-06-28

- 完成 Stage 1 `模型参数文件重构`，覆盖 `S1-P1-T1..S1-P2-T3`。
- `模型参数文件.md` 新增中文参数总目录，覆盖货币、汇率、时间、数据源、账户角色、事件类型、Interconnection、消费分类、标签、置信度、消费模型、投资模型、现金流、可视化和测试。
- 新增 `config/pfi_parameters.yaml` 作为唯一机器可读参数源；参数草案中的 `config/pfi_v022_parameters.yaml` 已记录为 draft alias，不新增第二个漂移文件。
- 新增 `tests/test_pfi_parameters_consistency.py`，验证 Markdown、YAML、前端合同和 HTML 中的核心参数一致。
- 新增 `docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md`，记录 Stage 1 验收、非目标、参数命名决策和后续 Stage 2 边界。
- 本轮不修改 `PFI/web/index.html`、`PFI/web/app/shell.js`，不实现真实汇率快照读取，不新增真实交易、自动投资、支付或券商提交能力。

## v0.2.1 前端优化 - 2026-06-27

- 建立 v0.2.1 前端优化 Stage 0 准备合同，锁定本轮是 PFI Web Shell 前端、交互、图表、上传命名、设置页和持仓编辑持久化优化，不是 V0.2 重构。
- 新增 `docs/pfi_v02/STAGE_V021_FRONTEND_OPTIMIZATION.md`，记录 roadmap、stage/task、acceptance criteria、stop condition、validation 和后续 pursuing goal 顺序。
- 新增 `src/pfi_v02/stage_v021_frontend_contract.py` 与 `tests/test_v021_stage0_frontend_contract.py`，把 CNY 基准、CNY/AUD 顶栏汇率、HTML 目标、多模态反馈设置页归属、统一导航和 P0-P8 任务清单固化为合同。
- 锁定后续 UI 货币契约：整体系统以 CNY 元为基准，所有页面顶部右上角显示当前 `AUD/CNY=4.69（YYYY/MM/DD HH:MM）` 徽标，读取当日 06:00 Australia/Sydney 汇率快照，缺失时显示中文空状态且不得伪造汇率。
- 本轮不重构 QBVS，不新增 Alpha/Ralpha/System/Development 产品一级入口，不提前实现后续 stage。

## 0.2.0 - 2026-06-27

- PFI 根项目确认为当前注册项目根。
- 三基人类入口统一为 Markdown 文件：`功能清单.md`、`开发记录.md`、`模型参数文件.md`。
- 补齐最小治理文件，记录 Stage 1/2 合同事实和生产未验证边界。
- 完成 PFI V0.2 Stage 2 本地合同验收，覆盖 phases 2A-2H。
- 新增 `docs/pfi_v02/STAGE2_ACCEPTANCE_AUDIT.md`，记录 phase/task evidence、stop-condition checks、validation results、本地 app-entry evidence 和缓存清理证据。
- 完成 PFI V0.2 Stage 3 本地可读 MVP，覆盖首页总览、账户地图、账本流水、待复核、同步全部、建议和报告入口。
- 新增 `src/pfi_v02/stage3_read_mvp.py` 与 `tests/test_stage3_readable_mvp.py`，将 Stage 3 3A-3D acceptance 固化为本地合同测试。
- Web shell 默认首页接入 Stage 3 read-model，左侧显示 V0.2 8 个一级入口；旧策略回测、盘感训练、大数据模拟器和 QBVS 兼容入口保留。
- 完成 PFI V0.2 Stage 4 投资与消费智能分析 MVP，覆盖投资总览、收益归因、风险分析、行为复盘、消费总览、分类分析、订阅检测、异常消费和现金流预测。
- 新增 `src/pfi_v02/stage4_analysis_mvp.py` 与 `tests/test_stage4_analysis_mvp.py`，将 Stage 4 4A/4B acceptance 固化为本地合同测试。
- Web shell 首页、投资管理和消费管理接入 Stage 4 analysis read-model；旧策略回测、盘感训练、大数据模拟器和 QBVS 独立系统引用继续保留。
- 完成 PFI V0.2 Stage 5 建议、报告、Alpha 只读出口 MVP，覆盖 recommendation model、review lifecycle、投资建议、消费建议、Top N ranking、四类报告、导出中心和 `pfi_context_snapshot_v1`。
- 新增 `src/pfi_v02/stage5_advice_report_alpha.py` 与 `tests/test_stage5_advice_report_alpha.py`，将 Stage 5 5A/5B/5C acceptance 固化为本地合同测试。
- Web shell 首页、建议与复盘、报告与洞察接入 Stage 5；仍保持 8 个一级入口，不新增 Alpha/Ralpha/System/Development 产品入口。
- 生产联通、真实账户凭证、支付提交、券商下单、Alpha repo 修改和实盘交易仍为独立后续 gate，未在 Stage 5 声明就绪。
- 完成 PFI V0.2 Stage 6 端到端验收与稳定化，覆盖 synthetic 多数据源、首页闭环、账本闭环、建议闭环、回归治理、交付回滚和 20 个总验收 gate。
- 新增 `src/pfi_v02/stage6_e2e_stabilization.py` 与 `tests/test_stage6_e2e_stabilization.py`，将 Stage 6 6A/6B/6C acceptance 固化为本地合同测试。
- Web shell 首页和报告与洞察接入 Stage 6；仍保持 8 个一级入口，不新增外部系统产品入口，QBVS 顶层独立且 PFI 不覆盖 QBVS。
- Stage 6 仍只证明本地 synthetic/read-only V0.2 可运行、可验证、可回滚；真实数据连接、外部 context consumer、PDF/ZIP、CDR/Open Banking 和生产发布证据为后续独立 gate。

## v0.2.1.1 Stage 1 - 2026-06-29

- 完成产品壳与路由受控重建：正式侧栏一级入口从旧 15 项收敛为 10 项。
- 新增正式一级入口 `市场与研究`，承接旧 `市场`、`研究` 与 `策略实验室`。
- `策略实验室` canonical route 改为 `/market-research/strategy-lab`；旧 `/strategy-lab` 和 `/investment/strategy-lab` 保留为兼容别名。
- Web Shell 路由从单纯 `replaceState` 升级为 `pushState` + `popstate`，支持浏览器前进后退。
- 新增 `docs/pfi_v0211/STAGE1_PRODUCT_SHELL_ROUTING.md` 与 `tests/test_v0211_stage1_product_shell_contract.py`。
- 本轮不实现图表、上传闭环、持仓编辑或报告。
