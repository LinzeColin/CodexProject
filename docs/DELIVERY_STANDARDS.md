# 交付标准

## 目标

系统目标是每日自动生成专业中文 TAB FIFA 盘口下注研究报告，不自动下注。任何推荐必须可解释、可追踪、可回测，并且在数据门禁不完整时 fail-closed。

## 合并前必须满足

| Gate | 标准 |
| --- | --- |
| 安全 | 本地 POST action token 和本地 Origin/Host 校验通过；无 public 私有持仓泄露 |
| 合规 | public raw access denied / AI controlled access rejected 时不得尝试规避 |
| Provider raw | The Odds API / OpticOdds 等第三方 TAB-labeled 数据必须先进入 staging；未通过 coverage 和人工 TAB final verification 不得发布正式 raw |
| 下注边界 | raw/private/preflight 任一未通过时，新增执行金额固定 AUD 0 |
| 测试 | Python full suite、Node security tests、shell syntax checks 通过 |
| 运行 | `http://127.0.0.1:8767/` 可加载；Downloads app 可打开本地入口 |
| 文档 | `docs/HANDOFF.md`、`docs/DEVELOPMENT_STATUS.md`、功能清单和交付包 manifest 更新 |

## 报告输出标准

- 中文专业商务风格。
- 以板块和盘口为主题，不以技术实现为主题。
- 推荐下注表必须包含：时间、板块、盘口、下注、赔率、金额、概率、EV、Edge、套利率、Risk of ruin、置信度、市场资金倾向分、原因。
- 当前数据门禁不完整时，买入/下注 cell 可以存在于历史或候选研究中，但当前新增执行金额必须为 AUD 0。
- 报告不得把 planned/proxy 模型写成已完成生产级 MCMC/xG/完整 Monte Carlo。

## 运行方式

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/github_sync/FIFA/tab-research-pipeline
python3 scripts/tab_fifa_app_server.py --port 8767
```

重建 Downloads 入口：

```bash
TAB_FIFA_FAST_ENTRY_REBUILD=1 python3 scripts/build_downloads_app_entry.py
```

完整验证：

```bash
PYTHONPYCACHEPREFIX=/private/tmp/tab-fifa-pycache-review python3 -m unittest tests.test_pipeline
node scripts/refresh_tab_readonly_security.test.mjs
node scripts/capture_tab_my_bets_readonly_security.test.mjs
bash -n scripts/run_tab_fifa_daily_automation.sh scripts/tab_real_refresh_smoke.sh scripts/verify_fifa_automation_readiness.sh
```

## 当前停止条件

进入完整正式 automation 前必须同时满足：

- 5/5 raw board ready。
- Provider raw 如被使用，必须有匹配 `refresh_id + board_id + sha256` 的 TAB 人工最终校验。
- Australia Markets ready。
- My Bets private position snapshot ready。
- automation preflight ready。
- public artifact safety ready。
- report publish ready。
