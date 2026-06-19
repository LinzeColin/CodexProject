import json
import argparse
from pathlib import Path

from tab_research.paths import resolve_workspace_root


ROOT = resolve_workspace_root(Path(__file__))

MARKET_BOUNDARIES = [
    "Result",
    "Double Chance",
    "Handicap",
    "Correct Score",
    "Total Goals Over/Under",
    "Both Teams to Score",
    "Result Over/Under Double",
    "Draw No Bet",
    "Half/Full Double",
    "1st Half Result",
    "Team To Score",
    "Goals",
    "Margin",
    "Doubles",
    "Half",
    "Team",
    "Others",
    "Language:",
]

CORE_MARKETS = [
    "Result",
    "Double Chance",
    "Handicap",
    "Total Goals Over/Under",
    "Both Teams to Score",
    "Draw No Bet",
]


def extract_market_sections(text: str) -> dict:
    lines = text.splitlines()
    starts = []
    for index, line in enumerate(lines):
        if line in MARKET_BOUNDARIES:
            starts.append((index, line))

    sections = {}
    for pos, (start, name) in enumerate(starts):
        if name not in CORE_MARKETS or name in sections:
            continue
        end = len(lines)
        for next_start, next_name in starts[pos + 1 :]:
            if next_start > start and next_name in MARKET_BOUNDARIES:
                end = next_start
                break
        value = "\n".join(lines[start:end]).strip()
        if len(value.splitlines()) > 2:
            sections[name] = value
    return sections


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--raw-in", default=str(ROOT / "outputs" / "tab_fifa_matches_main_markets_raw_v0_3.json"))
    parser.add_argument("--scraped", default=str(ROOT / "work" / "tab-research-pipeline" / "scraped_detail_v0_8.json"))
    parser.add_argument("--raw-out", default=str(ROOT / "outputs" / "tab_fifa_matches_main_markets_raw_v0_8.json"))
    parser.add_argument("--note", default="chrome_rescrape")
    args = parser.parse_args()

    raw_in = Path(args.raw_in)
    scraped_path = Path(args.scraped)
    raw_out = Path(args.raw_out)

    raw = json.loads(raw_in.read_text())
    scraped = json.loads(scraped_path.read_text())
    by_name = {match["match"]: match for match in raw["matches"]}

    for item in scraped["results"]:
        sections = extract_market_sections(item["text"])
        match = {
            "match": item["match"],
            "href": item["href"],
            "title": item["title"],
            "markets": sections,
            "errors": [],
            "scrape_note": args.note,
        }
        if set(CORE_MARKETS).issubset(sections):
            match["partial_core_only"] = False
        else:
            match["partial_core_only"] = True
            match["market_availability"] = "tab_only_result" if set(sections) == {"Result"} else "partial_core"
            if set(sections) != {"Result"}:
                match["errors"] = item["errors"]
        by_name[item["match"]] = match

    raw["matches"] = [by_name[name] for name in by_name]
    raw["generated_at"] = scraped["generated_at"]
    raw["source"] = raw.get("source", "") + f" + {args.note}"
    raw_out.write_text(json.dumps(raw, indent=2, ensure_ascii=False))
    print(f"wrote={raw_out}")
    print(f"matches={len(raw['matches'])}")


if __name__ == "__main__":
    main()
