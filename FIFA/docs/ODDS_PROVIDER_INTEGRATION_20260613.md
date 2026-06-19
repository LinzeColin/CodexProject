# Odds Provider Integration - 2026-06-13

## Purpose

Replace TAB AI-controlled public-page scraping with authorized TAB-labeled odds feeds.

This path is research/report only. It does not log into TAB, click odds, add selections to Bet Slip, or submit bets.

## Providers

| Provider | Why used | Current implementation |
|---|---|---|
| The Odds API | Lists Australian bookmaker key `tab`; supports AU region, bookmaker filter, decimal odds, h2h/spreads/totals/outrights | Matches-first request builder, live fetch, TAB bookmaker filter, Result/Total O/U/Handicap mapping, optional Team Total payload mapping, futures outright adapter, coverage manifest |
| OpticOdds | Markets TAB real-time sportsbook API, structured JSON/XML, futures/alternate/player props, some limits/liquidity availability | Request builder, live fetch, TAB bookmaker filter for nested/flat odds payloads, coverage manifest |

## Safety Gate

Provider data always enters staging first:

- `outputs/provider_raw/<refresh_id>/`
- `outputs/odds_provider_raw_latest.json`
- `outputs/odds_provider_coverage_latest.json`

Formal raw publication requires:

1. Provider payload is TAB-labeled.
2. Raw snapshot validates against existing board parser/gate.
3. A manual TAB final-verification file approves the exact `refresh_id + board_id + sha256`.
4. Scope publish and full automation are separated: verified Matches raw can be published for match-board research, but full automation remains blocked until the full required non-region board set, private My Bets snapshot, and preflight gates are ready.

Until then, executable new stake remains `AUD 0`.

## Commands

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/github_sync/FIFA/tab-research-pipeline

cp config/odds_providers.local.env.example config/odds_providers.local.env
# Edit config/odds_providers.local.env locally. Do not commit real keys.
# Keep the .example filename unchanged; it is the GitHub-safe template only.
export TAB_FIFA_THE_ODDS_API_SPORTS="soccer_fifa_world_cup"
export TAB_FIFA_THE_ODDS_API_SPORT_DISCOVERY="1"
export TAB_FIFA_PROVIDER_SCOPE="matches"
export TAB_FIFA_THE_ODDS_API_MATCH_MARKETS="h2h,totals,spreads"

export TAB_FIFA_OPTICODDS_ENDPOINT="/fixtures/odds"
export TAB_FIFA_OPTICODDS_QUERY="sport=soccer&sportsbook=TAB"

python3 refresh_odds_provider_raw.py --provider the_odds_api --scope matches
```

Region-specific boards such as Australia Markets are ignored by default. `Team Total Goals Over/Under` is supported when provider payloads include `team_totals`; only request it through `TAB_FIFA_THE_ODDS_API_EXTRA_MATCH_MARKETS` after confirming provider support.

Credit-aware event-level alternate market probe:

```bash
python3 refresh_odds_provider_raw.py \
  --provider the_odds_api \
  --scope matches \
  --event-market-probe-limit 5 \
  --event-odds-limit 5 \
  --event-odds-markets totals,alternate_totals
```

Do not probe all 68 matches by default. The 2026-06-13 small probes proved that event-level odds can add `Total Goals Over/Under` through `alternate_totals`; Team Total should be routed to OpticOdds official access or TAB manual final verification instead of continuing The Odds API team-total blind probes. The probe runner now excludes historical event IDs that already have the requested target market, preventing repeated credit spend on the same fixtures.

Publish only after manual verification:

```bash
python3 refresh_odds_provider_raw.py \
  --input-json /path/to/provider_payload.json \
  --refresh-id <refresh_id> \
  --verification-file outputs/provider_tab_final_verification_latest.json \
  --publish-verified
```

## Current Status

- Code framework: implemented.
- Unit tests: implemented.
- Real provider key test: run successfully for The Odds API Matches on 2026-06-13 21:46 AEST; duplicate-probe fix and subsequent alternate probes refreshed coverage through 2026-06-14 00:00 AEST.
- OpticOdds live test: blocked by Cloudflare `1010 Access denied`; do not bypass browser signature. The blocked attempt is stored separately and last-good coverage is preserved.
- Matches-first provider scope: implemented.
- Latest live coverage: `soccer_fifa_world_cup`, 68 Matches, Result 68/68, Handicap 47/68, Total O/U 55/68, Team Total O/U 0/68, latest probe cost 13, used 180 and remaining 320.
- Current provider analysis status: Result/Handicap research-ready; event-level probe recovered Total O/U above the usable threshold and The Odds API queue is now exhausted; Team Total O/U remains the primary provider-coverage gap and is now a fallback path.
- Provider KPI artifacts: `provider_kpi_latest.json`, `provider_kpi_latest.md`, `provider_kpi_latest.pdf`; GitHub copy under `artifacts/latest/provider_kpi_latest.*`.
- Provider alternate-plan artifacts: `provider_alternate_plan_latest.json`, `provider_alternate_plan_latest.md`, `provider_alternate_plan_latest.pdf`; current The Odds API Total O/U queue `0`, Team Total fallback queue `68`, recommended batch `0`, estimated next-batch credits `0-0`, status `fallback_required`.
- Full automation coverage: not proven and intentionally not implied by Matches-only publish.
- Australia Markets via provider: intentionally ignored by default for this path.
- My Bets private position: still requires user authorization.

## Source Pointers

- The Odds API V4 docs: https://the-odds-api.com/liveapi/guides/v4/
- The Odds API AU bookmaker list: https://the-odds-api.com/sports-odds-data/bookmaker-apis.html
- OpticOdds TAB API page: https://opticodds.com/sportsbooks/tab-api
- OpticOdds getting started: https://developer.opticodds.com/docs/odds-api-getting-started-guide
- OpticOdds API FAQ: https://developer.opticodds.com/docs/api-faq
