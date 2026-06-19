# TAB FIFA Live Board Discovery Dashboard

本报告自动发现 TAB Soccer 当前公开导航中实际列出的 FIFA/World Cup 板块；只读，不自动下注。

## Executive Summary

- status: `blocked`
- primary_gap: TAB live 导航缺失 2 个 expected board：Australia Markets、Team Futures Multi
- expected boards: `3/5`
- missing expected boards: `2`
- observed world cup links: `30`
- route_mismatch_active: `True`
- recommended_next_action: 先按 unavailable review queue 复核缺失板块；缺失期间只允许生成研究/诊断视图，不发布当前可执行下注日报。

## Expected Board Status

| 板块 | live nav | matched | automation decision | 下一步 |
|---|---|---:|---|---|
| 2026 World Cup Matches | listed | 20 | refresh_allowed | 允许进入只读 raw refresh。 |
| 2026 World Cup Futures | listed | 1 | refresh_allowed | 允许进入只读 raw refresh。 |
| 2026 World Cup Group Betting | listed | 19 | refresh_allowed | 允许进入只读 raw refresh。 |
| 2026 World Cup Australia Markets | missing_from_live_nav | 0 | temporarily_unavailable_review | 标记 unavailable；重新发现或等待 TAB 重新列出该板块。 |
| 2026 World Cup Team Futures Multi | missing_from_live_nav | 0 | temporarily_unavailable_review | 标记 unavailable；重新发现或等待 TAB 重新列出该板块。 |

## Unavailable Review Queue

| 顺序 | 板块 | 原因 | 操作 | 成功门禁 |
|---:|---|---|---|---|
| 1 | 2026 World Cup Australia Markets | TAB Soccer live nav 未列出该 expected board | 重新发现 TAB Soccer live board list；若仍缺失，保持 unavailable，不用旧盘口生成下注建议。 | live nav 出现该板块，且 deep link resolves to expected board |
| 2 | 2026 World Cup Team Futures Multi | TAB Soccer live nav 未列出该 expected board | 重新发现 TAB Soccer live board list；若仍缺失，保持 unavailable，不用旧盘口生成下注建议。 | live nav 出现该板块，且 deep link resolves to expected board |

## Discovery Retry Queue

| 顺序 | 板块 | 原因 | 操作 | 成功门禁 |
|---:|---|---|---|---|

## Observed World Cup Links

| 顺序 | 链接文本 | mapped expected board |
|---:|---|---|
| 1 | World Cup Group B (SUI/BIH/CAN/QAT) | 2026 World Cup Group Betting |
| 2 | World Cup Group C (BRA/MAR/SCO/HAI) | 2026 World Cup Group Betting |
| 3 | World Cup Group D (USA/TUR/PAR/AUS) | 2026 World Cup Group Betting |
| 4 | World Cup Group E (GER/ECU/CIV/CUW) | 2026 World Cup Group Betting |
| 5 | World Cup Group F (NED/JPN/SWE/TUN) | 2026 World Cup Group Betting |
| 6 | World Cup Group G (BEL/EGY/IRN/NZL) | 2026 World Cup Group Betting |
| 7 | World Cup Group H (ESP/URU/KSA/CPV) | 2026 World Cup Group Betting |
| 8 | World Cup Group I (FRA/NOR/SEN/IRQ) | 2026 World Cup Group Betting |
| 9 | World Cup Group J (ARG/AUT/ALG/JOR) | 2026 World Cup Group Betting |
| 10 | 2026 World Cup Matches | 2026 World Cup Matches |
| 11 | 2026 World Cup Futures | 2026 World Cup Futures |
| 12 | 2026 World Cup Group Betting | 2026 World Cup Group Betting |
| 13 | World Cup Group B (SUI/BIH/CAN/QAT) |  |
| 14 | WC26 Group B WinnerSun 14 Jun 5:00 |  |
| 15 | World Cup Group C (BRA/MAR/SCO/HAI) |  |
| 16 | WC26 Group C WinnerSun 14 Jun 8:00 |  |
| 17 | World Cup Group D (USA/TUR/PAR/AUS) |  |
| 18 | WC26 Group D WinnerSun 14 Jun 14:00 |  |
| 19 | World Cup Group E (GER/ECU/CIV/CUW) |  |
| 20 | WC26 Group E WinnerMon 15 Jun 3:00 |  |

## old_new_compare / 新旧发现变化

- compare_status: `compared_with_previous_artifact`
- previous_generated_at: `2026-06-13T15:02:46.033373+10:00`
- changed_count: `0/9`
- summary: 0/9 个关键指标发生变化。

| 指标 | 当前 | 上一版 | 变化 |
|---|---:|---:|---:|
| status | blocked | blocked | 0 |
| route_mismatch_active | true | true | 0 |
| discovery_ready | true | true | 0 |
| quality_status | ready | ready | 0 |
| access_denied | false | false | 0 |
| listed_expected_count | 3 | 3 | 0 |
| missing_expected_count | 2 | 2 | 0 |
| observed_world_cup_link_count | 30 | 30 | 0 |
| retry_required_count | 0 | 0 | 0 |

> live 导航缺失的板块不得用旧 raw 或旧报告生成当前可执行下注建议；只能进入人工复核/重新发现队列。