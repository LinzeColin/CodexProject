# PFI v0.2.1 Stage 8 最终验收审计

更新时间：2026-06-28 Australia/Sydney

## 目标

本文件用于完成 `Stage 8 / S8 最终验收`，对应任务：

| Phase | Stage | Task ID | 验收目标 | 状态 |
| --- | --- | --- | --- | --- |
| P8 | Stage 8 | `V021-P8-S8-T01` | 前端合同测试 | 已纳入 Stage 0-8 前端合同套件 |
| P8 | Stage 8 | `V021-P8-S8-T02` | 浏览器验收 | 覆盖桌面和手机关键路径 |
| P8 | Stage 8 | `V021-P8-S8-T03` | 命令验收 | 覆盖单测、JS、治理、diff 和 app 验收 |

Stop gate：`PFI-V021-S8-FINAL-ACCEPTANCE-GATE`。

## 范围

本轮只做 `PFI/web` HTML Web Shell、PFI v0.2.1 合同、项目文档、GitHub main 同步、本机 app 入口刷新和本机非必要缓存清理。

不做：

- 不新增真实交易、支付、券商提交或实盘自动下单。
- 不执行实盘自动下单。
- 不收集交易密码。
- 不把 QBVS 重新放回 PFI。
- 不改 ADP、EEI、Alpha、Serenity、OpenAIDatabase。
- 不把私有 runtime SQLite、WAL/SHM、用户本地缓存或 app bundle 提交到 Git。

## Stage 0-8 整体检查矩阵

| Stage | 验收面 | 当前证据 |
| --- | --- | --- |
| Stage 0 | v0.2.1 前端优化范围、CNY 基准、HTML Web Shell 目标、15 个入口任务清单 | `build_v021_stage0_contract()`、`tests/test_v021_stage0_frontend_contract.py` |
| Stage 1 | 15 个一级入口、V0.1 入口保留、数据源与上传、导入中心、策略实验室合并 | `build_v021_stage1_contract()`、`tests/test_v021_stage1_navigation_contract.py` |
| Stage 2 | 中文化、运行边界 UI 清理、真实响应式交付面 | `build_v021_stage2_contract()`、`tests/test_v021_stage2_copy_cleanup_contract.py` |
| Stage 3 | 设置页独立路由、运行反馈归口设置页、全局模糊搜索 | `build_v021_stage3_contract()`、`tests/test_v021_stage3_settings_search_contract.py` |
| Stage 4 | 账户、投资、消费趋势图和 CNY 趋势基准 | `build_v021_stage4_contract()`、`tests/test_v021_stage4_trend_contract.py` |
| Stage 5 | 上传中心、拖拽、失败反馈、导入中心和账本复核入口 | `build_v021_stage5_contract()`、`tests/test_v021_stage5_upload_import_contract.py` |
| Stage 6 | 持仓 SQLite 合同、服务 CRUD、前端保存后刷新恢复 | `build_v021_stage6_contract()`、`tests/test_v021_stage6_holdings_persistence.py` |
| Stage 7 | 全入口按钮可点击、三态反馈、hash 路由状态、移动端入口不竖排 | `build_v021_stage7_contract()`、`tests/test_v021_stage7_clicksafe_feedback.py` |
| Stage 8 | 最终验收合同、浏览器验收、命令验收、GitHub/main、本机 app 和缓存收口 | `build_v021_stage8_contract()`、`tests/test_v021_stage8_final_acceptance.py` |

## 复审退回补充验收

2026-06-28 复审退回后，Stage 8 增加以下硬门槛：

- 正式 UI 不出现运行边界、使用限制、隐私边界、只读、实盘、交易密码、不登录、不下单、不支付等边界/限制类可见文案；这些约束只保留在文档、合同和测试中。
- 持仓编辑生产保存路径必须为 `Web Shell -> /api/holdings -> V021HoldingsPersistenceService -> SQLite operational database`；浏览器缓存只能保存明确标注的未提交草稿。
- 账户与资产、投资管理、消费管理趋势图必须从 SQLite 运行读模型派生；数据不足时显示中文空状态，不使用硬编码 demo 数组。
- 一级入口“策略实验室”和投资管理内“策略实验室”必须统一到 `/investment/strategy-lab`，复用同一功能面板和状态。
- 设置页必须独立，运行反馈控制台、多模态反馈、触感、声音、视觉、通知只在 `/settings` 显示。
- 验收必须包含行为测试、浏览器点击、SQLite 查询、刷新恢复和服务重启后读取，不能只检查 marker 或函数名。

补充合同测试：`tests/test_v021_review_rework_contract.py`。

## 命令验收

本轮最终命令验收必须覆盖：

```bash
node --check PFI/web/app/shell.js
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=PFI/src python3 -B -m unittest PFI.tests.test_v021_stage0_frontend_contract PFI.tests.test_v021_stage1_navigation_contract PFI.tests.test_v021_stage2_copy_cleanup_contract PFI.tests.test_v021_stage3_settings_search_contract PFI.tests.test_v021_stage4_trend_contract PFI.tests.test_v021_stage5_upload_import_contract PFI.tests.test_v021_stage6_holdings_persistence PFI.tests.test_v021_stage7_clicksafe_feedback PFI.tests.test_v021_stage8_final_acceptance -q
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m unittest discover -s tests -q
python3 scripts/validate_project_governance.py --project PFI
git diff --check -- PFI
zsh scripts/macosAppAcceptanceLite.sh --project-root . --summary-json
```

当前命令结果：

- `node --check PFI/web/app/shell.js`：通过。
- v0.2.1 前端合同与复审回归：`58 passed`。
- 完整 PFI pytest：`198 passed, 64 subtests passed`。
- 项目治理：`errors 0 / warnings 0`。
- `git diff --check -- PFI`：通过。
- `macOS app acceptance lite`：`29 pass / 0 fail / 2 info`。
- GitHub main：本轮复审修复提交后同步到 `main`。
- `.app` 入口：`/Applications/PFI.app`、`~/Downloads/PFI.app` 是签名 app bundle；`~/Desktop/PFI.app` 是指向 `/Applications/PFI.app` 的符号链接；三者 `PFI_PROJECT_ROOT` 均指向 canonical PFI，`codesign --verify --deep --strict` 通过。
- 运行健康：`http://127.0.0.1:8501/_stcore/health` 返回 `ok`。

## 浏览器验收

浏览器验收使用 Chrome headless，覆盖：

- Chrome headless desktop `1440x1100`。
- Chrome headless mobile `390x920`。
- 15 个一级入口和 V0.1 兼容入口。
- 顶栏 `AUD/CNY` 汇率徽标。
- 全局模糊搜索。
- `数据源与上传` 上传中心、拖拽上传、失败反馈、导入中心、账本复核入口。
- `投资管理 > 持仓` 持仓编辑、保存、刷新恢复。
- `设置` 运行反馈控制台。
- Stage 7 点击安全清单与 `进行中/成功/失败` 三态反馈。
- console errors 必须为 `0`。

截图证据：

- `/tmp/pfi-v021-stage8-final-desktop-verified.png`
- `/tmp/pfi-v021-stage8-final-mobile-verified.png`

当前浏览器结果：

- desktop：15 个一级入口全部可点击；策略实验室进入 `#/investment/strategy-lab` 且复用投资管理功能面板；首页不显示设置反馈控制台，`/settings` 显示；正式 UI 禁词扫描为空；持仓编辑先显示“未提交草稿”，保存后显示“已写入 SQLite 数据库”；`/api/holdings` 查到 SQLite 行；`/api/trends` 来源为 `SQLite 运行读模型`，投资市值为 `CNY 108.00`；刷新页面后从 SQLite 读取；服务重启后再次打开仍读取同一持仓；console errors `0`。
- mobile：AUD/CNY 徽标、横向入口可读性、上传/导入面板、全局搜索和命令反馈均通过。
- console errors：`0`。

## GitHub 与本机入口验收

Stage 8 通过条件：

- GitHub main 指向包含 Stage 8 commit 的最新 hash。
- canonical PFI 文件和 `origin/main:PFI/...` 关键文件 hash 一致。
- `/Applications/PFI.app`、`~/Downloads/PFI.app`、`~/Desktop/PFI.app` 的 `PFI_PROJECT_ROOT` 都指向 canonical PFI。
- `macOS app acceptance lite` 通过。
- `http://127.0.0.1:8501/_stcore/health` 返回健康。

## 本机非必要缓存清理

仅允许清理：

- `PFI/**/__pycache__`
- `PFI/**/.pytest_cache`
- `PFI/**/*.pyc`
- 本轮 `/private/tmp/codexproject-pfi-v021-stage8-main` 临时 worktree

不得清理：

- `~/.pfi` 私有账本和 runtime 数据。
- `MetaDatabase` 原始数据归档。
- `Serenity-Alipay/data/*.sqlite` 或 WAL/SHM。
- LaunchAgents、PID 文件、app launcher 配置。
- EEI、ADP、Alpha、OpenAIDatabase 等其它项目工作树。

## Stop Condition

只有当 Stage 0-8 前端合同、完整 PFI 单测、JS 检查、项目治理、diff 检查、Chrome 桌面/手机验收、GitHub main 同步、canonical PFI 同步、PFI.app 刷新和缓存清理均完成后，`Stage 8` 才能声明完成。本轮复审修复在上述本地验收项上已通过，最终状态以 GitHub main push 成功为准。
