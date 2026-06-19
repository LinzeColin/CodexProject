from __future__ import annotations

import json
import os
import re
import tempfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List
from xml.sax.saxutils import escape as xml_escape
from zoneinfo import ZoneInfo

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.platypus import Flowable, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from tab_research.bankroll import allocate_time_adjusted_stakes, build_bankroll_plan
from tab_research.boards import audit_portfolio, board_by_id
from tab_research.io import atomic_publish_file, atomic_write_json, single_instance_lock
from tab_research.model_compare import MODEL_COMPARISON_JSON
from tab_research.odds import parse_decimal_odds
from tab_research.raw_refresh import audit_raw_refresh
from tab_research.recommendations import apply_execution_stakes_to_portfolio_compare
from tab_research.safety import audit_safety, ensure_private_tree_permissions
from tab_research.paths import resolve_output_dir, resolve_private_dir, resolve_workspace_root
from tab_research.visuals import build_visual_summary, chart_by_id


ROOT = resolve_workspace_root(Path(__file__))
OUT = resolve_output_dir(Path(__file__))
PRIVATE_DATA_DIR = resolve_private_dir(Path(__file__))
REPORT_TZ = ZoneInfo(os.getenv("TAB_FIFA_REPORT_TZ", "Australia/Sydney"))
REPORT_DATE = os.getenv("TAB_FIFA_REPORT_DATE", datetime.now(REPORT_TZ).strftime("%d%m%Y"))
if not re.fullmatch(r"\d{8}", REPORT_DATE):
    raise ValueError("TAB_FIFA_REPORT_DATE must use DDMMYYYY digits only")
REPORT_DIR = Path(os.getenv("TAB_FIFA_REPORT_DIR", str(Path.home() / "Downloads" / "FIFA Report"))).expanduser()
PDF_PATH = REPORT_DIR / f"{REPORT_DATE}.pdf"
OUTPUT_COPY_PATH = OUT / f"{REPORT_DATE}.pdf"
BANKROLL_PLAN_PATH = OUT / f"tab_fifa_bankroll_plan_{REPORT_DATE}.json"
PRIVATE_BANKROLL_PLAN_PATH = PRIVATE_DATA_DIR / f"tab_fifa_bankroll_plan_{REPORT_DATE}.json"
LOCK_PATH = OUT / ".tab_fifa_daily_report.lock"
CODE_DIR = Path(__file__).resolve().parent
MATCHES_BOARD = board_by_id("world_cup_matches")
FUTURES_BOARD = board_by_id("world_cup_futures")
GROUP_BOARD = board_by_id("world_cup_group_betting")
AUSTRALIA_BOARD = board_by_id("world_cup_australia_markets")
TEAM_MULTI_BOARD = board_by_id("world_cup_team_futures_multi")
FONT_REGULAR = "STHeiti-Light-Local"
FONT_BOLD = "STHeiti-Medium-Local"


def load_json(name: str) -> Dict:
    return json.loads((OUT / name).read_text())


def load_private_json(name: str) -> Dict:
    path = PRIVATE_DATA_DIR / name
    if path.exists():
        return json.loads(path.read_text())
    return {}


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def aud(value: float) -> str:
    return f"AUD {value:,.0f}"


def aud_or_pending(value) -> str:
    return aud(value) if value is not None else "待同步"


def odds_or_pending(value) -> str:
    odds = parse_decimal_odds(value)
    return f"{odds:.2f}" if odds is not None else "待同步"


def text_or_pending(value) -> str:
    value = "" if value is None else str(value)
    return value if value else "待同步"


def report_display_date() -> str:
    if len(REPORT_DATE) == 8 and REPORT_DATE.isdigit():
        return f"{REPORT_DATE[:2]}/{REPORT_DATE[2:4]}/{REPORT_DATE[4:]}"
    return datetime.now(REPORT_TZ).strftime("%d/%m/%Y")


def days_to_first_match() -> int:
    first_match_date = datetime(2026, 6, 12, tzinfo=REPORT_TZ).date()
    report_date = datetime.strptime(REPORT_DATE, "%d%m%Y").date()
    return max(0, (first_match_date - report_date).days)


def resolve_portfolio_compare(portfolio_compare_override: Dict | None = None) -> Dict:
    if portfolio_compare_override is not None:
        return portfolio_compare_override
    return load_json("portfolio_daily_compare_latest.json") if (OUT / "portfolio_daily_compare_latest.json").exists() else {}


def para(text: str, style: ParagraphStyle) -> Paragraph:
    return Paragraph(pdf_escape(text).replace("\n", "<br/>"), style)


def table(rows: List[List], widths: List[float], header: bool = True, buy_action_col: int | None = None) -> Table:
    converted = []
    for row in rows:
        converted.append([
            cell if isinstance(cell, Flowable) or hasattr(cell, "getKeepWithNext") else Paragraph(pdf_escape(cell), STYLES["TableCell"])
            for cell in row
        ])
    tbl = Table(converted, colWidths=widths, repeatRows=1 if header else 0)
    style = [
        ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#D8DEE9")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]
    if header:
        style.extend(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#FBFCFE")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#172033")),
                ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD),
            ]
        )
    for idx in range(1 if header else 0, len(rows)):
        if idx % 2 == 0:
            style.append(("BACKGROUND", (0, idx), (-1, idx), colors.HexColor("#F5F7FA")))
        if buy_action_col is not None:
            action_text = plain_cell_text(rows[idx][buy_action_col])
            if "买入" in action_text:
                style.extend(
                    [
                        ("BACKGROUND", (buy_action_col, idx), (buy_action_col, idx), colors.HexColor("#C62828")),
                        ("TEXTCOLOR", (buy_action_col, idx), (buy_action_col, idx), colors.white),
                    ]
                )
    tbl.setStyle(TableStyle(style))
    return tbl


def plain_cell_text(cell) -> str:
    return cell.getPlainText() if hasattr(cell, "getPlainText") else str(cell)


def pdf_escape(value) -> str:
    return xml_escape("" if value is None else str(value), {"'": "&apos;", '"': "&quot;"})


def section(title: str) -> List:
    return [Spacer(1, 7 * mm), Paragraph(pdf_escape(title), STYLES["H2"]), Spacer(1, 3 * mm)]


def subsection(title: str) -> List:
    return [Spacer(1, 5 * mm), Paragraph(pdf_escape(title), STYLES["H3"]), Spacer(1, 2 * mm)]


def pdf_chart(chart: Dict, width: float = 88 * mm) -> Drawing:
    items = chart.get("items", [])[:7]
    row_height = 12
    title_height = 15
    note_height = 10 if chart.get("note") else 0
    height = max(36, title_height + len(items) * row_height + note_height + 5)
    drawing = Drawing(width, height)
    drawing.add(
        String(
            0,
            height - 10,
            pdf_truncate(chart.get("title") or chart.get("id") or "Chart", 28),
            fontName=FONT_BOLD,
            fontSize=8,
            fillColor=colors.HexColor("#0B1F3A"),
        )
    )
    if not items:
        drawing.add(
            String(0, height - 26, "暂无数据", fontName=FONT_REGULAR, fontSize=7, fillColor=colors.HexColor("#5F6B7A"))
        )
        return drawing
    label_width = width * 0.45
    bar_width = width * 0.36
    value_x = label_width + bar_width + 4
    for index, item in enumerate(items):
        y = height - title_height - (index + 1) * row_height
        fraction = max(0.0, min(1.0, float(item.get("bar_fraction") or 0)))
        drawing.add(
            String(
                0,
                y + 3,
                pdf_truncate(item.get("label"), 24),
                fontName=FONT_REGULAR,
                fontSize=6.4,
                fillColor=colors.HexColor("#172033"),
            )
        )
        drawing.add(Rect(label_width, y + 2, bar_width, 6, fillColor=colors.HexColor("#EEF2F6"), strokeColor=None))
        drawing.add(
            Rect(
                label_width,
                y + 2,
                bar_width * fraction,
                6,
                fillColor=colors.HexColor(str(item.get("color") or "#1F4E79")),
                strokeColor=None,
            )
        )
        drawing.add(
            String(
                value_x,
                y + 3,
                pdf_truncate(item.get("display"), 10),
                fontName=FONT_REGULAR,
                fontSize=6.4,
                fillColor=colors.HexColor("#5F6B7A"),
            )
        )
    if chart.get("note"):
        drawing.add(
            String(
                0,
                3,
                pdf_truncate(chart.get("note"), 48),
                fontName=FONT_REGULAR,
                fontSize=6.2,
                fillColor=colors.HexColor("#5F6B7A"),
            )
        )
    return drawing


CORE_VISUAL_IDS = [
    "board_readiness",
    "report_compare",
    "recommendation_distribution",
    "stake_allocation",
    "match_value",
    "odds_probability_edge",
]
MODEL_VISUAL_IDS = [
    "model_divergence",
    "model_consensus",
    "model_source_coverage",
    "model_capability_coverage",
]


def append_visual_dashboard_sections(story: List, visual_summary: List[Dict]) -> None:
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("可视化仪表盘摘要", STYLES["H3"]))
    story.append(Spacer(1, 2 * mm))
    story.append(visual_chart_table(visual_summary, CORE_VISUAL_IDS))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("开源模型与价值边际扩展图表", STYLES["H3"]))
    story.append(Spacer(1, 2 * mm))
    story.append(visual_chart_table(visual_summary, MODEL_VISUAL_IDS))


def visual_chart_table(visual_summary: List[Dict], chart_ids: List[str]) -> Table:
    rows = []
    for index in range(0, len(chart_ids), 2):
        left = chart_by_id(visual_summary, chart_ids[index])
        right = chart_by_id(visual_summary, chart_ids[index + 1]) if index + 1 < len(chart_ids) else {}
        rows.append([pdf_chart(left), pdf_chart(right)])
    return table(rows, [94 * mm, 94 * mm], header=False)


def pdf_truncate(value, length: int) -> str:
    text = "" if value is None else str(value)
    return text if len(text) <= length else text[: max(0, length - 3)] + "..."


def model_source_table(model_comparison: Dict) -> Table:
    adoption = model_comparison.get("source_adoption", {})
    rows = adoption.get("rows") or [
        {
            "source": ref.get("name", ""),
            "display_name": ref.get("display_name", ref.get("name", "")),
            "method_family": ref.get("method_family", ""),
            "adoption_status": ref.get("adoption_status", ""),
            "coverage": ref.get("coverage", []),
            "reusable_features": ref.get("reusable_features", []),
            "layout_patterns": ref.get("layout_patterns", []),
            "report_usage": ref.get("report_usage", ""),
        }
        for ref in model_comparison.get("references", [])
    ]
    table_rows = [["开源来源", "方法族", "状态", "覆盖", "可复用/UI启发", "本系统用途"]]
    for item in rows[:5]:
        reusable = "; ".join((item.get("reusable_features") or [])[:2])
        layouts = "; ".join((item.get("layout_patterns") or [])[:2])
        table_rows.append(
            [
                item.get("display_name") or short_source_name(item.get("source")),
                item.get("method_family", ""),
                source_status_label(item.get("adoption_status")),
                ", ".join(item.get("coverage") or []),
                reusable + (" / " if reusable and layouts else "") + layouts,
                item.get("report_usage", ""),
            ]
        )
    if len(table_rows) == 1:
        table_rows.append(["待同步", "待同步", "待同步", "待同步", "待同步", "暂无开源模型采用数据。"])
    return table(table_rows, [26 * mm, 31 * mm, 23 * mm, 33 * mm, 42 * mm, 35 * mm])


def append_model_audit_section(story: List, model_comparison: Dict) -> None:
    story.append(Spacer(1, 5 * mm))
    story.append(Paragraph("模型交叉验证审计", STYLES["H3"]))
    story.append(Spacer(1, 2 * mm))
    story.append(
        para(
            "本节把当前市场Poisson、Elo/Dixon-Coles 和 goalmodel xG 路径放在同一审计层。"
            "高分歧不等于禁止下注，但必须降低确定性评级，并进入人工复核或缩小仓位。",
            STYLES["Body"],
        )
    )
    story.append(model_audit_summary_table(model_comparison))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph("Top分歧比赛", STYLES["H3"]))
    story.append(Spacer(1, 2 * mm))
    story.append(model_top_divergence_table(model_comparison))


def model_audit_summary_table(model_comparison: Dict) -> Table:
    summary = model_comparison.get("summary", {}) if isinstance(model_comparison, dict) else {}
    source_adoption = model_comparison.get("source_adoption", {}) if isinstance(model_comparison, dict) else {}
    return table(
        [
            ["指标", "当前值", "用途"],
            ["比较比赛", str(model_comparison.get("match_count", 0) if isinstance(model_comparison, dict) else 0), "与TAB比赛盘口逐场对照，缺失时不把模型共识当作下注依据。"],
            ["高分歧场次", str(summary.get("high_divergence_count", 0)), "当前模型与Elo/DC差异超过10个百分点时，自动降低结论确定性。"],
            ["平均当前-Elo/DC分歧", pct(float(summary.get("avg_current_vs_elo_disagreement") or 0)), "衡量盘口反推模型与开源强弱先验的整体冲突程度。"],
            [
                "开源参考源",
                f"{source_adoption.get('reference_count', len(model_comparison.get('references', [])) if isinstance(model_comparison, dict) else 0)}个 / 已落地{source_adoption.get('implemented_reference_count', 0)}个",
                "Hicruben用于Elo/DC/Monte Carlo参考；goalmodel用于xG到1X2/OU/BTTS；RyanSCodes用于时间衰减和攻防参数参考。",
            ],
        ],
        [36 * mm, 38 * mm, 116 * mm],
    )


def model_top_divergence_table(model_comparison: Dict) -> Table:
    rows = [["比赛", "共识注", "信心", "最大分歧", "当前模型1X2", "Elo/Dixon-Coles 1X2", "操作含义"]]
    for row in (model_comparison.get("rows", []) if isinstance(model_comparison, dict) else [])[:6]:
        consensus = row.get("consensus", {})
        disagreement = row.get("disagreement", {})
        rows.append(
            [
                row.get("match", ""),
                consensus.get("selection", ""),
                confidence_label(consensus.get("confidence", "")),
                pct(float(disagreement.get("max_abs_current_vs_elo_dc") or 0)),
                model_probability_triple(row.get("current_market_poisson", {})),
                model_probability_triple(row.get("open_source_elo_dixon_coles", {})),
                "人工复核/缩小仓位" if disagreement.get("high_divergence") else "可作为交叉验证支持",
            ]
        )
    if len(rows) == 1:
        rows.append(["待同步", "待同步", "待同步", "待同步", "待同步", "待同步", "模型对比数据缺失，不进入执行依据。"])
    return table(rows, [30 * mm, 22 * mm, 15 * mm, 18 * mm, 28 * mm, 32 * mm, 42 * mm])


def model_probability_triple(probabilities: Dict) -> str:
    return "{home}/{draw}/{away}".format(
        home=pct(float(probabilities.get("home_win") or 0)),
        draw=pct(float(probabilities.get("draw") or 0)),
        away=pct(float(probabilities.get("away_win") or 0)),
    )


def confidence_label(value) -> str:
    return {
        "high": "高",
        "medium": "中",
        "low": "低",
    }.get(str(value or ""), str(value or ""))


def source_status_label(value) -> str:
    return {
        "implemented_proxy": "已接入",
        "design_reference": "设计参考",
    }.get(str(value or ""), str(value or ""))


def short_source_name(value) -> str:
    text = str(value or "")
    return text.split("/", 1)[-1] if "/" in text else text


def recommendation_counts_for_pdf(payloads: List[tuple[str, Dict]]) -> List[Dict]:
    counts = []
    for name, payload in payloads:
        recommendations = payload.get("recommendations", [])
        counts.append(
            {
                "name": name,
                "count": len(recommendations),
                "stake_aud": sum(float(item.get("stake_aud") or 0) for item in recommendations),
            }
        )
    return counts


def top_match_candidates(matches: Dict) -> List[Dict]:
    preferred = [
        "Netherlands v Japan|Result|Japan",
        "Brazil v Morocco|Result|Morocco",
        "France v Senegal|Result|Senegal",
        "England v Croatia|Result|Croatia",
        "Belgium v Egypt|Total Goals Over/Under|Under 2.5 Goals",
    ]
    keyed = {f"{item['match']}|{item['market']}|{item['selection']}": item for item in matches["recommendations"]}
    selected = [keyed[key] for key in preferred if key in keyed]
    selected_keys = {f"{item['match']}|{item['market']}|{item['selection']}" for item in selected}
    for item in matches["recommendations"]:
        key = f"{item['match']}|{item['market']}|{item['selection']}"
        if key not in selected_keys:
            selected.append(item)
            selected_keys.add(key)
        if len(selected) == 5:
            break
    return selected[:5]


def top_futures_candidates(futures: Dict, team_multi: Dict) -> List[Dict]:
    rows = []
    for item in futures["recommendations"]:
        rows.append(
            {
                "market_group": "World Cup Futures",
                "board": "Futures",
                "selection": f"{item['team']} - {item['market']}",
                "odds": item["odds"],
                "probability": item["no_vig_probability"],
                "method": "48-team no-vig path",
                "action": "观察/不下注",
                "stake": "AUD 0 / 0u",
                "reason": item["rationale"],
            }
        )
    for item in team_multi["recommendations"]:
        rows.append(
            {
                "market_group": "Team Futures Multi",
                "board": "Team Futures Multi",
                "selection": f"{item['team']} - {item['market']}",
                "odds": item["odds"],
                "probability": item["no_vig_probability"],
                "method": "14-team subset no-vig",
                "action": "观察/不下注",
                "stake": "AUD 0 / 0u",
                "reason": item["rationale"],
            }
        )
    preferred = [
        "Belgium - To Qualify for Quarter Final",
        "Colombia - To Qualify for Quarter Final",
        "Japan - To Qualify for Quarter Final",
        "Morocco - To Qualify for Quarter Final",
        "Croatia - To Qualify for Quarter Final",
    ]
    by_selection = {item["selection"]: item for item in rows}
    return [by_selection[name] for name in preferred if name in by_selection][:5]


def top_group_candidates(group: Dict) -> List[Dict]:
    return [
        {
            "selection": f"Group {item['group']} - {item['team']} Winner",
            "odds": item["odds"],
            "probability": item["no_vig_probability"],
            "action": "观察/不下注",
            "stake": "AUD 0 / 0u",
            "reason": item["rationale"],
        }
        for item in group["recommendations"][:5]
    ]


def top_australia_candidates(australia: Dict) -> List[Dict]:
    priority = [
        ("Team Total Group Goals Scored O/U", "AUS Under 3.5 Group Gls"),
        ("AUS Concede In Every Group Match", "AUS Concede Every Grp Match"),
        ("Team Total Group Goals Conceded O/U", "AUS Concede Under 5.5 Grp Gls"),
        ("AUS Group Point O/U", "AUS Over 2.5 Grp Pts"),
        ("AUS Group Exact Finishing Position", "AUS 4th In Grp D"),
    ]
    indexed = {}
    for market in australia["markets"]:
        for row in market["rows"]:
            indexed[(market["market"], row["selection"])] = {
                "market": market["market"],
                "selection": row["selection"],
                "odds": row["odds"],
                "probability": row.get("probability", 0),
                "method": market.get("probability_method", ""),
            }
    return [
        {
            **indexed[key],
            "action": "观察/不下注",
            "stake": "AUD 0 / 0u",
            "reason": australia_reason(key[0], key[1]),
        }
        for key in priority
        if key in indexed
    ]


def australia_reason(market: str, selection: str) -> str:
    reasons = {
        "Team Total Group Goals Scored O/U": "价格方向与低进球预期一致，但需逐场xG模型确认，不宜单靠盘口概率下注。",
        "AUS Concede In Every Group Match": "方向符合Group D防守压力，但该盘口只有单边价格，无法完整评估水位。",
        "Team Total Group Goals Conceded O/U": "低于5.5失球具备概率优势，但仍受美国/土耳其比赛节奏影响。",
        "AUS Group Point O/U": "超过2.5分说明至少一胜或多平，需等首发和赛前价格变化。",
        "AUS Group Exact Finishing Position": "第四名方向符合盘口排序，但赔率未显示足够价值边际。",
    }
    return reasons.get(market, f"{selection}进入观察池，当前不下注。")


def match_stake_summary(match_top: List[Dict]) -> List[Dict]:
    return [
        {
            "match": item["match"],
            "market": item["market"],
            "selection": item["selection"],
            "odds": item["odds"],
            "model_probability": item["model_probability"],
            "expected_value": item["expected_value"],
            "base_stake_aud": item["base_stake_aud"],
            "time_adjusted_stake_aud": item["time_adjusted_stake_aud"],
            "time_adjusted_stake_unit": item["time_adjusted_stake_unit"],
        }
        for item in match_top
    ]


def render_pdf(
    portfolio_compare_override: Dict | None = None,
    public_pdf_path: Path | None = None,
    public_bankroll_path: Path | None = None,
    private_pdf_path: Path | None = None,
    publish_private_pdf: bool = False,
) -> Dict:
    public_pdf_path = Path(public_pdf_path or OUTPUT_COPY_PATH)
    public_bankroll_path = Path(public_bankroll_path or BANKROLL_PLAN_PATH)
    ensure_private_tree_permissions(PRIVATE_DATA_DIR)
    matches = load_json(MATCHES_BOARD.recommendations_artifact)
    futures = load_json(FUTURES_BOARD.recommendations_artifact)
    groups = load_json(GROUP_BOARD.recommendations_artifact)
    australia = load_json(AUSTRALIA_BOARD.recommendations_artifact)
    team_multi = load_json(TEAM_MULTI_BOARD.recommendations_artifact)
    raw_refresh = audit_raw_refresh(OUT)
    portfolio = audit_portfolio(OUT)
    safety = audit_safety(CODE_DIR, OUT, private_dir=PRIVATE_DATA_DIR, allow_private_positions=True)
    assert_pdf_input_gates(matches, futures, groups, australia, team_multi, portfolio, safety, raw_refresh)
    matches_gate = matches.get("automation_gate", {})
    my_bets = load_private_json(f"tab_my_bets_positions_{REPORT_DATE}.json")
    position_summary = my_bets.get("summary", {})
    positions_ready = bool(position_summary and position_summary.get("bet_count") is not None)
    if positions_ready and position_summary.get("unknown_status_count", 0):
        raise RuntimeError(
            "Private position snapshot contains unknown settlement statuses; refusing to publish execution PDF until status mapping is updated."
        )
    placed_stake = position_summary.get("total_stake_aud") if positions_ready else None

    base_match_top = top_match_candidates(matches)
    futures_top = top_futures_candidates(futures, team_multi)
    group_top = top_group_candidates(groups)
    australia_top = top_australia_candidates(australia)
    australia_market_count = len(australia.get("markets", []))
    australia_price_count = sum(len(market.get("rows", [])) for market in australia.get("markets", []))
    timing_text = f"T-{days_to_first_match()}天左右，阵容/伤停仍会变化"

    base_match_exposure = sum(item["stake_aud"] for item in base_match_top)
    bankroll_plan = build_bankroll_plan(
        position_summary if positions_ready else {},
        base_candidate_exposure_aud=base_match_exposure if positions_ready else 0,
        unit_aud=40,
    )
    private_match_top = allocate_time_adjusted_stakes(base_match_top, bankroll_plan.current_window_target_aud, unit_aud=40)
    private_primary_exposure = sum(item["time_adjusted_stake_aud"] for item in private_match_top)

    # Public artifacts must not change when private My Bets snapshots change.
    # They keep a model-only execution view; private position-aware amounts stay
    # in the private bankroll summary/PDF path.
    public_bankroll_plan = build_bankroll_plan(
        {},
        base_candidate_exposure_aud=base_match_exposure,
        unit_aud=40,
    )
    public_match_top = allocate_time_adjusted_stakes(base_match_top, public_bankroll_plan.current_window_target_aud, unit_aud=40)
    public_primary_exposure = sum(item["time_adjusted_stake_aud"] for item in public_match_top)
    match_candidate_count = len(private_match_top)
    match_coverage = matches_gate.get("coverage", {})
    detail_coverage = match_coverage.get("detail_main_markets", {})
    full_coverage = match_coverage.get("full_main_markets", {})
    match_coverage_text = (
        f"{detail_coverage.get('covered', 0)}/{detail_coverage.get('total', 0)} detail; "
        f"{full_coverage.get('covered', 0)}/{full_coverage.get('total', 0)} full core"
    )
    model_comparison = load_json(MODEL_COMPARISON_JSON) if (OUT / MODEL_COMPARISON_JSON).exists() else {}
    portfolio_compare = apply_execution_stakes_to_portfolio_compare(
        resolve_portfolio_compare(portfolio_compare_override),
        public_match_top,
    )
    compare = portfolio_compare or matches.get("daily_compare", {})
    compare_summary = compare.get("summary", {}) if isinstance(compare, dict) else {}
    normalized_compare_summary = {
        "added_count": int(compare_summary.get("added_count") or 0),
        "removed_count": int(compare_summary.get("removed_count") or 0),
        "changed_count": int(compare_summary.get("changed_count") or 0),
        "retained_count": int(compare_summary.get("retained_count") or 0),
        "exposure_change_aud": float(compare_summary.get("exposure_change_aud") or 0),
    }
    visual_summary = build_visual_summary(
        board_statuses=portfolio.get("board_statuses", []),
        compare_summary=normalized_compare_summary,
        recommendation_counts=recommendation_counts_for_pdf(
            [
                ("Matches", {"recommendations": public_match_top}),
                ("Futures", futures),
                ("Group Betting", groups),
                ("Australia Markets", australia),
                ("Team Futures Multi", team_multi),
            ]
        ),
        match_recommendations=public_match_top[:7],
        model_rows=model_comparison.get("rows", [])[:7],
        model_references=model_comparison.get("references", []),
    )
    report_summary = {
        "report_date": REPORT_DATE,
        "pdf_path": str(public_pdf_path),
        "pdf_output_copy": str(public_pdf_path),
        "private_pdf_available": bool(publish_private_pdf),
        "private_pdf_path_omitted": True,
        "positions_ready": positions_ready,
        "base_selected_exposure_aud": round(base_match_exposure, 2),
        "time_adjusted_new_exposure_aud": round(public_primary_exposure, 2),
        "private_time_adjusted_new_exposure_aud": round(private_primary_exposure, 2),
        "bankroll_plan": asdict(bankroll_plan),
        "public_bankroll_plan": asdict(public_bankroll_plan),
        "match_stakes": match_stake_summary(public_match_top),
        "private_match_stakes": match_stake_summary(private_match_top),
    }
    public_summary = public_bankroll_summary(report_summary)
    story = []
    story.append(Paragraph("TAB FIFA 2026 盘口下注研究分析报告", STYLES["ReportTitle"]))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("专业盘口研究报告", STYLES["Subtitle"]))
    story.append(Spacer(1, 8 * mm))
    story.append(
        table(
            [
                ["报告日期", report_display_date()],
                ["数据来源", "TAB FIFA 只读盘口快照 + FIFA公开源 + 新闻事件监控"],
                ["预算假设", "总预算 AUD 3000-5000；模型中位预算 AUD 4000；1u = AUD 40"],
                ["已有投入", aud_or_pending(placed_stake)],
                ["本报告新增主执行仓位", f"{aud(private_primary_exposure)} / {private_primary_exposure / 40:.2f}u"],
                ["组合自动化状态", f"{portfolio['ready_required_board_count']}/{portfolio['required_board_count']} ready; 比赛盘口 {match_coverage_text}"],
            ],
            [45 * mm, 135 * mm],
            header=False,
        )
    )
    story.extend(section("一、执行摘要"))
    story.append(
        para(
            "本报告按4类市场组织：比赛盘口、长线/晋级盘口、小组盘口、澳大利亚专题盘口。"
            "每类市场只筛选1-5个最值得关注的候选，并给出明确操作行为。"
            + ("当前只有比赛盘口存在可执行仓位；其他市场均进入观察池，不建议立即下注。" if positions_ready else "持仓未同步时执行金额自动归零，只保留研究观察结论。")
            + (
                f"本次已读取TAB私有持仓：{position_summary.get('bet_count', 0)}笔已下注，"
                f"未结算持仓{aud(position_summary.get('open_stake_aud', 0))}。"
                if position_summary
                else "本次未读取到实际已下注明细，因此不伪造收益数据。"
            ),
            STYLES["Body"],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        table(
            [
                ["市场类别", "覆盖范围", "筛选候选", "操作结论", "新增金额"],
                ["比赛盘口", f"26场小组赛主盘口；{match_coverage_text}", f"{match_candidate_count}个主执行候选", "动态仓位买入" if positions_ready else "待同步/不执行", f"{aud(private_primary_exposure)}"],
                ["长线/晋级盘口", "48队Futures + 14队Team Futures Multi", f"{len(futures_top)}个观察候选", "不下注，等待路径模型", "AUD 0"],
                ["小组盘口", "12个小组Winner核心盘口", f"{len(group_top)}个观察候选", "不下注，等待逐场模拟", "AUD 0"],
                ["澳大利亚专题盘口", f"{australia_market_count}/{australia_market_count}盘口，{australia_price_count}个价格项", f"{len(australia_top)}个观察候选", "不下注，等待赛前模型确认", "AUD 0"],
            ],
            [32 * mm, 53 * mm, 35 * mm, 45 * mm, 22 * mm],
            buy_action_col=3,
        )
    )
    if portfolio_compare.get("by_board"):
        story.append(Spacer(1, 3 * mm))
        story.append(
            table(
                [["板块", "新增", "移除", "变化", "保留", "金额变化"]]
                + [
                    [
                        str(board.get("board_name", board_id)).replace("2026 World Cup ", ""),
                        board.get("added_count", 0),
                        board.get("removed_count", 0),
                        board.get("changed_count", 0),
                        board.get("retained_count", 0),
                        aud(board.get("exposure_change_aud", 0)),
                    ]
                    for board_id, board in portfolio_compare.get("by_board", {}).items()
                ],
                [45 * mm, 18 * mm, 18 * mm, 18 * mm, 18 * mm, 30 * mm],
            )
        )
    append_visual_dashboard_sections(story, visual_summary)
    append_model_audit_section(story, model_comparison)
    story.append(Spacer(1, 3 * mm))
    story.append(model_source_table(model_comparison))

    story.extend(section("二、持仓与收益监控"))
    if position_summary:
        realized_roi = position_summary.get("realized_roi", 0)
        potential_roi = (
            position_summary.get("potential_profit_if_all_win_aud", 0) / position_summary.get("open_stake_aud", 1)
            if position_summary.get("open_stake_aud", 0)
            else 0
        )
        story.append(
            table(
                [
                    ["项目", "当前值", "说明"],
                    ["已下注持仓金额", aud(position_summary.get("total_stake_aud", 0)), f"{position_summary.get('bet_count', 0)}笔TAB已下注记录。"],
                    ["未结算持仓金额", aud(position_summary.get("open_stake_aud", 0)), f"{position_summary.get('pending_count', 0)}笔Pending，结果未结算。"],
                    ["已实现盈亏", aud(position_summary.get("realized_pnl_aud", 0)), realized_pnl_note(position_summary)],
                    ["当前累计收益率", pct(realized_roi), "已实现口径：已实现盈亏 / 已结算投注金额；未结算投注不提前计入。"],
                    ["未结算最高潜在返还", aud(position_summary.get("estimated_return_if_all_win_aud", 0)), "仅表示全部未结算投注都命中时的返还，不代表预测收益。"],
                    ["未结算最高潜在毛利", f"{aud(position_summary.get('potential_profit_if_all_win_aud', 0))} / {pct(potential_roi)}", "未结算潜在毛利 = 预计返还 - stake。"],
                ],
                [45 * mm, 42 * mm, 103 * mm],
            )
        )
    else:
        story.append(
            table(
                [
                    ["项目", "当前值", "说明"],
                    ["已下注持仓金额", "待同步", "需要读取 TAB 私有持仓或导入已下注明细后计算。"],
                    ["未结算持仓金额", "待同步", "按未结算投注 stake 汇总。"],
                    ["已实现盈亏", "待同步", "按已结算投注返回金额减 stake 计算。"],
                    ["当前累计收益率", "待同步", "累计收益率 = 已实现盈亏 / 累计已下注金额。"],
                ],
                [45 * mm, 35 * mm, 110 * mm],
            )
        )

    story.extend(section("三、资金时间效应模型"))
    story.append(
        para(
            "资金使用按时间滚动，而不是静态锁死预算。前面已下注盘口结算后，胜利会释放本金并增加余额，失败会降低后续可用本金；"
            + (
                "因此当前窗口不应因为后面还有比赛就过度压低仓位。当前执行上限按中位预算AUD 4,000、未结算持仓和未投入预算共同计算。"
                if positions_ready
                else "但本次未读取到私有持仓快照，因此资金模型 fail-closed：不生成新增执行金额。"
            ),
            STYLES["Body"],
        )
    )
    story.append(
        table(
            [
                ["项目", "金额/比例", "含义"],
                ["预算区间", f"{aud(bankroll_plan.budget_min_aud)} - {aud(bankroll_plan.budget_max_aud)}", "按你给出的总预算区间建模，中位预算为AUD 4,000。"],
                ["未结算持仓", aud(bankroll_plan.open_stake_aud) if positions_ready else "待同步", "已经下注但尚未结算，会随赛果转化为返还或亏损。"],
                ["当前未投入预算", f"{aud(bankroll_plan.uncommitted_min_aud)} / {aud(bankroll_plan.uncommitted_mid_aud)} / {aud(bankroll_plan.uncommitted_max_aud)}", "分别对应总预算AUD 3,000 / 4,000 / 5,000。"],
                ["本窗口执行目标", f"{aud(bankroll_plan.current_window_target_aud)} / {bankroll_plan.current_window_target_unit:.2f}u", "仅在持仓同步且预算未满时使用当前窗口预算；缺持仓或满仓时归零。"],
                ["Pending+新增总暴露", f"{aud(bankroll_plan.total_pending_plus_new_aud)} / {pct(bankroll_plan.total_pending_plus_new_pct_mid)}", "按中位预算口径衡量已下注Pending加本次新增后的总占用。"],
            ],
            [42 * mm, 48 * mm, 100 * mm],
        )
    )
    story.append(Spacer(1, 3 * mm))
    story.append(
        table(
            [
                ["结算情景", "中位余额", "后续策略含义"],
                ["当前Pending全输", aud(bankroll_plan.lose_all_balance_mid_aud), "后续预算进入防守模式，只保留高EV盘口，降低单注上限。"],
                ["当前Pending仅返还本金", aud(bankroll_plan.stake_return_balance_mid_aud), "后续恢复到中位预算，按正常窗口继续筛选价值盘口。"],
                ["当前Pending全部命中", aud(bankroll_plan.win_all_balance_mid_aud), f"余额增加，未结算持仓最高潜在收益率为{pct(bankroll_plan.win_all_roi_on_open_stake)}，下一轮可提高但不追涨。"],
            ],
            [42 * mm, 32 * mm, 116 * mm],
        )
    )

    story.extend(section("四、已下注明细监控"))
    rows = [["时间", "注名", "盘口", "金额", "赔率", "预计返还", "状态", "监控结论"]]
    if my_bets.get("bets"):
        for bet in my_bets["bets"]:
            rows.append(
                [
                    text_or_pending(bet.get("placed_at_text")),
                    text_or_pending(bet.get("selection")),
                    text_or_pending(bet.get("market") or bet.get("bet_type")),
                    aud_or_pending(bet.get("stake_aud")),
                    odds_or_pending(bet.get("odds")),
                    aud_or_pending(bet.get("estimated_return_aud")),
                    text_or_pending(bet.get("status")),
                    position_monitoring_note(bet),
                ]
            )
    else:
        rows.append(["待同步", "待同步", "需要读取TAB私有持仓", "待同步", "待同步", "待同步", "待同步", "未读取到持仓明细时不生成虚假收益。"])
    story.append(table(rows, [24 * mm, 28 * mm, 36 * mm, 18 * mm, 14 * mm, 22 * mm, 17 * mm, 31 * mm]))

    story.extend(section("五、主执行下注建议：比赛盘口"))
    story.append(
        para(
            f"仓位原则：当前距首批比赛仍有阵容与伤停不确定性，但资金按时间滚动，不能只为了等待后续比赛而把当前价值盘口压到过低。"
            f"建议执行下表{match_candidate_count}个候选，总额控制在{aud(private_primary_exposure)}；其余低边际盘口暂不放入主执行单。",
            STYLES["Body"],
        )
    )
    rows = [["盘口", "操作", "金额", "概率", "赔率", "EV", "判断依据"]]
    for item in private_match_top:
        rows.append(
            [
                f"{item['match']} / {item['market']} / {item['selection']}",
                "动态仓位买入" if item["time_adjusted_stake_aud"] > 0 else "观察",
                f"{aud(item['time_adjusted_stake_aud'])} / {item['time_adjusted_stake_unit']:.2f}u",
                pct(item["model_probability"]),
                f"{item['odds']:.2f}",
                pct(item["expected_value"]),
                chinese_match_reason(item),
            ]
        )
    story.append(table(rows, [42 * mm, 20 * mm, 24 * mm, 18 * mm, 16 * mm, 17 * mm, 50 * mm], buy_action_col=1))

    story.extend(section("六、观察不下注：长线/晋级盘口"))
    story.append(
        para(
            "长线盘口会锁定资金到淘汰赛阶段，且强依赖抽签路径、轮换和伤停。当前筛选出5个方向用于跟踪，金额为0。",
            STYLES["Body"],
        )
    )
    rows = [["盘口", "赔率", "概率", "操作", "金额", "原因"]]
    for item in futures_top:
        rows.append([item["selection"], f"{item['odds']:.2f}", pct(item["probability"]), item["action"], item["stake"], chinese_futures_reason(item["selection"])])
    story.append(table(rows, [48 * mm, 18 * mm, 20 * mm, 24 * mm, 22 * mm, 57 * mm]))

    story.extend(section("七、观察不下注：小组盘口"))
    rows = [["盘口", "赔率", "概率", "操作", "金额", "原因"]]
    for item in group_top:
        rows.append([item["selection"], f"{item['odds']:.2f}", pct(item["probability"]), item["action"], item["stake"], chinese_group_reason(item["selection"])])
    story.append(table(rows, [48 * mm, 18 * mm, 20 * mm, 24 * mm, 22 * mm, 57 * mm]))

    story.extend(section("八、观察不下注：澳大利亚专题盘口"))
    story.append(
        para(
            "Australia Markets已经展开全部14个盘口。以下5个是概率/解释性较强的方向，但当前均未形成足够价值边际，结论为不下注。",
            STYLES["Body"],
        )
    )
    rows = [["盘口", "赔率", "概率", "方法", "操作", "金额", "原因"]]
    for item in australia_top:
        rows.append(
            [
                f"{item['market']} / {item['selection']}",
                f"{item['odds']:.2f}",
                pct(item["probability"]),
                item["method"],
                item["action"],
                item["stake"],
                item["reason"],
            ]
        )
    story.append(table(rows, [42 * mm, 15 * mm, 18 * mm, 30 * mm, 22 * mm, 20 * mm, 42 * mm]))

    story.extend(section("九、资金与时间执行结论"))
    story.append(
        table(
            [
                ["阶段", "时间判断", "操作"],
                ["当前", timing_text, f"执行比赛盘口主候选，新增{aud(private_primary_exposure)}；金额来自时间效应预算上限，不是固定小仓。"],
                ["第一批比赛结算后", "Mexico/Spain/Germany等已下注盘口会先影响余额", "用实际结算结果重算可用本金；赢则释放并增加后续预算，输则降低后续预算上限。"],
                ["赛前48小时", "首发、训练、伤停新闻清晰后", "重新跑报告；若赔率与模型边际仍在，按更新后的余额情景决定是否加仓。"],
                ["赛前24小时", "临场价格与阵容确认", "取消受伤停冲击的候选；不追短赔，也不因余额增加而无条件放大。"],
                ["预算控制", f"你已投入{aud_or_pending(placed_stake)}，当前窗口目标{aud(private_primary_exposure)}", "后续预算由真实赛果驱动，而不是预先把剩余预算静态锁死。"],
            ],
            [30 * mm, 55 * mm, 104 * mm],
        )
    )

    story.extend(section("十、风险控制"))
    story.append(
        para(
            "本报告不是收益保证。当前推荐集中在underdog和低比分方向，波动较高。"
            "Brazil/Morocco同时出现Morocco胜和Under 2.5，相关性较高，不应按独立风险处理。"
            "若赛前出现关键伤停、轮换或赔率大幅下调，应取消或降低对应仓位。",
            STYLES["Body"],
        )
    )

    actual_private_pdf_path = Path(private_pdf_path) if private_pdf_path else PRIVATE_DATA_DIR / f"{REPORT_DATE}.private.pdf"
    if publish_private_pdf:
        publish_pdf(story, actual_private_pdf_path)
        try:
            actual_private_pdf_path.chmod(0o600)
        except OSError:
            pass
        report_summary["private_pdf_available"] = True
    public_story = public_report_story(
        portfolio=portfolio,
        match_top=public_match_top,
        futures_top=futures_top,
        group_top=group_top,
        australia_top=australia_top,
        primary_exposure=public_primary_exposure,
        match_coverage_text=match_coverage_text,
        australia_market_count=australia_market_count,
        australia_price_count=australia_price_count,
        visual_summary=visual_summary,
        portfolio_compare=portfolio_compare,
        model_comparison=model_comparison,
    )
    publish_pdf(public_story, public_pdf_path)
    OUT.mkdir(parents=True, exist_ok=True)
    PRIVATE_DATA_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_json(PRIVATE_BANKROLL_PLAN_PATH, report_summary)
    atomic_write_json(public_bankroll_path, public_summary)
    return report_summary


def publish_pdf(story: List, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    tmp_pdf_handle = tempfile.NamedTemporaryFile(
        prefix=f".{destination.stem}.",
        suffix=".pdf.tmp",
        dir=destination.parent,
        delete=False,
    )
    tmp_pdf_path = Path(tmp_pdf_handle.name)
    tmp_pdf_handle.close()
    doc = SimpleDocTemplate(
        str(tmp_pdf_path),
        pagesize=A4,
        rightMargin=14 * mm,
        leftMargin=14 * mm,
        topMargin=14 * mm,
        bottomMargin=14 * mm,
        title="TAB FIFA 2026 盘口下注研究分析报告",
        author="Codex Research Pipeline",
    )
    try:
        doc.build(story, onFirstPage=footer, onLaterPages=footer)
        atomic_publish_file(tmp_pdf_path, destination)
    except Exception:
        tmp_pdf_path.unlink(missing_ok=True)
        raise


def public_report_story(
    portfolio: Dict,
    match_top: List[Dict],
    futures_top: List[Dict],
    group_top: List[Dict],
    australia_top: List[Dict],
    primary_exposure: float,
    match_coverage_text: str,
    australia_market_count: int,
    australia_price_count: int,
    visual_summary: List[Dict],
    portfolio_compare: Dict,
    model_comparison: Dict,
) -> List:
    match_action = "动态仓位买入" if primary_exposure > 0 else "观察/不执行"
    story = [
        Paragraph("TAB FIFA 2026 盘口下注研究分析报告（公开脱敏副本）", STYLES["ReportTitle"]),
        Spacer(1, 4 * mm),
        Paragraph("公开脱敏研究副本", STYLES["Subtitle"]),
        Spacer(1, 8 * mm),
        table(
            [
                ["报告日期", report_display_date()],
                ["数据来源", "TAB FIFA 只读盘口快照 + FIFA公开源 + 新闻事件监控"],
                ["公开副本说明", "不包含逐笔已下注明细、账户路径、私有持仓明细；完整私有报告仅保存在本机私有目录。"],
                ["本报告新增主执行仓位", f"{aud(primary_exposure)} / {primary_exposure / 40:.2f}u"],
                ["组合自动化状态", f"{portfolio['ready_required_board_count']}/{portfolio['required_board_count']} ready; 比赛盘口 {match_coverage_text}"],
            ],
            [45 * mm, 135 * mm],
            header=False,
        ),
    ]
    story.extend(section("一、公开摘要"))
    story.append(
        para(
            "本副本用于公开输出归档，只保留研究结论、候选盘口、金额建议和风险控制；"
            "不读取、不推导、不展示 TAB 私有持仓状态；持仓监控仅进入本机私有产物。",
            STYLES["Body"],
        )
    )
    story.append(
        table(
            [
                ["市场类别", "覆盖范围", "筛选候选", "操作结论", "新增金额"],
                ["比赛盘口", f"26场小组赛主盘口；{match_coverage_text}", f"{len(match_top)}个主执行候选", match_action, aud(primary_exposure)],
                ["长线/晋级盘口", "48队Futures + 14队Team Futures Multi", f"{len(futures_top)}个观察候选", "不下注，等待路径模型", "AUD 0"],
                ["小组盘口", "12个小组Winner核心盘口", f"{len(group_top)}个观察候选", "不下注，等待逐场模拟", "AUD 0"],
                ["澳大利亚专题盘口", f"{australia_market_count}/{australia_market_count}盘口，{australia_price_count}个价格项", f"{len(australia_top)}个观察候选", "不下注，等待赛前模型确认", "AUD 0"],
            ],
            [32 * mm, 53 * mm, 35 * mm, 45 * mm, 22 * mm],
            buy_action_col=3,
        )
    )
    if portfolio_compare.get("by_board"):
        story.append(Spacer(1, 3 * mm))
        story.append(
            table(
                [["板块", "新增", "移除", "变化", "保留", "金额变化"]]
                + [
                    [
                        str(board.get("board_name", board_id)).replace("2026 World Cup ", ""),
                        board.get("added_count", 0),
                        board.get("removed_count", 0),
                        board.get("changed_count", 0),
                        board.get("retained_count", 0),
                        aud(board.get("exposure_change_aud", 0)),
                    ]
                    for board_id, board in portfolio_compare.get("by_board", {}).items()
                ],
                [45 * mm, 18 * mm, 18 * mm, 18 * mm, 18 * mm, 30 * mm],
            )
        )
    append_visual_dashboard_sections(story, visual_summary)
    append_model_audit_section(story, model_comparison)
    story.append(Spacer(1, 3 * mm))
    story.append(model_source_table(model_comparison))
    story.extend(section("二、主执行下注建议：比赛盘口"))
    rows = [["盘口", "操作", "金额", "概率", "赔率", "EV", "判断依据"]]
    for item in match_top:
        rows.append(
            [
                f"{item['match']} / {item['market']} / {item['selection']}",
                "动态仓位买入" if item["time_adjusted_stake_aud"] > 0 else "观察",
                f"{aud(item['time_adjusted_stake_aud'])} / {item['time_adjusted_stake_unit']:.2f}u",
                pct(item["model_probability"]),
                f"{item['odds']:.2f}",
                pct(item["expected_value"]),
                chinese_match_reason(item),
            ]
        )
    story.append(table(rows, [42 * mm, 20 * mm, 24 * mm, 18 * mm, 16 * mm, 17 * mm, 50 * mm], buy_action_col=1))
    story.extend(section("三、风险控制"))
    story.append(
        para(
            "公开副本不包含账户或逐笔持仓信息。本报告不是收益保证；赛前伤停、首发、红牌、点球和赔率跳动都会改变建议有效性。",
            STYLES["Body"],
        )
    )
    return story


def assert_pdf_input_gates(
    matches: Dict,
    futures: Dict,
    groups: Dict,
    australia: Dict,
    team_multi: Dict,
    portfolio: Dict,
    safety: Dict | None = None,
    raw_refresh: Dict | None = None,
) -> None:
    failures = []
    gate_specs = [
        ("matches", matches.get("automation_gate", {}), "automation_ready"),
        ("futures", futures.get("automation_gate", {}), "automation_ready"),
        ("group_betting", groups.get("automation_gate", {}), "automation_ready"),
        ("australia_markets", australia.get("automation_gate", {}), "automation_ready"),
        ("team_futures_multi", team_multi.get("automation_gate", {}), "automation_ready"),
        ("portfolio", portfolio, "portfolio_automation_ready"),
    ]
    for name, gate, ready_key in gate_specs:
        if not gate.get(ready_key):
            reasons = "; ".join(gate.get("blocking_reasons", [])) or f"{ready_key} is false"
            failures.append(f"{name}: {reasons}")
    if safety is None:
        failures.append("safety: safety gate is missing")
    elif not safety.get("automation_safety_ready"):
        failures.append("safety: " + ("; ".join(safety.get("blocking_reasons", [])) or "safety gate is false"))
    if raw_refresh is None:
        failures.append("raw_refresh: raw refresh gate is missing")
    elif not raw_refresh.get("raw_refresh_ready"):
        failures.append("raw_refresh: " + ("; ".join(raw_refresh.get("blocking_reasons", [])) or "raw refresh gate is false"))
    if failures:
        raise RuntimeError("PDF input gates failed; refusing to publish execution PDF: " + " | ".join(failures))


def public_bankroll_summary(report_summary: Dict) -> Dict:
    return {
        "report_date": report_summary["report_date"],
        "pdf_output_copy": Path(report_summary["pdf_output_copy"]).name,
        "base_selected_exposure_aud": report_summary["base_selected_exposure_aud"],
        "time_adjusted_new_exposure_aud": report_summary["time_adjusted_new_exposure_aud"],
        "match_candidate_count": len(report_summary["match_stakes"]),
        "private_pdf_path_omitted": True,
        "private_fields_omitted": [
            "私有PDF路径",
            "持仓读取状态",
            "未结算持仓明细",
            "待结算潜在返还",
            "潜在收益明细",
            "逐笔私有持仓行",
            "逐项执行仓位",
        ],
    }


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont(FONT_REGULAR, 8)
    canvas.setFillColor(colors.HexColor("#667085"))
    canvas.drawString(14 * mm, 9 * mm, "TAB FIFA 2026 盘口研究报告 | 仅作研究分析，不自动下注")
    canvas.drawRightString(196 * mm, 9 * mm, f"第 {doc.page} 页")
    canvas.restoreState()


def register_pdf_fonts() -> None:
    global FONT_REGULAR, FONT_BOLD
    try:
        pdfmetrics.registerFont(TTFont(FONT_REGULAR, "/System/Library/Fonts/STHeiti Light.ttc"))
        pdfmetrics.registerFont(TTFont(FONT_BOLD, "/System/Library/Fonts/STHeiti Medium.ttc"))
    except Exception:
        FONT_REGULAR = "Helvetica"
        FONT_BOLD = "Helvetica-Bold"


register_pdf_fonts()
STYLES = getSampleStyleSheet()
STYLES.add(
    ParagraphStyle(
        name="ReportTitle",
        fontName=FONT_BOLD,
        fontSize=21,
        leading=28,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#0B1F3A"),
        spaceAfter=5 * mm,
    )
)
STYLES.add(
    ParagraphStyle(
        name="Subtitle",
        fontName=FONT_REGULAR,
        fontSize=11,
        leading=15,
        alignment=TA_CENTER,
        textColor=colors.HexColor("#526070"),
    )
)
STYLES.add(
    ParagraphStyle(
        name="H2",
        fontName=FONT_BOLD,
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#0B1F3A"),
        spaceAfter=2 * mm,
    )
)
STYLES.add(
    ParagraphStyle(
        name="H3",
        fontName=FONT_BOLD,
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#1F4E79"),
    )
)
STYLES.add(
    ParagraphStyle(
        name="Body",
        fontName=FONT_REGULAR,
        fontSize=9.0,
        leading=13,
        alignment=TA_LEFT,
        textColor=colors.HexColor("#1F2937"),
    )
)
STYLES.add(
    ParagraphStyle(
        name="TableCell",
        fontName=FONT_REGULAR,
        fontSize=7.2,
        leading=9.0,
        textColor=colors.HexColor("#111827"),
    )
)


def chinese_match_reason(item: Dict) -> str:
    key = f"{item['match']}|{item['market']}|{item['selection']}"
    reasons = {
        "Netherlands v Japan|Result|Japan": "日本战术纪律、压迫组织和近周期稳定性高于普通受让方定价；3.70赔率下模型概率仍高于盈亏平衡点。风险在于荷兰身体对抗和定位球优势。",
        "Brazil v Morocco|Result|Morocco": "摩洛哥具备强防守和反击质量，巴西存在名气溢价；6.00长赔给出较高EV。风险在于巴西个人能力和早段进球打穿防线。",
        "France v Senegal|Result|Senegal": "塞内加尔阵容身体条件和转换速度足以支撑长赔小仓；7.50赔率提供补偿。风险是法国前场深度明显更强。",
        "England v Croatia|Result|Croatia": "克罗地亚大赛经验和中场控制力使其不应被过度低估；英格兰热门属性可能压低主胜赔率。风险是英格兰阵容厚度和冲击力。",
        "Belgium v Egypt|Total Goals Over/Under|Under 2.5 Goals": "双方节奏预期偏谨慎，1.95赔率下低比分概率略高于盈亏平衡点。风险是早段进球、点球或红牌破坏小球结构。",
    }
    base = reasons.get(key, "该盘口通过模型概率、盈亏平衡概率和赔率边际筛选，当前只适合小仓执行。")
    model_summary = (item.get("model_signal") or {}).get("summary_zh") or item.get("model_divergence_summary", "")
    if model_summary and "模型交叉验证" not in base:
        return f"{base} {model_summary}"
    return base


def chinese_futures_reason(selection: str) -> str:
    if selection.startswith("Belgium"):
        return "比利时更适合晋级深度盘而非冠军盘，但长线资金锁定时间长，等待路径和阵容确认。"
    if selection.startswith("Colombia"):
        return "哥伦比亚价格具备观察价值，关键在小组路径和淘汰赛对位，不宜提前占用预算。"
    if selection.startswith("Japan"):
        return "日本与比赛盘口模型方向一致，但晋级八强受路径影响大，先观察不下注。"
    if selection.startswith("Morocco"):
        return "摩洛哥长赔方向有吸引力，但需要结合巴西小组赛结果和淘汰赛路径判断。"
    if selection.startswith("Croatia"):
        return "克罗地亚大赛经验支撑观察价值，但年龄结构和伤停风险较高。"
    return "长线盘口路径方差大，当前不下注。"


def chinese_group_reason(selection: str) -> str:
    if "Colombia" in selection:
        return "哥伦比亚小组第一价格相对有竞争力，但需模拟葡萄牙及同组赛程。"
    if "Japan" in selection:
        return "日本小组第一方向与比赛模型一致，但仍需逐场验证荷兰/突尼斯/欧洲队对位。"
    if "Croatia" in selection:
        return "克罗地亚受英格兰热门定价影响具备观察价值，但小组第一容错率低。"
    if "Morocco" in selection:
        return "摩洛哥小组第一高度依赖对巴西结果，暂不提前下注。"
    if "Australia" in selection:
        return "澳大利亚主场区域因素可观察，但Group D整体难度高，当前不下注。"
    return "小组盘口需要逐场路径模拟，当前不下注。"


def realized_pnl_note(position_summary: Dict) -> str:
    settled_count = position_summary.get("settled_count", 0)
    if settled_count:
        return f"已结算口径：{settled_count}笔已结算投注按返还金额减stake计算；未结算投注不提前计入。"
    return "当前读取到的世界杯相关投注全部未结算，已实现盈亏暂为0。"


def position_monitoring_note(bet: Dict) -> str:
    stake = bet.get("stake_aud", 0) or 0
    odds = bet.get("odds", 0) or 0
    selection = bet.get("selection", "")
    market = bet.get("market", "")
    if bet.get("bet_type") == "Multi":
        return "多串一旦任一腿失效即归零，赛前48小时必须逐腿复核。"
    if stake >= 400 and odds <= 1.5:
        return "低赔率重仓，收益弹性有限；不建议同方向继续加仓。"
    if odds <= 1.15:
        return "极低赔率，主要风险是冷门尾部事件；只做结果监控。"
    if "Not To Qualify" in market:
        return "晋级反向盘需持续跟踪同组积分和净胜球路径。"
    if "Winner" in market:
        return "小组第一盘依赖三场路径，赛前阵容变化会显著影响概率。"
    if "Over" in selection or "Goals" in market:
        return "球队进球盘需跟踪首发前锋、轮换和比赛节奏。"
    return "当前为Pending，赛前新闻和赔率变化触发复核。"


if __name__ == "__main__":
    with single_instance_lock(LOCK_PATH):
        summary = render_pdf()
    print(summary["pdf_path"])
