# 武汉开明智能工业运维助手

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
