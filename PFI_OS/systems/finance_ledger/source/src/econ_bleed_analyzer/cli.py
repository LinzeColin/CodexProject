from __future__ import annotations

import argparse
from pathlib import Path

from .alipay import load_transactions
from .classifier import classify_transactions, load_rules
from .reports import generate_outputs, load_tag_config
from .review import load_review_decisions


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Analyze Alipay/WeChat CSV bills with economic bleed mechanisms.")
    parser.add_argument("--input", nargs="+", required=True, help="Alipay/WeChat CSV file(s), glob-expanded paths, or directories.")
    parser.add_argument("--rules", default="configs/classification_rules.json", help="Classification rule JSON path.")
    parser.add_argument("--review-decisions", default="", help="Optional manual review decision CSV generated from review/review_decisions_template.csv.")
    parser.add_argument("--tag-library", default="", help="Optional tag library JSON/CSV exported from tag_library.html.")
    parser.add_argument("--output", default="outputs/alipay_analysis_latest", help="Output directory.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    transactions = load_transactions(args.input)
    if not transactions:
        raise SystemExit("未读取到交易记录。")
    rules = load_rules(args.rules)
    classified = classify_transactions(transactions, rules)
    review_decisions = load_review_decisions(args.review_decisions)
    tag_library_rows, tag_filter_preset_rows = load_tag_config(args.tag_library)
    outputs = generate_outputs(
        classified,
        Path(args.output),
        review_decisions=review_decisions,
        tag_library_rows=tag_library_rows,
        tag_filter_preset_rows=tag_filter_preset_rows,
    )
    print(f"已处理 {len(transactions)} 笔交易")
    if args.review_decisions:
        print(
            "复核确认："
            f"纳入 {len(review_decisions.included)} 个交易键，"
            f"排除 {len(review_decisions.excluded)} 个交易键，"
            f"无效 {len(review_decisions.invalid_rows)} 行"
        )
    for name, path in outputs.items():
        print(f"{name}: {path}")
    return 0
