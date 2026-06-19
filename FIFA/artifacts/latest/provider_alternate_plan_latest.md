# Provider Alternate Markets Plan

- generated_at: `2026-06-14T05:52:49.722197+10:00`
- status: `in_progress`
- refresh_id: `20260613T194716Z-provider-2fec0bef`
- event_count: `64`
- probe_queue_count: `50`
- recommended_batch_size: `1`
- current_executable_new_stake_aud: `AUD 0`

## Operational Decision

- status: `alternate_probe_plus_team_total_manual`
- title: 非 Team Total 可小批量补齐，Team Total 转人工
- primary_action: 先按 recommended command 小批量补 50 场非 Team Total alternate/value markets；Team Total 继续 TT-001 人工校验。
- why: The Odds API 已完成 14 个 TAB event-market 样本，Team Total 可用样本 0；但 BTTS/Double Chance/Draw No Bet/alternate spreads/totals 已在样本中可见。
- operator_next_step: 执行推荐命令时保持小批量；完成后重建 KPI。Team Total 不跟随 The Odds API 盲扫，继续 TT-001 人工只读填写。
- credit_guidance: 下一批建议 1 场，预计 4-7 credits。
- stake_policy: provider event odds 只增加研究覆盖；formal publish、TAB 人工最终校验和持仓 gate 未通过前，新增执行金额保持 AUD 0。

## Market Family Gaps

| Market family | Covered | Coverage | Required | Status |
|---|---:|---:|---:|---|
| Handicap | 46/64 | 71.88% | 70.00% | `ready` |
| Total Goals Over/Under | 51/64 | 79.69% | 70.00% | `ready` |
| Both Teams to Score | 14/64 | 21.88% | 35.00% | `gap` |
| Double Chance | 11/64 | 17.19% | 35.00% | `gap` |
| Draw No Bet | 12/64 | 18.75% | 35.00% | `gap` |
| Team Total Goals Over/Under | 0/64 | 0.00% | 50.00% | `fallback_required` |

## Next Probe Queue

| Match | Missing | Markets | Action |
|---|---|---|---|
| Argentina v Algeria | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Austria v Jordan | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Portugal v DR Congo | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| England v Croatia | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Ghana v Panama | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Uzbekistan v Colombia | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Czech Republic v South Africa | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Mexico v South Korea | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| USA v Australia | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Scotland v Morocco | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Brazil v Haiti | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Turkey v Paraguay | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Netherlands v Sweden | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Germany v Ivory Coast | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Ecuador v Curaçao | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Tunisia v Japan | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Spain v Saudi Arabia | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Belgium v Iran | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| Uruguay v Cape Verde | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |
| New Zealand v Egypt | Double Chance, Draw No Bet, Both Teams to Score | double_chance, draw_no_bet, btts | 先 probe /events/{eventId}/markets；只有 TAB 返回目标 markets 时再拉 /events/{eventId}/odds。 |

## Fallback Queue

| Match | Missing | Action |
|---|---|---|
| Qatar v Switzerland | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Brazil v Morocco | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Haiti v Scotland | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Australia v Turkey | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Germany v Curaçao | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Netherlands v Japan | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Ivory Coast v Ecuador | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Sweden v Tunisia | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Spain v Cape Verde | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Belgium v Egypt | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Saudi Arabia v Uruguay | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Iran v New Zealand | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| France v Senegal | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Iraq v Norway | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Argentina v Algeria | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Austria v Jordan | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Portugal v DR Congo | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| England v Croatia | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Ghana v Panama | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |
| Uzbekistan v Colombia | Team Total Goals Over/Under | OpticOdds 授权 raw 或 TAB 人工最终校验候选盘口；不继续用 The Odds API team_totals 盲扫。 |

## Recommended Command

```bash
python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches --event-market-probe-limit 1 --event-odds-limit 1 --event-odds-markets double_chance,draw_no_bet,btts
```

Truthfulness: 本计划只描述授权 provider 覆盖缺口和下一批最小 probe，不代表下注建议，也不会自动下注。
