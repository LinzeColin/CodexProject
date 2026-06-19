# FIFA / Football Result Analysis MVP

This is a compliant MVP for football match result analysis and prediction support. It stores public/manual data, computes explainable probabilities, saves predictions, runs backtests, and generates Markdown reports.

It does not implement automatic betting, account automation, captcha/login/paywall bypass, odds manipulation, or guaranteed profit claims.

## Stack

- Python 3.9+
- FastAPI
- SQLite
- Standard-library `unittest` tests for core prediction/backtest logic

## Quick Start

```bash
cd /Users/linzezhang/Documents/Codex/2026-06-03/files-mentioned-by-the-user-fifa/work/fifa-analysis-system
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8000
```

Open:

- Website dashboard: http://127.0.0.1:8000/
- API docs: http://127.0.0.1:8000/docs
- Health: http://127.0.0.1:8000/health

On startup, the app automatically seeds the FIFA World Cup 2026 context:

- FIFA World Cup 2026 competition
- all 48 qualified teams
- default official/public information sources
- system seed articles marking qualification context

Manual configuration is only for adding extra sources or overriding data.

## Test

```bash
python3 -m unittest discover -s tests -v
```

## MVP API

- `GET /health`
- `GET /`
- `GET /api/dashboard`
- `POST /bootstrap/world-cup-2026`
- `GET /teams`
- `POST /teams`
- `GET /competitions`
- `POST /competitions`
- `GET /matches`
- `POST /matches`
- `GET /matches/{match_id}`
- `POST /imports/matches`
- `POST /imports/matches.csv`
- `POST /imports/team-stats`
- `GET /crawl-sources`
- `POST /crawl-sources`
- `POST /crawl-jobs/run`
- `GET /crawl-jobs`
- `GET /crawl-logs`
- `GET /news-articles`
- `POST /predictions`
- `GET /predictions`
- `GET /predictions/{prediction_id}`
- `POST /backtests`
- `GET /backtests`
- `POST /reports/match/{match_id}`
- `GET /reports`
- `GET /reports/{report_id}.md`
- `GET /refresh/status`
- `POST /refresh/run`
- `GET /refresh/runs`

## Example Flow

Create teams:

```bash
curl -X POST http://127.0.0.1:8000/teams \
  -H 'content-type: application/json' \
  -d '{"name":"Australia","country":"AU","team_type":"national","fifa_rank":25}'

curl -X POST http://127.0.0.1:8000/teams \
  -H 'content-type: application/json' \
  -d '{"name":"Canada","country":"CA","team_type":"national","fifa_rank":60}'
```

Configure a compliant public RSS source and run a crawl:

```bash
curl -X POST http://127.0.0.1:8000/crawl-sources \
  -H 'content-type: application/json' \
  -d '{"name":"Example RSS","base_url":"https://example.com/rss.xml","source_type":"rss","terms_note":"Public RSS only; confirm terms before production use."}'

curl -X POST 'http://127.0.0.1:8000/crawl-jobs/run?source_id=1'
curl http://127.0.0.1:8000/news-articles
```

The crawler is intentionally source-based. It can collect configured public RSS/Atom feeds or public page titles, checks `robots.txt`, logs every job, and does not bypass login, captcha, paywalls, rate limits, or platform controls.

## Dynamic Refresh

The app runs like a lightweight dynamic monitoring site. By default, the background scheduler refreshes every 4 hours:

```env
ENABLE_SCHEDULER=true
REFRESH_INTERVAL_HOURS=4
```

Each refresh cycle:

- crawls every enabled compliant source in `crawl_sources`
- stores newly discovered public articles in `news_articles`
- creates fresh predictions for scheduled/postponed matches
- creates fresh Markdown reports
- records a row in `refresh_runs`

Manual controls:

```bash
curl http://127.0.0.1:8000/refresh/status
curl -X POST http://127.0.0.1:8000/refresh/run
curl http://127.0.0.1:8000/refresh/runs
```

Create competition and match, import stats, then run:

```bash
curl -X POST http://127.0.0.1:8000/predictions \
  -H 'content-type: application/json' \
  -d '{"match_id":1}'
```

## Model

The MVP uses `rules-v1.0.0`, an explainable softmax scoring model.

Factors:

- Recent form: `recent_points / (matches_played * 3)`, weight `1.4`
- Attack: `recent_goals_for / matches_played / 3`, weight `0.9`
- Defense: `1 / (1 + recent_goals_against / matches_played)`, weight `0.8`
- FIFA ranking advantage: `clamp((opponent_rank - team_rank) / 100, -1, 1)`, weight `0.7`
- Home advantage: fixed MVP value, weight `0.35`
- Injury impact: `-injury_impact`, weight `0.8`
- Fatigue: `-fatigue_index`, weight `0.5`
- News sentiment: `[-1, 1]`, weight `0.25`
- Trend score: `[-1, 1]`, weight `0.2`

Missing data is represented in `missing_data_warnings` and defaults to neutral values.

## Disclaimer

本结果仅为基于公开数据和模型规则的概率分析，不构成投注建议、财务建议或保证性判断。体育比赛存在高度不确定性，请自行承担决策风险。
