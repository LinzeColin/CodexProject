# OpMe_System 中文 Owner 快速入口

<!-- CODEX_CHINESE_READABILITY_START -->

中文优先，默认全局中文。用户可读优先。
最小验证：先确认当前状态、证据、风险、下一步和回滚，再进入路径、命令和历史记录。
本轮 Owner-flow 治理任务：本页只改善 Owner 阅读路径和中文入口。
不改产品 canonical current_task，不改运行代码，不触发外部自动化。

## 一句话结论

运营管理系统项目，当前重点是区分 active source、交付包、示例输入、测试入口和历史归档，防止 Owner 误用旧材料。
本页只提供 Owner 第一屏判断；详细字段、路径和历史放在下方原文与 `docs/governance/`。

## 中文瘦身原则

- 本入口瘦身不是删除事实，而是把反复计算、英文键名解释和历史索引移到下方；第一屏只留下 负责人当下要判断的状态、证据、风险、动作和回滚。
- 后续执行者 继续开发时，不应重新扫描全量治理目录；只取当前任务、下一门禁、必要证据和失败去向，避免上下文被重复材料消耗。
- 需要复盘时再读取机器字段、路线图、事件、登记表和运行清单；这些材料仍是事实源，但不进入每一次小开发动作的默认输入。
- 若为了变短而让 负责人看不懂、让证据来源消失或让 待定 被写成完成，本次瘦身即视为失败，必须回滚入口或补证据。
- 英文项目名、路径和命令只作定位；当英文数量变多时，必须用中文说明其业务含义、验收边界和开发影响。

## 当前状态
本项目已纳入 Lean v2 中文入口；当前事实以仓库文件、治理记录、测试命令和 run manifest 为准，缺证据时保持 待定。

## Owner 操作入口

先读本页，再按需进入 `功能清单`、`开发记录`、`模型参数文件` 和 `docs/governance/`；日常开发只带走当前任务、下一门禁、风险、回滚和必要证据。

## 证据与验证

证据以仓库事实和验证命令为准；中文说明只解释事实，不替代事实。

## 风险与边界

不把旧报告、示例、路径列表或英文键名当作当前完成事实；瘦身只移出重复治理计算，不删除治理真相。

## 下一步

先补缺失证据，再运行 变更范围快速门禁；完整治理计算留给计划任务或手动 all scope。

## 回滚

若入口误导 Owner，回滚本标记区文本；不迁移数据、不改业务代码、不触发外部服务。

## 摘要

- 项目 ID： `OpMe_System`
- 项目路径：`OpMe_System`
- 当前阶段： `S5`
- 当前分段： `S5PA`
- 当前任务： `S5PAT03`
- 下一门禁： `S5PA-GATE-IN-PROGRESS`
- 证据状态： `以仓库内 docs/governance、测试结果、run manifest 和当前文件为准；没有证据的内容只按待确认处理。`
- 中文人类入口：`README.md`、`功能清单`、`开发记录`、`模型参数文件`。
<!-- CODEX_CHINESE_READABILITY_END -->

# OpMe_System 中文 Owner 可读入口

# 武汉开明智能工业运维助手

- S6PAT02 中文 Owner 快速入口：用户可读优先；中文优先，默认全局中文。
- 本轮 Owner-flow 治理任务：`S6PAT02` / `ACC-S6PAT02`，只补 Owner 路径，不改产品 canonical current_task；下一 Gate：`S6PA-GATE` 仍在进行中。
- 本轮边界：只补 Owner 可读路径，不改运行代码，不改 `backend/`、`frontend/`、`app_bundle/`、`samples/`，不移动文件，不触发外部自动化。

| Owner 判断项 | 当前路径 | 状态 |
|---|---|---|
| active source | `backend/`、`frontend/` | 主动运行源码，本轮不改 |
| delivery bundle | `app_bundle/`、`scripts/install_app_entries.sh` | 交付构建输入，本轮不改 |
| demo input | `samples/` | 演示上传样例，本轮不改 |
| historical archive | `governance/archive/other8_wave1_pending/OpMe_System/` | 只读历史资料，不重新进入默认开发循环 |

- 最小验证路径：进入 `OpMe_System/`，运行 `set PYTHONPATH=backend&& .venv\Scripts\python.exe -m pytest backend\tests -q`；本轮实测结果为 `8 passed, 1 warning`。
- 失败去向：若出现 `No module named app`，先确认 `PYTHONPATH=backend`；若 `.venv` 或 `pytest` 缺失，先按 `backend/requirements.txt` 恢复依赖；若 API/PDF 断言失败，再查 `OpMe_System/docs/OpMe_structure_report.md` 和 `backend/tests/`。
- 回滚：revert S6PAT02 OpMe_System README 提交即可；不需要恢复运行数据、报告或 archive。

本项目把原始 `wuhan_kaiming_codex_package.zip` 中的 CLI/规则原型升级为本地 Web + PDF 工业运维控制台，覆盖旋转窑动态调测、回转窑故障诊断、大齿圈修复、机械加工咨询、报告中心和模型配置。

## 已实现能力

- FastAPI 后端：`/api/cases`、`/api/dashboard/summary`、`/api/reports/{case_id}`、`/api/settings/models`。
- SQLite 历史库：案例、报告、模型配置、模型调用日志、审计日志、知识库文档索引。
- React 控制台：总览 dashboard、四模块工作台、ECharts 图表、报告下载、模型设置。
- PDF 报告：每次案例创建自动生成 PDF，也可在报告中心手动重生成。
- 模型路由：DeepSeek、Qwen、豆包默认配置；无密钥或调用失败时自动降级到离线规则。
- 本地 Docker Compose 交付，同时保留本地脚本启动方式。

## 启动

优先使用 Docker：

```bash
./scripts/dev.sh
```

正常启动后访问：

- 前端：http://localhost:5173
- 后端健康检查：http://localhost:8000/api/health

如果 Docker 不可用，`scripts/dev.sh` 会自动降级为本地 Python + npm 启动。

也可以安装 macOS 双击入口：

```bash
./scripts/install_app_entries.sh
```

该脚本会把 `Wuhan Kaiming OpMe.app` 同步到：

- `~/Downloads/Wuhan Kaiming OpMe.app`
- `/Applications/Wuhan Kaiming OpMe.app`

同时会安装当前最稳定的双击入口：

- `~/Downloads/Wuhan Kaiming OpMe.command`
- `/Applications/Wuhan Kaiming OpMe.command`

如果 `.app` 被 macOS Gatekeeper/LaunchServices 拦截，直接双击 `.command`。`.command` 会打开 Terminal 并启动本地服务，使用期间保持该 Terminal 窗口打开；关闭窗口等同于停止本地运行环境。首次打开时会按 `backend/requirements.txt` 和 `frontend/package-lock.json` 恢复依赖，然后启动本地 Web 控制台。

macOS `.app` 图标由 `scripts/generate_app_icon.py` 生成，源文件和正式图标位于 `app_bundle/assets/OpMeIcon.png` 与 `app_bundle/assets/OpMeIcon.icns`。如需重绘图标：

```bash
.venv/bin/python scripts/generate_app_icon.py
./scripts/install_app_entries.sh
```

## 结构入口

| 用途 | 路径 |
|---|---|
| 后端运行源码 | `backend/` |
| 前端运行源码 | `frontend/` |
| macOS 交付构建入口 | `app_bundle/` |
| 启动、安装、验证脚本 | `scripts/` |
| 演示上传样例 | `samples/` |
| S4PCT01 结构迁移报告 | `docs/OpMe_structure_report.md` |
| 历史备份与原始原型 | `governance/archive/other8_wave1_pending/OpMe_System/` |

`backups/generated-artifacts/` 和 `work/original/` 已作为历史材料归档，不再作为
日常开发入口。`app_bundle/` 保留为交付构建输入；生成的 `.app` 和 iconset 仍由
`.gitignore` 管理。

## 验证

```bash
./scripts/smoke_test.sh
```

验证内容包括：

- 后端规则分析和 API 测试。
- 自动 PDF 生成。
- 前端生产构建。

## 使用方式

1. 打开前端总览页。
2. 进入任一模块，使用默认样例或上传 `samples/` 中的 JSON/CSV。
3. 点击“生成分析与PDF”。
4. 在模块结果区查看图表，在报告中心下载 PDF。
5. 在模型设置中填写 OpenAI-compatible `base_url`、模型名和 API key；未填写时系统继续使用离线规则。

## 风险边界

本系统输出为技术建议和报告模板，不替代现场检测、施工方案审批或专业工程师签字确认。涉及停机、焊接、热处理、起吊、设备改造时，必须按企业安全规程执行。

## 回滚建议

- 数据文件位于 `data/wuhan_kaiming.sqlite`。
- PDF 位于 `reports/`。
- 若要回到干净演示状态，可停止服务后移走 `data/` 和 `reports/`，再重新启动。

## Governance

Machine sources of truth live under `docs/governance/`.

中文人类入口：`功能清单`、`开发记录`、`模型参数文件`。这三份文件必须直接保留
owner 可读的功能摘要、Roadmap/任务、模型/参数、证据状态、限制和下一步门禁；
它们不是跳转页，也不是第二套可编辑机器事实源。机器真相仍以
`docs/governance/` 下的 Lean v2 文件为准。
