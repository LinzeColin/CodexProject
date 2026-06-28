# PFI v0.2.1.1 Stage 4 持久化与同步

更新时间：2026-06-29

## 目标

本轮只完成 `S4 持久化与同步`。目标是把 Stage 3 的持仓编辑入口接到真实本机 SQLite 链路，并证明同一份持仓读模型会同步到首页、投资管理和报告与洞察。

本轮不做 Stage 5 图表最终验收，不伪造账户、收益、消费或持仓趋势，不声明真实账户生产联通。

## 最小范围

- `src/pfi_v02/stage_v0211_ui_recovery.py`：新增 Stage 4 合同。
- `src/pfi_v02/stage_v021_runtime_api.py`：新增持仓同步读模型和持仓报告 API。
- `web/index.html`：补齐持仓编辑字段。
- `web/app/shell.js`：保存后刷新后端读模型，并把读模型应用到首页、投资和报告卡片。
- `tests/test_v0211_stage4_persistence_sync_contract.py`：Stage 4 合同、SQLite 查询、重开读回和同步读模型测试。
- 三基文件、README、CHANGELOG、HANDOFF 同步记录本轮边界。

## 本轮完成

| 验收点 | 实现 | 说明 |
| --- | --- | --- |
| 持仓写入 SQLite | `POST /api/holdings` -> `V021HoldingsPersistenceService` | 写入 `v021_holding_snapshots` 和 `v021_position_adjustments`。 |
| 刷新后读回 | `GET /api/holdings` | 页面再次打开持仓时从后端读取，不使用浏览器缓存作为生产来源。 |
| 重启后读回 | SQLite operational DB | 服务重启后仍读取同一 DB 文件。 |
| 首页同步 | `/api/read-model` 的 `home` 区块 | 首页净资产、现金、投资市值读取运行读模型。 |
| 投资同步 | `/api/trends` 和 `/api/read-model` 的 `investment` 区块 | 投资市值、成本、未实现盈亏来自持仓快照。 |
| 报告同步 | `/api/reports/holdings` | 报告与洞察读取同一持仓报告模型。 |
| 字段完整 | 标的、名称、数量、成本、价格、币种、账户、更新时间、备注 | 备注写入 `metadata.note`。 |

## 真实数据边界

- 当前正式 operational DB 可为空；为空时正式页面必须显示中文空状态，不显示模拟收益或模拟持仓。
- 本轮测试中的写入验证使用隔离临时 SQLite，只验证“用户手工输入 -> 保存 -> SQLite -> 重开读取 -> 同步读模型”的行为，不写入正式库、不写入 MetaDatabase、不提交任何样例数据文件。
- 浏览器 `localStorage` 只允许保存明确标注的“未提交草稿”；点击保存后生产路径必须调用本机 API。

## 非目标

- 不做 Stage 5 账户、投资、消费图表最终验收。
- 不新增 demo/sample/synthetic/fixture/mock/fake 文件作为正式产品数据源。
- 不声明券商、支付、交易账户或真实账户生产联通。
- 不迁移或清空用户正式 SQLite 数据。

## 验收

- `build_v0211_stage4_contract()` 存在并锁定 `V0211-S4-T01`。
- `tests/test_v0211_stage4_persistence_sync_contract.py` 通过。
- `保存持仓修改` 函数不调用 `localStorage.setItem`、`sessionStorage` 或 `indexedDB` 作为生产保存。
- SQLite 查询能看到保存后的 snapshot 和 adjustment。
- 重开 `V021HoldingsPersistenceService` 后仍能读回相同持仓。
- `/api/read-model` 和 `/api/reports/holdings` 读取同一 SQLite 数据。
- 真实 8501 入口能打开投资持仓页、保存按钮、首页、投资页、报告页，并保持中文状态反馈。

## 后续

下一轮只能进入 `S5 真实图表与最终验收`，重点是账户、投资、消费趋势图、全入口点击、数据验收、桌面/移动截图和最终禁词扫描。
