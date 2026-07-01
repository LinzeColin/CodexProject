# PFI Handoff

Last updated: 2026-07-01 Australia/Sydney

## Current v0.2.4 Repair Pack Handoff

PFI v0.2.4 是 v0.2.3 closeout 后的修补包。用户提供的来源文件命名为
`v0.2.3-repair`，当前线程按用户最新要求映射为 `v0.2.4`。

当前状态：

- 当前事实源：`/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi`。
- 当前 run：`Stage 9 / Phase 9.1 - 回归规则`。
- 每次 run work 最多完成一个 phase、一个 whole-stage review 或一个独立 upload gate；本轮只完成 Stage 9 Phase 9.1，不进入 Phase 9.2/9.3、whole-stage review 或 GitHub upload。
- 本轮建立 Stage 9 regression guardrails；不重装 app bundle，不修改 launcher C/Info.plist 或真实数据源。
- 来源资料：`/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_Roadmap.md` 和 `/Users/linzezhang/Downloads/PFI/PFI_v0.2.3_Repair_TaskPack.zip`。
- 当前 main 复核结论：TaskPack 内关于 `pfi_v023` docs/tests 缺失、`shell.js` 阻断的 GitHub audit 已对当前 checkout 过时；当前 `PFI/docs/pfi_v023` 存在，`test_v023_*.py` 存在，`PFI/web/app/shell.js` 通过 `node --check`。
- v0.2.4 pre-stage evidence 位于 `PFI/reports/pfi_v024/pre_stage_0/`。
- 当前 Stage 0 进度：Phase 0.1 需求合同冻结 candidate pass；Phase 0.2 历史约束废弃 candidate pass；Phase 0.3 测试与证据 candidate pass；Stage 0 whole-stage review pass。
- 当前 Stage 1 进度：Phase 1.1、Phase 1.2、Phase 1.3 均为 candidate pass；Stage 1 whole-stage review pass；Stage 1 已上传 GitHub main，`HEAD == origin/main == remote main` 于 `99dea6212dd79b1b0027e8152fa18d81321d46a8`。
- 当前 Stage 2 进度：Phase 2.1 入口链路映射 candidate pass；Phase 2.2 版本链路实现 candidate pass；Phase 2.3 实机验收 candidate pass；Stage 2 whole-stage review pass；Stage 2 reviewed package 曾上传到 GitHub main，Stage 2 commit 为 `c34af606f9793272e92d067fbe808dfdf100ec84`；当前 `origin/main` 已被非 PFI 提交推进。
- 当前 Stage 3 进度：Phase 3.1 导航合同 candidate pass；Phase 3.2 路由实现 candidate pass；Phase 3.3 导航验收 candidate pass；Stage 3 whole-stage review pass；Stage 3 GitHub main upload complete。
- 当前 Stage 4 进度：Phase 4.1 状态机定义 candidate pass；Phase 4.2 read model 挂链 candidate pass；Phase 4.3 验收 candidate pass；Stage 4 whole-stage review pass；Stage 4 GitHub main upload complete。
- 当前 Stage 5 进度：Phase 5.1 首页重建 candidate pass；Phase 5.2 二级页面差异化 candidate pass；Phase 5.3 交互状态 candidate pass；Stage 5 whole-stage review pass；Stage 5 GitHub main upload complete after terminal remote verification。
- 当前 Stage 6 进度：Phase 6.1 设计系统 candidate pass；Phase 6.2 动效反馈 candidate pass；Phase 6.3 触感与设置隔离 candidate pass；Stage 6 whole-stage review pass；Stage 6 GitHub main upload complete after terminal remote verification。
- 当前 Stage 7 进度：Phase 7.1 报告结构 candidate pass；Phase 7.2 页面展示 candidate pass；Phase 7.3 验收 candidate pass；Stage 7 whole-stage review pass；Stage 7 GitHub main upload complete after terminal remote verification。
- 当前 Stage 8 进度：Phase 8.1 自动验收 candidate pass；Phase 8.2 截图验收 candidate pass；Phase 8.3 人工验收已由用户回复 `1` 确认；Stage 8 whole-stage review pass；Stage 8 GitHub main upload complete after terminal remote verification。
- 当前 Stage 9 进度：Phase 9.1 回归规则 candidate pass；Phase 9.2 交付冻结未开始；Phase 9.3 用户验收未开始；Stage 9 whole-stage review 未开始；Stage 9 GitHub upload 未执行。
- Phase 0.1 evidence 位于 `PFI/reports/pfi_v024/stage_0/phase_0_1/`。
- Phase 0.2 evidence 位于 `PFI/reports/pfi_v024/stage_0/phase_0_2/`。
- Phase 0.3 evidence 位于 `PFI/reports/pfi_v024/stage_0/phase_0_3/`。
- Stage 0 whole-stage review evidence 位于 `PFI/reports/pfi_v024/stage_0/whole_stage_review/`。
- Stage 1 Phase 1.1 evidence 位于 `PFI/reports/pfi_v024/stage_1/phase_1_1/`。
- Stage 1 Phase 1.2 evidence 位于 `PFI/reports/pfi_v024/stage_1/phase_1_2/`。
- Stage 1 Phase 1.3 evidence 位于 `PFI/reports/pfi_v024/stage_1/phase_1_3/`。
- Stage 1 whole-stage review evidence 位于 `PFI/reports/pfi_v024/stage_1/whole_stage_review/`。
- Stage 2 Phase 2.1 evidence 位于 `PFI/reports/pfi_v024/stage_2/phase_2_1/`。
- Stage 2 Phase 2.2 evidence 位于 `PFI/reports/pfi_v024/stage_2/phase_2_2/`。
- Stage 2 Phase 2.3 evidence 位于 `PFI/reports/pfi_v024/stage_2/phase_2_3/`。
- Stage 2 whole-stage review evidence 位于 `PFI/reports/pfi_v024/stage_2/whole_stage_review/`。
- Stage 3 Phase 3.1 evidence 位于 `PFI/reports/pfi_v024/stage_3/phase_3_1/`。
- Stage 3 Phase 3.2 evidence 位于 `PFI/reports/pfi_v024/stage_3/phase_3_2/`。
- Stage 3 Phase 3.3 evidence 位于 `PFI/reports/pfi_v024/stage_3/phase_3_3/`。
- Stage 3 whole-stage review evidence 位于 `PFI/reports/pfi_v024/stage_3/whole_stage_review/`。
- Stage 3 GitHub main upload evidence 位于 `PFI/reports/pfi_v024/stage_3/github_main_upload/`。
- Stage 4 Phase 4.1 evidence 位于 `PFI/reports/pfi_v024/stage_4/phase_4_1/`。
- Stage 4 Phase 4.2 evidence 位于 `PFI/reports/pfi_v024/stage_4/phase_4_2/`。
- Stage 4 Phase 4.3 evidence 位于 `PFI/reports/pfi_v024/stage_4/phase_4_3/`。
- Stage 4 whole-stage review evidence 位于 `PFI/reports/pfi_v024/stage_4/whole_stage_review/`。
- Stage 4 GitHub main upload evidence 位于 `PFI/reports/pfi_v024/stage_4/github_main_upload/`。
- Stage 5 Phase 5.1 evidence 位于 `PFI/reports/pfi_v024/stage_5/phase_5_1/`。
- Stage 5 Phase 5.2 evidence 位于 `PFI/reports/pfi_v024/stage_5/phase_5_2/`。
- Stage 5 Phase 5.3 evidence 位于 `PFI/reports/pfi_v024/stage_5/phase_5_3/`。
- Stage 5 whole-stage review evidence 位于 `PFI/reports/pfi_v024/stage_5/whole_stage_review/`。
- Stage 5 GitHub main upload evidence 位于 `PFI/reports/pfi_v024/stage_5/github_main_upload/`。
- Stage 6 Phase 6.1 evidence 位于 `PFI/reports/pfi_v024/stage_6/phase_6_1/`。
- Stage 6 Phase 6.2 evidence 位于 `PFI/reports/pfi_v024/stage_6/phase_6_2/`。
- Stage 6 Phase 6.3 evidence 位于 `PFI/reports/pfi_v024/stage_6/phase_6_3/`。
- Stage 6 whole-stage review evidence 位于 `PFI/reports/pfi_v024/stage_6/whole_stage_review/`；复审发现 4 项均已 fixed：缺少 whole-stage review gate、缺少亮色桌面/移动截图、body 背景 fallback 不可验证、趋势图仍读取旧 root token。
- Stage 6 GitHub main upload evidence 位于 `PFI/reports/pfi_v024/stage_6/github_main_upload/`。
- Stage 7 Phase 7.1 evidence 位于 `PFI/reports/pfi_v024/stage_7/phase_7_1/`。
- Stage 7 Phase 7.2 evidence 位于 `PFI/reports/pfi_v024/stage_7/phase_7_2/`。
- Stage 7 Phase 7.3 evidence 位于 `PFI/reports/pfi_v024/stage_7/phase_7_3/`。
- Stage 7 whole-stage review evidence 位于 `PFI/reports/pfi_v024/stage_7/whole_stage_review/`。
- Stage 7 GitHub main upload evidence 位于 `PFI/reports/pfi_v024/stage_7/github_main_upload/`。
- Stage 8 Phase 8.1 evidence 位于 `PFI/reports/pfi_v024/stage_8/phase_8_1/`。
- Stage 8 Phase 8.2 evidence 位于 `PFI/reports/pfi_v024/stage_8/phase_8_2/`。
- Stage 8 Phase 8.3 evidence 位于 `PFI/reports/pfi_v024/stage_8/phase_8_3/`。
- Stage 8 whole-stage review evidence 位于 `PFI/reports/pfi_v024/stage_8/whole_stage_review/`。
- Stage 8 GitHub main upload evidence 位于 `PFI/reports/pfi_v024/stage_8/github_main_upload/`。
- Stage 9 Phase 9.1 evidence 位于 `PFI/reports/pfi_v024/stage_9/phase_9_1/`。
- 当前 Stage 2 build identity：`PFI v0.2.3 Repair` / `pfi-v024-stage2-phase22` / `PFI-V024-STAGE2-ENTRY-CONSISTENCY`。
- 当前 Stage 2 bundle hash：`e8928ed7f3067ae3e732aacda74427a61b69fbcfe855b2254118e7dafe38f8e4`。
- 当前真实浏览器验收服务：`http://127.0.0.1:8502`，app/local/clear-cache/new-profile 四条路径 build id 与 bundle hash 一致。
- 当前 Stage 3 导航合同：`PFI-V024-STAGE3-PHASE31-NAVIGATION`，正式一级入口固定 10 个，`市场与研究` 是第 9 个正式一级入口，`首页/市场/研究/持仓/策略实验室/数据与系统` 仅作为 alias/command。
- 当前 Stage 3 route 合同：`PFI-V024-STAGE3-PHASE32-ROUTES`，`routes.js` 解析 10 个一级 route、45 个二级 route 和 6 个旧入口 redirect；`shell.js` 优先读取 `PFI_V024_STAGE3_ROUTES`。
- 当前 Stage 3 browser navigation 合同：`PFI-V024-STAGE3-PHASE33-BROWSER-NAVIGATION`，真实浏览器验证 desktop/mobile 各 10 个 primary entries、6 个 v0.1 alias redirect、direct URL alias、点击导航和 back/forward，console/page errors 均为空。
- 当前 Stage 3 whole-stage review：`PFI/reports/pfi_v024/stage_3/whole_stage_review/evidence.json`，复审发现 3 项均已 fixed：缺少 whole-stage review gate、状态文件仍停在 Phase 3.3、Phase 3.3 浏览器证据需 review-time refresh。
- 当前 Stage 4 data state 合同：`PFI-V024-STAGE4-PHASE41-DATA-STATE`，冻结 10 个 metric status 和 11 个 required metric fields；非 ready 状态不得显示 `CNY 0.00`，`confirmed_zero` 必须携带真实证据链。
- 当前 Stage 4 read model status 合同：`PFI-V024-STAGE4-PHASE42-READ-MODEL-STATUS`，当前 `MetaDatabase/PFI` ready，`8815` 条记录、`4` 个原始文件、as of `2026-06-03`；净资产/现金/投资为 `source_missing`，消费总流出为 `ready`，五个页面 surface 共享同一 `read_model_hash`。
- 当前 Stage 4 Phase 4.3 验收：`PFI/reports/pfi_v024/stage_4/phase_4_3/browser_validation.json` 为 pass；截图包括 `data_missing_state.png` 和 `confirmed_zero_gate.png`；真实生产 `confirmed_zero` 指标数量为 `0`。
- 当前 Stage 4 whole-stage review：`PFI/reports/pfi_v024/stage_4/whole_stage_review/evidence.json` 为 pass；复审发现 3 项均已 fixed：缺少 whole-stage review gate、状态文件仍停在 Phase 4.3、Phase 4.3 浏览器证据需纳入整阶段验收。
- 当前 Stage 4 GitHub main upload：`PFI/reports/pfi_v024/stage_4/github_main_upload/evidence.json` 为 pass；上传后必须以 terminal 的 `git rev-parse HEAD`、`git rev-parse origin/main` 和 `git ls-remote origin refs/heads/main` 一致为最终事实源。
- 当前 Stage 5 Phase 5.1 首页：`PFI_V024_STAGE5_HOME` 读取 Stage 4 `read_model_status`，生成六问首页、数据状态卡和下一步任务流；默认首页已移除 `功能面板 / PFI 功能入口 / 功能已准备 / 进入操作面板` 机械层文案。
- 当前 Stage 5 Phase 5.2 二级页面：`PFI_V024_STAGE5_PAGES` 暴露 45 个差异化二级页面；route validation 为 pass，10 个正式一级入口均至少 4 个二级页面，无缺失 Stage 3 secondary route、无孤儿 route、无 title-only clone group。
- 当前 Stage 5 Phase 5.3 交互状态：`PFI_V024_STAGE5_UX_STATE` 暴露 45 个二级页面的 loading/success/error/empty 四态；UX validation 和 history validation 均为 pass，空态/错误态都有可行动 route。
- 当前 Stage 5 whole-stage review：`PFI/reports/pfi_v024/stage_5/whole_stage_review/evidence.json` 为 pass；复审发现 3 项均已 fixed：缺少 whole-stage review gate、缺少 screenshot pass-gate 覆盖、静态 browser validation 可选 read-model-status 404。
- 当前 Stage 5 GitHub main upload：`PFI/reports/pfi_v024/stage_5/github_main_upload/evidence.json` 为 pass；上传后必须以 terminal 的 `git rev-parse HEAD`、`git rev-parse origin/main` 和 `git ls-remote origin refs/heads/main` 一致为最终事实源。
- 当前 Stage 7 Phase 7.1 报告结构：`PFI-V024-STAGE7-PHASE71-REPORT-SCHEMA` 固定净资产、现金、投资、消费、现金流、数据质量 6 类报告；每份报告必须包含结论、公式、参数、数据范围、样本量、指标来源、置信度、缺口、异常项、复核入口和导出字段。
- 当前 Stage 7 Phase 7.1 数据边界：读取 Stage 4 `read_model_status`，真实 `MetaDatabase/PFI` ready，`8815` 条记录、`4` 个原始文件、as of `2026-06-03`；净资产、现金、投资和现金流缺少输入时保持 blocked，只生成缺口与数据质量报告。
- 当前 Stage 7 Phase 7.2 页面展示：`PFI-V024-STAGE7-PHASE72-PAGE-DISPLAY` 使用 Phase 7.1 `report_schema.json`，报告中心显示净资产、现金、投资、消费、现金流、数据质量 6 份报告。
- 当前 Stage 7 Phase 7.2 页面字段：每份报告可见结论、公式、参数、样本量、数据范围、置信度、缺口和复核入口；阻断报告不显示财务假零，不输出完整财务结论。
- 当前 Stage 7 Phase 7.3 验收：`PFI-V024-STAGE7-PHASE73-ACCEPTANCE` 生成 `report_acceptance_gate.json`、`browser_validation.json`、`sample_data_quality_report.html` 和 `formula_visibility.png`；acceptance gate 与 browser validation 均 pass。
- 当前 Stage 7 whole-stage review：`PFI/reports/pfi_v024/stage_7/whole_stage_review/evidence.json` 为 pass；复审发现 3 项均已 fixed：缺少 whole-stage review gate、顶层状态仍停在 Phase 7.3、缺少整阶段命令/证据汇总。
- 当前 Stage 7 GitHub main upload：`PFI/reports/pfi_v024/stage_7/github_main_upload/evidence.json` 为 pass；上传后必须以 terminal 的 `git rev-parse HEAD`、`git rev-parse origin/main` 和 `git ls-remote origin refs/heads/main` 一致为最终事实源。
- 当前 Stage 8 Phase 8.1 自动验收：`PFI/reports/pfi_v024/stage_8/phase_8_1/evidence.json` 为 candidate pass；真实浏览器自动验证 route click、entry version、data state、report center 四个分项均 pass，console/page/http errors 为空。
- 当前 Stage 8 Phase 8.2 截图验收：`PFI/reports/pfi_v024/stage_8/phase_8_2/evidence.json` 为 candidate pass；真实浏览器生成 app home、localhost home、10 个一级入口、移动端响应式和 `desktop_all_pages.png`，app/localhost bundle hash 一致，console/page/http errors 为空。
- 当前 Stage 8 Phase 8.3 人工验收：`PFI/reports/pfi_v024/stage_8/phase_8_3/evidence.json` 为 ready_for_user_acceptance；`manual_acceptance.md` 和 `defects.md` 已准备，用户回复 `1` 已在 whole-stage review evidence 中记录为人工验收通过来源。
- 当前 Stage 8 whole-stage review：`PFI/reports/pfi_v024/stage_8/whole_stage_review/evidence.json` 为 pass；复审发现 3 项均已 fixed：缺少 whole-stage review gate、顶层状态仍停在 Phase 8.3 pending、缺少整阶段证据汇总。
- 当前 Stage 8 GitHub main upload：`PFI/reports/pfi_v024/stage_8/github_main_upload/evidence.json` 为 pass；上传后 terminal 已证明 `HEAD == origin/main == remote main == ab09727d7c22ea5d7a65868c26526330d528a101`。
- 当前 Stage 9 Phase 9.1 回归规则：`PFI/reports/pfi_v024/stage_9/phase_9_1/evidence.json` 为 candidate pass；guardrail evaluator 覆盖旧 UI signature、10 个正式一级入口/旧 alias 堆叠、非 ready 假零、mock/sample/synthetic/fixture/demo/fake 财务数据，以及机械文案和暗色控制台默认风格定义。
- 下一个 gate：进入 Stage 9 Phase 9.2 交付冻结；不得在同一 run 自动进入 Phase 9.2。

---

Last updated: 2026-06-30 Australia/Sydney

## Current v0.2.3 Recovery Handoff

PFI v0.2.3 Human Product Experience Recovery 已进入第三阶段整体项目复审 closeout。
当前事实源为 `/Users/linzezhang/Documents/Codex/main_worktree/CodexProject/pfi`，
GitHub source of truth 为 `git@github.com:LinzeColin/CodexProject.git` / `main`。

当前状态：

- Stage 1-11 stage-by-stage review 已完成。
- Stage 1-3、Stage 4-6、Stage 7-9、Stage 10-11 group review 已完成并各自有 evidence。
- Overall project review 本地证据位于 `PFI/reports/pfi_v023/overall_project_review/`。
- v0.2.3 正式一级入口固定 10 个，`市场与研究` 是正式一级入口，历史 9 入口约束作废。
- `MetaDatabase/PFI` 存在真实支付宝 raw/processed 数据；缺失外部 Downloads roadmap/taskpack/preview 只记录为缺失，不补造。
- 本轮清理只允许删除 PFI worktree 内可再生缓存；不得删除 `.venv`、reports、screenshots、app bundle、`MetaDatabase/PFI` 或用户数据。
- 最终完成 gate：验证测试、push 到 GitHub main、确认 `HEAD == origin/main == remote main`、创建并验证 bundle 备份、确认 worktree clean。

---

Last updated: 2026-06-29 Australia/Sydney

## Current Goal

最新任务：PFI v0.2.1.1 Product UI Recovery Stage 5/6。用户要求完成 Stage 5 和 Stage 6，并在 Stage 6 后做第二阶段项目级跨板块复审验收、修复暴露问题、同步 GitHub、刷新本机入口和清理非必要缓存。本轮 Stage 5 做账户、投资、消费真实图表与最终验收；用户口径的 Stage 6 做项目级复审 closeout。

PFI v0.2.2 Stage 1-13 复审并解决：第一阶段每次 run work 只复审解决 1 个 Stage，第二阶段整体项目复审解决已完成。正式页面、报告、图表、首页摘要和建议只允许读取真实 MetaDatabase 派生数据或中文真实空态；不得使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据作为验收依据。GitHub main 同步和 app 入口重装纳入本轮 closeout，均按 `PFI/` 与 `MetaDatabase/PFI/` path-limited 范围执行，不能带入 EEI/ADP/Alpha/Serenity/arxiv 等混合改动。阻塞项数量：`0`。

## Current Status

- Correct and only active PFI project root is `PFI/`.
- QBVS is independent top-level system `QBVS/`; PFI does not own or cover QBVS.
- Active QBVS runtime path is `QBVS/qbvs`.
- User raw-data archive root is `MetaDatabase/`; current PFI Alipay raw and processed data are under `MetaDatabase/PFI/alipay_daily/`.
- Former app shell source has been moved into `PFI/src/pfi_os`,
  `PFI/scripts`, `PFI/macos`, `PFI/assets`, `PFI/web`, `PFI/shared`, and
  `PFI/systems`.
- Installed app target is now `PFI.app`, bound by `PFI_PROJECT_ROOT`.
- Installed app entries in `/Applications`, `~/Downloads`, and `~/Desktop`
  resolve to this checkout.
- Local runtime data home is now `~/.pfi` or explicit `$PFI_DATA_HOME`.
- Current app URL after migration verification: `http://localhost:8501`.
- v0.2.1.1 Stage 0 准备轮已新增目标产物：`PRODUCT.md`、`docs/pfi_v0211/SOURCE_TASK_PACK_MANIFEST.md`、`docs/pfi_v0211/ROADMAP_LOCK.md`、`docs/pfi_v0211/STAGE0_PREPARATION.md`、`src/pfi_v02/stage_v0211_ui_recovery.py`、`tests/test_v0211_stage0_preparation_contract.py`。
- v0.2.1.1 执行层级锁定为 6 个 Stage：S0 准备轮、S1 产品壳与路由、S2 页面骨架与去 AI 化、S3 真实操作流、S4 持久化与同步、S5 真实图表与最终验收；每次 run work 最多完成 1 个 Stage。
- v0.2.1.1 Stage 1 已完成产品壳与路由：正式一级入口收敛为 10 个，策略实验室唯一正式路由为 `/market-research/strategy-lab`。
- v0.2.1.1 Stage 2 已建立 10 个正式一级入口的中文页面骨架和二级入口，默认首页改为用户任务语言，并清理正式 UI 中运行边界、Task Pack、Demo、Prototype、手机预览、运行反馈控制台、多模态交互反馈、证据抽屉、运行证据、任务中心等污染词。
- v0.2.1.1 Stage 2 交付文档为 `docs/pfi_v0211/STAGE2_PAGE_SKELETON_CLEANUP.md`，合同测试为 `tests/test_v0211_stage2_page_skeleton_contract.py`。
- v0.2.1.1 Stage 3 已建立真实操作流：`数据源与上传` 的解析预览、字段映射、确认入库和待复核队列；`账本流水` 的筛选、分类选择、保存复核和导出；`投资管理 > 持仓` 的持仓编辑表单、未提交草稿和保存入口；`设置` 的保存设置、恢复默认和状态反馈。
- v0.2.1.1 Stage 3 交付文档为 `docs/pfi_v0211/STAGE3_REAL_OPERATION_FLOWS.md`，合同测试为 `tests/test_v0211_stage3_real_operation_flow_contract.py`。
- v0.2.1.1 Stage 4 已建立持仓持久化与同步闭环：`POST /api/holdings` 写入 SQLite，`GET /api/holdings` 刷新读回，`/api/read-model` 同步首页、投资和报告读数，`/api/reports/holdings` 输出同一持仓报告。
- v0.2.1.1 Stage 4 交付文档为 `docs/pfi_v0211/STAGE4_PERSISTENCE_SYNC.md`，合同测试为 `tests/test_v0211_stage4_persistence_sync_contract.py`。
- v0.2.1.1 Stage 5 已锁定真实图表与最终验收：`/api/trends` 是账户、投资、消费趋势的唯一正式前端数据源；账户和投资读取 SQLite operational DB，消费读取 `MetaDatabase/PFI/alipay_daily` 真实支付宝流水；无真实数据时显示中文空状态。
- Stage 5 交付文档为 `docs/pfi_v0211/STAGE5_REAL_CHARTS_FINAL_ACCEPTANCE.md`，合同测试为 `tests/test_v0211_stage5_6_final_acceptance_contract.py`。
- Stage 6 项目级复审验收是用户口径的第二阶段 closeout，交付文档为 `docs/pfi_v0211/STAGE6_PROJECT_REVIEW_CLOSEOUT.md`，覆盖跨板块复审、GitHub main 同步、本机 PFI.app 入口刷新和非必要缓存清理。
- 当前复审状态：Stage 1-13 复审并解决已完成；整体项目复审解决已完成；GitHub main 同步纳入本轮 closeout；app 入口重装已完成并通过 macOS app acceptance lite。
- 当前 Stage 13 task IDs：`S13-P1-T1`、`S13-P1-T2`、`S13-P1-T3`。
- Stage 13 单轮历史边界：Stage 13 - 后置触发型复核；交付前人工指定触发 Codex Review Ticket；本轮只复审解决 Stage 13；整体项目复审解决不在本轮实现；GitHub 同步不在本轮执行；app 入口重装不在本轮执行；禁止全仓无差别扫描；仅对异常区域进行复核；不联网；不调用外部 LLM；问题、修复、验证、剩余风险已记录；阻塞项数量：`0`。
- 当前 Stage 13 验收锚点：Downloads 污染文件夹 `PFI_V022_STAGE0_PRE_CANONICAL_SYNC_20260628T090028` 等候选目录已归档迁移记录保留。
- 最新线程分工：side thread 已处理 `PFI/web/index.html`、`PFI/web/app/shell.js`、`PFI/src/pfi_os/app/streamlit_app.py` 和相关前端验收测试的入口、反馈污染、上传归位、真实数字搜索索引、功能卡片小字和阶段标签清理；主线程只补充全局搜索覆盖层关闭兜底，并完成真实 8501 浏览器矩阵复验。后续如继续改这些文件，必须先 review mixed diff，避免覆盖 side thread 改动。
- 最新真实 8501 UIUX 复验：`/tmp/pfi_stage12_review_recheck/summary.json` 通过；桌面和移动端均验证正式 UI 不显示 Stage 12 开发文档、不链接本地审查 HTML、不出现自动买卖词，7 个首页 workflow 卡片可见、`.workflow-meta=0`、一级入口和首页真实按钮可点击，全局搜索 `8815/406` 命中，console/page errors 均通过，水平溢出 `0px`。截图为 `/tmp/pfi_stage12_review_recheck/app-desktop.png` 和 `/tmp/pfi_stage12_review_recheck/app-mobile.png`。
- 最新测试数据边界：`PFI/` 扫描仍有 175 个文件、604 处 `demo/sample/synthetic/fixture/mock/fake/测试样例` 命中；完整 pytest 只能作为 legacy regression 信号，不能作为产品验收依据。
- Stage 13 当前复审输出：`docs/pfi_v022/reviews/STAGE13_REVIEW_20260629.md`、`reports/pfi_v022_stage13_review_summary.md`、`tests/test_v022_review_stage13.py`；`PFI/reports/pfi_v022_summary.md` 继续保持 Stage12-only。
- 整体复审输出：`docs/pfi_v022/reviews/OVERALL_PROJECT_REVIEW_20260629.md`、`docs/pfi_v022/reviews/TEST_DATA_AUDIT_FINAL_20260629.md`、`reports/pfi_v022_overall_closeout_summary.md`、`reports/pfi_v022_goal_closeout_audit.md`。
- Stage 1 contracts remain in `src/pfi_v02/stage1_ia.py`, `src/pfi_v02/core_models.py`, and `src/pfi_v02/classification_rules.py`.
- Stage 2 registry is implemented in `src/pfi_v02/stage2_registry.py`.
- Stage 2 import pipeline is implemented in `src/pfi_v02/stage2_import.py`.
- Stage 2 non-CSV and reconciliation contracts are implemented in `src/pfi_v02/stage2_contracts.py`.
- Stage 2 record is `docs/pfi_v02/STAGE2_DATA_SYNC_MVP.md`.
- Stage 2 acceptance audit is `docs/pfi_v02/STAGE2_ACCEPTANCE_AUDIT.md`.
- Stage 2 local contract acceptance is complete for phases 2A-2H.
- Stage 3 read-model is implemented in `src/pfi_v02/stage3_read_mvp.py`.
- Stage 3 record is `docs/pfi_v02/STAGE3_READABLE_MVP.md`.
- Stage 3 local readable MVP acceptance is complete for phases 3A-3D.
- Stage 4 analysis read-model is implemented in `src/pfi_v02/stage4_analysis_mvp.py`.
- Stage 4 record is `docs/pfi_v02/STAGE4_ANALYSIS_MVP.md`.
- Stage 4 local analysis MVP acceptance is complete for phases 4A-4B.
- Stage 5 advice/report/export model is implemented in `src/pfi_v02/stage5_advice_report_alpha.py`.
- Stage 5 record is `docs/pfi_v02/STAGE5_ADVICE_REPORT_ALPHA_EXPORT.md`.
- Stage 5 local advice/report/Alpha-read-only export acceptance is complete for phases 5A-5C.
- Stage 6 E2E stabilization model is implemented in `src/pfi_v02/stage6_e2e_stabilization.py`.
- Stage 6 record is `docs/pfi_v02/STAGE6_E2E_STABILIZATION.md`.
- Stage 6 local synthetic E2E, regression governance, delivery rollback, 20 gate audit, and ACC-* taskpack audit acceptance is complete for phases 6A-6C.
- Stage 0 preparation audit is `docs/pfi_v02/STAGE0_PREPARATION_AUDIT_20260627.md`.
- Stage 1-5 acceptance audit is `docs/pfi_v02/STAGE1_5_ACCEPTANCE_AUDIT_20260627.md`.
- v0.2.1 前端优化记录是 `docs/pfi_v02/STAGE_V021_FRONTEND_OPTIMIZATION.md`。
- v0.2.1 Stage 0/1 合同是 `src/pfi_v02/stage_v021_frontend_contract.py`，测试是 `tests/test_v021_stage0_frontend_contract.py` 和 `tests/test_v021_stage1_navigation_contract.py`。
- v0.2.1 Stage 2 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage2_contract()`，测试是 `tests/test_v021_stage2_copy_cleanup_contract.py`。
- v0.2.1 Stage 3 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage3_contract()`，测试是 `tests/test_v021_stage3_settings_search_contract.py`。
- v0.2.1 Stage 4 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage4_contract()`，测试是 `tests/test_v021_stage4_trend_contract.py`。
- v0.2.1 Stage 5 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage5_contract()`，测试是 `tests/test_v021_stage5_upload_import_contract.py`。
- v0.2.1 Stage 6 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage6_contract()`；SQLite 服务是 `src/pfi_v02/stage_v021_holdings_persistence.py`；测试是 `tests/test_v021_stage6_holdings_persistence.py`。
- v0.2.1 Stage 7 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage7_contract()`；Web Shell 点击安全函数是 `buildClickSafeInventory()` / `bindClickSafeFeedback()` / `setActionFeedback()`；测试是 `tests/test_v021_stage7_clicksafe_feedback.py`。
- v0.2.1 Stage 8 合同是 `src/pfi_v02/stage_v021_frontend_contract.py::build_v021_stage8_contract()`；最终验收审计是 `docs/pfi_v02/STAGE_V021_FINAL_ACCEPTANCE_AUDIT.md`；测试是 `tests/test_v021_stage8_final_acceptance.py`。
- v0.2.1 UI 货币基准已锁定为 CNY；历史旧徽标不再作为当前正式 UI。v0.2.2 Stage 2 当前徽标为 `AUD/CNY=4.69（YYYY/MM/DD HH:MM）`，含义为 `1 AUD = 4.69 CNY`，读取本地 06:00 Australia/Sydney 有效快照。
- v0.2.1 正式前端目标是 `PFI/web` HTML Web Shell；多模态反馈、触感、声音、视觉、通知和运行反馈控制台后续必须收敛到设置页。
- Web shell default homepage now restores owner workflow after consuming runtime summaries: 上传支付宝账单、同步全部、处理待复核、查看建议、生成报告、单标的回测、盘感训练。Stage 6 closeout status remains report/evidence content and must not replace homepage core actions.
- Web shell shows one unified 15-entry navigation list: 首页总览、账户与资产、账本流水、投资管理、消费管理、数据源与上传、建议与复盘、报告与洞察、首页、市场、研究、持仓、策略实验室、数据与系统、设置.
- v0.2.2 当前路线是数据库治理和 E2E 逻辑优化，不是前端重做；Stage 0 资料区为 `docs/pfi_v022/`。
- v0.2.2 Stage 0 baseline report 是 `docs/pfi_v022/STAGE0_BASELINE_REPORT.md`。
- v0.2.2 roadmap lock 是 `docs/pfi_v022/ROADMAP_LOCK.md`；来源资料 manifest 是 `docs/pfi_v022/SOURCE_TASK_PACK_MANIFEST.md`。
- v0.2.2 Stage 0 task IDs 是 `S0-P1-T1`、`S0-P1-T2`、`S0-P1-T3`、`S0-P2-T1`、`S0-P2-T2`。
- v0.2.2 Stage 0 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage0_contract()`；测试是 `tests/test_v022_stage0_database_governance.py`。
- v0.2.2 Stage 0 已新增参数变更记录 `config/parameter_changelog.md`；后续参数、公式、阈值、分类、标签、Interconnection 和汇率规则变化必须记录旧值、新值、原因和影响范围。
- v0.2.2 Stage 1 task IDs 是 `S1-P1-T1`、`S1-P1-T2`、`S1-P1-T3`、`S1-P2-T1`、`S1-P2-T2`、`S1-P2-T3`。
- v0.2.2 Stage 1 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage1_contract()`；机器参数读取函数是 `load_v022_parameter_catalog()`。
- v0.2.2 Stage 1 机器可读参数源是 `config/pfi_parameters.yaml`；参数草案中的 `config/pfi_v022_parameters.yaml` 已作为 draft alias 记录，不新增第二个漂移文件。
- v0.2.2 Stage 1 验收报告是 `docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md`；一致性测试是 `tests/test_pfi_parameters_consistency.py`。
- v0.2.2 Stage 2 task IDs 是 `S2-P1-T1`、`S2-P1-T2`、`S2-P1-T3`、`S2-P2-T1`、`S2-P2-T2`、`S2-P2-T3`。
- v0.2.2 Stage 2 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage2_contract()`；汇率读取模块是 `src/pfi_v02/stage_v022_fx.py`。
- v0.2.2 Stage 2 当前真实快照是 `data/fx_snapshots/AUD_CNY/2026-06-28.json`，`snapshot_id=fx_AUD_CNY_20260628`，`rate=4.6874`，来源 `Frankfurter v2 public API`，hash `2e0d770f16f07543bfe03f9189f1be923b2ef4518a346c79788655600040018b`。
- v0.2.2 Stage 2 普通本地运行只读 `data/fx_snapshots/`，不默认联网；显式刷新必须调用 `pfi_v02.stage_v022_fx refresh --allow-network`。
- v0.2.2 Stage 2 账本金额字段锁定为 `原始金额`、`原始币种`、`CNY金额`、`汇率快照ID`；缺失当日有效快照时显示 `汇率数据待更新`，不得伪造实时汇率。
- v0.2.2 Stage 2 复审并解决结果：`tests/test_v022_review_stage2.py` `4 passed`；完整 PFI pytest `262 passed, 225 subtests passed`；治理 `errors 0 / warnings 0`；JS 和 diff 通过。
- 当前 app 入口事实：8501 健康，`/Applications/PFI.app` 和 `~/Downloads/PFI.app` 绑定 canonical PFI；`~/Desktop/PFI.app` 缺失导致 macOS app acceptance lite `Blocked, pass=22, fail=7, info=2`。按当前 goal，不在 Stage 2 run 内重装入口，整体复审解决完成后再刷新。
- v0.2.2 Stage 3 task IDs 是 `S3-P1-T1`、`S3-P1-T2`、`S3-P1-T3`、`S3-P2-T1`、`S3-P2-T2`、`S3-P2-T3`。
- v0.2.2 Stage 3 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage3_contract()`；source/account profile 模块是 `src/pfi_v02/stage_v022_source_profile.py`。
- v0.2.2 Stage 3 验收报告是 `docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md`；合同测试是 `tests/test_v022_stage3_source_account_profiles.py`。
- v0.2.2 Stage 3 机器可读参数源是 `config/pfi_parameters.yaml`，Stage 4 后当前 schema 已升级为 `PFIParametersV022Stage4`，Stage 3 source/account profile 参数仍保留。
- v0.2.2 Stage 3 当前 source profile 支持 `wallet`、`bank`、`broker`、`fund_platform`、`bullion_platform`、`payment_platform`、`manual_snapshot`、`other`；capabilities 覆盖现金流水、投资交易、基金交易、黄金交易、余额快照、费用、退款、转账。
- v0.2.2 Stage 3 账户角色字段锁定为 `account_id`、`source_id`、`role`、`role_effective_from`、`role_effective_to`；未知角色进入复核队列。
- v0.2.2 Stage 3 指标计算策略为 `role_and_event_type`，不得按支付宝、微信、银行卡、券商等 source 名称硬编码。
- v0.2.2 Stage 3 复审并解决结果：`tests/test_v022_review_stage3.py` `4 passed`；已新增 `savings_account=储蓄账户`、`external_counterparty=外部对手方`，并统一 `income_account=收入接收账户`。
- v0.2.2 Stage 4 task IDs 是 `S4-P1-T1`、`S4-P1-T2`、`S4-P1-T3`、`S4-P2-T1`、`S4-P2-T2`、`S4-P2-T3`。
- v0.2.2 Stage 4 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage4_contract()`；Interconnection 模块是 `src/pfi_v02/stage_v022_interconnection.py`。
- v0.2.2 Stage 4 验收报告是 `docs/pfi_v022/STAGE4_INTERCONNECTION.md`；Interconnection Matrix 是 `docs/pfi_v02/INTERCONNECTION_MATRIX.md`。
- v0.2.2 Stage 4 合同测试是 `tests/test_v022_interconnection_no_double_count.py` 和 `tests/test_v022_consumption_investment_outflow.py`。
- v0.2.2 Stage 5 task IDs 是 `S5-P1-T1`、`S5-P1-T2`、`S5-P2-T1`、`S5-P2-T2`、`S5-P2-T3`、`S5-P3-T1`、`S5-P3-T2`、`S5-P3-T3`、`S5-P3-T4`。
- v0.2.2 Stage 5 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage5_contract()`；账本分类模块是 `src/pfi_v02/stage_v022_ledger_taxonomy.py`。
- v0.2.2 Stage 5 验收报告是 `docs/pfi_v022/STAGE5_LEDGER_TAXONOMY.md`；合同测试是 `tests/test_v022_stage5_ledger_taxonomy.py`。
- v0.2.2 Stage 5 当前事件类型表覆盖消费、投资入金、基金申购、黄金申购、投资买入、投资卖出、退款、费用、信用卡还款、内部转账、收入、估值、汇率兑换。
- v0.2.2 Stage 5 当前双消费口径：`消费总流出` 包含生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用并由退款抵消；`生活消费` 只包含普通生活消费并由退款抵消。
- v0.2.2 Stage 5 当前分类约束：`L1 ≤ 12`、每类 `L2 ≤ 5`、总 `L2 ≤ 50`、每笔交易主分类数量为 `1`，每个 L1 有 `future_merge_to` / `merge_candidate`；复审后分类验证会拒绝非单主分类 taxonomy，当前 12 个 L1 可压缩为 7 个 future merge 分组，低于 10 类目标。
- v0.2.2 Stage 6 task IDs 是 `S6-P1-T1`、`S6-P1-T2`、`S6-P1-T3`、`S6-P2-T1`、`S6-P2-T2`、`S6-P2-T3`、`S6-P3-T1`、`S6-P3-T2`、`S6-P3-T3`。
- v0.2.2 Stage 6 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage6_contract()`；标签视图模块是 `src/pfi_v02/stage_v022_tags_views.py`。
- v0.2.2 Stage 6 验收报告是 `docs/pfi_v022/STAGE6_TAGS_CUSTOM_VIEWS.md`；合同测试是 `tests/test_v022_stage6_tags_views.py`；本地 HTML 是 `web/pfi_v022_tag_views.html`。
- v0.2.2 Stage 6 当前持久化表：`pfi_tags`、`pfi_tag_assignments`、`pfi_tag_rules`、`pfi_tag_history`、`pfi_custom_views`。
- v0.2.2 Stage 6 当前默认标签组：通用、消费、投资、数据质量、现金流、复盘。
- v0.2.2 Stage 6 当前规则维度：金额、时间、分类、事件类型、账户角色。
- v0.2.2 Stage 7 task IDs 是 `S7-P1-T1`、`S7-P1-T2`、`S7-P1-T3`、`S7-P2-T1`、`S7-P2-T2`、`S7-P2-T3`、`S7-P2-T4`、`S7-P3-T1`、`S7-P3-T2`、`S7-P3-T3`、`S7-P4-T1`、`S7-P4-T2`、`S7-P4-T3`。
- v0.2.2 Stage 7 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage7_contract()`；公式评分模块是 `src/pfi_v02/stage_v022_formula_scoring.py`。
- v0.2.2 Stage 7 验收报告是 `docs/pfi_v022/STAGE7_FORMULA_SCORING.md`；合同测试是 `tests/test_v022_stage7_formula_scoring.py`。
- v0.2.2 Stage 7 置信度权重是字段完整度 30、金额方向 10、规则命中 20、商户/对手方 15、关联匹配 15、历史一致性 10；统一复核阈值是 `70`，禁止 source 分层阈值。
- v0.2.2 Stage 7 消费总流出包含生活消费、投资入金、基金申购、黄金申购、投资买入、金融费用并由退款抵消；生活消费只包含普通生活消费并由退款抵消。
- v0.2.2 Stage 7 投资市值公式是 `quantity * latest_price * fx_rate_to_cny`；收益公式显式纳入费用、税费和汇率影响。
- v0.2.2 Stage 7 现金流窗口是 `7/21/30/60/90/180/360`；储备金安全线是 `max(user_min_reserve_cny, average_fixed_monthly_expense_cny * reserve_months)`；投资挤压模型解释计划入金是否压低生活现金。
- v0.2.2 Stage 8 task IDs 是 `S8-P1-T1`、`S8-P1-T2`、`S8-P1-T3`、`S8-P2-T1`、`S8-P2-T2`、`S8-P2-T3`、`S8-P2-T4`、`S8-P3-T1`、`S8-P3-T2`、`S8-P3-T3`。
- v0.2.2 Stage 8 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage8_contract()`；Runtime Diff 模块是 `src/pfi_v02/stage_v022_runtime_diff.py`。
- v0.2.2 Stage 8 验收报告是 `docs/pfi_v022/STAGE8_RUNTIME_DIFF_IMPACTED_METRICS.md`；合同测试是 `tests/test_v022_stage8_runtime_diff.py`；本地复审票据模板是 `review_queue/CODEX_REVIEW_TICKET_TEMPLATE.md`。
- v0.2.2 Stage 8 依赖 hash keys：`raw_data_hash`、`normalized_transactions_hash`、`ledger_events_hash`、`interconnection_hash`、`parameter_hash`、`category_hash`、`tag_hash`、`fx_snapshot_hash`。
- v0.2.2 Stage 8 运行策略：无 diff 不联网、不生成 Codex ticket、不触发 LLM；普通 diff 只生成本地 diff report；重要业务冲突才生成本地中文 Codex Review Ticket。
- v0.2.2 Stage 8 P0 核心指标仅包括净资产、生活现金、投资资产、消费总流出、生活消费、投资收益、现金流窗口、待复核数量、Interconnection 异常数量；P1/P2 与 P0 分离。
- v0.2.2 Stage 9 task IDs 是 `S9-P1-T1`、`S9-P1-T2`、`S9-P1-T3`、`S9-P2-T1`、`S9-P2-T2`、`S9-P2-T3`、`S9-P3-T1`、`S9-P3-T2`、`S9-P3-T3`、`S9-P3-T4`、`S9-P4-T1`、`S9-P4-T2`、`S9-P4-T3`。
- v0.2.2 Stage 9 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage9_contract()`；可视化/UIUX 模块是 `src/pfi_v02/stage_v022_visualization_uiux.py`。
- v0.2.2 Stage 9 验收报告是 `docs/pfi_v022/STAGE9_VISUALIZATION_UIUX.md`；Mermaid 关系图是 `docs/pfi_v022/INTERCONNECTION_MAP.md`；合同测试是 `tests/test_v022_stage9_visualization_uiux.py`；本地 HTML 是 `web/interconnection-map.html`。
- v0.2.2 Stage 9 参数中心覆盖货币、汇率、分类、标签、阈值、公式、置信度、现金流窗口；每个参数显示中文名、当前值、作用、影响范围、是否可修改。
- v0.2.2 Stage 9 Interconnection Map 覆盖 `source -> raw -> normalized -> group -> event -> ledger -> metrics -> UI`；本地 HTML 可点击追踪数据源、事件类型、分类、标签、公式、影响板块。
- v0.2.2 Stage 9 现金流可视化包含现金流阶梯图、现金流瀑布图、储备金安全带、投资入金挤压图；现金流窗口为 `7/21/30/60/90/180/360`。
- v0.2.2 Stage 9 Metric Drilldown Debugger 覆盖本月消费、投资资产、现金流窗口的纳入、排除、调整、公式、参数和质量状态。
- v0.2.2 Stage 9 已在后续 Stage 10 前完成；Stage 10 报告、建议与复盘已单独实现。
- v0.2.2 Stage 10 - 报告、建议与复盘 task IDs 是 `S10-P1-T1`、`S10-P1-T2`、`S10-P1-T3`、`S10-P2-T1`、`S10-P2-T2`、`S10-P2-T3`。
- v0.2.2 Stage 10 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage10_contract()`；报告与建议模块是 `src/pfi_v02/stage_v022_report_advice_review.py`。
- v0.2.2 Stage 10 验收报告是 `docs/pfi_v022/STAGE10_REPORT_ADVICE_REVIEW.md`；合同测试是 `tests/test_v022_stage10_report_advice_review.py`。
- v0.2.2 Stage 10 月报必须同时显示 `消费总流出` 和 `生活消费`；投资报告必须显示收益、成本、费用、汇率、交易频率、风格、现金拖累；数据质量报告必须显示未匹配转账、重复候选、低置信、标签变更、参数变更、hash diff。
- v0.2.2 Stage 10 将“推荐”统一解释为 `行动建议与复盘`，不是自动投资建议、买卖指令、付款或券商提交。
- v0.2.2 Stage 10 行动建议类型覆盖数据修复建议、消费复盘建议、投资行为复盘建议、现金流风险建议、订阅优化建议、参数调整建议。
- v0.2.2 Stage 10 行动建议评分权重是财务影响 25、风险降低 20、紧急程度 15、置信度 15、可逆性 10、执行成本反比 10、学习价值 5。
- v0.2.2 Stage 10 生命周期支持 `pending`、`accepted`、`rejected`、`snoozed`、`reviewed`、`effect_measured`。
- v0.2.2 Stage 10 已在后续 Stage 11 中接受测试与验证总门；Stage 12 最终交付包和 Stage 13 后置触发型复核仍未实现。
- v0.2.2 Stage 11 - 测试与验证 task IDs 是 `S11-P1-T1`、`S11-P1-T2`、`S11-P1-T3`、`S11-P1-T4`、`S11-P2-T1`、`S11-P2-T2`、`S11-P2-T3`、`S11-P3-T1`、`S11-P3-T2`、`S11-P3-T3`。
- v0.2.2 Stage 11 合同是 `src/pfi_v02/stage_v022_database_governance.py::build_v022_stage11_contract()`；测试与验证模块是 `src/pfi_v02/stage_v022_test_validation.py`。
- v0.2.2 Stage 11 验收报告是 `docs/pfi_v022/STAGE11_TEST_VALIDATION.md`；合同测试是 `tests/test_v022_stage11_test_validation.py`。
- v0.2.2 Stage 11 金融逻辑测试覆盖投资入金计入消费总流出、基金申购计入消费总流出、退款抵消、信用卡还款不重复计入生活消费。
- v0.2.2 Stage 11 跨板块一致性测试要求 `首页消费总流出 = 消费页消费总流出 = 月报消费总流出`，以及 `首页投资资产 = 投资页投资资产 = 投资报告投资资产`。
- v0.2.2 Stage 11 现金流预测必须追溯到账本事件和计划事件。
- v0.2.2 Stage 11 可视化一致性测试要求每个图表可追溯 `metric_id`、`formula_id`、`parameter_hash`、`data_hash`；数据变化后受影响图表标记 `needs_update` 或 `updated`；真实 `8815` 条 `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` 标准化流水下显示 `compute time` 和 `cache status`；缺少真实 CBA -> Moomoo、信用卡还款、计划事件或持仓快照时显示中文真实空态。
- v0.2.2 Stage 11 明确不实现 Stage 12 文档同步与最终交付，也不执行 Stage 13 后置触发型复核。
- v0.2.2 Stage 4 当前规则：同一真实事件只有一个 `economic_event_id`；同一资金链路进入一个 `interconnection_group_id`；同一事件可多处展示但同一核心指标只计算一次。
- v0.2.2 Stage 4 消费口径：投资入金、基金申购、黄金申购、投资买入和费用进入消费总流出；投资入金、基金申购、投资买入不进入生活消费；退款抵消原消费；信用卡还款不重复计入生活消费。
- v0.2.2 Stage 4 stop condition：`投资入金未进入消费总流出`、`基金申购未进入消费总流出`、`投资入金错误进入生活消费`、同一 `interconnection_group_id` 重复计入核心金额。
- v0.2.2 Stage 4 Agent 1 复核消费、投资、现金流口径；Agent 2 复核 source -> transaction -> group -> economic event -> ledger -> metric 链路。
- `PFI_v0.2.2_UIUX_Logic_Review_Template.html` 只是后续逻辑审查页参考；Stage 0 不修改 `PFI/web/index.html`、`PFI/web/app/shell.js` 或新增审查页。
- 2026-06-27验收退回纠偏：默认 8501 顶部已新增 PFI 本机数据上传；真实支付宝导出 CSV parser 已支持说明区/中间表头/GB18030/尾随空列；旧支付宝原始账单 4 份已导入 `~/.pfi/runtime/imports/alipay_daily`，覆盖 `2022-06-06` 至 `2026-06-03`，`8815` 条标准化流水，`406` 条待复核；Web Shell 动态英文状态已中文化，8 个一级入口浏览器点击验证通过。
- 2026-06-27二次纠偏：QBVS 已从 `PFI/` 内部分离为顶层 `QBVS/`；PFI 合同改为 `qbvs_independent_system=true`；Web Shell 补回 V0.1 六入口；`MetaDatabase/` 保存支付宝原始 CSV、manifest 和标准化流水，供 GitHub 验收。
- 当前 GitHub 分支 `codex/pfi-stage6-meta-qbvs-sync` 已推送 commit `d0d0a4b8f50231e2c63293396a1fee8e03de7fda`；PFI/QBVS/MetaDatabase 相关工作区在该 commit 后干净。
- 2026-06-27 Stage 1-5 acceptance audit：根 `README.md` 和 `governance/projects.yaml` 已登记 `QBVS` 和 `MetaDatabase`；`MetaDatabase` 补三基和最小治理；PFI Stage 1-5 contracts `Ran 89 tests / OK`；QBVS smoke `Ran 1 test / OK`；PFI/QBVS/MetaDatabase governance `errors 0 / warnings 0`；Web Shell Chrome 点击验收 `14/14`、console errors `0`。
- 2026-06-27 v0.2.1 Stage 1：HTML Web Shell 左侧导航已改为 15 个统一入口；`数据与系统` 映射设置页；策略实验室旧入口和投资管理卡片都打开投资管理下的策略实验室状态；新增 `docs/pfi_v02/LEDGER_CLASSIFICATION_STANDARD.md`；三基文件已明确功能目录、开发日志、参数依据三种定位。
- 2026-06-27 v0.2.1 Stage 2：HTML Web Shell 与动态首页摘要完成中文可读文案清理；`Review lifecycle`、`PFI Context Export`、`Synthetic E2E`、`Rollback plan`、`Follow-up list`、`Top N`、`tradeoff`、`owner gate`、`parser / raw / batch` 等旧英文/机器文案被移出用户可见面；`运行边界`、`查看边界`、`验收边界`、`安全边界` 和英文 `Boundary` 被合同测试禁止；未新增 iframe、手机演示框或预览框。
- 2026-06-27 v0.2.1 Stage 3：`设置` 和 `数据与系统` 深链统一进入设置主工作区；业务页面不常驻反馈控制台；设置页包含运行反馈控制台、多模态反馈、触感、声音、视觉、通知、反馈测试和无障碍反馈；顶部全局搜索支持 15 个入口、V0.1 别名、工作区卡片、功能面板、任务中心、决策行和设置反馈控制项的模糊检索。
- 2026-06-27 v0.2.1 Stage 4：新增 `UNIFIED_TREND_DATA`；账户与资产显示现金/净资产趋势；投资管理显示市值/总收益/现金仓位趋势；消费管理显示支出/预算/现金流趋势；趋势图有中文标题、图例、CNY 基准、终点直接标签和中文空状态。
- 2026-06-27 v0.2.1 Stage 5：`数据源与上传` 页面新增上传中心和导入中心；文件选择、拖拽上传、等待/完成/失败中文状态、失败反馈、已选文件列表、导入批次、导入摘要和 `进入账本复核` 按钮可用；不执行外部真实上传、支付、券商提交或实盘自动下单。
- 2026-06-27 v0.2.1 Stage 6：`投资管理 > 持仓` 新增持仓编辑面板；SQLite operational database 新增 `v021_holding_snapshots` 和 `v021_position_adjustments` 合同；服务覆盖新增、读取、修改、软删除。2026-06-28 复审修复后，生产保存路径必须通过本机 `/api/holdings` 写入 SQLite；浏览器缓存只允许保存明确标注的未提交草稿。
- 2026-06-27 v0.2.1 Stage 7：所有可见按钮进入点击安全清单；按钮点击统一显示 `进行中/成功/失败` 反馈；`hashchange` 同步工作区和左侧高亮；移动端一级入口横向滚动且不竖排；桌面/手机浏览器验收覆盖 15 个一级入口、40 个代表按钮、15 个命令入口和三态反馈。
- 2026-06-28 v0.2.1 Stage 8：新增最终验收合同和审计；`V021-P8-S8-T01` 前端合同测试、`V021-P8-S8-T02` 浏览器验收、`V021-P8-S8-T03` 命令验收统一进入 `PFI-V021-S8-FINAL-ACCEPTANCE-GATE`；Stage 0-8 前端合同、完整 PFI 单测、JS、治理、diff、浏览器、GitHub main、canonical PFI、PFI.app 和缓存清理成为同一 closeout gate。
- 2026-06-28 v0.2.2 Stage 0：读取 v0.2.2 roadmap、Task Pack、参数草案、6 Agent 交叉验证草案、HTML 审查模板和新版 Stage -> Phase -> Task roadmap；生成 `docs/pfi_v022/STAGE0_BASELINE_REPORT.md`，列出现有参数、硬编码阈值、消费/投资/现金流/建议口径、数据源、账户角色、Stage 6 基线和 v0.2.2 冲突清单；合同测试锁定本轮不改 v0.2.1 前端显示。
- 2026-06-28 v0.2.2 Stage 0 补做：按 `S0-P1-T1..S0-P2-T2` 补齐开发记录任务章节、文件定位、非目标清单、`task_name`、`parameter_version` 和 `config/parameter_changelog.md`。
- 2026-06-28 v0.2.2 Stage 0 验证：Stage 0 合同 `Ran 9 tests / OK`；完整 PFI 单测 `Ran 156 tests / OK`；项目治理 `errors 0 / warnings 0`；`node --check PFI/web/app/shell.js` 通过；`git diff --check -- PFI` 通过；`PFI/web` 无 diff。
- 2026-06-28 v0.2.2 Stage 1：新增 `config/pfi_parameters.yaml`、`docs/pfi_v022/STAGE1_PARAMETER_GOVERNANCE.md`、`tests/test_pfi_parameters_consistency.py`；`模型参数文件.md` 补中文参数总目录、公式解释、阈值说明和变量别名；`config/parameter_changelog.md` 记录 `S1-P1-T1..S1-P2-T3` 参数变更。
- 2026-06-28 v0.2.2 Stage 2：新增 `src/pfi_v02/stage_v022_fx.py`、`data/fx_snapshots/AUD_CNY/2026-06-28.json`、`docs/pfi_v022/STAGE2_CNY_FX_GOVERNANCE.md` 和 `tests/test_v022_fx_effective_date.py`；`config/pfi_parameters.yaml`、三基文件、README、HANDOFF、roadmap lock 和 Web Shell 徽标同步为 `AUD/CNY` 当前快照口径。
- 2026-06-28 v0.2.2 Stage 0 补做复核：新增 `docs/pfi_v022/STAGE0_REDO_ACCEPTANCE_20260628.md`，单独复核 `S0-P1-T1..S0-P2-T2`、Milestone 0 acceptance criteria、stop condition、Agent 1/3 自检和验证命令；不回滚 Stage 1/2，不修改 v0.2.1 Web Shell，不提前做 Stage 3。
- 2026-06-28 v0.2.2 Stage 3：新增 `src/pfi_v02/stage_v022_source_profile.py`、`docs/pfi_v022/STAGE3_SOURCE_ACCOUNT_PROFILE.md` 和 `tests/test_v022_stage3_source_account_profiles.py`；`config/pfi_parameters.yaml`、三基文件、README、HANDOFF、roadmap lock 和 governance 同步为 Stage 3 source/account profile 口径。
- 2026-06-28 v0.2.2 Stage 4：新增 `src/pfi_v02/stage_v022_interconnection.py`、`docs/pfi_v022/STAGE4_INTERCONNECTION.md`、`docs/pfi_v02/INTERCONNECTION_MATRIX.md`、`tests/test_v022_interconnection_no_double_count.py` 和 `tests/test_v022_consumption_investment_outflow.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage4`；三基文件和参数变更记录同步记录 no-double-count、双消费口径、Metric Dependency Graph、Agent 1/Agent 2 复核和 stop condition。
- 2026-06-28 v0.2.2 Stage 5：新增 `src/pfi_v02/stage_v022_ledger_taxonomy.py`、`docs/pfi_v022/STAGE5_LEDGER_TAXONOMY.md` 和 `tests/test_v022_stage5_ledger_taxonomy.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage5`；三基文件、README、roadmap lock 和参数变更记录同步记录统一账本事件、双消费口径、12 大类 / 50 中类 taxonomy、future_merge 字段、Agent 1/Agent 3 复核和 stop condition。
- 2026-06-28 v0.2.2 Stage 6：新增 `src/pfi_v02/stage_v022_tags_views.py`、`docs/pfi_v022/STAGE6_TAGS_CUSTOM_VIEWS.md`、`web/pfi_v022_tag_views.html` 和 `tests/test_v022_stage6_tags_views.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage6`；三基文件、README、roadmap lock 和参数变更记录同步记录 `pfi_tags`、`pfi_tag_assignments`、`pfi_tag_rules`、`pfi_tag_history`、`pfi_custom_views`、默认标签库、自定义标签生命周期、标签报告和自定义视图。
- 2026-06-28 v0.2.1 UIUX 退回整改：`web/styles/tokens.css` 改为深色玻璃工作台风格；`web/index.html` 顶部动作显示“搜索/任务/证据/设置”；`web/app/shell.js` 新增 `restoreOwnerHomeWorkflow()` 并修复视觉波纹反馈条件；`src/pfi_os/app/streamlit_app.py` 移除真实上传面板外层嵌套 expander 并把 Web Shell iframe 高度调整为 `1120`。验证：v0.2.1 前端合同 `49 passed`，`node --check web/app/shell.js` 通过，`git diff --check -- PFI` 通过，真实 8501 console errors `0`，关键点击链上传/搜索/设置/策略实验室通过。
- 2026-06-28 v0.2.1 UIUX 二次退回修复：首屏新增 `视觉回弹/触感回馈/声音提示` 反馈信号条；`bindOwnerFeedbackSignals()` 触发状态条、toast、波纹、触感和声音降级；Streamlit 原生上传控件已本地化为中文 `拖拽 CSV / ZIP 到这里`、`选择文件`、`单文件上限 200MB`；支付宝导入摘要状态 `Ready` 映射为 `就绪`；新增 `tests/test_v021_uiux_multimodal_style_regression.py`。真实 8501 验证：`Drag and drop files here=false`、`Browse files=false`、`Deploy=false`、`Ready=0`、`就绪=4`。
- 2026-06-28 v0.2.1 UIUX 三次退回修复：旧 `视觉回弹/触感回馈/声音提示` 说明按钮条已移除，首屏改为 `data-feedback-hub` 多模态交互反馈中枢；包含 `视觉状态轨道`、`触感强度`、`声音反馈`、强度条和事件日志；`bindFeedbackHub()` / `updateFeedbackHub()` 会在点击后更新 `data-feedback-hub-state`、`data-action-feedback`、toast 和日志；视觉反馈默认开启并修复 `reduce-motion` 反向逻辑；顶栏可见汇率统一为 `AUD/CNY=4.69（2026/06/28 06:00）`。真实 8501 Chrome 验证：`data-feedback-hub=1`、旧 `data-owner-feedback-strip=0`、旧 `.feedback-signal=0`、点击后状态 `视觉状态轨道 · 成功`，截图 `/tmp/pfi-uiux-feedback-hub-clicked.png`。
- 2026-06-28 v0.2.1 复审硬失败修复：`PFI/web` 和注入首页摘要不再出现 `只读/实盘/运行边界/使用限制/隐私边界/交易密码/不下单/不支付/不登录` 等正式 UI 禁词；新增 `src/pfi_v02/stage_v021_runtime_api.py`；`web/app/shell.js` 保存持仓调用 `/api/holdings`，本机 API 调用 `V021HoldingsPersistenceService` 写入 SQLite，`/api/trends` 从 SQLite 运行读模型派生账户、投资和消费趋势；策略实验室一级入口和投资管理内部入口统一到 `/investment/strategy-lab`。
- 2026-06-28 v0.2.1 复审最终本地验收：v0.2.1 合同 `58 passed`；完整 PFI pytest `198 passed, 64 subtests passed`；`node --check PFI/web/app/shell.js` 和 `git diff --check -- PFI` 通过；Chrome/系统浏览器真实点击 15 个入口、设置隔离、正式 UI 禁词扫描、持仓保存到 SQLite、API 查询、趋势读模型、刷新读取和 API 重启后读取均通过，console errors `0`；`macOS app acceptance lite` `29 pass / 0 fail / 2 info`；三处 `PFI.app` 入口均指向 canonical PFI，其中 Desktop 为 `/Applications/PFI.app` 符号链接。
- 2026-06-28 v0.2.2 Stage 5 closeout 运行修复：`src/pfi_os/app/streamlit_app.py` 移除原生上传面板内嵌 `st.expander()`，避免 Streamlit `Expanders may not be nested`；`page_icon` 改为 `None`，避免浏览器请求 `/PFI` 产生 404。`tests/test_v021_stage8_final_acceptance.py` 增加对应回归断言。
- 2026-06-28 v0.2.2 Stage 6 closeout 运行修复：`src/pfi_os/app/streamlit_app.py` 正式 UI 不再显示 `runtime` 路径、`Web Shell` 和 `manifest` 等开发词；父页面保留本机上传，8 个一级入口由上方工作台 iframe 展示；`web/pfi_v022_tag_views.html` 补齐 6 个默认标签组并避免 favicon 404。
- 2026-06-28 v0.2.2 Stage 7：新增 `src/pfi_v02/stage_v022_formula_scoring.py`、`docs/pfi_v022/STAGE7_FORMULA_SCORING.md` 和 `tests/test_v022_stage7_formula_scoring.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage7`；三基文件、README、roadmap lock 和参数变更记录同步记录 100 分置信度、统一 70 分复核线、双消费公式、投资市值/收益/行为公式、现金流窗口、储备金安全线和投资挤压生活现金模型。
- 2026-06-28 v0.2.2 Stage 8：新增 `src/pfi_v02/stage_v022_runtime_diff.py`、`docs/pfi_v022/STAGE8_RUNTIME_DIFF_IMPACTED_METRICS.md`、`review_queue/CODEX_REVIEW_TICKET_TEMPLATE.md` 和 `tests/test_v022_stage8_runtime_diff.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage8`；三基文件、README、roadmap lock 和参数变更记录同步记录 dependency hash、P0/P1/P2 impacted metrics、no-diff 外部触发禁用和本地中文 Codex Review Ticket。
- 2026-06-28 v0.2.2 Stage 9：新增 `src/pfi_v02/stage_v022_visualization_uiux.py`、`docs/pfi_v022/STAGE9_VISUALIZATION_UIUX.md`、`docs/pfi_v022/INTERCONNECTION_MAP.md`、`web/interconnection-map.html` 和 `tests/test_v022_stage9_visualization_uiux.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage9`；三基文件、README、roadmap lock 和参数变更记录同步记录参数中心、Interconnection Map、Metric Dependency Graph、现金流可视化和 Metric Drilldown Debugger。
- 2026-06-28 v0.2.2 Stage 10：新增 `src/pfi_v02/stage_v022_report_advice_review.py`、`docs/pfi_v022/STAGE10_REPORT_ADVICE_REVIEW.md` 和 `tests/test_v022_stage10_report_advice_review.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage10`；三基文件、README、roadmap lock 和参数变更记录同步记录月报双消费口径、投资成本行为报告、Interconnection 数据质量报告、行动建议评分公式和建议生命周期。
- 2026-06-28 v0.2.2 Stage 11：新增 `src/pfi_v02/stage_v022_test_validation.py`、`docs/pfi_v022/STAGE11_TEST_VALIDATION.md` 和 `tests/test_v022_stage11_test_validation.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage11`；三基文件、README、roadmap lock 和参数变更记录同步记录金融逻辑单元测试、跨板块一致性测试和可视化一致性测试。
- 2026-06-28 v0.2.2 Stage 12 - 文档同步与交付：新增 `src/pfi_v02/stage_v022_delivery.py`、`web/pfi_v022_logic_review.html`、`docs/pfi_v022/STAGE12_DELIVERY_REPORT.md`、`docs/pfi_v022/SIX_AGENT_DELIVERY_REVIEW.md`、`reports/pfi_v022_summary.md` 和 `tests/test_v022_stage12_delivery.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage12`，新增 `delivery` 参数域和 `stage12_task_ids`；`S12-P1-T1`、`S12-P1-T2`、`S12-P1-T3`、`S12-P2-T1`、`S12-P2-T2`、`S12-P2-T3` 均完成；三基文件、README、roadmap lock 和参数变更记录同步记录参数中心、标签系统、Interconnection 可视化、双消费口径、现金流图表、diff ticket、Stage -> Phase -> Task、2 轮 × 6 Agent 自检和用户人工复核。
- 2026-06-28 v0.2.2 Stage 13：新增 `src/pfi_v02/stage_v022_post_review.py`、`docs/pfi_v022/STAGE13_POST_REVIEW.md`、`review_queue/codex_review_stage13_owner_specified_20260628.md`、`docs/pfi_v022/DOWNLOADS_CLEANUP_STAGE13.md` 和 `tests/test_v022_stage13_post_review.py`；`config/pfi_parameters.yaml` 升级为 `PFIParametersV022Stage13`，新增 `post_review` 参数域和 `stage13_task_ids`；Downloads 中 `PFI_V022_STAGE0_PRE_CANONICAL_SYNC_20260628T090028` 等 6 个 PFI 预同步临时目录已归档并移出 Downloads，`PFI.app` 和用户 taskpack/roadmap/zip/md 源文件保留；复核记录已包含问题、修复、验证、剩余风险。

## Decisions

- Do not re-embed `QBVS/qbvs` inside `PFI/`.
- Any future QBVS change must happen under `CodexProject/QBVS`.
- Put new shared PFI V0.2 contracts at the `PFI/` root.
- Keep PFI strategy backtesting, 盘感训练 and 大数据模拟器 under PFI `投资管理`.
- Keep V0.1 compatibility entries visible as aliases in the same navigation list: 首页、市场、研究、持仓、策略实验室、数据与系统.
- Do not recreate a separate `strategy` product workspace; PFI strategy backtesting, 盘感训练 and simulator stay under `投资管理`.
- Do not recreate visible new/old navigation group titles.
- Keep PFI research-only: no trading password, no automatic real-money orders.
- Non-CSV sources are first-class: 支付宝基金、中国大陆券商、ABC Bullion do not rely on CSV as the primary contract.
- Low-confidence OCR/screenshot/recording input is candidate-only and must enter review before acceptance.
- Stage 3 `sync_all_plan` is a plan/preview only. It does not log in, submit payments, submit broker orders, or mutate real accounts.
- Stage 3 legacy FX values were deterministic local fixtures for UI/test readability. v0.2.2 Stage 2 introduces real local snapshot reading for current `AUD/CNY` display while still prohibiting ordinary-run network refresh.
- Stage 4 attribution values are deterministic local estimates. If evidence is insufficient, PFI must show `estimate/需要复核` rather than precise conclusions.
- Stage 4 consumption analysis excludes transfers and investment records from living consumption.
- Stage 4 cashflow forecast separates life cash from investment cash.
- Stage 5 recommendations are review queue items. They are not orders, payment actions, or automatic real-money decisions.
- Stage 5 Alpha export is only `pfi_context_snapshot_v1`; it does not add Alpha/Ralpha/System first-level entries and does not modify the Alpha repository.
- Stage 5 context constraints keep `trading_password_available=false` and `live_trade_submission_authorized=false`.
- Stage 6 is synthetic/read-only E2E only. It proves local V0.2 can run, verify, and rollback; it does not prove real account production connectivity.
- Stage 6 follow-ups are separate gates: external Alpha context consumer, real account data connection, PDF/ZIP package, CDR/Open Banking, and production release evidence.

## Validation Commands

```bash
PYTHONPATH=src python3 -B -m unittest tests.test_stage1_ia_contract tests.test_stage1_core_models tests.test_stage1_classification_rules tests.test_stage2_data_source_registry tests.test_stage2_cba_csv_import tests.test_stage2_alipay_import tests.test_stage2_non_csv_contracts tests.test_stage3_readable_mvp tests.test_stage4_analysis_mvp tests.test_stage5_advice_report_alpha tests.test_stage6_e2e_stabilization -q
cd ../QBVS && PYTHONPATH=. python3 -B -m unittest tests.test_s3pct02_lifecycle -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -B -m pfi_os.examples.macos_app_acceptance_lite --project-root . --summary-json
node --check web/app/shell.js
git diff --check
```

Latest Stage 2 target result: `Ran 22 tests / OK`.
Latest closeout result: Stage 1+2 contracts `Ran 45 tests / OK`; legacy QBVS smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; PFI.app resolves to `CodexProject/PFI`; port 8501 is served by canonical PFI `.venv`; no PFI LaunchAgent found.
Latest Stage 3 closeout result: Stage 1+2+3 contracts `Ran 59 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Python compile `OK`; Web shell syntax `OK`.
Latest Stage 4 closeout result: Stage 1+2+3+4 contracts `Ran 71 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Stage 4 contract `Ran 12 tests / OK`; Python compile `OK`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`.
Latest Stage 5 closeout result: Stage 1+2+3+4+5 contracts `Ran 85 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Stage 5 contract `Ran 14 tests / OK`; Python compile `OK`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; browser validation screenshot `/tmp/pfi-stage5-browser-verified.png`.
Latest Stage 6 closeout result: Stage 1+2+3+4+5+6 contracts `Ran 95 tests / OK`; legacy QBVS lifecycle smoke `Ran 1 test / OK`; project governance validation `errors 0 / warnings 0`; human-entry Markdown contract `Ran 2 tests / OK`; Stage 6 contract `Ran 10 tests / OK`; Python compile `OK`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; browser validation screenshot `/tmp/pfi-stage6-browser-verified.png`.
Latest验收退回纠偏 result: `tests.test_stage2_alipay_import` `Ran 7 tests / OK`; Stage 1 classification + Stage 2 targeted contracts `Ran 32 tests / OK`; Python compile `OK`; Web shell syntax `OK`; real old Alipay import `4/4 files`, `8815` records, `406` review; browser validation `upload panel true`, `private ledger true`, `file input 1`, `navCount 8`, all primary entry clicks OK, no raw `ready`/`Synthetic E2E`; screenshot `/tmp/pfi-alipay-upload-verified-v2.png`.
Latest v0.2.1 Stage 1 target result: Stage 1 target contracts `Ran 22 tests / OK`; full PFI unittest discover `Ran 112 tests / OK`; `node --check web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop clicked `15/15` entries with screenshot `/tmp/pfi-v021-stage1-nav-verified.png`; Chrome headless mobile 390x844 validated `数据源与上传` and `策略实验室` with screenshot `/tmp/pfi-v021-stage1-mobile-verified.png`.
Latest v0.2.1 Stage 2 target result: Stage 2 contract `Ran 4 tests / OK`; Stage 0/1/2 frontend contracts `Ran 16 tests / OK`; Stage 4/5/6 regression contracts `Ran 36 tests / OK`; full PFI unittest discover `Ran 116 tests / OK`; `node --check PFI/web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop clicked `15/15` entries and validated `复盘生命周期`、`PFI 上下文导出`、`策略实验室`, console errors `0`, screenshot `/tmp/pfi-v021-stage2-copy-desktop-verified.png`; Chrome headless mobile 390x844 validated `15` entries and `数据源与上传`, screenshot `/tmp/pfi-v021-stage2-copy-mobile-verified.png`.
Latest v0.2.1 Stage 3 target result: Stage 0/1/2/3 frontend contracts `Ran 21 tests / OK`; full PFI unittest discover `Ran 121 tests / OK`; `node --check PFI/web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop verified settings route, legacy data-system deep link, fuzzy searches `xf`、`fk`、`ledger`, keyboard jump and console errors `0`, screenshot `/tmp/pfi-v021-stage3-settings-search-desktop-verified.png`; Chrome headless mobile 390x844 verified fuzzy search `fk` -> `运行反馈控制台`, screenshot `/tmp/pfi-v021-stage3-settings-search-mobile-verified.png`.
Latest v0.2.1 Stage 4 target result: Stage 0/1/2/3/4 frontend contracts `Ran 26 tests / OK`; full PFI unittest discover `Ran 126 tests / OK`; `node --check PFI/web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop verified `/accounts`、`/investment`、`/consumption` trend titles, CNY baseline, legends and nonblank canvas with console errors `0`, screenshot `/tmp/pfi-v021-stage4-trends-desktop-verified.png`; Chrome headless mobile 390x844 verified `消费管理` trend panel and nonblank canvas, screenshot `/tmp/pfi-v021-stage4-trends-mobile-verified.png`.
Latest v0.2.1 Stage 5 target result: Stage 0/1/2/3/4/5 frontend contracts `Ran 31 tests / OK`; full PFI unittest discover `Ran 131 tests / OK`; `node --check PFI/web/app/shell.js` OK; governance `errors 0 / warnings 0`; `git diff --check -- PFI` OK; Chrome headless desktop verified `/sources-upload` upload panel, file picker upload, drag/drop upload, failure feedback, import center summary, review-link jump to `账本流水`, console errors `0`, screenshot `/tmp/pfi-v021-stage5-upload-desktop-verified.png`; Chrome headless mobile 390x844 verified upload/import panel and review entry, screenshot `/tmp/pfi-v021-stage5-upload-mobile-verified.png`.
Latest v0.2.1 Stage 6 target result: Stage 0/1/2/3/4/5/6 frontend contracts `Ran 37 tests / OK`; target Stage 6 contract `Ran 6 tests / OK`; full PFI unittest discover `Ran 137 tests / OK`; governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; browser desktop verified `/investment?tab=holdings` edit/save/reload/reopen persistence with console errors `0`, screenshot `/tmp/pfi-v021-stage6-holdings-desktop-verified.png`; browser mobile 390x844 verified holdings panel and 3 rows, screenshot `/tmp/pfi-v021-stage6-holdings-mobile-verified.png`.
Latest v0.2.1 Stage 7 target result: Stage 0/1/2/3/4/5/6/7 frontend contracts `Ran 42 tests / OK`; target Stage 7 contract `Ran 5 tests / OK`; full PFI unittest discover `Ran 142 tests / OK`; governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; browser desktop/mobile verified 15 primary entries, 14 unique route aliases, 40 representative clicks, 15 command entries, `progress/success/failure` feedback states, zero console errors, screenshots `/tmp/pfi-v021-stage7-clicksafe-desktop-verified.png` and `/tmp/pfi-v021-stage7-clicksafe-mobile-verified.png`.
Latest v0.2.1 Stage 8 target result: Stage 0/1/2/3/4/5/6/7/8 frontend contracts `Ran 47 tests / OK`; target Stage 8 contract `Ran 5 tests / OK`; full PFI unittest discover `Ran 147 tests / OK`; governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; browser desktop/mobile verified 15 primary entries, 14 unique route aliases, AUD/CNY 06:00 badge, global fuzzy search, upload picker/drag/drop/failure feedback, ledger review entry, holdings persistence, settings feedback console, progress/success/failure feedback states, zero console errors, screenshots `/tmp/pfi-v021-stage8-final-desktop-verified.png` and `/tmp/pfi-v021-stage8-final-mobile-verified.png`; GitHub main synced at `f6a53db5`; canonical `PFI/` content matches `origin/main`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; `/Applications/PFI.app`、`~/Downloads/PFI.app`、`~/Desktop/PFI.app` all point to canonical PFI; `http://127.0.0.1:8501/_stcore/health` returned `ok`.
Latest v0.2.2 Stage 2 target result: Stage 2 FX contract `Ran 7 tests / OK`; Stage 0+1+2 targeted governance contracts `Ran 24 tests / OK`; full PFI unittest discover `Ran 171 tests / OK`; governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; local FX read returned `fx_AUD_CNY_20260628`, `rate=4.6874`, `ordinary_runtime_network_refresh=false`.
Latest v0.2.2 Stage 4 review closeout result: Stage 4 review target `4 passed, 26 subtests passed`; Stage 4 related regression `24 passed, 79 subtests passed`; full PFI pytest `270 passed, 251 subtests passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; parameter JSON parse `OK`; macOS app acceptance lite `Blocked, pass=22, fail=7, info=2` because `/Users/linzezhang/Desktop/PFI.app` is missing while runtime 8501 is healthy; GitHub main sync commit `795a509badd2f44de5ce95f67e07402b509b3b4b`.
Latest v0.2.2 Stage 5 target result: Stage 5 ledger taxonomy contracts `5 passed`; Stage 0-5 v0.2.2 contracts `45 passed`; full PFI pytest `203 passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; Streamlit app compile `OK`; macOS app acceptance lite `29 pass / 0 fail / 2 info`; `/Applications/PFI.app` launched canonical PFI on port `8501`, PID `87045`; browser validation confirmed PFI 首页、数据源上传、投资管理、消费管理、AUD/CNY 徽标和原生上传控件可见，nested expander error `false`, console errors `0`, screenshot `/tmp/pfi-v022-stage5-app-verified.png`; GitHub `main` closeout sync completed for PFI-only changes.
Latest v0.2.2 Stage 5 review rework result: target review set `18 passed, 85 subtests passed`; side thread UI cleanup set `24 passed, 7 subtests passed`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; true 8501 desktop/mobile matrix `/tmp/pfi_uiux_recheck_stage5_fixed2/summary.json` shows iframe=1, native upload patch false, 15/15 primary entries visible and clickable, `8815/406` real Alipay search hits, upload/import center visible, business feedback pollution 0, settings feedback visible, forbidden visible text 0, console/page errors 0. GitHub sync intentionally not run in this correction turn because the latest handoff says this round should not sync and the worktree has mixed side-thread/user changes.
Latest v0.2.2 Stage 6 review rework result: Stage 6 target + review tests `9 passed, 139 subtests passed`; Stage 0-6 related regression `54 passed, 243 subtests passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; `http://127.0.0.1:8501/_stcore/health` returned `ok`; true 8501 desktop/mobile matrix `/tmp/pfi_stage6_review_recheck/summary.json` passed with 15 primary entries visible/clickable, 7 homepage workflow buttons clickable, real Alipay search hits for `8815/406`, strategy lab top entry and investment inner entry on the same route, settings feedback isolated from business pages, forbidden visible text `0`, console/page errors `0`, mobile horizontal overflow `0px`. Full PFI pytest and macOS app acceptance were not rerun in this correction turn; GitHub sync intentionally not run because the worktree has mixed side-thread/user changes and this is not the overall goal closeout.
Latest v0.2.2 Stage 7 review rework result: target + review tests `10 passed, 38 subtests passed`; Stage 0-7 related regression `61 passed, 245 subtests passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; `http://127.0.0.1:8501/_stcore/health` returned `ok`; formulas now load real `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` with `8815` Alipay records for confidence, consumption, and cashflow; investment formulas return Chinese empty state when no real holdings/sell trades exist; true 8501 desktop/mobile matrix `/tmp/pfi_stage7_review_recheck/summary.json` passed with 15 primary entries visible/clickable, 7 homepage workflow buttons clickable, real Alipay search hits for `8815/406`, strategy lab top entry and investment inner entry on the same route, settings feedback isolated from business pages, forbidden visible text `0`, console/page errors `0`, mobile horizontal overflow `0px`. Full PFI pytest and macOS app acceptance were not rerun in this correction turn; GitHub sync intentionally not run because the worktree has mixed side-thread/user changes and this is not the overall goal closeout.
Latest v0.2.2 Stage 8 review rework result: Stage 8 target + review tests `11 passed, 44 subtests passed`; Stage 0-8 related regression `69 passed, 262 subtests passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; `http://127.0.0.1:8501/_stcore/health` returned `ok`; runtime diff now loads real `MetaDatabase/PFI/alipay_daily/raw` and `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` with `4` raw files and `8815` normalized Alipay records, while missing Interconnection grouping uses Chinese real empty state; true 8501 desktop/mobile matrix `/tmp/pfi_stage8_review_recheck/summary.json` passed with 15 primary entries visible/clickable, 7 homepage workflow buttons clickable, real Alipay search hits for `8815/406`, strategy lab top entry and investment inner entry on the same route, settings feedback isolated from business pages, forbidden visible text `0`, console/page errors `0`, mobile horizontal overflow `0px`. Full PFI pytest and macOS app acceptance were not rerun in this correction turn; GitHub sync intentionally not run because the worktree has mixed side-thread/user changes and this is not the overall goal closeout.
Latest v0.2.2 Stage 9 review rework result: Stage 9 target + review tests `13 passed, 68 subtests passed`; Stage 0-9 related regression `82 passed, 330 subtests passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; `http://127.0.0.1:8501/_stcore/health` returned `ok`; visualization/UIUX now loads real `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` with `8815` Alipay records, `4` raw files, `406` review records, `56` default tags and `0` advice items; no real holdings or Interconnection grouping use Chinese empty states; local HTML matrix `/tmp/pfi_stage9_review_recheck/stage9-html-summary.json` passed with 12 map nodes, 3 drilldown nodes, forbidden fake values `0`, external requests `0`, console/page errors `0`; true 8501 desktop/mobile matrix `/tmp/pfi_stage9_review_recheck/summary.json` passed with 15 primary entries visible/clickable, 7 homepage workflow buttons clickable, real Alipay search hits for `8815/406`, strategy lab top entry and investment inner entry on the same route, settings feedback isolated from business pages, forbidden visible text `0`, console/page errors `0`, mobile horizontal overflow `0px`. Full PFI pytest and macOS app acceptance were not rerun in this correction turn; GitHub sync intentionally not run because the worktree has mixed side-thread/user changes and this is not the overall goal closeout.
Latest v0.2.2 Stage 10 review rework result: Stage 10 target + review tests `11 passed, 18 subtests passed`; Stage 0-10 related regression `93 passed, 348 subtests passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; `http://127.0.0.1:8501/_stcore/health` returned `ok`; report/advice now loads real `MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv` with `8815` Alipay records, `406` review records, `CNY 3,082,013.96` review amount coverage, `181` large-spend records and `CNY 1,213,978.31` large-spend amount; recommendations are real-triggered for 数据修复、消费复盘、现金流风险、参数调整, while 投资行为复盘 and 订阅优化 use Chinese empty states when no real evidence exists; true 8501 desktop/mobile matrix `/tmp/pfi_stage10_review_recheck/summary.json` passed with key entries visible, advice/report clicks, real Alipay search hits for `8815/406`, forbidden visible text `0`, console/page errors `0`, mobile horizontal overflow `0px`. Full PFI pytest and macOS app acceptance were not rerun in this correction turn; GitHub sync intentionally not run because the worktree has mixed side-thread/user changes and this is not the overall goal closeout.
Latest v0.2.2 Stage 11 review rework result: Stage 11 target + review tests `11 passed, 15 subtests passed`; Stage 0-11 related regression `104 passed, 363 subtests passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; `http://127.0.0.1:8501/_stcore/health` returned `ok`; true 8501 desktop/mobile matrix `/tmp/pfi_stage11_review_recheck/summary.json` passed with 7 homepage workflow cards visible, `.workflow-meta=0`, primary entries and real homepage buttons clickable, global search hits for `406/8815`, forbidden visible Stage 11/development/test-data terms `0`, console/page errors `0`, horizontal overflow `0px`, screenshots `/tmp/pfi_stage11_review_recheck/desktop.png` and `/tmp/pfi_stage11_review_recheck/mobile.png`. Full PFI pytest and macOS app entry reinstall were not rerun in this correction turn; GitHub sync intentionally not run because the worktree has mixed side-thread/user changes and this is not the overall goal closeout.
Latest v0.2.2 Stage 12 review rework result: Stage 12 target + review tests `10 passed, 35 subtests passed`; Stage 0-12 related regression `114 passed, 398 subtests passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; `http://127.0.0.1:8501/_stcore/health` returned `ok`; Stage 12 summary/report are now Stage12-only and no longer claim Stage 13 execution or Downloads cleanup; local HTML matrix `/tmp/pfi_stage12_review_recheck/summary.json` passed with 7 clickable sections, external requests `0`, console/page errors `0`, screenshot `/tmp/pfi_stage12_review_recheck/stage12-html.png`; true 8501 desktop/mobile matrix `/tmp/pfi_stage12_review_recheck/summary.json` passed with official UI not showing Stage 12 docs or linking `pfi_v022_logic_review`, 7 homepage workflow cards visible, `.workflow-meta=0`, primary entries and real homepage buttons clickable, global search hits for `406/8815`, forbidden visible terms `0`, console/page errors `0`, horizontal overflow `0px`, screenshots `/tmp/pfi_stage12_review_recheck/app-desktop.png` and `/tmp/pfi_stage12_review_recheck/app-mobile.png`. Full PFI pytest, macOS app entry reinstall, GitHub sync and Downloads cleanup were not run in this correction turn because this is not the overall goal closeout.
Latest v0.2.2 Stage 13 review result: Stage 13 target + review tests `10 passed, 87 subtests passed`; Stage 0-13 v0.2.2 related regression `135 passed, 593 subtests passed`; project governance `errors 0 / warnings 0`; Web shell syntax `OK`; `git diff --check -- PFI` `OK`; `http://127.0.0.1:8501/_stcore/health` returned `ok`; true 8501 desktop/mobile matrix `/tmp/pfi_stage13_review_recheck/summary.json` passed with required Chinese entries and `AUD/CNY` visible, 7 workflow cards, `.workflow-meta=0`, clicks for `首页总览`、`数据源与上传`、`上传中心`、`导入中心`、`建议与复盘`、`报告与洞察`、`设置`, global search hits for `406/8815`, forbidden Stage 13/development/test-data terms `0`, console/page errors `0`, horizontal overflow `0px`, screenshots `/tmp/pfi_stage13_review_recheck/app-desktop.png` and `/tmp/pfi_stage13_review_recheck/app-mobile.png`. Required boundary remains: 本轮只复审解决 Stage 13；整体项目复审解决不在本轮实现；GitHub 同步不在本轮执行；app 入口重装不在本轮执行；阻塞项数量：`0`。
Latest v0.2.2 overall project review result: 整体项目复审解决已完成；Stage 0-13 已复审解决；真实 MetaDatabase `8815` 条标准化支付宝流水作为正式验收数据源；正式页面、报告、图表、首页摘要和建议不得使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据作为验收依据；完整 PFI pytest `321 passed, 729 subtests passed`；Stage 0-13 + overall 回归 `139 passed, 692 subtests passed`；真实 8501 浏览器矩阵 `/tmp/pfi_v022_overall_review_recheck/summary.json` 为 `131 pass / 0 fail`；macOS app acceptance lite `29 pass / 0 fail / 2 info`；整体复审报告为 `docs/pfi_v022/reviews/OVERALL_PROJECT_REVIEW_20260629.md`，最终测试数据审计为 `docs/pfi_v022/reviews/TEST_DATA_AUDIT_FINAL_20260629.md`；GitHub main 同步纳入本轮 closeout；阻塞项数量：`0`。

## Next

1. 后续 PFI 开发先确认 canonical checkout、8501 health、app 入口和 GitHub main 是否一致。
2. 如继续 v0.2.2 之后的阶段，先读取本文件、`docs/pfi_v022/reviews/OVERALL_PROJECT_REVIEW_20260629.md` 和 `docs/pfi_v022/reviews/TEST_DATA_AUDIT_FINAL_20260629.md`。

## Latest v0.2.1.1 Stage 1 Result

- 2026-06-29：Stage 1 产品壳与路由已在干净临时 worktree 实施。
- 当前正式一级入口为 10 个，新增一级入口 `市场与研究`，移除侧栏中的旧 alias 入口。
- 旧入口保留为 route/search/command alias：`首页 -> /home`、`市场 -> /market-research?tab=market`、`研究 -> /market-research?tab=research`、`持仓 -> /investment?tab=holdings`、`策略实验室 -> /market-research/strategy-lab`、`数据与系统 -> /settings?tab=data-system`。
- 策略实验室唯一正式路由为 `/market-research/strategy-lab`；旧 `#/strategy-lab` 和 `#/investment/strategy-lab` 兼容重定向。
- 本轮不做图表、上传闭环、持仓编辑、报告，也不声明 v0.2.1.1 整体完成。

## Latest v0.2.1.1 Stage 2 Result

- 2026-06-29：Stage 2 页面骨架与去 AI 化在干净临时 worktree 实施。
- 10 个正式一级入口均具备中文页面骨架和二级入口；`数据源与上传` 固定包含 `上传中心` 和 `导入中心`。
- 默认首页使用净资产、现金余额、投资市值、本月支出、待复核交易、数据源状态和中文快捷操作。
- 正式 UI 不再展示运行边界、Task Pack、Demo、Prototype、手机预览、运行反馈控制台、多模态交互反馈、证据抽屉、运行证据、任务中心。
- 设置相关反馈、主题、语言和备份项只归属 `设置` 页。
- 本轮不做数据库 migration、上传入库闭环、持仓 SQLite 闭环、真实图表数据接入，也不声明 v0.2.1.1 整体完成。
- 验证结果：完整 PFI 测试 `336 passed, 729 subtests passed`；Chrome headless 真实浏览器矩阵 `/tmp/pfi_v0211_stage2_browser/summary.json` 为 `55 pass / 0 fail`；Web Shell 语法和 `git diff --check -- PFI` 通过。

## Latest v0.2.3 Stage 1 Result

- 2026-06-29：Stage 1 App 入口与前端版本一致性在独立 worktree `main_worktree/CodexProject/pfi-stage1` 实施。
- `~/Downloads/PFI.app` 已由 `scripts/installPFIEntryApps.sh --downloads-only` 安装并绑定当前 checkout 的 `PFI_PROJECT_ROOT`。
- `PFI.app` bundle version 更新为 `0.2.3 / 20260629.1`；启动 URL 固定携带 `pfi_app_version=0.2.3`、`pfi_build=20260629-stage1` 和 `pfi_ui_contract=PFI-V023-STAGE1-APP-ENTRY-BUNDLE-CONSISTENCY`。
- Streamlit 嵌入 Web Shell 时注入 `projectRoot`、`webBundleHash`、`webIndexSha256`、`shellJsSha256`、`buildId` 和 `uiContractVersion`，用于验证 app 入口、localhost 和当前 frontend bundle 一致。
- 真实 `~/Downloads/PFI.app` runtime acceptance 通过：app acceptance `10 pass / 0 fail`，8501 health 通过，运行中 cache guard 通过，停止后 cache dry-run 通过。
- 全新 Chrome profile 浏览器验收通过：iframe 内 `window.PFI_STAGE1_ENTRY_METADATA` 的 build id、UI contract version、bundle hash、index hash 和 shell hash 均与当前磁盘 bundle 一致。
- 验证结果：Stage 0/1/app-entry 合同 `18 passed`；完整 PFI pytest `369 passed`；`node --check PFI/web/app/shell.js`、Python compile、`zsh -n` 和 `git diff --check -- PFI` 均通过。
- 本轮未做 Stage 2 页面重建、路由重做、数据计算/read model、报告生成或任何假财务数据。

## Latest v0.2.3 Stage 2 Phase 1 Result

- 2026-06-30：Stage 2 Phase 1 任务包恢复与防幻觉门已迁移并验收于项目级长期 worktree `main_worktree/CodexProject/pfi`（branch `codex/pfi`）。
- 本 phase 只检查并记录 v0.2.3 Stage 2 的真实任务包来源，不做页面、路由、数据、报告或 app 入口开发。
- 当前 GitHub main 只有 v0.2.3 Stage 0/1 交付物；新电脑未找到 Stage 0 记录的 `~/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_Roadmap.txt` 和 `~/Downloads/PFI_v0.2.3_Human_Product_Experience_Recovery_TaskPack.zip`。
- 在真实 v0.2.3 Stage 2 Roadmap/TaskPack 恢复或用户明确指定替代源前，不得把 v0.2.1.1、v0.2.2 或旧 PFI V0.2 的 Stage 2 当作当前任务包。
- 中间 phase 完成不上传 GitHub main；只在整个 Stage 2 完成并复审解决后统一上传。
