#!/usr/bin/env python3
"""Build a deterministic weekly report from the redacted Memory Atlas snapshot."""

from __future__ import annotations

import argparse
import json
import os
import tempfile
from datetime import date, timedelta
from pathlib import Path
from typing import Any


SNAPSHOT_PATH = Path("data/derived/visualization/memory_atlas.json")
WEEKLY_OUTPUT_DIR = Path("data/derived/weekly")


def _clean_text(value: Any, fallback: str = "") -> str:
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return fallback
    text = " ".join(str(value).split())
    return text or fallback


def _normalized_key(value: Any) -> str:
    return _clean_text(value).casefold().replace("-", "_").replace(" ", "_")


def _valid_date(value: Any) -> date | None:
    if not isinstance(value, str) or len(value) != 10:
        return None
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        return None
    return parsed if parsed.isoformat() == value else None


def _is_decision(node: dict[str, Any]) -> bool:
    return _normalized_key(node.get("category")) in {"decision", "important_decision", "\u51b3\u7b56", "\u91cd\u8981\u51b3\u7b56"}


def _is_pending_proposal(node: dict[str, Any]) -> bool:
    return _normalized_key(node.get("category")) in {
        "pending_proposal",
        "proposal_pending",
        "\u5f85\u6388\u6743\u63d0\u6848",
        "\u5f85\u51b3\u63d0\u6848",
    }


def _is_high_importance(node: dict[str, Any]) -> bool:
    return _normalized_key(node.get("importance")) in {"high", "critical", "\u9ad8", "\u6700\u9ad8", "\u9ad8\u91cd\u8981\u6027"}


def _dated_node_sort_key(item: tuple[date, dict[str, Any]]) -> tuple[Any, ...]:
    node_date, node = item
    return (
        -node_date.toordinal(),
        _clean_text(node.get("id")),
        _clean_text(node.get("label")),
        _clean_text(node.get("statement")),
    )


def _optional_dated_node_sort_key(item: tuple[date | None, dict[str, Any]]) -> tuple[Any, ...]:
    node_date, node = item
    return (
        node_date is None,
        -(node_date.toordinal() if node_date is not None else 0),
        _clean_text(node.get("id")),
        _clean_text(node.get("label")),
        _clean_text(node.get("statement")),
    )


def _recommendation_rows(value: Any) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if isinstance(value, list):
        rows.extend(item for item in value if isinstance(item, dict))
    elif isinstance(value, dict):
        direct = value.get("current")
        if isinstance(direct, list):
            rows.extend(item for item in direct if isinstance(item, dict))
        for group_name in ("memory", "meta_data"):
            group = value.get(group_name)
            if not isinstance(group, dict):
                continue
            current = group.get("current")
            if isinstance(current, list):
                rows.extend(item for item in current if isinstance(item, dict))

    unique: dict[tuple[str, ...], dict[str, Any]] = {}
    for row in rows:
        key = tuple(
            _clean_text(row.get(field))
            for field in ("id", "title", "statement", "reason", "scope", "importance")
        )
        unique.setdefault(key, row)
    return sorted(unique.values(), key=lambda row: tuple(
        _clean_text(row.get(field))
        for field in ("id", "title", "statement", "reason", "scope", "importance")
    ))


def _render_node(node_date: date | None, node: dict[str, Any]) -> str:
    label = _clean_text(node.get("label")) or _clean_text(node.get("id"), "\u672a\u547d\u540d\u8bb0\u5fc6")
    statement = _clean_text(node.get("statement"), "\u65e0\u6458\u8981\u3002")
    date_text = node_date.isoformat() if node_date is not None else "\u65e5\u671f\u672a\u77e5"
    return f"- `{date_text}` **{label}**\uff1a{statement}"


def _render_recommendation(row: dict[str, Any]) -> str:
    title = (
        _clean_text(row.get("title"))
        or _clean_text(row.get("statement"))
        or _clean_text(row.get("id"), "\u672a\u547d\u540d\u5efa\u8bae")
    )
    details: list[str] = []
    statement = _clean_text(row.get("statement"))
    reason = _clean_text(row.get("reason"))
    scope = _clean_text(row.get("scope"))
    if statement and statement != title:
        details.append(statement)
    if reason:
        details.append(f"\u539f\u56e0\uff1a{reason}")
    if scope:
        details.append(f"\u8303\u56f4\uff1a{scope}")
    return f"- **{title}**\uff1a{' '.join(details) if details else '\u65e0\u8865\u5145\u8bf4\u660e\u3002'}"


def _append_section(lines: list[str], heading: str, items: list[str]) -> None:
    lines.extend(("", f"## {heading}", ""))
    lines.extend(items or ["- \u65e0\u3002"])


def _render_report(
    snapshot: dict[str, Any],
    anchor: date,
    range_start: date,
    memory_count: int,
    recent_nodes: list[tuple[date, dict[str, Any]]],
    pending_nodes: list[tuple[date | None, dict[str, Any]]],
    recommendations: list[dict[str, Any]],
) -> str:
    overview = snapshot.get("overview") if isinstance(snapshot.get("overview"), dict) else {}
    generated_at = _clean_text(overview.get("generated_at"), "\u672a\u63d0\u4f9b")
    decisions = [item for item in recent_nodes if _is_decision(item[1])]
    high_changes = [
        item
        for item in recent_nodes
        if _is_high_importance(item[1]) and not _is_decision(item[1]) and not _is_pending_proposal(item[1])
    ]

    lines = [
        "# Memory Atlas \u672c\u5468\u62a5\u544a",
        "",
        f"> \u672c\u62a5\u544a\u4ec5\u4f7f\u7528\u8131\u654f\u6d3e\u751f\u5feb\u7167 `{SNAPSHOT_PATH.as_posix()}` \u751f\u6210\uff0c\u4e0d\u8bfb\u53d6 raw/private \u8d44\u6599\uff0c\u4e0d\u8fdb\u884c remote \u5199\u5165\u3002",
        "",
        "## \u5feb\u7167 / \u8303\u56f4 / \u8ba1\u6570\uff08Snapshot / Range / Count\uff09",
        "",
        f"- Snapshot\uff1a`{SNAPSHOT_PATH.as_posix()}`",
        f"- Snapshot \u751f\u6210\u65f6\u95f4\uff1a`{generated_at}`",
        f"- Anchor\uff1a`{anchor.isoformat()}`\uff08memory \u8282\u70b9\u6700\u5927\u6709\u6548 date\uff09",
        f"- Range\uff1a`{range_start.isoformat()}` \u81f3 `{anchor.isoformat()}`\uff08inclusive\uff0c\u5171 7 \u5929\uff09",
        f"- Count\uff1amemory \u8282\u70b9\u603b\u6570 `{memory_count}`\uff0c\u6700\u8fd1 7 \u5929 `{len(recent_nodes)}`",
        f"- Pending proposal count\uff1a`{len(pending_nodes)}`",
        f"- Agent recommendation count\uff1a`{len(recommendations)}`",
    ]
    _append_section(lines, "\u8fd1\u671f\u51b3\u7b56", [_render_node(*item) for item in decisions])
    _append_section(lines, "\u9ad8\u91cd\u8981\u6027\u53d8\u5316", [_render_node(*item) for item in high_changes])
    _append_section(lines, "Pending proposal\uff08\u5f85\u6388\u6743\u63d0\u6848\uff09", [_render_node(*item) for item in pending_nodes])
    _append_section(lines, "Agent recommendations\uff08\u5f53\u524d agent \u5efa\u8bae\uff09", [_render_recommendation(row) for row in recommendations])
    lines.extend(
        (
            "",
            "## \u6570\u636e\u4e0e\u64cd\u4f5c\u8fb9\u754c",
            "",
            f"- \u8f93\u5165\u8fb9\u754c\uff1a\u4ec5\u4f7f\u7528\u8131\u654f\u6d3e\u751f\u5feb\u7167 `{SNAPSHOT_PATH.as_posix()}`\u3002",
            "- Raw boundary\uff1a\u4e0d\u8bfb\u53d6 OpenAI export\u3001Codex transcript\u3001private archive \u6216\u5176\u4ed6 raw \u6570\u636e\uff0c\u4e0d\u4fee\u6539 raw \u6570\u636e\u3002",
            "- Remote boundary\uff1a\u4e0d\u8bbf\u95ee\u8fdc\u7a0b\u670d\u52a1\uff0c\u4e0d\u6267\u884c remote push\u3002",
            "- \u5199\u5165\u8fb9\u754c\uff1a\u4ec5\u539f\u5b50\u5199\u5165\u672c\u5730 `data/derived/weekly/` \u4e0b\u7684\u5f53\u5468 Markdown \u62a5\u544a\u3002",
            "",
        )
    )
    return "\n".join(lines)


def _write_if_changed_atomic(path: Path, content: str) -> bool:
    encoded = content.encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return False

    path.parent.mkdir(parents=True, exist_ok=True)
    file_descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(file_descriptor, "wb") as handle:
            os.fchmod(handle.fileno(), 0o644)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        if temp_path.exists():
            temp_path.unlink()
    return True


def build_weekly_report(database_dir: Path) -> dict[str, Any]:
    database_dir = Path(database_dir).resolve()
    snapshot_file = database_dir / SNAPSHOT_PATH
    snapshot = json.loads(snapshot_file.read_text(encoding="utf-8"))
    if not isinstance(snapshot, dict):
        raise ValueError("\u8131\u654f\u6d3e\u751f\u5feb\u7167\u5fc5\u987b\u662f JSON object\u3002")

    source_contract = snapshot.get("source_contract")
    if isinstance(source_contract, dict) and source_contract.get("raw_private_data_included") is True:
        raise ValueError("\u5feb\u7167\u58f0\u660e\u5305\u542b raw/private \u6570\u636e\uff0c\u5df2\u505c\u6b62\u751f\u6210\u3002")

    nodes_value = snapshot.get("nodes")
    if not isinstance(nodes_value, list):
        raise ValueError("\u8131\u654f\u6d3e\u751f\u5feb\u7167\u7f3a\u5c11 nodes array\u3002")
    memory_nodes = [
        node for node in nodes_value if isinstance(node, dict) and node.get("kind") == "memory"
    ]
    dated_nodes = [
        (node_date, node)
        for node in memory_nodes
        if (node_date := _valid_date(node.get("date"))) is not None
    ]
    if not dated_nodes:
        raise ValueError("\u5feb\u7167\u4e2d\u6ca1\u6709\u5e26\u6709\u6548 date \u7684 memory \u8282\u70b9\u3002")

    anchor = max(node_date for node_date, _node in dated_nodes)
    range_start = anchor - timedelta(days=6)
    week_start = anchor - timedelta(days=anchor.weekday())
    recent_nodes = sorted(
        (item for item in dated_nodes if range_start <= item[0] <= anchor),
        key=_dated_node_sort_key,
    )
    pending_nodes = sorted(
        (
            (_valid_date(node.get("date")), node)
            for node in memory_nodes
            if _is_pending_proposal(node)
        ),
        key=_optional_dated_node_sort_key,
    )
    recommendations = _recommendation_rows(snapshot.get("agent_recommendations"))
    report = _render_report(
        snapshot,
        anchor,
        range_start,
        len(memory_nodes),
        recent_nodes,
        pending_nodes,
        recommendations,
    )

    output = WEEKLY_OUTPUT_DIR / f"{week_start.isoformat()}.memory_atlas_weekly_report.md"
    changed = _write_if_changed_atomic(database_dir / output, report)
    return {
        "status": "PASS",
        "snapshot": SNAPSHOT_PATH.as_posix(),
        "anchor": anchor.isoformat(),
        "range": {
            "start": range_start.isoformat(),
            "end": anchor.isoformat(),
            "inclusive_days": 7,
        },
        "counts": {
            "memory_total": len(memory_nodes),
            "memory_recent": len(recent_nodes),
            "pending_proposals": len(pending_nodes),
            "agent_recommendations": len(recommendations),
        },
        "output": output.as_posix(),
        "writes_files": changed,
        "output_changed": changed,
        "raw_mutation": False,
        "remote_push": False,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a deterministic Chinese weekly report from the redacted Memory Atlas snapshot."
    )
    parser.add_argument("--database-dir", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        result = build_weekly_report(args.database_dir)
    except FileNotFoundError:
        result = {
            "status": "FAIL",
            "message_zh": "\u627e\u4e0d\u5230\u8131\u654f\u6d3e\u751f\u5feb\u7167\u3002",
            "writes_files": False,
            "raw_mutation": False,
            "remote_push": False,
        }
        exit_code = 1
    except json.JSONDecodeError:
        result = {
            "status": "FAIL",
            "message_zh": "\u8131\u654f\u6d3e\u751f\u5feb\u7167\u4e0d\u662f\u6709\u6548 JSON\u3002",
            "writes_files": False,
            "raw_mutation": False,
            "remote_push": False,
        }
        exit_code = 1
    except ValueError as error:
        result = {
            "status": "FAIL",
            "message_zh": str(error),
            "writes_files": False,
            "raw_mutation": False,
            "remote_push": False,
        }
        exit_code = 1
    except OSError:
        result = {
            "status": "FAIL",
            "message_zh": "\u5468\u62a5\u6587\u4ef6\u5199\u5165\u5931\u8d25\u3002",
            "writes_files": False,
            "raw_mutation": False,
            "remote_push": False,
        }
        exit_code = 1
    else:
        exit_code = 0
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
