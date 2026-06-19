from __future__ import annotations

import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

from .artifact_compare import build_artifact_old_new_compare
from .io import atomic_write_json, atomic_write_text
from .markdown_visuals import mermaid_bar, mermaid_pie
from .model import apply_quality_overlay, estimate_xg, novig_probabilities, poisson_distribution, probability_of
from .parser import parse_market_pairs
from .sidecar_pdf import chart_from_items, render_sidecar_pdf


MODEL_COMPARISON_VERSION = "v0_1"
MODEL_COMPARISON_JSON = f"tab_fifa_model_comparison_{MODEL_COMPARISON_VERSION}.json"
MODEL_COMPARISON_MD = f"tab_fifa_model_comparison_{MODEL_COMPARISON_VERSION}.md"
MODEL_COMPARISON_PDF = f"tab_fifa_model_comparison_{MODEL_COMPARISON_VERSION}.pdf"
DC_RHO = -0.13


OPEN_SOURCE_REFERENCES = [
    {
        "name": "Hicruben/world-cup-2026-prediction-model",
        "display_name": "Hicruben 2026 WC",
        "url": "https://github.com/Hicruben/world-cup-2026-prediction-model",
        "license": "MIT",
        "method_family": "Elo + Dixon-Coles + Monte Carlo",
        "adoption_status": "implemented_proxy",
        "verified_at": "2026-06-12",
        "coverage": ["1X2", "晋级路径", "模型分歧", "回测评价", "Monte Carlo", "Track record"],
        "applied_ideas": [
            "Elo rating seed",
            "Dixon-Coles low-score correction",
            "Monte Carlo-ready match probability output",
            "walk-forward out-of-sample evaluation pattern",
            "live track-record and reliability-curve reporting pattern",
        ],
        "github_evidence": [
            "公开 README 描述为 Elo ratings -> Dixon-Coles bivariate Poisson -> Monte Carlo simulation。",
            "README 提到 48-team、50,000-simulation、real bracket conditioning 和自动按赛果更新。",
            "README 提供 backtest.mjs、calibrate.mjs、predict.mjs、track-record.mjs，以及 RPS/log-loss/Brier/ECE 评价。",
            "2026-06-12 复核：README 显示 7 commits、MIT license、live track record 2/2 correct picks updated 2026-06-12。",
        ],
        "reusable_features": [
            "48队赛事路径 Monte Carlo 接口",
            "walk-forward + reliability curve 回测摘要",
            "CLI 预测与校准脚本分层",
            "live track record 命中/失误列表",
            "可嵌入 widgets 和 open data 输出",
            "透明模型说明和非自动下注免责声明",
        ],
        "layout_patterns": [
            "方法论、回测指标、示例预测分块展示",
            "用进度条/百分比呈现三结果概率",
            "把 track record、calibration、widgets/open data 作为一眼可扫的运营区块",
            "把 live prediction、methodology、bracket simulator 分为独立入口",
            "把 live track record、reliability curve、open data/widgets 组合成运营 Dashboard。",
        ],
        "report_usage": "用于48队强弱先验、低比分修正和比赛结果概率交叉验证；其walk-forward/reliability/track-record思路进入本地模型审计，Monte Carlo路径作为晋级/淘汰赛模拟接口。",
    },
    {
        "name": "opisthokonta/goalmodel",
        "display_name": "goalmodel",
        "url": "https://github.com/opisthokonta/goalmodel",
        "license": "GPL-3.0",
        "method_family": "Expected goals probability model",
        "adoption_status": "implemented_proxy",
        "verified_at": "2026-06-12",
        "coverage": ["1X2", "Over/Under", "BTTS", "xG反推", "评分规则", "Dispersion", "Extra time offset"],
        "applied_ideas": [
            "expected-goals to 1X2",
            "over/under probabilities",
            "both-teams-to-score probabilities",
            "reverse-engineering expected goals from market probabilities",
            "Brier/log score evaluation roadmap",
            "dispersion and two-step estimation caveats",
            "extra-time offset design for knockout scenarios",
        ],
        "github_evidence": [
            "公开 README 列出 predict_expg、predict_goals、predict_result、predict_ou、predict_btts。",
            "README 列出 p1x2、pbtts、expg_from_ou、expg_from_probabilities、weights_dc、score_predictions。",
            "默认模型使用攻防参数、主场优势和 Poisson 进球强度表达，并包含 CMP/Negative Binomial、two-step 与 extra-time offset 讨论。",
            "2026-06-12 复核：README 明确 score_predictions 支持 log、brier、rps，并说明 expg_from_probabilities 可从 bookmaker odds 反推 xG。",
        ],
        "reusable_features": [
            "同一 xG 分布同时驱动 1X2、OU、BTTS",
            "市场概率反推 xG",
            "时间衰减权重和评分规则",
            "攻防参数与主场优势解释层",
            "进球分布过度/不足离散的风险提示",
            "淘汰赛加时 offset 建模接口",
        ],
        "layout_patterns": [
            "按预测函数族分组展示能力覆盖",
            "把模型公式和可调用函数并列作为证据",
            "在报告中把 1X2、OU、BTTS 放入同一模型能力矩阵",
        ],
        "report_usage": "用于市场隐含概率反推xG，并把同一xG分布转换为1X2、大小球、BTTS和评分规则敏感性检查。",
    },
    {
        "name": "RyanSCodes/Dixon-Coles-Football-Predictor",
        "display_name": "RyanSCodes DC",
        "url": "https://github.com/RyanSCodes/Dixon-Coles-Football-Predictor",
        "license": "No release license declared",
        "method_family": "Dixon-Coles weighted history",
        "adoption_status": "design_reference",
        "verified_at": "2026-06-12",
        "coverage": ["时间衰减", "攻防参数", "低比分校正", "Poisson比分矩阵"],
        "applied_ideas": ["exponential time decay", "home advantage parameter", "attack-defense parameters", "Poisson score matrix"],
        "github_evidence": [
            "公开 README 标注 Python 2.7，并说明基于 Dixon-Coles method。",
            "README 描述主场优势、每队攻防参数和 Poisson 进球分布。",
            "README 说明历史结果按时间指数衰减，旧结果对当前状态影响更低。",
            "2026-06-12 复核：GitHub 页面未显示 license 文件，当前只能作为 design reference，不复制实现。",
        ],
        "reusable_features": [
            "指数时间衰减思路",
            "主场优势参数",
            "攻防参数拆分",
            "比分矩阵汇总成胜平负概率",
        ],
        "layout_patterns": [
            "把时间衰减列为模型风险说明，不直接复制旧实现",
            "用攻防参数解释模型分歧来源",
            "把 legacy runtime/license 风险作为人工复核提示",
        ],
        "report_usage": "作为后续回测/时间衰减权重设计参考；当前不复制其Python 2.7实现。",
    },
    {
        "name": "martineastwood/penaltyblog",
        "display_name": "penaltyblog",
        "url": "https://github.com/martineastwood/penaltyblog",
        "license": "MIT",
        "method_family": "Poisson + Dixon-Coles + bookmaker odds utilities",
        "adoption_status": "implemented_proxy",
        "verified_at": "2026-06-12",
        "coverage": [
            "1X2",
            "Asian Handicap",
            "Over/Under",
            "No-vig implied probability",
            "Poisson",
            "Bivariate Poisson",
            "Dixon-Coles",
            "Bayesian uncertainty",
            "Team ratings",
            "JSON workflow",
        ],
        "applied_ideas": [
            "bookmaker overround removal",
            "Poisson/Dixon-Coles market probability cross-check",
            "Asian handicap and totals market coverage roadmap",
            "team rating layer beyond raw market odds",
            "fast batch modelling and JSON workflow separation",
            "visual modelling and betting insight workflow patterns",
        ],
        "github_evidence": [
            "GitHub README 标注 penaltyblog 是生产级 Python football analytics 包，覆盖数据分析、outcome modelling 和 betting insights。",
            "README features 列出 Poisson、Bivariate Poisson、Dixon-Coles、Bayesian 模型、Elo/ratings、Asian handicap、over/under 和 bookmaker margin removal。",
            "GitHub 页面显示 MIT license、v1.11.0 latest Jun 2 2026、833 commits。",
            "2026-06-12 复核：README 提供 Colab examples，包括 match prediction、implied probabilities、xT 和 StatsBomb 数据。",
        ],
        "reusable_features": [
            "赔率去水和 overround removal 统一口径",
            "Poisson / Bivariate Poisson / Dixon-Coles 模型覆盖",
            "Asian handicap 与大小球概率扩展路线",
            "Elo/Massey/Colley/Pi team ratings 借鉴",
            "批量 JSON workflow 和 lazy processing 思路",
            "Bayesian uncertainty 用于置信区间和模型风险提示",
            "publication-ready pitch / chart visualization 参考",
        ],
        "layout_patterns": [
            "把数据、模型、赔率、ratings 和可视化分成能力矩阵",
            "用 Quick Start / Examples 引导用户从预测到 implied probability",
            "把 bookmaker odds decoding 单独列为下注前置校验",
            "在 Dashboard 中区分模型概率、盘口概率和不确定性",
        ],
        "report_usage": "用于强化本地 no-vig、EV、Edge、大小球/让球和模型不确定性口径；本地仍使用自有实现，不直接依赖外部包执行下注。",
    },
    {
        "name": "ML-KULeuven/socceraction",
        "display_name": "socceraction",
        "url": "https://github.com/ML-KULeuven/socceraction",
        "license": "MIT",
        "method_family": "SPADL + xT + VAEP action value",
        "adoption_status": "design_reference",
        "verified_at": "2026-06-12",
        "coverage": [
            "SPADL",
            "Atomic-SPADL",
            "xT",
            "VAEP",
            "Atomic-VAEP",
            "Event stream preprocessing",
            "Player action value",
            "Provider adapters",
        ],
        "applied_ideas": [
            "event stream to common SPADL abstraction",
            "xT / VAEP action-value indicators for player and team form",
            "provider adapter design for StatsBomb/Wyscout/Opta-style data",
            "separate free sample data from paid event feeds",
            "attribution and citation requirement in public work",
        ],
        "github_evidence": [
            "GitHub About 描述为把足球 event stream 转成 SPADL，并用 VAEP 或 xT 评价球员动作。",
            "官方 FAQ 说明 socceraction 提供 VAEP、API clients 和 proprietary data formats 到 SPADL 的 converters。",
            "官方 FAQ 提到 StatsBomb/Wyscout 免费 sample 或 StatsBomb/Wyscout/Opta 订阅数据源，适合事件流预处理。",
            "2026-06-12 复核：GitHub 页面显示 MIT license，latest release v1.5.3 Aug 15 2024。",
        ],
        "reusable_features": [
            "把球员事件数据转为可比较的 action value 指标",
            "xT / VAEP 作为基本面强弱和伤停影响的解释层",
            "SPADL/Atomic-SPADL 数据标准化路径",
            "provider adapter 抽象适合未来接入事件数据",
            "免费样本/付费数据的证据质量分层",
            "引用与 attribution 作为公开报告合规提示",
        ],
        "layout_patterns": [
            "球员/球队 action value 雷达或 Top贡献表",
            "事件数据来源质量标签：sample、paid、missing",
            "把战术/球员基本面与盘口概率分开展示",
            "在报告中显示 action-value unavailable 时的降级说明",
        ],
        "report_usage": "用于未来把球员事件、战术和基本面转成 xT/VAEP 解释层；当前无事件流原始数据时只作设计参考和缺口提示。",
    },
    {
        "name": "openfootball/worldcup.json",
        "display_name": "openfootball worldcup.json",
        "url": "https://github.com/openfootball/worldcup.json",
        "license": "Public Domain / CC0-style dedication",
        "method_family": "World Cup public schedule JSON",
        "adoption_status": "design_reference",
        "verified_at": "2026-06-12",
        "coverage": [
            "World Cup 2026 schedule",
            "JSON fixture feed",
            "No API key",
            "Public domain data",
            "Source text files",
            "SQLite/CSV export path",
        ],
        "applied_ideas": [
            "public raw JSON as fixture sanity-check feed",
            "source text file trace for group and knockout stages",
            "no-api-key fallback for schedule and date validation",
            "public-domain license posture for report-safe fixtures",
            "SQLite/CSV export pattern for local database seeding",
        ],
        "github_evidence": [
            "GitHub About 描述 worldcup.json 为 free open public domain football data，包含 Canada/USA/Mexico 2026，No API key required。",
            "README 提供 raw GitHub URL 示例：/2026/worldcup.json，可作为公开 JSON HTTP API 使用。",
            "README 指出 2026 World Cup group stage 与 knockout source text files 分别在 /worldcup/2026--usa/cup.txt 和 cup_finals.txt。",
            "README License 说明 schema、data 和 scripts dedicated to public domain，no restrictions whatsoever。",
        ],
        "reusable_features": [
            "2026 World Cup 赛程与阶段校验",
            "raw JSON 公开源作为 TAB raw 以外的赛程 fallback",
            "source text file trace 便于定位赛程变更",
            "本地 SQLite fixture seed 和日报日期校验",
            "Public domain 数据合规标记",
            "No API key 数据源健康检查",
        ],
        "layout_patterns": [
            "赛程源状态卡：TAB raw / openfootball fallback / 手动复核",
            "按 group、round、date 展示 fixture sanity check",
            "把 public-domain 数据源与 TAB 盘口源分开标注",
            "在 Dashboard 中显示 schedule freshness 和 mismatch queue",
        ],
        "report_usage": "用于赛程、日期、阶段和本地数据库 seed 的公开交叉验证；不提供赔率，不替代 TAB 实时盘口 raw。",
    },
]


HICRUBEN_ELO_RATINGS = {
    "Argentina": 2064,
    "France": 2040,
    "Spain": 2074,
    "Brazil": 1994,
    "England": 1982,
    "Portugal": 1934,
    "Netherlands": 1942,
    "Germany": 1927,
    "Belgium": 1871,
    "Colombia": 1884,
    "Uruguay": 1833,
    "Croatia": 1878,
    "Morocco": 1875,
    "Switzerland": 1807,
    "USA": 1794,
    "Mexico": 1830,
    "Japan": 1851,
    "Senegal": 1830,
    "Ecuador": 1790,
    "Australia": 1769,
    "South Korea": 1742,
    "Iran": 1733,
    "Canada": 1725,
    "Ghana": 1630,
    "Tunisia": 1666,
    "Cote d Ivoire": 1706,
    "Saudi Arabia": 1619,
    "Qatar": 1552,
    "Egypt": 1671,
    "Algeria": 1676,
    "Scotland": 1616,
    "Paraguay": 1653,
    "Czechia": 1613,
    "Bosn-Herzegovina": 1566,
    "South Africa": 1562,
    "New Zealand": 1567,
    "Panama": 1582,
    "Jordan": 1515,
    "Haiti": 1481,
}


HOST_TEAMS = {"Mexico", "Canada", "USA"}


def write_model_comparison(raw: Dict, output_dir: Path, version: str = MODEL_COMPARISON_VERSION) -> Dict:
    payload = generate_model_comparison(raw, version=version)
    json_name = f"tab_fifa_model_comparison_{version}.json"
    md_name = f"tab_fifa_model_comparison_{version}.md"
    pdf_name = f"tab_fifa_model_comparison_{version}.pdf"
    json_path = Path(output_dir) / json_name
    payload["old_new_compare"] = build_artifact_old_new_compare(json_path, payload, model_compare_metrics())
    atomic_write_json(json_path, payload)
    atomic_write_text(Path(output_dir) / md_name, render_model_comparison_markdown(payload))
    pdf_summary = write_model_comparison_pdf(payload, Path(output_dir) / pdf_name)
    payload["artifacts"] = {
        "json": json_name,
        "markdown": md_name,
        "pdf": pdf_name,
        "pdf_summary": pdf_summary,
    }
    atomic_write_json(json_path, payload)
    return {
        **payload,
        "json_artifact": json_name,
        "markdown_artifact": md_name,
        "pdf_artifact": pdf_name,
        "pdf_summary": pdf_summary,
    }


def model_compare_metrics() -> List[Tuple[str, str]]:
    return [
        ("ready", "ready"),
        ("match_count", "match_count"),
        ("model_count", "model_count"),
        ("high_divergence_count", "summary.high_divergence_count"),
        ("avg_current_vs_elo_disagreement", "summary.avg_current_vs_elo_disagreement"),
        ("reference_count", "source_adoption.reference_count"),
        ("implemented_reference_count", "source_adoption.implemented_reference_count"),
        ("design_reference_count", "source_adoption.design_reference_count"),
        ("github_source_audit_ready", "model_dashboard.github_source_audit_ready"),
        ("automation_view_ready", "automation_view.automation_view_ready"),
    ]


def write_model_comparison_pdf(payload: Dict, output_path: Path) -> Dict:
    summary = payload.get("summary", {})
    source_adoption = payload.get("source_adoption", {})
    dashboard = payload.get("model_dashboard", {})
    compare = payload.get("old_new_compare") or {}
    extra_tables = [
        {
            "title": "Open-source Model Dashboard",
            "headers": ["Metric", "Value"],
            "rows": [
                ["Decision", str(dashboard.get("decision", ""))],
                ["Matched games", str(int(dashboard.get("match_count") or 0))],
                ["High divergence", str(int(dashboard.get("high_divergence_count") or 0))],
                ["Average disagreement", percent(dashboard.get("avg_disagreement") or 0)],
                ["Implemented refs", f"{dashboard.get('implemented_reference_count', 0)}/{dashboard.get('reference_count', 0)}"],
                ["Next action", str(dashboard.get("next_action", ""))],
            ],
        },
        {
            "title": "Automation 使用视角",
            "headers": ["Gate", "Status", "Evidence / Action"],
            "rows": [
                [
                    str(row.get("gate", "")),
                    str(row.get("status", "")),
                    str(row.get("evidence", "")),
                ]
                for row in (payload.get("automation_view") or {}).get("gates", [])
            ],
        },
        {
            "title": "GitHub Source Audit",
            "headers": ["Source", "License", "Status", "Current Evidence"],
            "rows": [
                [
                    str(row.get("display_name", "")),
                    str(row.get("license", "")),
                    str(row.get("adoption_status", "")),
                    "; ".join(str(item) for item in (row.get("github_evidence") or [])[-2:]),
                ]
                for row in (source_adoption.get("rows") or [])
            ],
        },
        {
            "title": "Reusable Dashboard Patterns",
            "headers": ["Source", "Patterns"],
            "rows": [
                [str(row.get("display_name", "")), "; ".join(str(item) for item in (row.get("layout_patterns") or [])[:3])]
                for row in (source_adoption.get("rows") or [])
            ],
        },
    ]
    if compare.get("rows"):
        extra_tables.append(
            {
                "title": "新旧模型对比变化",
                "headers": ["指标", "当前", "上一版", "变化"],
                "rows": [
                    [str(row.get("metric", "")), str(row.get("current", "")), str(row.get("previous", "")), str(row.get("delta", ""))]
                    for row in compare.get("rows", [])
                ],
            }
        )
    charts = [
        chart_from_items("Open-source Model Dashboard", model_dashboard_items(dashboard), color="#1F4E79"),
        chart_from_items("模型分歧 Top7", model_disagreement_items(payload.get("rows", [])), color="#C7352B"),
        chart_from_items("共识置信度", consensus_confidence_items(payload.get("rows", [])), color="#2A7A5E"),
        chart_from_items("开源能力覆盖", source_coverage_items(source_adoption), color="#1F4E79"),
        chart_from_items("GitHub 采用状态", source_adoption_items(source_adoption), color="#7A4E9D"),
        chart_from_items("Automation 模型门禁", automation_view_items(payload.get("automation_view", {})), color="#A56710"),
    ]
    pdf = render_sidecar_pdf(
        Path(output_path),
        title="TAB FIFA Open-source Model Dashboard",
        subtitle="Elo / Dixon-Coles / goalmodel / penaltyblog / socceraction / openfootball 交叉验证、GitHub 源审计和模型分歧 Dashboard；仅用于研究分析，不自动下注。",
        summary_rows=[
            ("dashboard_decision", str(dashboard.get("decision", ""))),
            ("model_risk", str(dashboard.get("model_risk", ""))),
            ("比较比赛", str(payload.get("match_count", 0))),
            ("模型数量", str(payload.get("model_count", 0))),
            ("高分歧场次", str(summary.get("high_divergence_count", 0))),
            ("平均当前-Elo/DC分歧", percent(summary.get("avg_current_vs_elo_disagreement", 0))),
            ("GitHub参考源", str(source_adoption.get("reference_count", len(payload.get("references", []))))),
            ("已落地参考", str(source_adoption.get("implemented_reference_count", 0))),
            ("automation view", str((payload.get("automation_view") or {}).get("automation_role", ""))),
        ],
        charts=charts,
        table_headers=["比赛", "共识注", "信心", "最大分歧", "当前模型1X2", "Elo/DC 1X2"],
        table_rows=model_comparison_pdf_rows(payload.get("rows", [])),
        extra_tables=extra_tables,
    )
    return {
        **pdf,
        "match_count": int(payload.get("match_count") or 0),
        "reference_count": int(source_adoption.get("reference_count") or len(payload.get("references", []))),
    }


def generate_model_comparison(raw: Dict, version: str = MODEL_COMPARISON_VERSION) -> Dict:
    rows = []
    for match in raw.get("matches", []):
        row = compare_match_models(match)
        if row:
            rows.append(row)
    rows.sort(key=lambda item: item["disagreement"]["max_abs_current_vs_elo_dc"], reverse=True)
    source_adoption = build_source_adoption(OPEN_SOURCE_REFERENCES)
    summary = summarize_rows(rows)
    payload = {
        "version": version,
        "source": "tab_fifa_open_source_model_dashboard",
        "references": OPEN_SOURCE_REFERENCES,
        "source_adoption": source_adoption,
        "model_count": 3,
        "models": [
            {
                "id": "current_market_poisson",
                "description": "现有 TAB 市场反推 xG + 人工质量 overlay + 独立 Poisson。",
            },
            {
                "id": "open_source_elo_dixon_coles",
                "description": "参考开源 2026 世界杯模型的 Elo seed、Dixon-Coles 低比分修正和 xG 映射。",
            },
            {
                "id": "goalmodel_market_dc_proxy",
                "description": "参考 goalmodel 的 expected-goals -> 1X2/OU/BTTS 路径，在市场反推 xG 上加入 Dixon-Coles 修正。",
            },
        ],
        "match_count": len(rows),
        "ready": len(rows) >= 20,
        "rows": rows,
        "summary": summary,
    }
    payload["model_dashboard"] = build_model_dashboard(payload, source_adoption, summary)
    payload["automation_view"] = build_automation_view(payload, source_adoption, summary)
    return payload


def build_model_dashboard(payload: Dict, source_adoption: Dict, summary: Dict) -> Dict:
    match_count = int(payload.get("match_count") or 0)
    high_divergence = int(summary.get("high_divergence_count") or 0)
    avg_disagreement = float(summary.get("avg_current_vs_elo_disagreement") or 0)
    ref_count = int(source_adoption.get("reference_count") or 0)
    implemented_count = int(source_adoption.get("implemented_reference_count") or 0)
    high_divergence_ratio = (high_divergence / match_count) if match_count else 0
    return {
        "title": "Open-source Model Dashboard",
        "decision": "用于交叉验证，不单独触发下注",
        "match_count": match_count,
        "model_count": int(payload.get("model_count") or 0),
        "high_divergence_count": high_divergence,
        "high_divergence_ratio": high_divergence_ratio,
        "avg_disagreement": avg_disagreement,
        "reference_count": ref_count,
        "implemented_reference_count": implemented_count,
        "design_reference_count": int(source_adoption.get("design_reference_count") or 0),
        "github_source_audit_ready": ref_count >= 3 and implemented_count >= 2,
        "model_risk": "高分歧比赛进入人工复核；开源模型只做概率交叉验证，不替代 TAB 实时盘口。",
        "next_action": "把 high divergence 场次优先放入报告解释和人工复核队列。",
        "reading_path": [
            "先看 high_divergence_count 和 avg_disagreement。",
            "再看 GitHub source audit 判断模型证据来源。",
            "最后看 Top Divergence 表决定哪些盘口需要人工复核。",
        ],
    }


def build_automation_view(payload: Dict, source_adoption: Dict, summary: Dict) -> Dict:
    match_count = int(payload.get("match_count") or 0)
    high_divergence = int(summary.get("high_divergence_count") or 0)
    github_ready = bool((payload.get("model_dashboard") or {}).get("github_source_audit_ready"))
    model_ready = bool(payload.get("ready"))
    review_required = high_divergence > 0
    return {
        "title": "Automation 使用视角",
        "automation_role": "研究交叉验证层，不是执行授权层",
        "automation_view_ready": model_ready and github_ready,
        "scheduler_stage": "日报生成时先写 model comparison，再重建 source model registry、recommendation operations 和 visual inventory。",
        "fail_closed_policy": "模型对比只能提高/降低置信度并生成复核队列；raw/private/preflight/public-safety 任一门禁失败时，新增可执行金额仍为 AUD 0。",
        "manual_review_policy": "高分歧比赛必须进入人工复核，不能由模型分歧结果直接触发下注。",
        "prohibited_actions": ["不自动下注", "不点击赔率", "不添加投注单", "不绕过 TAB raw/private 门禁"],
        "gates": [
            {
                "gate": "model_cross_check_ready",
                "status": "ready" if model_ready else "partial",
                "score": 1 if model_ready else 0,
                "evidence": f"可比较比赛 {match_count}；ready={model_ready}",
            },
            {
                "gate": "github_source_audit_ready",
                "status": "ready" if github_ready else "partial",
                "score": 1 if github_ready else 0,
                "evidence": f"GitHub/开源参考 {source_adoption.get('implemented_reference_count', 0)}/{source_adoption.get('reference_count', 0)} 已吸收。",
            },
            {
                "gate": "high_divergence_review_queue",
                "status": "manual_review_required" if review_required else "clear",
                "score": high_divergence,
                "evidence": f"高分歧场次 {high_divergence}；只进入报告解释和人工复核。",
            },
            {
                "gate": "execution_unlock",
                "status": "blocked_by_design",
                "score": 0,
                "evidence": "模型对比报告不能解锁下注；执行仍由 raw/private/preflight/public-safety 门禁决定。",
            },
        ],
        "dashboard_usage": [
            "推荐报告使用模型分歧解释概率置信度。",
            "高分歧场次进入人工复核，不直接买入。",
            "Source Model Registry 和 Report Visual Inventory 使用本视角判断模型报告是否具备 automation 证据。",
        ],
    }


def build_source_adoption(references: List[Dict]) -> Dict:
    implemented = [ref for ref in references if ref.get("adoption_status") == "implemented_proxy"]
    design_only = [ref for ref in references if ref.get("adoption_status") != "implemented_proxy"]
    coverage_counts: Dict[str, int] = {}
    for ref in references:
        for item in ref.get("coverage", []):
            coverage_counts[item] = coverage_counts.get(item, 0) + 1
    return {
        "reference_count": len(references),
        "implemented_reference_count": len(implemented),
        "design_reference_count": len(design_only),
        "coverage_counts": coverage_counts,
        "rows": [
            {
                "source": ref["name"],
                "display_name": ref.get("display_name", ref["name"]),
                "method_family": ref.get("method_family", ""),
                "adoption_status": ref.get("adoption_status", ""),
                "coverage": ref.get("coverage", []),
                "report_usage": ref.get("report_usage", ""),
                "license": ref.get("license", ""),
                "url": ref.get("url", ""),
                "verified_at": ref.get("verified_at", ""),
                "github_evidence": ref.get("github_evidence", []),
                "reusable_features": ref.get("reusable_features", []),
                "layout_patterns": ref.get("layout_patterns", []),
            }
            for ref in references
        ],
    }


def compare_match_models(match: Dict) -> Dict:
    name = match.get("match", "")
    home, away = split_match_name(name)
    if not home or not away:
        return {}
    markets = match.get("markets", {})
    result_prices = parse_market_pairs(markets.get("Result", ""), "Result")
    if not all(selection in result_prices for selection in [home, "Draw", away]):
        return {}
    home_name, home_odds = home, result_prices[home]
    draw_odds = result_prices["Draw"]
    away_name, away_odds = away, result_prices[away]
    market_home, market_draw, market_away = novig_probabilities([home_odds, draw_odds, away_odds])
    under_25_market = infer_under_25_probability(markets)

    current_home_xg, current_away_xg = estimate_xg(market_home, market_away, under_25_market)
    current_home_xg, current_away_xg, overlay_note = apply_quality_overlay(name, current_home_xg, current_away_xg)
    current_distribution = poisson_distribution(current_home_xg, current_away_xg, max_goals=10)
    current_probs = probability_pack(current_distribution)

    goalmodel_distribution = dixon_coles_distribution(current_home_xg, current_away_xg, rho=DC_RHO, max_goals=10)
    goalmodel_probs = probability_pack(goalmodel_distribution)

    home_rating, away_rating, rating_source = resolve_ratings(home, away, market_home, market_away)
    home_bonus = 35 if home in HOST_TEAMS else (-18 if away in HOST_TEAMS else 0)
    elo_home_xg = expected_goals_from_elo(home_rating, away_rating, home_bonus)
    elo_away_xg = expected_goals_from_elo(away_rating, home_rating, -home_bonus / 2)
    elo_distribution = dixon_coles_distribution(elo_home_xg, elo_away_xg, rho=DC_RHO, max_goals=10)
    elo_probs = probability_pack(elo_distribution)

    consensus = consensus_signal(
        {
            home_name: [current_probs["home_win"], goalmodel_probs["home_win"], elo_probs["home_win"]],
            "Draw": [current_probs["draw"], goalmodel_probs["draw"], elo_probs["draw"]],
            away_name: [current_probs["away_win"], goalmodel_probs["away_win"], elo_probs["away_win"]],
        }
    )
    disagreements = {
        "home": abs(current_probs["home_win"] - elo_probs["home_win"]),
        "draw": abs(current_probs["draw"] - elo_probs["draw"]),
        "away": abs(current_probs["away_win"] - elo_probs["away_win"]),
    }
    return {
        "match": name,
        "home": home,
        "away": away,
        "ratings": {
            "home": round(home_rating, 1),
            "away": round(away_rating, 1),
            "source": rating_source,
        },
        "xg": {
            "current_market_poisson": {"home": round(current_home_xg, 3), "away": round(current_away_xg, 3)},
            "open_source_elo_dixon_coles": {"home": round(elo_home_xg, 3), "away": round(elo_away_xg, 3)},
        },
        "market_no_vig": {"home_win": market_home, "draw": market_draw, "away_win": market_away},
        "current_market_poisson": current_probs,
        "goalmodel_market_dc_proxy": goalmodel_probs,
        "open_source_elo_dixon_coles": elo_probs,
        "consensus": consensus,
        "disagreement": {
            "home": round(disagreements["home"], 4),
            "draw": round(disagreements["draw"], 4),
            "away": round(disagreements["away"], 4),
            "max_abs_current_vs_elo_dc": round(max(disagreements.values()), 4),
            "high_divergence": max(disagreements.values()) >= 0.10,
        },
        "notes": [
            overlay_note,
            "Elo/DC layer is a cross-check, not an automatic staking engine.",
            "Goalmodel proxy uses expected-goals path for 1X2, OU and BTTS sensitivity.",
        ],
    }


def infer_under_25_probability(markets: Dict) -> float:
    totals = parse_market_pairs(markets.get("Total Goals Over/Under", ""), "Total Goals Over/Under")
    if "Under 2.5 Goals" in totals and "Over 2.5 Goals" in totals:
        under, _over = novig_probabilities([totals["Under 2.5 Goals"], totals["Over 2.5 Goals"]])
        return under
    return 0.54


def probability_pack(distribution: Dict[Tuple[int, int], float]) -> Dict:
    return {
        "home_win": probability_of(distribution, lambda h, a: h > a),
        "draw": probability_of(distribution, lambda h, a: h == a),
        "away_win": probability_of(distribution, lambda h, a: h < a),
        "over_2_5": probability_of(distribution, lambda h, a: h + a >= 3),
        "under_2_5": probability_of(distribution, lambda h, a: h + a <= 2),
        "btts_yes": probability_of(distribution, lambda h, a: h >= 1 and a >= 1),
        "btts_no": probability_of(distribution, lambda h, a: h == 0 or a == 0),
    }


def dixon_coles_distribution(home_xg: float, away_xg: float, rho: float = DC_RHO, max_goals: int = 10) -> Dict[Tuple[int, int], float]:
    raw: Dict[Tuple[int, int], float] = {}
    for home in range(max_goals + 1):
        p_home = poisson_pmf(home, home_xg)
        for away in range(max_goals + 1):
            raw[(home, away)] = p_home * poisson_pmf(away, away_xg) * dc_tau(home, away, home_xg, away_xg, rho)
    total = sum(raw.values())
    if total <= 0:
        return poisson_distribution(home_xg, away_xg, max_goals=max_goals)
    return {score: probability / total for score, probability in raw.items()}


def dc_tau(home_goals: int, away_goals: int, home_xg: float, away_xg: float, rho: float) -> float:
    if home_goals == 0 and away_goals == 0:
        return 1 - home_xg * away_xg * rho
    if home_goals == 0 and away_goals == 1:
        return 1 + home_xg * rho
    if home_goals == 1 and away_goals == 0:
        return 1 + away_xg * rho
    if home_goals == 1 and away_goals == 1:
        return 1 - rho
    return 1


def expected_goals_from_elo(rating: float, opponent: float, home_bonus: float = 0) -> float:
    return max(0.3, min(3.5, 1.35 + ((rating + home_bonus) - opponent) / 350))


def resolve_ratings(home: str, away: str, market_home: float, market_away: float) -> Tuple[float, float, str]:
    home_known = HICRUBEN_ELO_RATINGS.get(home)
    away_known = HICRUBEN_ELO_RATINGS.get(away)
    implied_diff = math.log(max(market_home, 0.01) / max(market_away, 0.01)) * 260
    if home_known is not None and away_known is not None:
        return float(home_known), float(away_known), "hicruben_elo_seed"
    if home_known is not None:
        return float(home_known), clamp_rating(home_known - implied_diff), "partial_hicruben_market_implied"
    if away_known is not None:
        return clamp_rating(away_known + implied_diff), float(away_known), "partial_hicruben_market_implied"
    return clamp_rating(1700 + implied_diff / 2), clamp_rating(1700 - implied_diff / 2), "market_implied_fallback"


def clamp_rating(value: float) -> float:
    return max(1300.0, min(2150.0, float(value)))


def consensus_signal(options: Dict[str, List[float]]) -> Dict:
    scored = []
    for selection, values in options.items():
        mean = sum(values) / len(values)
        spread = max(values) - min(values)
        scored.append((selection, mean, spread))
    scored.sort(key=lambda item: (item[1], -item[2]), reverse=True)
    selection, mean, spread = scored[0]
    return {
        "selection": selection,
        "mean_probability": round(mean, 4),
        "model_spread": round(spread, 4),
        "confidence": "high" if spread < 0.06 else ("medium" if spread < 0.12 else "low"),
    }


def summarize_rows(rows: List[Dict]) -> Dict:
    if not rows:
        return {
            "high_divergence_count": 0,
            "avg_current_vs_elo_disagreement": 0,
            "top_divergence_matches": [],
            "rating_source_counts": {},
        }
    high = [row for row in rows if row["disagreement"]["high_divergence"]]
    avg = sum(row["disagreement"]["max_abs_current_vs_elo_dc"] for row in rows) / len(rows)
    source_counts: Dict[str, int] = {}
    for row in rows:
        source = row["ratings"]["source"]
        source_counts[source] = source_counts.get(source, 0) + 1
    return {
        "high_divergence_count": len(high),
        "avg_current_vs_elo_disagreement": round(avg, 4),
        "top_divergence_matches": [
            {
                "match": row["match"],
                "max_abs_current_vs_elo_dc": row["disagreement"]["max_abs_current_vs_elo_dc"],
                "consensus": row["consensus"],
            }
            for row in rows[:5]
        ],
        "rating_source_counts": source_counts,
    }


def split_match_name(match: str) -> Tuple[str, str]:
    if " v " not in match:
        return "", ""
    return tuple(match.split(" v ", 1))  # type: ignore[return-value]


def poisson_pmf(k: int, lam: float) -> float:
    return math.exp(-lam) * lam**k / math.factorial(k)


def render_model_comparison_markdown(payload: Dict) -> str:
    summary = payload["summary"]
    dashboard = payload.get("model_dashboard", {})
    automation_view = payload.get("automation_view", {})
    compare = payload.get("old_new_compare") or {}
    lines = [
        f"# TAB FIFA Open-source Model Dashboard {payload['version']}",
        "",
        "本文件用于把开源模型和公开数据思想纳入本地研究系统：Elo/Dixon-Coles 作为独立交叉验证，goalmodel 与 penaltyblog 强化进球/盘口概率和赔率去水口径，socceraction 指向球员事件基本面，openfootball 指向赛程公开数据校验。它不直接自动下注。",
        "",
        "## Open-source Model Dashboard",
        "",
        f"- 决策定位：`{dashboard.get('decision', '')}`",
        f"- 比较比赛：`{dashboard.get('match_count', 0)}`；模型数量：`{dashboard.get('model_count', 0)}`",
        f"- 高分歧场次：`{dashboard.get('high_divergence_count', 0)}` / `{float(dashboard.get('high_divergence_ratio') or 0) * 100:.2f}%`",
        f"- 平均当前-Elo/DC分歧：`{float(dashboard.get('avg_disagreement') or 0) * 100:.2f}%`",
        f"- GitHub 源审计：`{dashboard.get('implemented_reference_count', 0)}/{dashboard.get('reference_count', 0)}` 已落地；source audit ready `{bool(dashboard.get('github_source_audit_ready'))}`",
        f"- 模型风险：{dashboard.get('model_risk', '')}",
        f"- 下一步：{dashboard.get('next_action', '')}",
        f"- Automation 角色：`{automation_view.get('automation_role', '')}`",
        "",
        "```mermaid",
        "pie showData",
        f'  "implemented GitHub refs" : {int(dashboard.get("implemented_reference_count") or 0)}',
        f'  "design refs" : {int(dashboard.get("design_reference_count") or 0)}',
        "```",
        "",
        "## Visual Summary",
        "",
        "### Model disagreement by match",
        "",
        mermaid_bar("Model disagreement by match", model_disagreement_items(payload.get("rows", [])), y_label="percentage points"),
        "",
        "### Consensus confidence mix",
        "",
        mermaid_pie("Consensus confidence mix", consensus_confidence_items(payload.get("rows", []))),
        "",
        "### Open-source capability coverage",
        "",
        mermaid_bar("Open-source capability coverage", source_coverage_items(payload.get("source_adoption", {})), y_label="reference count"),
        "",
        "### GitHub reference adoption mix",
        "",
        mermaid_pie("GitHub reference adoption mix", source_adoption_items(payload.get("source_adoption", {}))),
        "",
        "### Automation model gates",
        "",
        mermaid_bar("Automation model gates", automation_view_items(automation_view), y_label="score"),
        "",
        "## Automation 使用视角",
        "",
        f"- automation_view_ready: `{bool(automation_view.get('automation_view_ready'))}`",
        f"- scheduler_stage: {md(automation_view.get('scheduler_stage'))}",
        f"- fail_closed_policy: {md(automation_view.get('fail_closed_policy'))}",
        f"- manual_review_policy: {md(automation_view.get('manual_review_policy'))}",
        f"- prohibited_actions: {md('、'.join(automation_view.get('prohibited_actions') or []))}",
        "",
        "| Gate | Status | Evidence / Action |",
        "|---|---|---|",
    ]
    for row in automation_view.get("gates") or []:
        lines.append(f"| {md(row.get('gate'))} | {md(row.get('status'))} | {md(row.get('evidence'))} |")
    lines.extend(
        [
            "",
        "## References",
        "",
        "| Source | URL | Method | Status | Verified | Coverage | Reusable / UI Pattern | Report Usage |",
        "|---|---|---|---|---|---|---|---|",
        ]
    )
    for ref in payload["references"]:
        reusable = "; ".join((ref.get("reusable_features") or [])[:2])
        layout = "; ".join((ref.get("layout_patterns") or [])[:2])
        lines.append(
            f"| {ref['name']} | {ref.get('url', '')} | {ref.get('method_family', '')} | "
            f"{ref.get('adoption_status', '')} | {ref.get('verified_at', '')} | "
            f"{', '.join(ref.get('coverage', []))} | {reusable}; {layout} | {ref.get('report_usage', '')} |"
        )
    lines.extend(
        [
            "",
            "## GitHub Source Audit",
            "",
            "| Source | License | Adoption | Current Evidence | Dashboard Pattern |",
            "|---|---|---|---|---|",
        ]
    )
    for row in (payload.get("source_adoption") or {}).get("rows", []):
        current_evidence = "; ".join((row.get("github_evidence") or [])[-2:])
        pattern = "; ".join((row.get("layout_patterns") or [])[:3])
        lines.append(
            f"| {row.get('display_name', row.get('source', ''))} | {row.get('license', '')} | {row.get('adoption_status', '')} | {md(current_evidence)} | {md(pattern)} |"
        )
    if compare:
        lines.extend(
            [
                "",
                "## old_new_compare / 新旧模型变化",
                "",
                f"- compare_status: `{compare.get('status', '')}`",
                f"- previous_generated_at: `{compare.get('previous_generated_at', '')}`",
                f"- changed_count: `{compare.get('changed_count', 0)}/{compare.get('metric_count', 0)}`",
                f"- summary: {md(compare.get('summary'))}",
                "",
                "| 指标 | 当前 | 上一版 | 变化 |",
                "|---|---:|---:|---:|",
            ]
        )
        for row in compare.get("rows") or []:
            lines.append(f"| {md(row.get('metric'))} | {md(row.get('current'))} | {md(row.get('previous'))} | {md(row.get('delta'))} |")
    lines.extend(
        [
            "",
            "## Summary",
            "",
            f"- match_count: `{payload['match_count']}`",
            f"- ready: `{payload['ready']}`",
            f"- high_divergence_count: `{summary['high_divergence_count']}`",
            f"- avg_current_vs_elo_disagreement: `{summary['avg_current_vs_elo_disagreement']:.1%}`",
            "",
            "## Top Divergence",
            "",
            "| Match | Current Home | Elo-DC Home | Current Draw | Elo-DC Draw | Current Away | Elo-DC Away | Consensus |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["rows"][:12]:
        current = row["current_market_poisson"]
        elo = row["open_source_elo_dixon_coles"]
        lines.append(
            "| {match} | {ch:.1%} | {eh:.1%} | {cd:.1%} | {ed:.1%} | {ca:.1%} | {ea:.1%} | {consensus} ({confidence}) |".format(
                match=row["match"],
                ch=current["home_win"],
                eh=elo["home_win"],
                cd=current["draw"],
                ed=elo["draw"],
                ca=current["away_win"],
                ea=elo["away_win"],
                consensus=row["consensus"]["selection"],
                confidence=row["consensus"]["confidence"],
            )
        )
    return "\n".join(lines)


def md(value) -> str:
    return str(value or "").replace("|", "/").replace("\n", " ")


def model_comparison_pdf_rows(rows: List[Dict]) -> List[List[str]]:
    table_rows: List[List[str]] = []
    for row in rows[:12]:
        current = row.get("current_market_poisson", {})
        elo = row.get("open_source_elo_dixon_coles", {})
        consensus = row.get("consensus", {})
        disagreement = row.get("disagreement", {})
        table_rows.append(
            [
                str(row.get("match", "")),
                str(consensus.get("selection", "")),
                confidence_label(consensus.get("confidence", "")),
                percent(disagreement.get("max_abs_current_vs_elo_dc", 0)),
                probability_triple(current),
                probability_triple(elo),
            ]
        )
    return table_rows


def probability_triple(probabilities: Dict) -> str:
    return "{home}/{draw}/{away}".format(
        home=percent(probabilities.get("home_win", 0)),
        draw=percent(probabilities.get("draw", 0)),
        away=percent(probabilities.get("away_win", 0)),
    )


def confidence_label(value) -> str:
    return {
        "high": "高",
        "medium": "中",
        "low": "低",
    }.get(str(value or ""), str(value or ""))


def percent(value) -> str:
    return f"{float(value or 0) * 100:.2f}%"


def model_dashboard_items(dashboard: Dict) -> List[Tuple[str, float]]:
    return [
        ("matches", float(dashboard.get("match_count") or 0)),
        ("high divergence", float(dashboard.get("high_divergence_count") or 0)),
        ("GitHub refs", float(dashboard.get("reference_count") or 0)),
        ("implemented refs", float(dashboard.get("implemented_reference_count") or 0)),
    ]


def model_disagreement_items(rows: List[Dict]) -> List[Tuple[str, float]]:
    items = []
    for row in rows[:7]:
        disagreement = row.get("disagreement", {}).get("max_abs_current_vs_elo_dc", 0)
        items.append((row.get("match", "unknown"), float(disagreement or 0) * 100))
    return items


def consensus_confidence_items(rows: List[Dict]) -> List[Tuple[str, float]]:
    counts: Dict[str, int] = {}
    for row in rows:
        confidence = str(row.get("consensus", {}).get("confidence") or "unknown")
        counts[confidence] = counts.get(confidence, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def source_coverage_items(source_adoption: Dict) -> List[Tuple[str, float]]:
    coverage_counts = source_adoption.get("coverage_counts") or {}
    return sorted(
        ((str(label), float(count or 0)) for label, count in coverage_counts.items()),
        key=lambda item: (-item[1], item[0]),
    )[:8]


def source_adoption_items(source_adoption: Dict) -> List[Tuple[str, float]]:
    return [
        ("implemented proxy", float(source_adoption.get("implemented_reference_count") or 0)),
        ("design reference", float(source_adoption.get("design_reference_count") or 0)),
    ]


def automation_view_items(automation_view: Dict) -> List[Tuple[str, float]]:
    items: List[Tuple[str, float]] = []
    for row in automation_view.get("gates") or []:
        score = row.get("score")
        try:
            numeric_score = float(score)
        except (TypeError, ValueError):
            numeric_score = 0.0
        items.append((str(row.get("gate") or "gate"), numeric_score))
    return items
