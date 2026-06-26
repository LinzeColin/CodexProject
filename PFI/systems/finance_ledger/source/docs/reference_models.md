# 开源参考模型映射

本项目以本地隐私、可复核分类、生产统计口径和 PDF 正式报告为主线。以下开源项目作为功能和界面参考，但不复制其代码或 UI。来源均按 GitHub README 在 2026-06-05 做过在线核验；自动生成的审计文件为 `audit/reference_models.json`、`audit/reference_source_log.json` 和 `audit/reference_source_log.csv`。

| 参考项目 | 来源证据摘要 | 可借鉴点 | 已吸收实现 | 暂未覆盖 |
|---|---|---|---|---|
| `dtsola/xiaoyaoprivatebill` | README 说明本地隐私、支付宝 CSV、微信 CSV/XLSX、多维分析、响应式设计、Vue/Flask 和 Docker。 | 本地隐私优先；支付宝/微信多格式方向；年度、月度、分类、时间、消费洞察、交易记录；响应式 dashboard。 | 本地处理；支付宝/微信 CSV/XLSX 导入；dashboard；周期 PDF；审计 hash；交易明细查询与导出。 | 银行卡/券商流水导入。 |
| `ryaraghav/personal-finance-agent` | README 说明多银行适配、商户/类别分析、自然语言 NL2SQL、人工覆盖和只读 SQL 校验。 | 多来源统一 schema；商户聚合分类；主类/子类；人工覆盖；只读查询；NL2SQL 必须只读和拦截写操作。 | `ClassifiedTransaction` 统一字段；生产分摊表；复核 CSV 回灌；SQLite 只读分析基础；新增固定问题模板 `ask` 和 `/api/ask`，不开放任意 SQL。 | LLM 驱动的自由文本 NL2SQL 尚未启用；如启用必须先做 schema 白名单、只读校验和人工确认。 |
| `Hessel2333/alipay_record_analysis` | README 列出年度总览、月度分析、分类分析、时间分析、智能洞察、交易记录、ECharts 和响应式布局。 | 年度/月度/分类/时间/洞察/交易记录页面；多维筛选；响应式布局。 | 周/月/季/半年/年/账单周期报告；dashboard；交易明细查询页。 | Flask Web 服务。 |
| `vogo/aliwepaystat` | README 明确支付宝/微信 CSV 导入 SQLite，后续查询统计基于 SQLite，支持 CLI、JSON 和 Web 管理。 | 支付宝和微信导入 SQLite；基于数据库查询统计；CLI query；Web 管理。 | 支付宝/微信 CSV/XLSX 写入 `consumption.sqlite`；CSV/JSON 辅助输出；静态 dashboard 和查询页读取生产口径；`scripts/query_analysis.py` 预设只读查询；`scripts/serve_ledger.py` 提供本机只读 HTTP API。 | 带登录权限的 Web 管理服务和远程部署版。 |
| `Benature/bill` / `MickLife KeepAccounts_v2.0` | README 说明微信支付宝官方账单合并、逐笔标记、月度/类型可视化、Excel 透视图、下拉分类和人工补充。 | 微信支付宝合并；逐笔标记类型；月度/类别可视化；人工补充和校正。 | 支付宝/微信 CSV/XLSX 多文件去重合并；逐笔主类/子类/风险标签；复核工作台分类校正。 | Excel 数据透视表形态。 |
| `actualbudget/actual` | README 说明 Actual 是 local-first、免费开源个人财务应用，支持同步、本地-only/自托管部署、信封预算、账户管理文档和多包架构。 | local-first；预算信封法；账户管理；本地-only/自托管；长期维护文档。 | 本地 SQLite/报告文件；预算压力雷达；消费控制行动计划；只读 API 和周更维护流程。 | 完整账户余额同步、信封预算编辑器、多端同步服务。 |
| `firefly-iii/firefly-iii` | README 说明 Firefly III 是 self-hosted 个人财务管理器，支持预算、分类、标签、导入、财务报表、REST API、规则交易、复式记账、目标和 Docker。 | self-hosted；预算/分类/标签；REST API；规则化交易；复式记账；目标储蓄；安全控制。 | SQLite 表/视图；本地只读 API；标签库；风险标签；分类规则；复核候选；周期 PDF 和 Dashboard。 | 完整复式记账、用户认证、2FA、远程 Web 管理、周期交易编辑。 |
| `maybe-finance/maybe` | README 说明 Maybe 是可 Docker self-hosted 的完整个人财务应用，但仓库已归档且不再主动维护。 | 完整个人财务 app 产品形态；Docker self-hosted；现代 Web app 结构；维护风险提示。 | 运行控制台；交付包；源码/报告/SQLite/审计/测试一体化；不把归档项目作为依赖。 | 完整账户聚合、登录、多用户和在线托管。 |

当前优先级：先把本地分析链路做稳；支付宝/微信 CSV/XLSX、SQLite、静态交互页、本机只读 API、预算压力视图和复核闭环已接入。后续再决定是否扩展银行卡/券商流水、完整账户余额、信封预算编辑器、复式记账、自然语言查询、认证或远程 Web 管理服务。

## UI/布局模式吸收矩阵

| UI/布局模式 | 参考项目 | 本系统落地 | 复用边界 |
|---|---|---|---|
| 本地隐私优先入口 | `dtsola/xiaoyaoprivatebill`、`actualbudget/actual`、`maybe-finance/maybe` | `index.html`、`operations_center.html`、`user_manual_report.pdf` 集中呈现本地静态入口、SQLite 文件和本机只读 API 命令。 | 只吸收本地优先的信息架构，不复制视觉风格。 |
| KPI + 现金流 + 类别 + 风险 dashboard | `Hessel2333/alipay_record_analysis`、`dtsola/xiaoyaoprivatebill`、`firefly-iii/firefly-iii` | `dashboard.html` 和周期 PDF 提供现金流折线、主类环形、预算压力雷达、风险矩阵、时间热力和对手方集中度。 | 图表编码按经济放血机制重构，不照搬外部图表实现。 |
| 交易明细筛选、搜索反馈和导出 | `Hessel2333/alipay_record_analysis`、`vogo/aliwepaystat`、`Benature/bill` | `transaction_explorer.html` 支持模糊搜索、搜索反馈、标签组合、明细折叠、分页、小图和 CSV 导出。 | 保持静态本地页面，不引入远程管理服务。 |
| 下拉式人工复核与批量校正 | `Benature/bill`、`ryaraghav/personal-finance-agent`、`firefly-iii/firefly-iii` | `review_workbench.html` 提供复核决定、主类/子类、风险标签、候选动作、分组矩阵和确认 CSV 回灌。 | 候选建议不自动写入生产统计，未确认大额继续隔离。 |
| 标签库 + 标签组合行为分析 | `firefly-iii/firefly-iii`、`actualbudget/actual`、`dtsola/xiaoyaoprivatebill` | `tag_library.html`、`behavior_analysis.html` 和消费控制行动报告支持标签编辑、组合筛选和多图形态。 | 标签用于本地消费控制，不扩展为多用户权限后台。 |
| SQLite/只读 API 数据契约 | `vogo/aliwepaystat`、`firefly-iii/firefly-iii`、`ryaraghav/personal-finance-agent` | `finance_ledger_data_contract.md`、`serve_ledger.py`、`query_analysis.py` 提供事实表、汇总表、mart 视图、本机只读 API 和固定问题模板。 | 默认绑定 127.0.0.1；远程部署需另做认证、脱敏、备份和访问日志。 |
| 验收工作台 + 开源参考工作台 | `maybe-finance/maybe`、`actualbudget/actual`、`firefly-iii/firefly-iii` | `acceptance_workbench.html`、`reference_model_lab.html` 和开源对标 PDF 提供 A/B/C 验收、ChatGPT 对照接入、吸收度图表和 UI 模式矩阵。 | 只做验收和对标辅助，不把外部项目作为运行依赖。 |
