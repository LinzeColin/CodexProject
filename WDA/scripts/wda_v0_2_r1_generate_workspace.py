#!/usr/bin/env python3
"""Generate the WDA v0.2-R1 local human-readable intelligence workspace.

This script is intentionally local-first:
- full-sensitive report content is written only under WDA_MetaData;
- repo docs contain structure, counts, runbooks, and safety boundaries only;
- SQLite is opened read-only;
- no exporter, network upload, RAG, Web, or Matrix process is started.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import sqlite3
import stat
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_DB = Path(
    "/Users/linzezhang/Downloads/WDA_MetaData/v0_1/data_core_seed/wda_v0_1_seed.sqlite"
)
DEFAULT_ANALYSIS_ROOT = Path(
    "/Users/linzezhang/Downloads/WDA_MetaData/v0_1/analysis_layer"
)
DEFAULT_OUTPUT_ROOT = Path("/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r1")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
REPO_DOCS_ROOT = PROJECT_ROOT / "docs" / "v0_2_r1_full_auto_human_readable_workspace"

REPORT_SECTION_TITLES = [
    "先说结论",
    "为什么",
    "证据",
    "对我有什么影响",
    "我下一步该做什么",
    "不确定的地方",
    "可忽略的事项",
    "可自动化/模板化事项",
]

REQUIRED_ANALYSIS_FILES = [
    "subject_stats.csv",
    "subject_timeline.csv",
    "keyword_signal_hits.csv",
    "todo_signal_candidates.csv",
    "opportunity_signal_candidates.csv",
    "risk_signal_candidates.csv",
    "behavior_pattern_indicators.csv",
    "analysis_validation_report.json",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate WDA v0.2-R1 local Chinese reports and repo-safe docs."
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--analysis-root", type=Path, default=DEFAULT_ANALYSIS_ROOT)
    parser.add_argument("--output-root", type=Path, default=DEFAULT_OUTPUT_ROOT)
    parser.add_argument("--repo-docs-root", type=Path, default=REPO_DOCS_ROOT)
    return parser.parse_args()


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def utc_ms(ms: Any) -> str:
    try:
        value = int(ms)
    except (TypeError, ValueError):
        return "UNKNOWN"
    if value <= 0:
        return "UNKNOWN"
    return datetime.fromtimestamp(value / 1000, tz=timezone.utc).strftime(
        "%Y-%m-%d %H:%M:%S UTC"
    )


def mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def write_text(path: Path, text: str) -> None:
    mkdir(path.parent)
    path.write_text(text.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, data: Any) -> None:
    write_text(path, json.dumps(data, ensure_ascii=False, indent=2))


def write_csv(path: Path, fieldnames: list[str], rows: Iterable[dict[str, Any]]) -> None:
    mkdir(path.parent)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({name: row.get(name, "") for name in fieldnames})


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def bullet(lines: Iterable[str]) -> str:
    material = [line for line in lines if line]
    if not material:
        return "- 暂无。"
    return "\n".join(f"- {line}" for line in material)


def table(headers: list[str], rows: Iterable[Iterable[Any]]) -> str:
    rows = list(rows)
    header = "| " + " | ".join(headers) + " |"
    divider = "| " + " | ".join(["---"] * len(headers)) + " |"
    body = []
    for row in rows:
        body.append("| " + " | ".join(str(value) for value in row) + " |")
    return "\n".join([header, divider] + body)


def clean_text(text: Any) -> str:
    if text is None:
        return ""
    return " ".join(str(text).replace("\r", " ").replace("\n", " ").split())


def excerpt(text: Any, limit: int = 160) -> str:
    value = clean_text(text)
    if not value:
        return "（空文本或非文本消息）"
    if len(value) <= limit:
        return value
    return value[:limit] + "..."


def safe_filename(value: str) -> str:
    allowed = []
    for ch in value:
        if ch.isalnum() or ch in "-_":
            allowed.append(ch)
        else:
            allowed.append("_")
    return "".join(allowed).strip("_") or "item"


def report_template(
    title: str,
    conclusion: list[str],
    why: list[str],
    evidence: list[str],
    impact: list[str],
    actions: list[str],
    uncertainty: list[str],
    ignore: list[str],
    automate: list[str],
) -> str:
    sections = {
        "先说结论": conclusion,
        "为什么": why,
        "证据": evidence,
        "对我有什么影响": impact,
        "我下一步该做什么": actions,
        "不确定的地方": uncertainty,
        "可忽略的事项": ignore,
        "可自动化/模板化事项": automate,
    }
    out = [f"# {title}", ""]
    for name in REPORT_SECTION_TITLES:
        out.extend([f"## {name}", "", bullet(sections[name]), ""])
    return "\n".join(out)


def open_seed_readonly(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        raise FileNotFoundError(f"SQLite seed not found: {db_path}")
    return sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)


def fetch_seed(db_path: Path) -> dict[str, Any]:
    con = open_seed_readonly(db_path)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    counts = {}
    for table_name in [
        "messages",
        "conversations",
        "contacts",
        "subjects",
        "message_subject_links",
        "media_index",
    ]:
        try:
            counts[table_name] = cur.execute(
                f"select count(*) from {table_name}"
            ).fetchone()[0]
        except sqlite3.Error:
            counts[table_name] = 0

    subjects = [
        dict(row)
        for row in cur.execute(
            """
            select subject_id, subject_label, subject_category, confidence,
                   expected_rows, actual_rows, excluded_noise
            from subjects
            order by subject_id
            """
        )
    ]
    conversations = [
        dict(row)
        for row in cur.execute(
            """
            select conversation_id, conversation_type, message_count_declared,
                   display_title, last_message_at_ms
            from conversations
            order by conversation_id
            """
        )
    ]
    contacts = [
        dict(row)
        for row in cur.execute(
            """
            select contact_id, display_name, contact_type, first_seen_ms, last_seen_ms
            from contacts
            order by contact_id
            """
        )
    ]
    messages = [
        dict(row)
        for row in cur.execute(
            """
            select m.message_id, m.conversation_id, m.sender_id, m.direction,
                   m.timestamp_ms, m.message_type, m.text, l.subject_id
            from messages m
            join message_subject_links l on l.message_id = m.message_id
            order by l.subject_id, m.timestamp_ms, m.message_id
            """
        )
    ]
    noise_hits = cur.execute(
        "select count(*) from messages where coalesce(text, '') like '%李晶工作交接%'"
    ).fetchone()[0]
    integrity = cur.execute("pragma integrity_check").fetchone()[0]
    con.close()
    return {
        "counts": counts,
        "subjects": subjects,
        "conversations": conversations,
        "contacts": contacts,
        "messages": messages,
        "noise_hits": noise_hits,
        "integrity": integrity,
    }


def load_analysis(analysis_root: Path) -> dict[str, Any]:
    missing = [
        name for name in REQUIRED_ANALYSIS_FILES if not (analysis_root / name).exists()
    ]
    if missing:
        raise FileNotFoundError(f"Missing analysis outputs: {', '.join(missing)}")
    data = {
        "subject_stats": read_csv(analysis_root / "subject_stats.csv"),
        "subject_timeline": read_csv(analysis_root / "subject_timeline.csv"),
        "keyword_hits": read_csv(analysis_root / "keyword_signal_hits.csv"),
        "todo": read_csv(analysis_root / "todo_signal_candidates.csv"),
        "opportunity": read_csv(analysis_root / "opportunity_signal_candidates.csv"),
        "risk": read_csv(analysis_root / "risk_signal_candidates.csv"),
        "behavior": read_csv(analysis_root / "behavior_pattern_indicators.csv"),
    }
    with (analysis_root / "analysis_validation_report.json").open(
        "r", encoding="utf-8"
    ) as f:
        data["validation"] = json.load(f)
    return data


def group_by(rows: Iterable[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        grouped[str(row.get(key, ""))].append(row)
    return dict(grouped)


def signal_counts(rows: list[dict[str, str]]) -> Counter:
    return Counter(row.get("signal_category", "UNKNOWN") for row in rows)


def signal_lines(rows: list[dict[str, str]], limit: int = 8) -> list[str]:
    lines = []
    for row in rows[:limit]:
        msg = row.get("message_id", "")
        conv = row.get("conversation_id", "")
        ts = utc_ms(row.get("timestamp_ms"))
        terms = row.get("terms") or row.get("term") or row.get("signal_category", "")
        text = row.get("text_full_sensitive", "")
        lines.append(f"`{msg}` / `{conv}` / {ts} / 线索 `{terms}`：{excerpt(text)}")
    return lines


def subject_stats_map(analysis: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {row["subject_id"]: row for row in analysis["subject_stats"]}


def behavior_map(analysis: dict[str, Any]) -> dict[str, dict[str, str]]:
    return {row["subject_id"]: row for row in analysis["behavior"]}


def create_configs(output_root: Path) -> None:
    config_root = output_root / "config"
    write_text(
        config_root / "export_policy.yaml",
        """# WDA v0.2-R1 export policy
host: old_computer
route: pinned_wechat_cli_wxkey_family
coverage: all_conversations
manual_contact_selection: false
chunking:
  enabled: true
  chunk_size_conversations: 50
  checkpoint_after_each_conversation: true
  resume_from_checkpoint: true
media:
  include_media_paths: false
privacy:
  upload_raw_data: false
  expose_key_material: false
outputs:
  old_computer_root: ~/Downloads/WDA_MetaData/v0_2_r1_old_export/
  transfer_bundle_name: wda_v0_2_r1_full_export_transfer_bundle.zip
stop_conditions:
  - key_material_written_to_transfer_bundle
  - raw_database_or_decrypted_database_in_transfer_bundle
  - exporter_outputs_outside_wda_metadata
  - unbounded_hang_without_checkpoint
""",
    )
    write_text(
        config_root / "analysis_policy.yaml",
        """# WDA v0.2-R1 analysis policy
analysis_host: new_computer
input_priority:
  - local_data_core_sqlite
  - local_analysis_layer_outputs
reports:
  language: zh-CN
  require_sections:
    - 先说结论
    - 为什么
    - 证据
    - 对我有什么影响
    - 我下一步该做什么
    - 不确定的地方
    - 可忽略的事项
    - 可自动化/模板化事项
claims:
  personality_or_psychology_claims: forbidden
  evidence_backed_observable_patterns: allowed
modules:
  contact_radar: enabled
  communication_behavior: enabled
  work_handoff: enabled
  work_information_summary: enabled
  work_optimization: enabled
  todo_extraction: enabled
  opportunity_discovery: enabled
  risk_detection: enabled
  money_invoice_contract_acceptance: enabled
  personal_behavior_optimization: enabled
  relationship_roi: enabled
  evidence_index: enabled
""",
    )
    write_text(
        config_root / "privacy_policy.yaml",
        """# WDA v0.2-R1 privacy policy
local_full_sensitive_analysis: allowed
redact_local_inputs: false
network_upload: forbidden
commit_to_git:
  raw_messages: forbidden
  contacts: forbidden
  sqlite_database: forbidden
  raw_import_pack: forbidden
  transfer_bundle: forbidden
  key_material: forbidden
  decrypted_databases: forbidden
repo_safe_docs:
  allowed:
    - structure
    - counts
    - sanitized templates
    - runbooks
    - validation summaries
  forbidden:
    - raw private message text
    - full-sensitive reports
    - contact values not already approved for docs
    - key material
""",
    )
    write_text(
        config_root / "report_templates.yaml",
        """# WDA v0.2-R1 report template contract
default_sections:
  - 先说结论
  - 为什么
  - 证据
  - 对我有什么影响
  - 我下一步该做什么
  - 不确定的地方
  - 可忽略的事项
  - 可自动化/模板化事项
human_style:
  language: clear_chinese
  audience: non_engineer_operator
  main_output: action_recommendations_with_evidence
evidence_reference:
  include_message_id: true
  include_conversation_id: true
  include_timestamp: true
  include_local_sensitive_excerpt: true
""",
    )


def create_pipeline_specs(output_root: Path) -> None:
    write_text(
        output_root / "old_computer_export_runner_spec.md",
        """# 旧电脑全量导出 Runner Spec

## 先说结论

- 旧电脑负责 WeChat live-read / export；新电脑负责 WDA_HOME、导入、分析和报告。
- 用户目标是一台机器一条命令：旧电脑执行全量导出命令，新电脑执行导入分析报告命令。
- v0.2-R1 不在新电脑运行 WeChat exporter，也不接触 key material。

## 一次性准备

- 继续使用已验证过的 `wechat-cli` / `wxkey` 路线和 pinned commit。
- 输出目录必须限制在旧电脑本地 `~/Downloads/WDA_MetaData/v0_2_r1_old_export/`。
- transfer bundle 只允许包含 message-level JSON/JSONL/manifest/checksum，不允许包含 key、config、DB、log、tool_work、sensitive_local_state。

## 目标命令形态

```bash
./run_wda_old_full_export.sh --all-conversations --chunk-size 50 --resume --include-media-paths false --output ~/Downloads/WDA_MetaData/v0_2_r1_old_export/
```

## 自动化要求

- 自动列出所有会话，不要求用户逐个选择联系人。
- 自动分批导出，按 conversation checkpoint。
- 每个 chunk 写 checksum、row count、failure log。
- 失败后按 checkpoint 继续，不重跑已成功 chunk。
- 导出结束后生成 transfer bundle 和 non-sensitive summary。

## 停止条件

- exporter 写出 key material、raw DB、decrypted DB、login/MMKV/protected-store 文件。
- 输出目录不在 WDA_MetaData。
- 需要用户手工逐个联系人确认。
- 无 checkpoint 的长时间挂起。
""",
    )
    write_text(
        output_root / "new_computer_import_runner_spec.md",
        """# 新电脑导入与分析 Runner Spec

## 先说结论

- 新电脑是 WDA Control Plane。
- v0.2-R1 当前可运行入口会基于本机已验证 SQLite seed 与 analysis outputs 生成中文可读工作区。
- 全量导出 transfer bundle 到达后，后续 runner 应自动执行 validate -> import -> analyze -> report。

## 当前可运行命令

```bash
/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r1/run_wda_v0_2_r1.sh
```

## 全量版本目标流程

1. 验证 transfer bundle checksum。
2. 拒绝 key/config/DB/log/tool_work/sensitive_local_state。
3. 转换为 WDA Raw Import Pack。
4. 写入新电脑本地 Data Core SQLite。
5. 运行 deterministic analysis。
6. 生成中文报告和 dashboard。
7. 只把 repo-safe docs 提交到 GitHub。

## 不做

- 不在新电脑运行 WeChat exporter。
- 不上传 raw data。
- 不启动 RAG/Web/Matrix。
- 不把 full-sensitive 报告或 SQLite 提交到 Git。
""",
    )
    write_text(
        output_root / "transfer_policy.md",
        """# Transfer Policy

## 先说结论

- 旧电脑到新电脑只转移 bounded/full message-level export bundle，不转移工具状态、key、DB、日志或缓存。
- transfer bundle 必须带 manifest、checksum、row counts、chunk index 和 failure summary。

## 允许

- message-level JSONL/JSON。
- conversations/contacts/media index metadata。
- import_manifest.json。
- checksum 文件。
- non-sensitive run summary。

## 禁止

- key material。
- decrypted DB 或 raw WeChat DB。
- login、MMKV、key-value stores。
- sensitive_local_state、tool_work、raw logs。
- 全量 WeChat cache。
""",
    )
    write_text(
        output_root / "full_auto_runbook.md",
        """# WDA v0.2-R1 Full-Auto Runbook

## 先说结论

- 旧电脑一条命令导出全量会话。
- 新电脑一条命令生成 WDA 中文情报工作区。
- 当前 v0.2-R1 已落地新电脑报告生成入口；旧电脑全量 exporter 仍需要按 spec 做一次性 runner 固化。

## 新电脑当前命令

```bash
/Users/linzezhang/Downloads/WDA_MetaData/v0_2_r1/run_wda_v0_2_r1.sh
```

## 旧电脑目标命令

```bash
./run_wda_old_full_export.sh --all-conversations --resume --include-media-paths false
```

## 成功标准

- dashboard/index.html 可直接打开。
- reports/ 下有中文行动报告。
- evidence_index.md 保留 message_id / conversation_id / timestamp 证据引用。
- repo 中只提交结构、counts、runbook 和 safety boundary。
""",
    )


def make_query_examples(output_root: Path, db_path: Path) -> None:
    write_text(
        output_root / "query_examples.sql",
        f"""-- WDA v0.2-R1 query examples
-- Open read-only:
-- sqlite3 'file:{db_path}?mode=ro'

select 'subject_message_counts' as query_name;
select s.subject_id, s.subject_label, count(*) as message_count
from subjects s
join message_subject_links l on l.subject_id = s.subject_id
group by s.subject_id, s.subject_label
order by message_count desc;

select 'risk_signal_refs' as query_name;
select m.message_id, m.conversation_id, m.timestamp_ms, m.direction, m.message_type
from messages m
where coalesce(m.text, '') like '%问题%'
   or coalesce(m.text, '') like '%风险%'
   or coalesce(m.text, '') like '%不行%'
limit 50;

select 'money_invoice_contract_refs' as query_name;
select m.message_id, m.conversation_id, m.timestamp_ms, m.direction, m.message_type
from messages m
where coalesce(m.text, '') like '%付款%'
   or coalesce(m.text, '') like '%发票%'
   or coalesce(m.text, '') like '%合同%'
   or coalesce(m.text, '') like '%验收%'
limit 50;
""",
    )


def create_local_runner(output_root: Path, script_path: Path, args: argparse.Namespace) -> None:
    runner = output_root / "run_wda_v0_2_r1.sh"
    write_text(
        runner,
        f"""#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${{PYTHON_BIN:-/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3}}"
REPO_SCRIPT="{script_path}"
DB_PATH="${{WDA_V0_2_R1_DB:-{args.db}}}"
ANALYSIS_ROOT="${{WDA_V0_2_R1_ANALYSIS_ROOT:-{args.analysis_root}}}"
OUTPUT_ROOT="${{WDA_V0_2_R1_OUTPUT_ROOT:-{args.output_root}}}"
REPO_DOCS_ROOT="${{WDA_V0_2_R1_REPO_DOCS_ROOT:-{args.repo_docs_root}}}"

"$PYTHON_BIN" -B "$REPO_SCRIPT" \\
  --db "$DB_PATH" \\
  --analysis-root "$ANALYSIS_ROOT" \\
  --output-root "$OUTPUT_ROOT" \\
  --repo-docs-root "$REPO_DOCS_ROOT"
""",
    )
    current = runner.stat().st_mode
    runner.chmod(current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def generate_subject_reports(
    output_root: Path,
    seed: dict[str, Any],
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    reports_root = output_root / "reports"
    contact_root = reports_root / "contact_radar"
    mkdir(contact_root)
    by_subject_messages = group_by(seed["messages"], "subject_id")
    by_subject_hits = group_by(analysis["keyword_hits"], "subject_id")
    by_subject_todo = group_by(analysis["todo"], "subject_id")
    by_subject_opportunity = group_by(analysis["opportunity"], "subject_id")
    by_subject_risk = group_by(analysis["risk"], "subject_id")
    stats = subject_stats_map(analysis)
    behavior = behavior_map(analysis)
    inventory: list[dict[str, Any]] = []

    index_rows = []
    for subject in seed["subjects"]:
        sid = subject["subject_id"]
        label = subject["subject_label"]
        msg_rows = by_subject_messages.get(sid, [])
        hit_rows = by_subject_hits.get(sid, [])
        todo_rows = by_subject_todo.get(sid, [])
        opp_rows = by_subject_opportunity.get(sid, [])
        risk_rows = by_subject_risk.get(sid, [])
        stat_row = stats.get(sid, {})
        behavior_row = behavior.get(sid, {})
        signal_counter = signal_counts(hit_rows)
        first_ts = stat_row.get("first_timestamp_utc") or utc_ms(
            stat_row.get("first_timestamp_ms")
        )
        last_ts = stat_row.get("last_timestamp_utc") or utc_ms(
            stat_row.get("last_timestamp_ms")
        )
        top_categories = ", ".join(
            f"{name}:{count}" for name, count in signal_counter.most_common(5)
        )
        page_name = f"{safe_filename(sid)}.md"
        page_path = contact_root / page_name
        report = report_template(
            f"联系人雷达：{label}",
            [
                f"当前样本中该对象覆盖 {len(msg_rows)} 条消息，时间范围 {first_ts} 到 {last_ts}。",
                f"主要线索集中在：{top_categories or '暂无明显关键词线索'}。",
            ],
            [
                "结论来自本地 SQLite seed、subject_stats.csv、keyword_signal_hits.csv 和各类候选信号表。",
                "这里只描述可观察消息行为和关键词线索，不做性格或心理判断。",
            ],
            [
                f"消息数 `{len(msg_rows)}`；待办候选 `{len(todo_rows)}`；机会候选 `{len(opp_rows)}`；风险候选 `{len(risk_rows)}`。",
                f"方向分布 inbound `{stat_row.get('inbound_count', '0')}` / outbound `{stat_row.get('outbound_count', '0')}` / system `{stat_row.get('system_count', '0')}`。",
            ]
            + signal_lines(hit_rows, limit=8),
            [
                "高频待办、金额、合同、验收、风险词会影响后续跟进优先级。",
                "如果该对象是工作相关联系人，应优先检查未闭环事项和金额/发票/合同线索。",
            ],
            [
                "先处理风险候选，再处理待办候选，最后复核机会候选。",
                "把 evidence message_id 复制到本地 SQLite 查询或 evidence_index 中复核上下文。",
            ],
            [
                "当前 v0.2-R1 本地报告仍基于已验证 500-row seed，不代表全量历史。",
                "关键词命中只能提示线索，不能替代人工判断最终事实。",
            ],
            [
                "纯表情、系统消息、寒暄类短确认可先降权。",
                "没有金额/合同/验收词的普通沟通不必立即进入工作交接。",
            ],
            [
                "可把重复待办转成固定提醒模板。",
                "可把金额/发票/合同/验收线索自动汇总成每周检查表。",
                f"可为该对象设置未闭环事项自动巡检，依据 message_id 和 subject_id `{sid}`。",
            ],
        )
        write_text(page_path, report)
        inventory.append(
            {
                "path": str(page_path),
                "kind": "contact_radar_subject_report",
                "sensitivity": "local_full_sensitive",
                "rows_or_items": len(msg_rows),
            }
        )
        index_rows.append(
            [
                label,
                len(msg_rows),
                len(todo_rows),
                len(opp_rows),
                len(risk_rows),
                f"[打开](./{page_name})",
            ]
        )

    radar_table = table(["对象", "消息", "待办", "机会", "风险", "页面"], index_rows)
    write_text(
        contact_root / "index.md",
        "\n".join(
            [
                "# 联系人雷达",
                "",
                "## 先说结论",
                "",
                f"- 当前样本覆盖 {len(index_rows)} 个 subject/contact radar 页面，应优先查看风险和待办较多的对象。",
                "",
                "## 为什么",
                "",
                "- 联系人雷达把 subject-level 消息数、待办、机会和风险候选集中到一个入口，减少人工翻记录。",
                "",
                "## 证据",
                "",
                radar_table,
                "",
                "## 对我有什么影响",
                "",
                "- 可以把沟通对象按行动优先级排序，而不是只按最近聊天或主观印象处理。",
                "",
                "## 我下一步该做什么",
                "",
                "- 先打开风险候选较多的对象页面，再复核待办和金额/合同/验收线索。",
                "",
                "## 不确定的地方",
                "",
                "- 当前页面基于 v0.1 500-row seed，不代表全量联系人历史。",
                "",
                "## 可忽略的事项",
                "",
                "- 消息量低且无风险/待办/机会线索的对象可以暂时降权。",
                "",
                "## 可自动化/模板化事项",
                "",
                "- 可按风险、待办、机会、金额/合同/验收命中自动生成联系人优先级队列。",
                "",
            ]
        ),
    )
    inventory.append(
        {
            "path": str(contact_root / "index.md"),
            "kind": "contact_radar_index",
            "sensitivity": "local_navigation",
            "rows_or_items": len(index_rows),
        }
    )
    return inventory


def generate_center_reports(
    output_root: Path,
    seed: dict[str, Any],
    analysis: dict[str, Any],
) -> list[dict[str, Any]]:
    reports_root = output_root / "reports"
    mkdir(reports_root)
    inventory: list[dict[str, Any]] = []
    counts = seed["counts"]
    keyword_counter = signal_counts(analysis["keyword_hits"])
    top_signal_text = ", ".join(
        f"{name}:{count}" for name, count in keyword_counter.most_common()
    )

    reports = {
        "today_briefing.md": report_template(
            "今日简报（以当前样本最新窗口为准）",
            [
                f"当前可读工作区已覆盖 {counts.get('messages', 0)} 条消息、{counts.get('conversations', 0)} 个会话、{counts.get('contacts', 0)} 个联系人。",
                "本次最值得先看的不是总量，而是风险、待办、金额/发票/合同/验收、机会四类行动线索。",
            ],
            [
                f"关键词/信号分布：{top_signal_text or '暂无'}。",
                "当前报告来自本地 full-sensitive seed 和 analysis CSV，不调用外部 API。",
            ],
            [
                f"待办候选 `{len(analysis['todo'])}` 条。",
                f"机会候选 `{len(analysis['opportunity'])}` 条。",
                f"风险候选 `{len(analysis['risk'])}` 条。",
                f"金额/发票/合同/验收线索 `{keyword_counter.get('money_payment_invoice_contract_acceptance', 0)}` 条。",
            ],
            [
                "可以把沟通历史直接转成当天可执行检查清单。",
                "可以减少翻聊天记录找信息的时间。",
            ],
            [
                "先看 risk_center.md。",
                "再看 todo_action_center.md。",
                "最后看 opportunity_center.md 和 contact_radar/。",
            ],
            [
                "当前 v0.2-R1 运行于 500-row seed，不代表全量历史。",
                "全量结论要等旧电脑全量自动导出和新电脑全量导入完成。",
            ],
            [
                "普通寒暄、重复确认、系统消息可暂不处理。",
            ],
            [
                "可每日自动生成 briefing。",
                "可把风险/待办/机会分别生成固定任务列表。",
            ],
        ),
        "todo_action_center.md": report_template(
            "待办行动中心",
            [f"发现 {len(analysis['todo'])} 条待办/承诺候选，建议按风险和时间优先级复核。"],
            ["候选来自固定关键词匹配，例如需要、今天、明天、安排、提交、确认、回复。"],
            signal_lines(analysis["todo"], limit=20),
            ["待办遗漏会直接影响交付、付款、客户跟进和内部协作。"],
            ["逐条复核 evidence message_id，把仍有效事项转入真实任务系统。"],
            ["关键词命中不等于真实未完成；需要结合上下文判断是否已闭环。"],
            ["已完成、已撤销、纯讨论的事项可忽略。"],
            ["可自动转为待办草稿；可按联系人生成跟进模板。"],
        ),
        "risk_center.md": report_template(
            "风险中心",
            [f"发现 {len(analysis['risk'])} 条风险/阻塞候选，应优先复核。"],
            ["风险候选来自问题、风险、不行、错等固定词，不做主观推断。"],
            signal_lines(analysis["risk"], limit=20),
            ["风险线索可能影响交付、回款、客户关系或内部协同。"],
            ["先确认是否仍未解决，再为未解决项指定责任人、截止时间和下一步沟通。"],
            ["短句风险词可能只是口语表达，需要读上下文确认。"],
            ["已解决或无业务影响的吐槽可忽略。"],
            ["可自动生成风险台账草稿和每周复盘清单。"],
        ),
        "opportunity_center.md": report_template(
            "机会中心",
            [f"发现 {len(analysis['opportunity'])} 条机会候选，可作为业务跟进池。"],
            ["机会候选来自项目、计划、报价、方案、客户、需求等词。"],
            signal_lines(analysis["opportunity"], limit=20),
            ["机会线索可以帮助识别潜在项目、客户需求和下一轮报价/方案动作。"],
            ["按客户/联系人复核，筛出仍有价值的机会，并补一个下一步动作。"],
            ["关键词命中只能提示可能性，不代表机会真实成立。"],
            ["历史已失效项目、纯泛聊需求可忽略。"],
            ["可自动形成机会清单、报价提醒、方案跟进模板。"],
        ),
        "work_handoff_summary.md": report_template(
            "工作交接总结",
            [
                "当前样本可以形成第一版交接提纲：风险、待办、金额/合同/验收、机会、联系人雷达。",
            ],
            ["交接内容来自本地消息证据，不依赖记忆或主观补写。"],
            [
                f"待办候选 `{len(analysis['todo'])}`。",
                f"风险候选 `{len(analysis['risk'])}`。",
                f"机会候选 `{len(analysis['opportunity'])}`。",
                f"金额/发票/合同/验收线索 `{keyword_counter.get('money_payment_invoice_contract_acceptance', 0)}`。",
            ],
            ["交接人可以少讲背景，直接按证据列表交接。"],
            ["先把 risk_center、todo_action_center、evidence_index 三个文件作为交接附件。"],
            ["全量历史尚未导入，不能作为最终完整交接包。"],
            ["无 evidence_id 的主观判断不应进入正式交接。"],
            ["可按 subject/contact 自动生成交接模板。"],
        ),
        "work_information_summary.md": report_template(
            "工作信息总结",
            ["当前样本已能抽取工作信息线索，但不应声称覆盖所有历史工作信息。"],
            ["信息线索主要来自金额、发票、合同、验收、项目、方案、客户、需求等关键词。"],
            [
                f"金额/发票/合同/验收线索 `{keyword_counter.get('money_payment_invoice_contract_acceptance', 0)}`。",
                f"机会/项目信息线索 `{keyword_counter.get('opportunity', 0)}`。",
            ]
            + signal_lines(
                [
                    r
                    for r in analysis["keyword_hits"]
                    if r.get("signal_category")
                    in {
                        "money_payment_invoice_contract_acceptance",
                        "opportunity",
                    }
                ],
                limit=15,
            ),
            ["可以把聊天记录中散落的业务信息变成可查的证据索引。"],
            ["优先复核金额、发票、合同、验收类线索，再补充项目状态。"],
            ["非文本消息和图片/文件内容未解析，可能遗漏附件里的关键信息。"],
            ["表情、确认收到、不含业务词的寒暄可忽略。"],
            ["可自动生成项目/客户信息卡片。"],
        ),
        "work_optimization.md": report_template(
            "工作优化建议",
            [
                "优化重点不是增加报表，而是把风险、待办、金额/合同/验收线索自动前置。",
            ],
            ["当前样本显示可行动线索分散在多个联系人/会话，需要自动聚合。"],
            [
                f"全部信号命中 `{len(analysis['keyword_hits'])}`。",
                f"待办 `{len(analysis['todo'])}` / 风险 `{len(analysis['risk'])}` / 机会 `{len(analysis['opportunity'])}`。",
            ],
            ["减少手动翻记录、减少遗漏付款/发票/合同/验收和待办。"],
            [
                "建立每日 briefing。",
                "建立每周风险/待办复盘。",
                "金额/合同/验收线索单独进入工作检查表。",
            ],
            ["当前样本太小，不能评估全量工作负载。"],
            ["纯技术验证 CSV 可以降为后台，不作为用户主入口。"],
            ["可自动生成例会材料、交接摘要和客户跟进清单。"],
        ),
        "personal_behavior_review.md": report_template(
            "个人行为优化",
            ["当前只给出可观察沟通行为建议，不做心理或性格判断。"],
            ["依据方向分布、问号/感叹号、短确认、活跃时间等可观察指标。"],
            [
                f"behavior_pattern_indicators rows `{len(analysis['behavior'])}`。",
                "详见各 subject 的 inbound/outbound/system、question_marker_count、short_ack_count。",
            ],
            ["有助于发现哪些沟通容易只停留在确认，哪些需要明确下一步。"],
            [
                "对待办类消息主动补截止时间。",
                "对风险类消息主动补责任人和下一步。",
                "对金额/合同/验收类消息主动补证据附件位置。",
            ],
            ["当前样本不是全量历史，不评估长期行为特征。"],
            ["不含业务线索的情绪化短句不作为优化依据。"],
            ["可自动提示“这条消息是否需要截止时间/责任人/附件”。"],
        ),
        "relationship_roi.md": report_template(
            "关系投入 ROI",
            ["当前只能做关系投入线索排序，不能计算真实 ROI 金额。"],
            ["ROI 线索来自消息量、待办、风险、机会、金额/合同/验收命中。"],
            [
                f"联系人/subject 数 `{counts.get('subjects', 0)}`。",
                f"机会候选 `{len(analysis['opportunity'])}`；风险候选 `{len(analysis['risk'])}`。",
            ],
            ["帮助判断哪些联系人需要优先投入时间，哪些可以模板化处理。"],
            ["优先关注高风险、高机会、高金额/合同/验收线索对象。"],
            ["未接入全量历史和真实成交/回款数据，不能得出财务 ROI。"],
            ["低业务线索、重复寒暄可降低优先级。"],
            ["可自动生成联系人优先级队列。"],
        ),
    }

    for name, content in reports.items():
        path = reports_root / name
        write_text(path, content)
        inventory.append(
            {
                "path": str(path),
                "kind": "human_readable_report",
                "sensitivity": "local_full_sensitive",
                "rows_or_items": "mixed",
            }
        )

    evidence_rows = []
    for row in analysis["keyword_hits"]:
        evidence_rows.append(
            f"- `{row.get('message_id')}` / `{row.get('conversation_id')}` / "
            f"{utc_ms(row.get('timestamp_ms'))} / `{row.get('signal_category')}` / "
            f"`{row.get('term')}`：{excerpt(row.get('text_full_sensitive'))}"
        )
    write_text(
        reports_root / "evidence_index.md",
        "\n".join(
            [
                "# 证据索引",
                "",
                "## 先说结论",
                "",
                "- 本文件是本地 full-sensitive 证据索引，用于把结论追溯到 message_id、conversation_id、timestamp 和本地文本摘录。",
                "",
                "## 为什么",
                "",
                "- WDA 的行动建议必须能回到具体证据，避免只生成无法复核的总结。",
                "",
                "## 证据",
                "",
                *evidence_rows[:1000],
                "",
                "## 对我有什么影响",
                "",
                "- 你可以从任何报告跳回 evidence message_id，确认原始上下文后再行动。",
                "",
                "## 我下一步该做什么",
                "",
                "- 复核风险、待办、金额/合同/验收类证据，确认哪些仍需处理。",
                "",
                "## 不确定的地方",
                "",
                "- 当前索引只覆盖已导入样本；非文本消息和附件内容未被解析。",
                "",
                "## 可忽略的事项",
                "",
                "- 已闭环、无业务影响、纯寒暄或系统消息类证据可降权。",
                "",
                "## 可自动化/模板化事项",
                "",
                "- 可按 evidence category 自动生成待办草稿、风险台账、机会池和交接附件。",
                "",
                "本文件不要提交到 GitHub。",
                "",
            ]
        ),
    )
    inventory.append(
        {
            "path": str(reports_root / "evidence_index.md"),
            "kind": "evidence_index",
            "sensitivity": "local_full_sensitive",
            "rows_or_items": len(evidence_rows),
        }
    )
    return inventory


def generate_dashboard(
    output_root: Path,
    seed: dict[str, Any],
    analysis: dict[str, Any],
    inventory: list[dict[str, Any]],
) -> None:
    dashboard_root = output_root / "dashboard"
    mkdir(dashboard_root)
    counts = seed["counts"]
    cards = [
        ("消息", counts.get("messages", 0)),
        ("会话", counts.get("conversations", 0)),
        ("联系人", counts.get("contacts", 0)),
        ("Subjects", counts.get("subjects", 0)),
        ("待办候选", len(analysis["todo"])),
        ("风险候选", len(analysis["risk"])),
        ("机会候选", len(analysis["opportunity"])),
        ("关键词信号", len(analysis["keyword_hits"])),
    ]
    report_links = [
        ("今日简报", "../reports/today_briefing.md"),
        ("联系人雷达", "../reports/contact_radar/index.md"),
        ("工作交接总结", "../reports/work_handoff_summary.md"),
        ("工作信息总结", "../reports/work_information_summary.md"),
        ("工作优化建议", "../reports/work_optimization.md"),
        ("待办行动中心", "../reports/todo_action_center.md"),
        ("风险中心", "../reports/risk_center.md"),
        ("机会中心", "../reports/opportunity_center.md"),
        ("个人行为优化", "../reports/personal_behavior_review.md"),
        ("关系投入 ROI", "../reports/relationship_roi.md"),
        ("证据索引", "../reports/evidence_index.md"),
        ("操作指南", "../operator_guide.md"),
    ]
    md = [
        "# WDA v0.2-R1 中文情报工作区",
        "",
        "## 先说结论",
        "",
        "- 这是本地 full-sensitive 工作区入口，不要提交到 GitHub。",
        "- 当前报告基于 v0.1 已验证 500-row seed；全量会话需要旧电脑全量 exporter runner 完成后再导入。",
        "- 优先阅读：今日简报 -> 风险中心 -> 待办行动中心 -> 联系人雷达 -> 证据索引。",
        "",
        "## 数据概览",
        "",
        table(["指标", "数量"], cards),
        "",
        "## 报告入口",
        "",
    ]
    md.extend(f"- [{label}]({href})" for label, href in report_links)
    write_text(dashboard_root / "index.md", "\n".join(md))

    cards_html = "\n".join(
        f"<div class='card'><div class='num'>{html.escape(str(value))}</div><div>{html.escape(label)}</div></div>"
        for label, value in cards
    )
    links_html = "\n".join(
        f"<li><a href='{html.escape(href)}'>{html.escape(label)}</a></li>"
        for label, href in report_links
    )
    write_text(
        dashboard_root / "index.html",
        f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WDA v0.2-R1 中文情报工作区</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", sans-serif; margin: 32px; line-height: 1.6; color: #202124; background: #f8f9fb; }}
    main {{ max-width: 1080px; margin: auto; }}
    h1 {{ font-size: 28px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 12px; margin: 20px 0; }}
    .card {{ background: #fff; border: 1px solid #dde2ea; border-radius: 8px; padding: 14px; }}
    .num {{ font-size: 26px; font-weight: 700; }}
    section {{ background: #fff; border: 1px solid #dde2ea; border-radius: 8px; padding: 18px; margin: 16px 0; }}
    a {{ color: #1557b0; }}
  </style>
</head>
<body>
<main>
  <h1>WDA v0.2-R1 中文情报工作区</h1>
  <section>
    <h2>先说结论</h2>
    <p>这是本地 full-sensitive 工作区入口。当前报告基于 v0.1 已验证 500-row seed；全量会话需要旧电脑全量 exporter runner 完成后再导入。</p>
    <p>推荐阅读顺序：今日简报 -> 风险中心 -> 待办行动中心 -> 联系人雷达 -> 证据索引。</p>
  </section>
  <div class="cards">{cards_html}</div>
  <section>
    <h2>报告入口</h2>
    <ul>{links_html}</ul>
  </section>
</main>
</body>
</html>
""",
    )
    inventory.extend(
        [
            {
                "path": str(dashboard_root / "index.html"),
                "kind": "dashboard",
                "sensitivity": "local_navigation",
                "rows_or_items": len(cards),
            },
            {
                "path": str(dashboard_root / "index.md"),
                "kind": "dashboard",
                "sensitivity": "local_navigation",
                "rows_or_items": len(cards),
            },
        ]
    )


def create_operator_guide(output_root: Path, args: argparse.Namespace) -> None:
    write_text(
        output_root / "operator_guide.md",
        f"""# WDA v0.2-R1 Operator Guide

## 先说结论

- 新电脑运行一条命令即可重新生成本地中文工作区。
- 旧电脑全量导出仍需按 `old_computer_export_runner_spec.md` 固化一次性 runner。
- 本地 full-sensitive 输出只放在 `{output_root}`，不要提交到 GitHub。

## 新电脑一键命令

```bash
{output_root}/run_wda_v0_2_r1.sh
```

## 打开报告

- HTML dashboard: `{output_root}/dashboard/index.html`
- Markdown dashboard: `{output_root}/dashboard/index.md`
- 报告目录: `{output_root}/reports/`

## 查询本地 SQLite

```bash
sqlite3 'file:{args.db}?mode=ro' < {output_root}/query_examples.sql
```

## 不要提交

- raw messages
- contacts
- SQLite database
- Raw Import Pack
- transfer bundle
- key material
- decrypted DBs
- `{output_root}/reports/` 下的 full-sensitive 内容

## 旧电脑仍需一次性 setup

- 固化 pinned `wechat-cli` / `wxkey` full export runner。
- 自动 all-conversations 导出、chunk、checkpoint、resume。
- 只转移 message-level transfer bundle，不转移 key/config/DB/log/tool_work/sensitive_local_state。
""",
    )


def create_validation_report(
    output_root: Path,
    args: argparse.Namespace,
    seed: dict[str, Any],
    analysis: dict[str, Any],
    inventory: list[dict[str, Any]],
) -> dict[str, Any]:
    report = {
        "generated_at": now_iso(),
        "db_path": str(args.db),
        "analysis_root": str(args.analysis_root),
        "output_root": str(args.output_root),
        "sqlite_open_mode": "read_only",
        "sqlite_integrity_check": seed["integrity"],
        "counts": seed["counts"],
        "noise_hits_李晶工作交接": seed["noise_hits"],
        "analysis_rows": {
            "subject_stats": len(analysis["subject_stats"]),
            "subject_timeline": len(analysis["subject_timeline"]),
            "keyword_signal_hits": len(analysis["keyword_hits"]),
            "todo_signal_candidates": len(analysis["todo"]),
            "opportunity_signal_candidates": len(analysis["opportunity"]),
            "risk_signal_candidates": len(analysis["risk"]),
            "behavior_pattern_indicators": len(analysis["behavior"]),
        },
        "local_inventory_items": len(inventory),
        "rag_web_matrix_started": False,
        "wechat_exporter_run": False,
        "external_hard_drive_accessed": False,
        "openai_api_called_with_raw_content": False,
        "repo_raw_content_written": False,
        "current_automation": "new_computer_local_report_generation",
        "still_needs_one_time_old_computer_setup": True,
    }
    write_json(output_root / "validation_report.json", report)
    return report


def write_inventory(output_root: Path, inventory: list[dict[str, Any]]) -> None:
    write_csv(
        output_root / "report_inventory.csv",
        ["path", "kind", "sensitivity", "rows_or_items"],
        inventory,
    )


def generate_repo_docs(
    repo_docs_root: Path,
    output_root: Path,
    validation: dict[str, Any],
) -> None:
    mkdir(repo_docs_root)
    counts = validation["counts"]
    analysis_rows = validation["analysis_rows"]
    docs: dict[str, str] = {
        "README.md": f"""# WDA v0.2-R1 Full-Auto Human-Readable Workspace

## Summary

v0.2-R1 creates a local Chinese human-readable intelligence workspace from the
existing WDA Data Core seed and analysis layer.

Local output root:

`{output_root}`

Repo-safe scope:

- pipeline/runbook/specification
- aggregate counts
- report inventory
- validation and privacy boundary

No raw message content, contacts, SQLite DB, transfer bundle, keys, or decrypted
DB files are committed.
""",
        "full_auto_pipeline_design.md": """# Full-Auto Pipeline Design

## Current Automation

- New computer: one command regenerates local dashboard and Chinese reports from
  the existing local SQLite seed and analysis outputs.
- Local reports are full-sensitive and stay under WDA_MetaData.

## Full-Coverage Target

- Old computer: one command performs all-conversation export with chunking,
  checkpointing, resume, checksums, and failure logs.
- New computer: one command validates transfer bundle, imports into local Data
  Core, runs deterministic analysis, and generates Chinese reports.

## Boundary

This sprint does not run the old-computer exporter and does not claim full
coverage has already been produced.
""",
        "one_command_runbook.md": f"""# One-Command Runbook

## New Computer

```bash
{output_root}/run_wda_v0_2_r1.sh
```

Primary local entry:

`{output_root}/dashboard/index.html`

## Old Computer Target

The old computer still needs a pinned full-export runner. The target command is
documented in the local `old_computer_export_runner_spec.md`.

## Operator Impact

The user should not manually select every contact, manually create readable
artifacts, or repeatedly move files by hand.
""",
        "report_layer_summary.md": f"""# Report Layer Summary

## Generated Local Reports

- dashboard/index.html
- dashboard/index.md
- reports/today_briefing.md
- reports/contact_radar/
- reports/work_handoff_summary.md
- reports/work_information_summary.md
- reports/work_optimization.md
- reports/todo_action_center.md
- reports/risk_center.md
- reports/opportunity_center.md
- reports/personal_behavior_review.md
- reports/relationship_roi.md
- reports/evidence_index.md
- operator_guide.md

## Human Report Contract

Every human-facing report uses these Chinese sections:

- 先说结论
- 为什么
- 证据
- 对我有什么影响
- 我下一步该做什么
- 不确定的地方
- 可忽略的事项
- 可自动化/模板化事项
""",
        "automation_boundary.md": """# Automation Boundary

## Automated Now

- Read-only SQLite seed validation.
- Existing analysis output validation.
- Local Chinese dashboard/report generation.
- Local config, runbook, and operator guide generation.
- Repo-safe documentation generation.

## Still Needs One-Time Old-Computer Setup

- Pinned full-export runner.
- All-conversation export command.
- Chunk/checkpoint/resume hardening.
- Transfer bundle validation against full export.

## Not Started

- RAG.
- Web app.
- Matrix.
- Media DB handling.
- Full Raw Gate Go.
""",
        "old_computer_export_runner_spec.md": """# Old-Computer Export Runner Spec

The old computer should run the pinned `wechat-cli` / `wxkey` route because the
live-read path has already produced bounded message-level exports.

The full runner must:

- export all conversations without manual per-contact selection
- write only under WDA_MetaData
- use chunking, checkpointing, resume, checksums, and failure logs
- exclude key material, configs, DB files, raw logs, tool_work, and
  sensitive_local_state from transfer
- keep include_media_paths=false until media readiness is separately approved

This sprint does not execute the exporter.
""",
        "new_computer_import_runner_spec.md": """# New-Computer Import Runner Spec

The new computer is the WDA Control Plane. v0.2-R1 currently runs the local
report generator over the existing seed and analysis layer.

For full coverage, the next runner must perform:

1. transfer bundle checksum validation
2. forbidden-file exclusion validation
3. Raw Import Pack conversion
4. local Data Core import
5. deterministic analysis
6. Chinese report generation

All databases and full-sensitive outputs must stay under WDA_MetaData.
""",
        "privacy_and_repo_safety.md": """# Privacy and Repo Safety

## Allowed Locally

- Full-sensitive local analysis.
- Full-sensitive local reports under WDA_MetaData.
- Raw content use for local evidence-backed summaries.

## Forbidden in Git

- raw messages
- contacts
- SQLite DB
- Raw Import Pack
- transfer bundle
- keys
- decrypted DBs
- full-sensitive reports

## Forbidden Operationally

- raw data upload
- OpenAI API calls with raw content
- running new WeChat exporter tools in this sprint
- external hard drive access in this sprint
""",
        "validation_report.md": f"""# Validation Report

## Data Counts

| Item | Count |
| --- | ---: |
| messages | {counts.get('messages', 0)} |
| conversations | {counts.get('conversations', 0)} |
| contacts | {counts.get('contacts', 0)} |
| subjects | {counts.get('subjects', 0)} |
| media_index | {counts.get('media_index', 0)} |

## Analysis Rows

| Item | Count |
| --- | ---: |
| subject_stats | {analysis_rows.get('subject_stats', 0)} |
| subject_timeline | {analysis_rows.get('subject_timeline', 0)} |
| keyword_signal_hits | {analysis_rows.get('keyword_signal_hits', 0)} |
| todo_signal_candidates | {analysis_rows.get('todo_signal_candidates', 0)} |
| opportunity_signal_candidates | {analysis_rows.get('opportunity_signal_candidates', 0)} |
| risk_signal_candidates | {analysis_rows.get('risk_signal_candidates', 0)} |
| behavior_pattern_indicators | {analysis_rows.get('behavior_pattern_indicators', 0)} |

SQLite read-only open: pass.

SQLite integrity check: `{validation['sqlite_integrity_check']}`.

`李晶工作交接` hits: `{validation['noise_hits_李晶工作交接']}`.

RAG/Web/Matrix started: `false`.
""",
        "updated_handoff_note.md": f"""# Updated Handoff Note

v0.2-R1 generated a local Chinese human-readable intelligence workspace under:

`{output_root}`

Repo-safe docs live under:

`WDA/docs/v0_2_r1_full_auto_human_readable_workspace/`

Raw Gate remains below full Go. v0.2-R1 proves a productized local report layer
over the existing seed; it does not prove full-history export completion.
""",
    }
    for name, content in docs.items():
        write_text(repo_docs_root / name, content)

    inventory_rows = []
    for relative_path, sensitivity in [
        ("dashboard/index.html", "local_navigation"),
        ("dashboard/index.md", "local_navigation"),
        ("reports/today_briefing.md", "local_full_sensitive_report"),
        ("reports/contact_radar/", "local_full_sensitive_report_dir"),
        ("reports/work_handoff_summary.md", "local_full_sensitive_report"),
        ("reports/work_information_summary.md", "local_full_sensitive_report"),
        ("reports/work_optimization.md", "local_full_sensitive_report"),
        ("reports/todo_action_center.md", "local_full_sensitive_report"),
        ("reports/risk_center.md", "local_full_sensitive_report"),
        ("reports/opportunity_center.md", "local_full_sensitive_report"),
        ("reports/personal_behavior_review.md", "local_full_sensitive_report"),
        ("reports/relationship_roi.md", "local_full_sensitive_report"),
        ("reports/evidence_index.md", "local_full_sensitive_report"),
        ("operator_guide.md", "local_operator_guide"),
        ("run_wda_v0_2_r1.sh", "local_runner"),
        ("config/export_policy.yaml", "local_pipeline_config"),
        ("config/analysis_policy.yaml", "local_pipeline_config"),
        ("config/privacy_policy.yaml", "local_pipeline_config"),
        ("config/report_templates.yaml", "local_pipeline_config"),
        ("old_computer_export_runner_spec.md", "local_pipeline_spec"),
        ("new_computer_import_runner_spec.md", "local_pipeline_spec"),
        ("transfer_policy.md", "local_pipeline_spec"),
        ("full_auto_runbook.md", "local_runbook"),
    ]:
        inventory_rows.append(
            {
                "local_path": str(output_root / relative_path),
                "sensitivity": sensitivity,
                "git_policy": "do_not_commit_local_output",
            }
        )
    write_csv(
        repo_docs_root / "local_product_output_inventory.csv",
        ["local_path", "sensitivity", "git_policy"],
        inventory_rows,
    )


def main() -> int:
    args = parse_args()
    mkdir(args.output_root)
    mkdir(args.repo_docs_root)
    seed = fetch_seed(args.db)
    analysis = load_analysis(args.analysis_root)

    inventory: list[dict[str, Any]] = []
    create_configs(args.output_root)
    create_pipeline_specs(args.output_root)
    make_query_examples(args.output_root, args.db)
    create_local_runner(args.output_root, Path(__file__).resolve(), args)
    inventory.extend(generate_subject_reports(args.output_root, seed, analysis))
    inventory.extend(generate_center_reports(args.output_root, seed, analysis))
    generate_dashboard(args.output_root, seed, analysis, inventory)
    create_operator_guide(args.output_root, args)
    validation = create_validation_report(args.output_root, args, seed, analysis, inventory)
    write_inventory(args.output_root, inventory)
    generate_repo_docs(args.repo_docs_root, args.output_root, validation)

    print(
        json.dumps(
            {
                "status": "pass",
                "output_root": str(args.output_root),
                "repo_docs_root": str(args.repo_docs_root),
                "messages": seed["counts"].get("messages", 0),
                "subjects": seed["counts"].get("subjects", 0),
                "reports": len(inventory),
                "sqlite_integrity": seed["integrity"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
