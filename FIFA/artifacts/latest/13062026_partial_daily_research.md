# 13062026 TAB FIFA盘口研究诊断日报

本报告是每日 automation 的研究诊断产物；不自动下注、不点击赔率、不加入投注单。

## Executive Summary

- status: `ready_research_only`
- partial_daily_report_ready: `True`
- successful boards: `4/5`
- unavailable boards: `1`
- board scope source: `current_discovery+partial_raw_success` / fallback `False` / fresh `True` / current discovery `ready`
- partial freshness: `fresh_research_only` / age `0.61`h
- partial evidence source: `raw_refresh_research_only_latest.json`
- research-only staged raw: `partial_ready_research_only` / success `4`
- raw diagnostics: `failed`
- current_executable_new_stake_aud: `AUD 0`
- 下一步: 每日 automation 可生成 research-only PDF；继续只读发现缺失板块，直到可恢复完整正式日报。

## Board Research Scope

| 板块 | Live nav | 范围 | Fresh raw | 研究动作 | 下注动作 | 金额 | 原因 |
|---|---|---|---:|---|---|---:|---|
| 2026 World Cup Matches | listed | research_diagnostic_allowed | 是 | 纳入当日研究诊断 | No Bet / 不下注 |  | Matches 已在 partial raw 中成功抓取并通过验证；当前只允许 No-execution 研究使用。 |
| 2026 World Cup Futures | listed | research_diagnostic_allowed | 是 | 纳入当日研究诊断 | No Bet / 不下注 |  | Futures 已在 partial raw 中成功抓取并通过验证；当前只允许 No-execution 研究使用。 |
| 2026 World Cup Group Betting | listed | research_diagnostic_allowed | 是 | 纳入当日研究诊断 | No Bet / 不下注 |  | Group Betting 已在 partial raw 中成功抓取并通过验证；当前只允许 No-execution 研究使用。 |
| 2026 World Cup Australia Markets | missing_from_live_nav | unavailable_excluded | 否 | unavailable review，写入缺失说明 | No Bet / 不下注 |  | Australia Markets 在 partial raw 本轮失败；不得使用旧盘口补齐。 |
| 2026 World Cup Team Futures Multi | missing_from_live_nav | research_diagnostic_allowed | 是 | 纳入当日研究诊断 | No Bet / 不下注 |  | Team Futures Multi 已在 partial raw 中成功抓取并通过验证；当前只允许 No-execution 研究使用。 |

## Operation Policy

- **report_publish**: 允许发布 research-only 诊断日报，前提是 partial raw fresh 且缺失板块有 live discovery/unavailable 证据。
- **missing_board_policy**: 缺失板块只能写 No Bet / unavailable review，不使用旧盘口补齐。
- **stake_policy**: 公开 raw、私有持仓、正式 preflight 未全量通过前，新增执行金额固定 AUD 0。
- **automation_policy**: 该产物可由每日 automation 定时生成；但它不能创建投注单，也不能替代人工复核。

## Source Artifacts

- raw_refresh_health: `raw_refresh_health_latest.json`
- raw_refresh_diagnostics: `raw_refresh_diagnostics_latest.json`
- raw_refresh_research_only: `raw_refresh_research_only_latest.json`
- live_board_discovery: `live_board_discovery_latest.json`
- available_board_strategy: `available_board_strategy_latest.json`
- raw_refresh_recovery: `raw_refresh_recovery_latest.json`
- recommendation_operations: `recommendation_operations_latest.json`