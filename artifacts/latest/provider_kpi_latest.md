# Provider KPI

- generated_at: `2026-06-14T05:52:49.769539+10:00`
- status: `in_progress`
- overall_score: `61.50%`
- refresh_id: `20260613T194716Z-provider-2fec0bef`
- provider_analysis_ready: `True`
- formal_publish_allowed: `False`
- current_executable_new_stake_aud: `AUD 0`
- primary_gap: Team Total Score O/U 覆盖: 0/64 (0.00%)
- next_action: The Odds API 当前 TAB sample 未提供 Team Total；继续用小批量 event odds 补非 Team Total 的 alternate/value-support markets，同时把 Team Total 转入 OpticOdds/TAB 人工校验。

## Summary

- required_ready: `5/10`
- event_count: `64`
- covered_market_family_count: `3`

## Market Coverage

| Market | Covered | Coverage |
|---|---:|---:|
| Result | 64/64 | 100.00% |
| Handicap | 46/64 | 71.88% |
| Total Goals Over/Under | 51/64 | 79.69% |
| Team Total Goals Over/Under | 0/64 | 0.00% |

## KPI Rows

| KPI | Status | Score | Evidence | Next Action |
|---|---|---:|---|---|
| 授权 provider raw | `ready` | 100.00% | provider_analysis_ready=True | 先恢复 provider live refresh。 |
| Result 覆盖 | `ready` | 100.00% | 64/64 (100.00%) | Result 覆盖 已达到可用覆盖阈值；后续只做监控或候选场次人工复核。 |
| Handicap 覆盖 | `ready` | 100.00% | 46/64 (71.88%) | Handicap 覆盖 已达到可用覆盖阈值；后续只做监控或候选场次人工复核。 |
| Total Score O/U 覆盖 | `ready` | 100.00% | 51/64 (79.69%) | Total Score O/U 覆盖 已达到可用覆盖阈值；后续只做监控或候选场次人工复核。 |
| Team Total Score O/U 覆盖 | `blocked` | 0.00% | 0/64 (0.00%) | 切换授权 provider 或人工校验补齐 Team Total Score O/U 覆盖。 |
| Alternate markets 探测 | `ready` | 100.00% | event_market_probe_count=1 | 用 --event-market-probe-limit 小样本探测，再按可用 markets 拉 event odds。 |
| Alternate markets 补齐计划 | `partial` | 65.00% | status=in_progress / queue=50 / fallback=64 / batch=1 / credit=4-7 | 按计划小批量 probe，不要全量扫 68 场；Team Total 连续 0 覆盖则切换 provider 或人工校验。 |
| Provider credit 预算 | `partial` | 50.00% | used=299 / remaining=201 / last=7 / inferred_limit=500 | 把 probe limit 控制在小样本，优先推荐候选场次。 |
| 正式 raw 发布门禁 | `blocked` | 0.00% | formal_publish_allowed=False | 对推荐候选做 TAB 人工最终校验 hash。 |
| 完整 automation 门禁 | `blocked` | 0.00% | full_automation_allowed=False | 补齐 raw、持仓、正式日报、CLV 数据闭环。 |

## Last Blocked Provider Attempt (History Only)

- provider: `the_odds_api`
- blocker_code: `provider_refresh_failed`
- is_current_refresh_blocker: `False`
- last_good_coverage_preserved: `True`
- next_safe_action: 保留 last-good provider coverage；检查 provider endpoint/query、账户权限、rate limit 与返回 schema 后再重试。

## Alternate Plan

- status: `in_progress`
- probe_queue_count: `50`
- recommended_batch_size: `1`
- estimated_next_batch_credit: `4-7`

```bash
python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 1 --event-odds-limit 1 --event-odds-markets double_chance,draw_no_bet,btts
```

Truthfulness: Provider KPI 只证明授权数据源覆盖度和平台就绪度；不自动下注，也不把未覆盖盘口伪装为可执行建议。
