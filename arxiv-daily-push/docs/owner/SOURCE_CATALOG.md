# Source Catalog

- generated_at: 2026-06-22T16:30:00+10:00
- generated_from: `config/owner_controls.yaml`
- config_version: `owner-controls-v1`

## Boards

| Board ID | Enabled | Name | Weight |
|---|---:|---|---:|
| `B1` | `true` | 研究前沿 | 25 |
| `B2` | `false` | 顶级期刊 | 20 |
| `B3` | `false` | 中国政策法规 | 25 |
| `B4` | `false` | 美国科技金融官方信号 | 20 |
| `B5` | `true` | 跨板块总览 | 10 |

## Sources

| Source ID | Board | Enabled | Name | Method | Tier | Frequency | Weight | Health |
|---|---|---:|---|---|---|---|---:|---|
| `SRC-ARXIV` | `B1` | `true` | arXiv Atom API | `official_atom_api` | `required` | `daily` | 100 | `active` |
| `SRC-TOP-JOURNALS` | `B2` | `false` | Top journal public feeds | `planned_official_public_feeds` | `important` | `planned` | 0 | `planned` |
| `SRC-CHINA-POLICY` | `B3` | `false` | China official policy sources | `planned_official_web_or_rss` | `required` | `planned` | 0 | `planned` |
| `SRC-US-OFFICIAL` | `B4` | `false` | US official technology and finance signals | `planned_official_web_or_api` | `important` | `planned` | 0 | `planned` |
