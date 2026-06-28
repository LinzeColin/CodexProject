# PFI v0.2.1.1 Stage 1 Product Shell And Routing

更新时间：2026-06-29

## 本轮目标

Stage 1 只完成产品壳和路由：

- 正式一级入口固定为 10 个。
- 旧 v0.1 / v0.2.1 入口只作为路由别名、命令别名和搜索别名。
- 策略实验室只有一个正式运行入口：`市场与研究 > 策略实验室`。
- 浏览器前进、后退、hash route、active 状态使用同一套路由状态。

## 10 个正式一级入口

| 序号 | 一级入口 | workspace | route |
| --- | --- | --- | --- |
| 1 | 首页总览 | `home` | `/home` |
| 2 | 账户与资产 | `accounts` | `/accounts` |
| 3 | 账本流水 | `ledger` | `/ledger` |
| 4 | 投资管理 | `investment` | `/investment` |
| 5 | 消费管理 | `consumption` | `/consumption` |
| 6 | 数据源与上传 | `sync` | `/sources-upload` |
| 7 | 建议与复盘 | `recommendations` | `/review` |
| 8 | 报告与洞察 | `insights` | `/reports` |
| 9 | 市场与研究 | `market_research` | `/market-research` |
| 10 | 设置 | `settings` | `/settings` |

## 兼容别名

这些旧入口不再显示为一级入口，但保留搜索、命令和旧 URL 兼容：

| 旧入口 | 新 route | 新归属 |
| --- | --- | --- |
| 首页 | `/home` | 首页总览 |
| 市场 | `/market-research?tab=market` | 市场与研究 |
| 研究 | `/market-research?tab=research` | 市场与研究 |
| 持仓 | `/investment?tab=holdings` | 投资管理 |
| 策略实验室 | `/market-research/strategy-lab` | 市场与研究 |
| 数据与系统 | `/settings?tab=data-system` | 设置 |

兼容旧 URL：

- `#/strategy-lab` -> `#/market-research/strategy-lab`
- `#/investment/strategy-lab` -> `#/market-research/strategy-lab`
- `#/investment?tab=market` -> `#/market-research?tab=market`
- `#/investment?tab=research` -> `#/market-research?tab=research`

## 非目标

本轮不做：

- 不做图表。
- 不做上传闭环。
- 不做持仓编辑。
- 不做报告。
- 不声明 v0.2.1.1 整体完成。
- 不使用 demo/sample/synthetic/fixture/mock/fake 数据作为产品依据。

## 验收条件

- `PFI/web/index.html` 的 `data-primary-workspaces` 为 `10`。
- 侧边一级导航只有 10 个 `data-primary-entry="true"`。
- 侧边一级导航不包含 `nav-alias` 或 `data-entry-type="v01_alias"`。
- 命令面板和全局搜索仍能打开旧别名。
- 点击路径 `首页总览 -> 投资管理 -> 设置 -> 后退 -> 投资管理` 可用。
- 首页默认不显示设置栏、运行边界、反馈控制台、手机预览或 Task Pack。

## 验证命令

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python3 -B -m pytest tests/test_v0211_stage1_product_shell_contract.py -q -p no:cacheprovider
node --check web/app/shell.js
git diff --check -- PFI
```
