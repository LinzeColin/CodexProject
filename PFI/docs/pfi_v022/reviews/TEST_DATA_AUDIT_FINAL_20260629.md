# PFI v0.2.2 最终测试/样例/模拟数据审计

日期：2026-06-29 Australia/Sydney
范围：`PFI/` 正式运行路径、v0.2.2 Stage 0-13 验收路径、真实 `8501` 页面、legacy 命中清单。
结论：整体项目复审解决已关闭正式运行路径的数据污染风险。正式页面、报告、图表、首页摘要和建议只允许读取真实 MetaDatabase 派生数据或中文真实空态；不得使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据作为验收依据。阻塞项数量：`0`。

## 真实数据边界

- 真实原始数据根：`MetaDatabase/PFI/alipay_daily/raw`。
- 真实原始文件数：`4` 个支付宝 CSV。
- 真实标准化流水：`MetaDatabase/PFI/alipay_daily/processed/alipay_transactions.csv`，`8815` 条数据记录。
- 无真实持仓、无真实 Interconnection 分组、无真实浏览器性能测量时，只显示中文真实空态，不生成模拟数值。

## 审计结论

| 项目 | 结果 |
| --- | --- |
| 正式运行路径影响：`0` | 未发现正式 8501 页面、报告、图表、首页摘要或建议使用 demo/sample/synthetic/fixture/mock/fake/测试样例数据作为产品数据源。 |
| 正式可见页面污染：`0` | 真实浏览器矩阵禁词扫描未命中 `demo`、`sample`、`synthetic`、`fixture`、`mock`、`fake`、`测试样例`、`大量模拟记录`。 |
| v0.2.2 Stage 0-13 验收数据 | 使用真实 MetaDatabase、本地参数/分类/标签/hash/汇率快照，或中文真实空态。 |
| legacy 命中仍存在 | 旧 v0.2、研究系统、策略回测/Bootstrap、独立验证容量测试、历史文档仍有 demo/sample/synthetic/fixture/mock/fake/模拟 等词。 |
| 产品数据源影响 | `0`，legacy 命中不作为产品数据源。 |
| Stage 0-13 验收影响 | `0`，legacy 命中不作为 Stage 0-13 验收证据。 |

## legacy 命中分类

| 类别 | 示例路径 | 处理 |
| --- | --- | --- |
| 旧 v0.2 历史验收 | `PFI/src/pfi_v02/stage3_read_mvp.py`、`PFI/src/pfi_v02/stage4_analysis_mvp.py`、`PFI/src/pfi_v02/stage6_e2e_stabilization.py` | 标记为 legacy regression 背景，不作为 v0.2.2 产品验收。 |
| 策略回测/Bootstrap 模拟 | `PFI/src/pfi_os/reports/export.py`、`PFI/src/pfi_os/app/streamlit_app.py` | 属于研究模拟/策略稳健性术语，不得混入个人账本事实。 |
| 独立验证容量测试 | `PFI/src/pfi_os/integrations/independent_validation.py` | 只用于容量/分片 dry-run，不作为用户财务数据。 |
| 旧系统样例目录 | `PFI/systems/industry_research/source/data/sample` | 独立系统迁移资料，不进入 PFI 正式页面、报告、图表、首页摘要和建议。 |
| 旧文档记录 | `PFI/docs/governance/*`、`PFI/docs/pfi_v02/*` | 历史记录，不作为当前验收依据。 |

## 后续拆除队列

1. 旧 `stage3_read_mvp.py`、`stage4_analysis_mvp.py`、`stage6_e2e_stabilization.py` 的 fixture/demo 命名应在独立 legacy cleanup goal 中重命名或归档。
2. `PFI/systems/industry_research` 的 sample 目录应在系统拆分/归档任务中从 PFI 正式交付范围移出。
3. 策略回测、Bootstrap 和大数据模拟保留为研究工具，但 UI 与报告必须明确它们不是用户真实财务事实。

## 当前验收口径

整体复审不新增任何 demo records、sample bills、synthetic records、fixture CSV/JSON、mock/fake 财务事实或测试样例数据。现有 legacy 命中仍存在，但正式运行路径影响：`0`，正式可见页面污染：`0`，不作为产品数据源，不作为 Stage 0-13 验收证据。

## 收口关系

- GitHub main 同步：纳入本轮 closeout，只能同步 `PFI/` 与 `MetaDatabase/PFI/` 相关路径。
- app 入口重装：已刷新本机 app 入口并通过 macOS app acceptance lite `29 pass / 0 fail / 2 info`，本机 app 入口仍指向 canonical `CodexProject/PFI`。
