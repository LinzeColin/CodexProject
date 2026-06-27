# PFI v0.2.1 前端优化

更新时间：2026-06-27 Australia/Sydney

## Stage 0 目标

本轮是 `v0.2.1 前端优化` 的准备轮，任务 ID 为 `V021-P0-S0-T01`。目标是读取并锁定 roadmap，把后续前端优化拆成可逐 stage 验收的合同，不提前实现后续 stage。

权威输入：

- `/Users/linzezhang/Downloads/pfi_v0.2.1_frontend_optimization_task_pack_roadmap.md`
- `/Users/linzezhang/Downloads/pfi_os_delivery_stage1_clicksafe.html`
- 当前 GitHub / 本机产品根：`LinzeColin/CodexProject/PFI`
- 当前正式前端目标：`PFI/web/index.html` + `PFI/web/app/shell.js`

## 本轮范围

本轮只做准备和合同化：

- 锁定版本名：`v0.2.1 前端优化`。
- 锁定后续交付范围：PFI 前端、交互、图表、上传命名、设置页、持仓编辑持久化。
- 锁定正式 UI 目标：HTML Web Shell，不再把交付目标放在演示 HTML 或 Streamlit 侧栏。
- 锁定 CNY 作为系统基准货币。
- 锁定所有页面顶部右上角常态显示 CNY/AUD 汇率。
- 锁定 UIUX 多模态反馈归属：只在设置页管理，不常驻干扰业务页面。

## 明确不做

- 不重构 QBVS。
- 不把 QBVS 重新放回 PFI。
- 不新增 Alpha、Ralpha、System、Development 产品一级入口。
- 不声明真实账户生产联通。
- 不执行实盘下单、支付提交或券商提交。
- 不在 stage0 提前实现导航、图表、上传、设置页、持仓持久化等后续 stage 功能。

## CNY 基准与 CNY/AUD 汇率契约

PFI v0.2.1 之后整体系统以 CNY 元为基准。所有页面顶部右上角必须常态化展示汇率徽标：

```text
CNY/AUD=4.70（YYYYMMDD--HH:MM）
```

合同解释：

- `base_currency = CNY`。
- `quote_pair = CNY/AUD`。
- 展示语义：1 AUD 折算多少 CNY，用于用户读数和跨币种视图统一。
- 展示位置：所有页面顶部右上角。
- 数据时间：读取当日 06:00 Australia/Sydney 本地时间的汇率快照。
- 时间格式：`YYYYMMDD--HH:MM`。
- 示例：`CNY/AUD=4.70（20260627--06:00）`。
- 数据缺失时必须显示中文空状态：`汇率数据待更新`，不得伪造汇率。

Stage 1 之后的实现验收必须检查 HTML 顶栏、路由切换后保留、桌面和手机视口均可见。

## 统一导航目标

v0.2.1 最终一级入口按以下顺序显示，不展示新旧分组标题。旧入口作为别名或深链，不创建第二套页面。

| 顺序 | 可见入口 | 路由 | 页面归属 |
| --- | --- | --- | --- |
| 1 | 首页总览 | `/home` | 首页总览 |
| 2 | 账户与资产 | `/accounts` | 账户与资产 |
| 3 | 账本流水 | `/ledger` | 账本流水 |
| 4 | 投资管理 | `/investment` | 投资管理 |
| 5 | 消费管理 | `/consumption` | 消费管理 |
| 6 | 数据源与上传 | `/sources-upload` | 数据源与上传 |
| 7 | 建议与复盘 | `/review` | 建议与复盘 |
| 8 | 报告与洞察 | `/reports` | 报告与洞察 |
| 9 | 首页 | `/home` | 首页总览 |
| 10 | 市场 | `/investment?tab=market` | 投资管理 |
| 11 | 研究 | `/investment?tab=research` | 投资管理 |
| 12 | 持仓 | `/investment?tab=holdings` | 投资管理 |
| 13 | 策略实验室 | `/investment/strategy-lab` | 投资管理 |
| 14 | 数据与系统 | `/settings?tab=data-system` | 设置 |
| 15 | 设置 | `/settings` | 设置 |

禁用用户可见分组或模块名：

- `PFI 2.0 当前入口`
- `PFI 1.0 兼容入口`
- `V0.2 当前入口`
- `V0.1 兼容入口`
- `运行边界`
- `Boundary`
- `Non-execution boundary`

## HTML 与多模态反馈目标

正式交付目标是 `PFI/web` HTML Web Shell。`pfi_os_delivery_stage1_clicksafe.html` 只作为交互参考，不作为替代产品页面。

多模态反馈必须进入设置页：

- 运行反馈控制台
- 多模态反馈
- 触感反馈强度
- 声音反馈
- 视觉反馈
- 通知反馈
- 反馈测试
- 无障碍反馈

业务页面默认不常驻反馈控制台。手机浏览器支持震动时才调用 `navigator.vibrate`，不支持时静默降级。

## Roadmap 拆分

| Phase | Stage | Task ID | Task | Done 标准 |
| --- | --- | --- | --- | --- |
| P0 | S0 基线 | V021-P0-S0-T01 | 建立 v0.2.1 任务记录 | 文档、版本、范围明确。 |
| P1 | S1 导航合并 | V021-P1-S1-T01 | 删除新旧入口分组标题 | 入口统一显示，无分组字样。 |
| P1 | S1 导航合并 | V021-P1-S1-T02 | 数据源与同步改为数据源与上传 | 全站展示新名称。 |
| P1 | S1 导航合并 | V021-P1-S1-T03 | 低操作导入中心改为导入中心 | 全站展示导入中心。 |
| P1 | S1 导航合并 | V021-P1-S1-T04 | 合并策略实验室 | 只有一个策略实验室路由和状态源。 |
| P2 | S2 文案清理 | V021-P2-S2-T01 | 全局中文化 | 禁用英文扫描通过。 |
| P2 | S2 文案清理 | V021-P2-S2-T02 | 删除运行边界 UI 板块 | 用户界面不出现运行边界模块。 |
| P2 | S2 文案清理 | V021-P2-S2-T03 | 删除桌面手机预览框 | 桌面无手机演示框，手机真实响应式可用。 |
| P3 | S3 设置页 | V021-P3-S3-T01 | 设置页独立路由 | 默认不显示右侧设置。 |
| P3 | S3 设置页 | V021-P3-S3-T02 | 运行反馈控制台移入设置 | 设置页可配置反馈。 |
| P4 | S4 趋势模型 | V021-P4-S4-T01 | 新增统一趋势数据结构 | 三类页面可读同一趋势合同。 |
| P4 | S4 趋势模型 | V021-P4-S4-T02 | 账户与资产折线图 | 现金 / 净资产趋势显示。 |
| P4 | S4 趋势模型 | V021-P4-S4-T03 | 投资管理折线图 | 市值 / 总收益 / 现金仓位显示。 |
| P4 | S4 趋势模型 | V021-P4-S4-T04 | 消费管理折线图 | 支出 / 预算 / 现金流显示。 |
| P5 | S5 上传中心 | V021-P5-S5-T01 | 上传中心 | 上传、拖拽、状态、失败反馈可用。 |
| P5 | S5 上传中心 | V021-P5-S5-T02 | 导入中心 | 批次、摘要、复核入口可用。 |
| P6 | S6 持仓持久化 | V021-P6-S6-T01 | 持仓编辑数据模型 | adjustment 和 snapshot 可写入数据库。 |
| P6 | S6 持仓持久化 | V021-P6-S6-T02 | 持仓编辑服务 | 新增、修改、软删除、读取测试通过。 |
| P6 | S6 持仓持久化 | V021-P6-S6-T03 | 持仓编辑前端 | 刷新 / 重启后修改仍存在。 |
| P7 | S7 流畅度 | V021-P7-S7-T01 | 所有入口和按钮可点击 | 自动遍历无死按钮。 |
| P7 | S7 流畅度 | V021-P7-S7-T02 | 页面反馈统一 | 成功、失败、进行中都有反馈。 |
| P8 | S8 验收 | V021-P8-S8-T01 | 前端合同测试 | 新增测试通过。 |
| P8 | S8 验收 | V021-P8-S8-T02 | 浏览器验收 | 桌面 / 手机关键路径通过。 |
| P8 | S8 验收 | V021-P8-S8-T03 | 命令验收 | 单测、JS 检查、治理、diff 检查通过。 |

## Stage 0 验收标准

- `PFI/VERSION` 写明 `v0.2.1 前端优化`。
- 本文件存在，并写明 v0.2.1 是前端优化，不是 V0.2 重构。
- 三基文件已更新：`开发记录.md`、`功能清单.md`、`模型参数文件.md`。
- 新增 `src/pfi_v02/stage_v021_frontend_contract.py`。
- 新增 `tests/test_v021_stage0_frontend_contract.py`。
- 合同测试覆盖 CNY 基准、CNY/AUD 顶栏、HTML 目标、多模态反馈设置页归属、15 个统一入口、P0-P8 任务清单。
- 不重构 QBVS，不新增 Alpha/Ralpha/System/Development 产品一级入口。

## Stage 0 停止条件

满足以下条件即停止，不继续实现后续 stage：

- Stage 0 文档、版本、三基、合同测试完成。
- `tests.test_v021_stage0_frontend_contract` 通过。
- 既有 PFI Stage 1 IA 合同仍通过，证明没有提前破坏 V0.2 基线。
- `node --check web/app/shell.js` 通过。
- `python3 ../scripts/validate_project_governance.py --project PFI` 通过。
- `git diff --check -- PFI` 通过。

## 下一轮执行顺序

下一轮 pursuing goal 应从 P1/S1 开始，优先完成导航合并、数据源与上传命名、导入中心命名和策略实验室单一路由。不得跳到持仓持久化或图表实现，除非用户明确改变阶段顺序。

## Stage 1 完成记录

本轮完成 `P1 / S1 导航合并`，覆盖任务：

- `V021-P1-S1-T01`：删除 Web Shell 新旧入口分组标题。
- `V021-P1-S1-T02`：用户可见入口改为 `数据源与上传`。
- `V021-P1-S1-T03`：导入功能统一称为 `导入中心`。
- `V021-P1-S1-T04`：`策略实验室` 统一路由到 `投资管理` 下的 `/investment/strategy-lab`，不再创建独立 `strategy` 一级 workspace。

当前交付：

- HTML Web Shell 左侧导航统一为 15 个一级入口，顺序与上表一致。
- V0.1 六个入口继续保留为别名：`首页`、`市场`、`研究`、`持仓`、`策略实验室`、`数据与系统`。
- `数据与系统` 映射到设置页；`设置` 作为最后一个一级入口可点击。
- 三基文件已明确定位，避免功能目录、开发日志和参数依据互相复制。
- 新增 `docs/pfi_v02/LEDGER_CLASSIFICATION_STANDARD.md`，解释账本分类优先级、消费账户位置和复核阈值。

Stage 1 验收命令：

```bash
cd PFI
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest tests.test_v021_stage1_navigation_contract tests.test_stage1_ia_contract tests.test_stage1_classification_rules -q
node --check web/app/shell.js
python3 ../scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

## Stage 2 完成记录

本轮完成 `P2 / S2 文案清理`，覆盖任务：

- `V021-P2-S2-T01`：全局用户可见文案中文化，保留 `CNY/AUD`、`CSV`、`ZIP`、`JSON`、`Markdown`、`PDF`、`CDR/Open Banking` 等必要技术 token。
- `V021-P2-S2-T02`：删除 Web Shell 中用户可见的 `运行边界`、`查看边界`、`验收边界`、`安全边界` 和英文 `Boundary` 模块表达，统一改为 `使用限制`、`说明` 或 `验收要求`。
- `V021-P2-S2-T03`：确认正式交付目标仍为 `PFI/web` 响应式 HTML Web Shell；没有引入桌面手机演示框、预览框或 iframe 交付面。

当前交付：

- 新增 `build_v021_stage2_contract()` 和 `tests/test_v021_stage2_copy_cleanup_contract.py`。
- 静态 Web Shell 黑名单扫描覆盖 `Review lifecycle`、`PFI Context Export`、`Synthetic E2E`、`Rollback plan`、`Follow-up list`、`Top N`、`tradeoff`、`owner gate`、`parser / raw / batch` 等旧英文/机器文案。
- 动态首页证据抽屉改为中文标题和中文参数：`PFI 第 6 阶段 · 第 5 阶段 · 第 4 阶段输入 · 端到端验收与稳定化`、`任务包验收门禁`、`实盘提交授权=否`。
- Stage 5/6 的用户可见卡片不再展示 `stage5:*`、`stage6:*`、`changed-only governance` 等机器证据字段，改为 `建议证据`、`报告证据`、`总验收门禁`、`合成验收`、`回归治理`。
- 静态 HTML 内置摘要不再提供只有 schema、没有数据的 Stage 3/4/5/6 空 dashboard，避免文件态验收时出现 `0/0` 门禁或缺失上下文按钮；真实运行时仍由应用注入完整摘要。
- 15 个一级入口、V0.1 兼容入口、CNY/AUD 顶栏汇率徽标、策略实验室收口、上传入口和设置页入口均保持不变。

Stage 2 已通过的目标验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v021_stage2_copy_cleanup_contract -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v021_stage2_copy_cleanup_contract PFI.tests.test_v021_stage1_navigation_contract PFI.tests.test_v021_stage0_frontend_contract -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_stage4_analysis_mvp PFI.tests.test_stage5_advice_report_alpha PFI.tests.test_stage6_e2e_stabilization -q
node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s tests -q
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前结果：Stage 2 合同 `Ran 4 tests / OK`；Stage 0/1/2 合同 `Ran 16 tests / OK`；Stage 4/5/6 回归 `Ran 36 tests / OK`；完整 PFI 单测 `Ran 116 tests / OK`；Web Shell 语法检查通过；治理 `errors 0 / warnings 0`；`git diff --check -- PFI` 通过。

浏览器验收：

- Chrome headless desktop 1440x950：15/15 入口可点击；`建议与复盘 -> 复盘生命周期`、`报告与洞察 -> PFI 上下文导出`、`策略实验室` 关键路径通过；console errors `0`；截图 `/tmp/pfi-v021-stage2-copy-desktop-verified.png`。
- Chrome headless mobile 390x844：15 个入口存在；`数据源与上传` 关键路径通过；无 iframe / 手机演示框 / 预览框；截图 `/tmp/pfi-v021-stage2-copy-mobile-verified.png`。

## Stage 2 后续顺序

下一轮 pursuing goal 应从 `P3 / S3 设置页` 开始，优先完成设置页独立路由和运行反馈控制台归口。不得跳到趋势图、上传中心或持仓持久化，除非用户明确改变阶段顺序。

## Stage 3 完成记录

本轮完成 `P3 / S3 设置页与全局搜索`，覆盖任务：

- `V021-P3-S3-T01`：设置页独立路由，`/settings` 和旧入口 `/settings?tab=data-system` 都打开设置主工作区。
- `V021-P3-S3-T02`：运行反馈控制台移入设置页，业务页面默认不常驻反馈控制台。
- 用户追加验收：顶部搜索升级为全局模糊搜索，参考 VS Code / Google Chrome 的搜索体验，支持中文、英文技术词和短别名。

当前交付：

- `设置` 和 `数据与系统` 均映射到设置主工作区；设置页状态标记为 `data-settings-surface="primary_workspace"`。
- 禁止把设置能力做成右侧抽屉、右侧设置栏或业务页常驻设置面板。
- 设置页包含 `运行反馈控制台`、`多模态反馈`、`触感反馈强度`、`声音反馈`、`视觉反馈`、`通知反馈`、`反馈测试`、`无障碍反馈`。
- 顶部全局搜索覆盖 15 个一级入口、V0.1 兼容别名、工作区卡片、功能面板、任务中心行、决策行和设置反馈控制项。
- 全局搜索支持 substring、subsequence、alias keywords 和英文技术 token；示例：`xf` 命中 `消费管理`，`fk` 命中 `运行反馈控制台`，`ledger` 命中 `账本流水`。
- 键盘交互支持 `ArrowDown`、`ArrowUp`、`Enter`、`Escape` 和 `Ctrl/Cmd+K`。
- 搜索结果显示标题、分类、路径和简短提示；无结果时显示中文空状态 `没有匹配结果`。

Stage 3 已通过的目标验收命令：

```bash
node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v021_stage3_settings_search_contract PFI.tests.test_v021_stage2_copy_cleanup_contract PFI.tests.test_v021_stage1_navigation_contract PFI.tests.test_v021_stage0_frontend_contract -q
```

当前结果：Web Shell 语法检查通过；Stage 0/1/2/3 前端合同 `Ran 21 tests / OK`。

Stage 3 closeout 验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s tests -q
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前结果：完整 PFI 单测 `Ran 121 tests / OK`；治理 `errors 0 / warnings 0`；`git diff --check -- PFI` 通过。

浏览器验收：

- Chrome headless desktop 1440x950：`设置` 打开 `#/settings`；`/settings?tab=data-system` 深链恢复设置主工作区；`xf`、`fk`、`ledger` 模糊搜索命中并可回车跳转；console errors `0`；截图 `/tmp/pfi-v021-stage3-settings-search-desktop-verified.png`。
- Chrome headless mobile 390x844：顶部搜索可输入 `fk` 并命中 `运行反馈控制台`；截图 `/tmp/pfi-v021-stage3-settings-search-mobile-verified.png`。

## Stage 3 后续顺序

下一轮 pursuing goal 应从 `P4 / S4 趋势模型` 开始，优先完成统一趋势数据结构、账户与资产折线图、投资管理折线图和消费管理折线图。不得跳到上传中心或持仓持久化，除非用户明确改变阶段顺序。

## Stage 4 完成记录

本轮完成 `P4 / S4 趋势模型`，覆盖任务：

- `V021-P4-S4-T01`：新增统一趋势数据结构 `UNIFIED_TREND_DATA`。
- `V021-P4-S4-T02`：账户与资产折线图显示 `现金` 和 `净资产`。
- `V021-P4-S4-T03`：投资管理折线图显示 `市值`、`总收益` 和 `现金仓位`。
- `V021-P4-S4-T04`：消费管理折线图显示 `支出`、`预算` 和 `现金流`。

当前交付：

- 三类页面读取同一个趋势对象形状：`scope`、`title`、`unit`、`periods`、`series[]`、`emptyState`。
- 趋势数据以 CNY 为显示基准；当前为本地前端验收 fixture，不声明实时账户联通。
- 趋势面板提供中文标题、中文图例、CNY 基准徽标、网格、终点直接标签和中文空状态 `趋势数据待更新`。
- 桌面和手机都使用同一个响应式 HTML Web Shell，不新增 iframe、手机演示框或外部演示 HTML。
- 不新增 QBVS、Alpha、Ralpha、System、Development 一级入口；不新增交易、支付或券商提交动作。

Stage 4 已通过的目标验收命令：

```bash
node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v021_stage4_trend_contract PFI.tests.test_v021_stage3_settings_search_contract PFI.tests.test_v021_stage2_copy_cleanup_contract PFI.tests.test_v021_stage1_navigation_contract PFI.tests.test_v021_stage0_frontend_contract -q
```

当前结果：Web Shell 语法检查通过；Stage 0/1/2/3/4 前端合同 `Ran 26 tests / OK`。

Stage 4 closeout 验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s tests -q
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前结果：完整 PFI 单测 `Ran 126 tests / OK`；治理 `errors 0 / warnings 0`；`git diff --check -- PFI` 通过。

浏览器验收：

- Chrome headless desktop 1440x950：`账户与资产`、`投资管理`、`消费管理` 三个路由均显示中文趋势标题、CNY 基准、图例和非空 Canvas 折线；console errors `0`；截图 `/tmp/pfi-v021-stage4-trends-desktop-verified.png`。
- Chrome headless mobile 390x844：`消费管理` 显示 `支出、预算与现金流趋势`、CNY 基准和非空 Canvas 折线；截图 `/tmp/pfi-v021-stage4-trends-mobile-verified.png`。

## Stage 4 后续顺序

下一轮 pursuing goal 应从 `P5 / S5 上传中心` 开始，优先完成上传、拖拽、状态、失败反馈、导入批次、摘要和复核入口。不得跳到持仓 SQLite 持久化，除非用户明确改变阶段顺序。

## Stage 5 完成记录

本轮完成 `P5 / S5 上传中心`，覆盖任务：

- `V021-P5-S5-T01`：上传中心支持点击选择文件、拖拽投放、状态显示和失败反馈。
- `V021-P5-S5-T02`：导入中心显示批次、摘要和账本复核入口。

当前交付：

- 新增 `build_v021_stage5_contract()` 和 `tests/test_v021_stage5_upload_import_contract.py`。
- `数据源与上传` 页面内新增上传中心，不再只是说明按钮；支持 `CSV`、`ZIP`、`XLS`、`XLSX` 多文件本机预检。
- 上传区支持拖拽进入、拖拽停留、拖拽离开、投放文件和键盘触发文件选择。
- 上传状态显示 `等待选择文件`、`已选择 N 个文件 · 导入预检完成`、`失败反馈 N 项`。
- 失败反馈覆盖空选择、不支持的文件类型和文件过大，全部为中文提示。
- 导入中心显示批次、来源、文件数、记录数、待复核、状态和摘要。
- `进入账本复核` 按钮可点击跳转到账本流水。
- 顶部全局搜索可命中上传中心、拖拽上传、导入中心、导入批次、导入摘要、复核入口和失败反馈。
- 本轮只交付 HTML Web Shell 本机前端交互，不执行外部真实上传、支付、券商提交或实盘自动下单。

Stage 5 已通过的目标验收命令：

```bash
node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v021_stage5_upload_import_contract PFI.tests.test_v021_stage4_trend_contract PFI.tests.test_v021_stage3_settings_search_contract PFI.tests.test_v021_stage2_copy_cleanup_contract PFI.tests.test_v021_stage1_navigation_contract PFI.tests.test_v021_stage0_frontend_contract -q
```

当前结果：Web Shell 语法检查通过；Stage 0/1/2/3/4/5 前端合同 `Ran 31 tests / OK`。

Stage 5 closeout 验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s tests -q
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
```

当前结果：完整 PFI 单测 `Ran 131 tests / OK`；治理 `errors 0 / warnings 0`；`git diff --check -- PFI` 通过。

浏览器验收：

- Chrome headless desktop 1440x950：`/sources-upload` 显示上传/导入面板；文件选择、拖拽上传、失败反馈、导入中心摘要和 `进入账本复核` 跳转到账本流水均通过；console errors `0`；截图 `/tmp/pfi-v021-stage5-upload-desktop-verified.png`。
- Chrome headless mobile 390x844：上传/导入面板和复核入口可见；截图 `/tmp/pfi-v021-stage5-upload-mobile-verified.png`。

## Stage 5 后续顺序

下一轮 pursuing goal 应从 `P6 / S6 持仓持久化` 开始，优先完成持仓编辑数据模型、服务和刷新/重启后仍存在的前端持久化。不得跳到 Stage 7 流畅度，除非用户明确改变阶段顺序。
