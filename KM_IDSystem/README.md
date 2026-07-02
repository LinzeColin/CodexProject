# IDS / Industrial Data System

- STAGE-001 命名合同：新 UI、报告和正式文档统一使用 `IDS / Industrial Data System`。
- Legacy aliases：`Wuhan Kaiming OpMe`、`武汉开明智能工业运维助手`、`OpMe` 只作为迁移说明、历史证据、兼容路径或回滚上下文保留。
- S6PAT02 中文 Owner 快速入口：用户可读优先；中文优先，默认全局中文。
- 本轮 Owner-flow 治理任务：`S6PAT02` / `ACC-S6PAT02`，只补 Owner 路径，不改产品 canonical current_task；下一 Gate：`S6PA-GATE` 仍在进行中。
- 本轮边界：只补 Owner 可读路径，不改运行代码，不改 `backend/`、`frontend/`、`app_bundle/`、`samples/`，不移动文件，不触发外部自动化。

| Owner 判断项 | 当前路径 | 状态 |
|---|---|---|
| active source | `backend/`、`frontend/` | 主动运行源码，本轮不改 |
| delivery bundle | `app_bundle/`、`scripts/install_app_entries.sh` | 交付构建输入，本轮不改 |
| demo input | `samples/` | 演示上传样例，本轮不改 |
| historical archive | `governance/archive/other8_wave1_pending/KM_IDSystem/` | 只读历史资料，不重新进入默认开发循环 |

- 最小验证路径：进入 `KM_IDSystem/`，运行 `set PYTHONPATH=backend&& .venv\Scripts\python.exe -m pytest backend\tests -q`；本轮实测结果为 `8 passed, 1 warning`。
- 失败去向：若出现 `No module named app`，先确认 `PYTHONPATH=backend`；若 `.venv` 或 `pytest` 缺失，先按 `backend/requirements.txt` 恢复依赖；若 API/PDF 断言失败，再查 `KM_IDSystem/docs/OpMe_structure_report.md`（legacy 结构迁移报告）和 `backend/tests/`。
- 回滚：revert S6PAT02 KM_IDSystem README 提交即可；不需要恢复运行数据、报告或 archive。

IDS / Industrial Data System 把原始 CLI/规则原型升级为本地 Web + PDF 工业数据与运维控制台，覆盖旋转窑动态调测、回转窑故障诊断、大齿圈修复、机械加工咨询、报告中心和模型配置。

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

该脚本会把 `IDS Industrial Data System.app` 同步到：

- `~/Downloads/IDS Industrial Data System.app`
- `/Applications/IDS Industrial Data System.app`

同时会安装当前最稳定的双击入口：

- `~/Downloads/IDS Industrial Data System.command`
- `/Applications/IDS Industrial Data System.command`

如果 `.app` 被 macOS Gatekeeper/LaunchServices 拦截，直接双击 `.command`。`.command` 会打开 Terminal 并启动本地服务，使用期间保持该 Terminal 窗口打开；关闭窗口等同于停止本地运行环境。首次打开时会按 `backend/requirements.txt` 和 `frontend/package-lock.json` 恢复依赖，然后启动本地 Web 控制台。

macOS `.app` 图标由 `scripts/generate_app_icon.py` 生成，源文件和正式图标仍位于 `app_bundle/assets/OpMeIcon.png` 与 `app_bundle/assets/OpMeIcon.icns`；该文件名是 legacy asset path，不作为新产品显示名。如需重绘图标：

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
| S4PCT01 legacy 结构迁移报告 | `docs/OpMe_structure_report.md` |
| 历史备份与原始原型 | `governance/archive/other8_wave1_pending/KM_IDSystem/` |

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
