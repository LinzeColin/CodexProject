# 来源目录

- 生成时间: 2026-06-26T21:51:00+10:00
- 来源配置: `config/owner_controls.yaml`
- 配置版本: `owner-controls-v1`

## 板块

| 板块 ID | 启用 | 名称 | 权重 |
|---|---:|---|---:|
| `B1` | 是 | 研究前沿 | 25 |
| `B2` | 否 | 顶级期刊 | 20 |
| `B3` | 否 | 中国政策法规 | 25 |
| `B4` | 否 | 美国科技金融官方信号 | 20 |
| `B5` | 是 | 跨板块总览 | 10 |

## 来源

| 来源 ID | 板块 | 启用 | 名称 | 采集方式 | 层级 | 频率 | 权重 | 健康状态 |
|---|---|---:|---|---|---|---|---:|---|
| `SRC-ARXIV` | `B1` | 是 | arXiv Atom API | `official_atom_api` | `required` | `daily` | 100 | 已启用 (`active`) |
| `SRC-BIORXIV` | `B1` | 否 | bioRxiv public metadata API | `official_biorxiv_details_api` | `required` | `daily` | 0 | 影子测试 (`stage2_test`) |
| `SRC-MEDRXIV` | `B1` | 否 | medRxiv public metadata API | `official_medrxiv_details_api` | `required` | `daily` | 0 | 影子测试 (`stage2_test`) |
| `SRC-TOP-JOURNALS` | `B2` | 否 | Top journal public feeds | `planned_official_public_feeds` | `important` | `planned` | 0 | 规划中 (`planned`) |
| `SRC-CHINA-POLICY` | `B3` | 否 | China official policy sources | `planned_official_web_or_rss` | `required` | `planned` | 0 | 规划中 (`planned`) |
| `SRC-US-OFFICIAL` | `B4` | 否 | US official technology and finance signals | `planned_official_web_or_api` | `important` | `planned` | 0 | 规划中 (`planned`) |
