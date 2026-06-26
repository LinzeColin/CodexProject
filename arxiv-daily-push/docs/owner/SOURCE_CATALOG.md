# 来源目录

- 生成时间: 2026-06-22T21:00:00+10:00
- 来源配置: `config/owner_controls.yaml`
- 配置版本: `owner-controls-v1`

## 板块

| 板块 ID | 启用 | 名称 | 权重 |
|---|---:|---|---:|
| `B1` | `true` | 研究前沿 | 25 |
| `B2` | `false` | 顶级期刊 | 20 |
| `B3` | `false` | 中国政策法规 | 25 |
| `B4` | `false` | 美国科技金融官方信号 | 20 |
| `B5` | `true` | 跨板块总览 | 10 |

## 来源

| 来源 ID | 板块 | 启用 | 名称 | 方法 | 层级 | 频率 | 权重 | 健康状态 |
|---|---|---:|---|---|---|---|---:|---|
| `SRC-ARXIV` | `B1` | `true` | arXiv Atom API | `official_atom_api` | `required` | `daily` | 100 | `active` |
| `SRC-TOP-JOURNALS` | `B2` | `false` | Top journal public feeds | `planned_official_public_feeds` | `important` | `planned` | 0 | `planned` |
| `SRC-CHINA-POLICY` | `B3` | `false` | China official policy sources | `planned_official_web_or_rss` | `required` | `planned` | 0 | `planned` |
| `SRC-US-OFFICIAL` | `B4` | `false` | US official technology and finance signals | `planned_official_web_or_api` | `important` | `planned` | 0 | `planned` |
