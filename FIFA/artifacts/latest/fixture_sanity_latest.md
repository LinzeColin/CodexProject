# TAB FIFA 公开赛程校验 Dashboard

本报告使用 openfootball/worldcup.json 公开赛程对 TAB World Cup Matches raw 做 sanity-check。它不读取账户、不替代 TAB 赔率，也不是下注执行指令。

## Executive Summary

- status: `ready_with_delayed_public_source`
- fixture_sanity_ready: `True`
- openfootball_match_count: `104`
- tab_match_count: `26`
- matched_count: `23`
- mismatch_review_count: `84`
- source_freshness: `delayed_public_source_not_live`
- recommended_next_action: 优先人工复核 tab_only/openfootball_only 队名和日期差异；不要用公开源替代 TAB 赔率。

## 公开源说明

- source: `openfootball/worldcup.json`
- url: `https://raw.githubusercontent.com/openfootball/worldcup.json/master/2026/worldcup.json`
- license: `public domain / CC0`
- limitation: openfootball 不是 TAB 官方盘口源，也不是 live odds feed；只能校验赛程、队名、分组、场地和公开赛果，不能用于替代赔率抓取。

## 新旧变化

- compare_status: `compared`
- previous_generated_at: `2026-06-13T14:36:31.813793+10:00`
- matched_count_delta: `0`
- mismatch_review_delta: `0`

## 赛程校验明细

| 状态 | TAB比赛 | 公开赛程 | 日期 | 分组/轮次 | 场地 | 赛果 | 原因 |
|---|---|---|---|---|---|---|---|
| matched | Mexico v South Africa | Mexico v South Africa | 2026-06-11 13:00 UTC-6 | Group A Matchday 1 | Mexico City | 2-0 | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | South Korea v Czechia | South Korea v Czech Republic | 2026-06-11 20:00 UTC-6 | Group A Matchday 1 | Guadalajara (Zapopan) | 2-1 | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Canada v Bosn-Herzegovina | Canada v Bosnia & Herzegovina | 2026-06-12 15:00 UTC-4 | Group B Matchday 2 | Toronto | 1-1 | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | USA v Paraguay | USA v Paraguay | 2026-06-12 18:00 UTC-7 | Group D Matchday 2 | Los Angeles (Inglewood) | 4-1 | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Qatar v Switzerland | Qatar v Switzerland | 2026-06-13 12:00 UTC-7 | Group B Matchday 3 | San Francisco Bay Area (Santa Clara) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Brazil v Morocco | Brazil v Morocco | 2026-06-13 18:00 UTC-4 | Group C Matchday 3 | New York/New Jersey (East Rutherford) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Haiti v Scotland | Haiti v Scotland | 2026-06-13 21:00 UTC-4 | Group C Matchday 3 | Boston (Foxborough) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| tab_only_missing_openfootball | Australia v Turkiye |  |   |   |  |  | TAB raw 中出现，但 openfootball 当前公开源未匹配；需人工确认是否队名 alias、赛程源滞后或 TAB 板块扩展。 |
| tab_only_missing_openfootball | Germany v Curacao |  |   |   |  |  | TAB raw 中出现，但 openfootball 当前公开源未匹配；需人工确认是否队名 alias、赛程源滞后或 TAB 板块扩展。 |
| matched | Netherlands v Japan | Netherlands v Japan | 2026-06-14 15:00 UTC-5 | Group F Matchday 4 | Dallas (Arlington) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Cote d Ivoire v Ecuador | Ivory Coast v Ecuador | 2026-06-14 19:00 UTC-4 | Group E Matchday 4 | Philadelphia |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Sweden v Tunisia | Sweden v Tunisia | 2026-06-14 20:00 UTC-6 | Group F Matchday 4 | Monterrey (Guadalupe) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| tab_only_missing_openfootball | Spain v Cabo Verde |  |   |   |  |  | TAB raw 中出现，但 openfootball 当前公开源未匹配；需人工确认是否队名 alias、赛程源滞后或 TAB 板块扩展。 |
| matched | Belgium v Egypt | Belgium v Egypt | 2026-06-15 12:00 UTC-7 | Group G Matchday 5 | Seattle |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Saudi Arabia v Uruguay | Saudi Arabia v Uruguay | 2026-06-15 18:00 UTC-4 | Group H Matchday 5 | Miami (Miami Gardens) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Iran v New Zealand | Iran v New Zealand | 2026-06-15 18:00 UTC-7 | Group G Matchday 5 | Los Angeles (Inglewood) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | France v Senegal | France v Senegal | 2026-06-16 15:00 UTC-4 | Group I Matchday 6 | New York/New Jersey (East Rutherford) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Iraq v Norway | Iraq v Norway | 2026-06-16 18:00 UTC-4 | Group I Matchday 6 | Boston (Foxborough) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Argentina v Algeria | Argentina v Algeria | 2026-06-16 20:00 UTC-5 | Group J Matchday 6 | Kansas City |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Austria v Jordan | Austria v Jordan | 2026-06-16 21:00 UTC-7 | Group J Matchday 6 | San Francisco Bay Area (Santa Clara) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Portugal v DR Congo | Portugal v DR Congo | 2026-06-17 12:00 UTC-5 | Group K Matchday 7 | Houston |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | England v Croatia | England v Croatia | 2026-06-17 15:00 UTC-5 | Group L Matchday 7 | Dallas (Arlington) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Ghana v Panama | Ghana v Panama | 2026-06-17 19:00 UTC-4 | Group L Matchday 7 | Toronto |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Uzbekistan v Colombia | Uzbekistan v Colombia | 2026-06-17 20:00 UTC-6 | Group K Matchday 7 | Mexico City |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | USA v Australia | USA v Australia | 2026-06-19 12:00 UTC-7 | Group D Matchday 9 | Seattle |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| matched | Paraguay v Australia | Paraguay v Australia | 2026-06-25 19:00 UTC-7 | Group D Matchday 15 | San Francisco Bay Area (Santa Clara) |  | TAB match 与 openfootball 公开赛程队名匹配；可用于赛程/日期/分组 sanity-check。 |
| openfootball_only_not_in_tab_raw |  | Czech Republic v South Africa | 2026-06-18 12:00 UTC-4 | Group A Matchday 8 | Atlanta |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Mexico v South Korea | 2026-06-18 19:00 UTC-6 | Group A Matchday 8 | Guadalajara (Zapopan) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Czech Republic v Mexico | 2026-06-24 19:00 UTC-6 | Group A Matchday 14 | Mexico City |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | South Africa v South Korea | 2026-06-24 19:00 UTC-6 | Group A Matchday 14 | Monterrey (Guadalupe) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Switzerland v Bosnia & Herzegovina | 2026-06-18 12:00 UTC-7 | Group B Matchday 8 | Los Angeles (Inglewood) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Canada v Qatar | 2026-06-18 15:00 UTC-7 | Group B Matchday 8 | Vancouver |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Switzerland v Canada | 2026-06-24 12:00 UTC-7 | Group B Matchday 14 | Vancouver |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Bosnia & Herzegovina v Qatar | 2026-06-24 12:00 UTC-7 | Group B Matchday 14 | Seattle |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Scotland v Morocco | 2026-06-19 18:00 UTC-4 | Group C Matchday 9 | Boston (Foxborough) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Brazil v Haiti | 2026-06-19 20:30 UTC-4 | Group C Matchday 9 | Philadelphia |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Scotland v Brazil | 2026-06-24 18:00 UTC-4 | Group C Matchday 14 | Miami (Miami Gardens) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Morocco v Haiti | 2026-06-24 18:00 UTC-4 | Group C Matchday 14 | Atlanta |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Australia v Turkey | 2026-06-13 21:00 UTC-7 | Group D Matchday 3 | Vancouver |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Turkey v Paraguay | 2026-06-19 20:00 UTC-7 | Group D Matchday 9 | San Francisco Bay Area (Santa Clara) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Turkey v USA | 2026-06-25 19:00 UTC-7 | Group D Matchday 15 | Los Angeles (Inglewood) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Germany v Curaçao | 2026-06-14 12:00 UTC-5 | Group E Matchday 4 | Houston |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Germany v Ivory Coast | 2026-06-20 16:00 UTC-4 | Group E Matchday 10 | Toronto |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Ecuador v Curaçao | 2026-06-20 19:00 UTC-5 | Group E Matchday 10 | Kansas City |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Curaçao v Ivory Coast | 2026-06-25 16:00 UTC-4 | Group E Matchday 15 | Philadelphia |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Ecuador v Germany | 2026-06-25 16:00 UTC-4 | Group E Matchday 15 | New York/New Jersey (East Rutherford) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Netherlands v Sweden | 2026-06-20 12:00 UTC-5 | Group F Matchday 10 | Houston |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Tunisia v Japan | 2026-06-20 22:00 UTC-6 | Group F Matchday 10 | Monterrey (Guadalupe) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Japan v Sweden | 2026-06-25 18:00 UTC-5 | Group F Matchday 15 | Dallas (Arlington) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Tunisia v Netherlands | 2026-06-25 18:00 UTC-5 | Group F Matchday 15 | Kansas City |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Belgium v Iran | 2026-06-21 12:00 UTC-7 | Group G Matchday 11 | Los Angeles (Inglewood) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | New Zealand v Egypt | 2026-06-21 18:00 UTC-7 | Group G Matchday 11 | Vancouver |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Egypt v Iran | 2026-06-26 20:00 UTC-7 | Group G Matchday 16 | Seattle |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | New Zealand v Belgium | 2026-06-26 20:00 UTC-7 | Group G Matchday 16 | Vancouver |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Spain v Cape Verde | 2026-06-15 12:00 UTC-4 | Group H Matchday 5 | Atlanta |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Spain v Saudi Arabia | 2026-06-21 12:00 UTC-4 | Group H Matchday 11 | Atlanta |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Uruguay v Cape Verde | 2026-06-21 18:00 UTC-4 | Group H Matchday 11 | Miami (Miami Gardens) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Cape Verde v Saudi Arabia | 2026-06-26 19:00 UTC-5 | Group H Matchday 16 | Houston |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Uruguay v Spain | 2026-06-26 18:00 UTC-6 | Group H Matchday 16 | Guadalajara (Zapopan) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | France v Iraq | 2026-06-22 17:00 UTC-4 | Group I Matchday 12 | Philadelphia |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Norway v Senegal | 2026-06-22 20:00 UTC-4 | Group I Matchday 12 | New York/New Jersey (East Rutherford) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Norway v France | 2026-06-26 15:00 UTC-4 | Group I Matchday 16 | Boston (Foxborough) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Senegal v Iraq | 2026-06-26 15:00 UTC-4 | Group I Matchday 16 | Toronto |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Argentina v Austria | 2026-06-22 12:00 UTC-5 | Group J Matchday 12 | Dallas (Arlington) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Jordan v Algeria | 2026-06-22 20:00 UTC-7 | Group J Matchday 12 | San Francisco Bay Area (Santa Clara) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Algeria v Austria | 2026-06-27 21:00 UTC-5 | Group J Matchday 17 | Kansas City |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Jordan v Argentina | 2026-06-27 21:00 UTC-5 | Group J Matchday 17 | Dallas (Arlington) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Portugal v Uzbekistan | 2026-06-23 12:00 UTC-5 | Group K Matchday 13 | Houston |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Colombia v DR Congo | 2026-06-23 20:00 UTC-6 | Group K Matchday 13 | Guadalajara (Zapopan) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Colombia v Portugal | 2026-06-27 19:30 UTC-4 | Group K Matchday 17 | Miami (Miami Gardens) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | DR Congo v Uzbekistan | 2026-06-27 19:30 UTC-4 | Group K Matchday 17 | Atlanta |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | England v Ghana | 2026-06-23 16:00 UTC-4 | Group L Matchday 13 | Boston (Foxborough) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Panama v Croatia | 2026-06-23 19:00 UTC-4 | Group L Matchday 13 | Toronto |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Panama v England | 2026-06-27 17:00 UTC-4 | Group L Matchday 17 | New York/New Jersey (East Rutherford) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | Croatia v Ghana | 2026-06-27 17:00 UTC-4 | Group L Matchday 17 | Philadelphia |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 2A v 2B | 2026-06-28 12:00 UTC-7 |  Round of 32 | Los Angeles (Inglewood) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1E v 3A/B/C/D/F | 2026-06-29 16:30 UTC-4 |  Round of 32 | Boston (Foxborough) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1F v 2C | 2026-06-29 19:00 UTC-6 |  Round of 32 | Monterrey (Guadalupe) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1C v 2F | 2026-06-29 12:00 UTC-5 |  Round of 32 | Houston |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1I v 3C/D/F/G/H | 2026-06-30 17:00 UTC-4 |  Round of 32 | New York/New Jersey (East Rutherford) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 2E v 2I | 2026-06-30 12:00 UTC-5 |  Round of 32 | Dallas (Arlington) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1A v 3C/E/F/H/I | 2026-06-30 19:00 UTC-6 |  Round of 32 | Mexico City |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1L v 3E/H/I/J/K | 2026-07-01 12:00 UTC-4 |  Round of 32 | Atlanta |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1D v 3B/E/F/I/J | 2026-07-01 17:00 UTC-7 |  Round of 32 | San Francisco Bay Area (Santa Clara) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1G v 3A/E/H/I/J | 2026-07-01 13:00 UTC-7 |  Round of 32 | Seattle |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 2K v 2L | 2026-07-02 19:00 UTC-4 |  Round of 32 | Toronto |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1H v 2J | 2026-07-02 12:00 UTC-7 |  Round of 32 | Los Angeles (Inglewood) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1B v 3E/F/G/I/J | 2026-07-02 20:00 UTC-7 |  Round of 32 | Vancouver |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1J v 2H | 2026-07-03 18:00 UTC-4 |  Round of 32 | Miami (Miami Gardens) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 1K v 3D/E/I/J/L | 2026-07-03 20:30 UTC-5 |  Round of 32 | Kansas City |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | 2D v 2G | 2026-07-03 13:00 UTC-5 |  Round of 32 | Dallas (Arlington) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W74 v W77 | 2026-07-04 17:00 UTC-4 |  Round of 16 | Philadelphia |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W73 v W75 | 2026-07-04 12:00 UTC-5 |  Round of 16 | Houston |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W76 v W78 | 2026-07-05 16:00 UTC-4 |  Round of 16 | New York/New Jersey (East Rutherford) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W79 v W80 | 2026-07-05 18:00 UTC-6 |  Round of 16 | Mexico City |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W83 v W84 | 2026-07-06 14:00 UTC-5 |  Round of 16 | Dallas (Arlington) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W81 v W82 | 2026-07-06 17:00 UTC-7 |  Round of 16 | Seattle |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W86 v W88 | 2026-07-07 12:00 UTC-4 |  Round of 16 | Atlanta |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W85 v W87 | 2026-07-07 13:00 UTC-7 |  Round of 16 | Vancouver |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W89 v W90 | 2026-07-09 16:00 UTC-4 |  Quarter-final | Boston (Foxborough) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W93 v W94 | 2026-07-10 12:00 UTC-7 |  Quarter-final | Los Angeles (Inglewood) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W91 v W92 | 2026-07-11 17:00 UTC-4 |  Quarter-final | Miami (Miami Gardens) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W95 v W96 | 2026-07-11 20:00 UTC-5 |  Quarter-final | Kansas City |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W97 v W98 | 2026-07-14 14:00 UTC-5 |  Semi-final | Dallas (Arlington) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W99 v W100 | 2026-07-15 15:00 UTC-4 |  Semi-final | Atlanta |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | L101 v L102 | 2026-07-18 17:00 UTC-4 |  Match for third place | Miami (Miami Gardens) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |
| openfootball_only_not_in_tab_raw |  | W101 v W102 | 2026-07-19 15:00 UTC-4 |  Final | New York/New Jersey (East Rutherford) |  | openfootball 公开赛程存在，但当前 TAB raw 未出现；可能不是当前 TAB 列表窗口、TAB 未开盘、或 raw refresh 缺失。 |

> 该报告是公开赛程校验，不是赔率源、不是 live 数据源、不是下注执行指令；openfootball 源可能滞后。

> 不读取账户、不点击赔率、不添加 下注单、不自动下注；即使校验 ready，也不会解除 raw/private/preflight 门禁。