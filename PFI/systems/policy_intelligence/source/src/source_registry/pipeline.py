from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .analyzer import CODEX_ANALYSIS_MODE, TEMPLATE_ANALYSIS_MODE, codex_analysis, template_analysis
from .attachment_parser import extract_attachment_text
from .collector import HttpFetcher, clean_title, discover_documents, parse_html, save_snapshot
from .content_db import (
    begin_run,
    complete_run,
    connect_content,
    content_hash,
    document_by_id,
    document_with_analysis,
    init_content_database,
    append_report_timeline,
    mark_report_generated,
    next_report_run_id,
    report_timeline,
    upsert_external_reference_gaps,
    upsert_analysis,
    upsert_document,
)
from .db import connect, init_database
from .interpretation import (
    collect_interpretation_items,
    count_reference_items,
    interpretation_health_stats,
    interpretation_context_by_document,
    reference_platforms,
    seed_interpretation_sources,
)
from .monitor import write_monitor_status
from .queueing import queue_preview, sync_report_queue
from .reference_gaps import external_reference_gap_summary_for_items, external_reference_gaps_for_items
from .reporting import report_file_name, write_policy_report


@dataclass(frozen=True)
class PipelineConfig:
    source_db_path: Path
    content_db_path: Path
    data_dir: Path
    report_dir: Path
    max_sources: int = 5
    max_pages_per_source: int = 2
    max_links_per_page: int = 20
    max_analyze: int = 20
    min_authority_score: int = 60
    analysis_mode: str = "template"
    mode: str = "manual"
    allow_insecure_tls: bool = False
    interpretation_source_file: Path | None = Path("config/interpretation_sources.json")
    industry_priority_file: Path | None = Path("config/industry_priorities.json")
    document_since: str | None = "2025-01-01"
    max_interpretation_documents: int = 10
    fetch_interpretation_results: bool = False
    min_external_references_per_report: int = 5
    min_external_platforms_per_report: int = 2
    bilibili_cookie_file: Path | None = None
    search_secrets_file: Path | None = None
    platform_auth_file: Path | None = None
    fetch_search_result_pages: bool = False
    interpretation_request_timeout: int = 20
    interpretation_request_retries: int = 1
    interpretation_request_delay_seconds: float = 0.0
    quality_rules_file: Path | None = Path("rules/quality_gates.json")


def run_pipeline(config: PipelineConfig, fetcher: Any | None = None) -> dict[str, Any]:
    lock_path = config.data_dir / "pipeline.lock"
    with _pipeline_lock(lock_path):
        source_conn = None
        content_conn = None
        run_id = None
        target_analysis_mode = (
            CODEX_ANALYSIS_MODE if config.analysis_mode == "codex" else TEMPLATE_ANALYSIS_MODE
        )
        try:
            source_conn = connect(config.source_db_path)
            init_database(source_conn)
            content_conn = connect_content(config.content_db_path)
            init_content_database(content_conn)
            run_id = next_report_run_id(content_conn)
            begin_run(content_conn, run_id, config.mode)

            stats = {
                "sources_considered": 0,
                "pages_fetched": 0,
                "documents_discovered": 0,
                "new_documents": 0,
                "analyzed_documents": 0,
                "interpretation_items": 0,
                "external_reference_count": 0,
                "external_platform_count": 0,
                "min_external_references": config.min_external_references_per_report,
                "min_external_platforms": config.min_external_platforms_per_report,
                "external_reference_deficit": config.min_external_references_per_report,
                "external_platform_deficit": config.min_external_platforms_per_report,
                "external_reference_gaps": 0,
                "interpretation_attempts": 0,
                "interpretation_reference_successes": 0,
                "interpretation_leads": 0,
                "interpretation_missing_api_keys": 0,
                "interpretation_auth_required": 0,
                "interpretation_failed_requests": 0,
                "interpretation_search_landings": 0,
                "interpretation_auth_configured": 0,
                "interpretation_auth_missing": 0,
                "interpretation_auth_parser_pending": 0,
                "article_pages_fetched": 0,
                "article_excerpts_extracted": 0,
                "article_pages_blocked": 0,
                "article_pages_failed": 0,
                "public_site_searches": 0,
                "public_site_results": 0,
                "public_search_html_searches": 0,
                "public_search_html_results": 0,
                "video_details_enriched": 0,
                "video_author_profiles_enriched": 0,
                "video_subtitles_extracted": 0,
                "video_comments_extracted": 0,
                "video_danmaku_extracted": 0,
                "attachments_parsed": 0,
                "attachment_parse_failures": 0,
                "queued_reports": 0,
                "document_since": config.document_since or "",
            }
            report_path = None
            report_artifacts = {}
            try:
                selected_fetcher = fetcher or HttpFetcher(
                    allow_insecure_tls=config.allow_insecure_tls
                )
                sources = _crawl_sources(source_conn, config.min_authority_score, config.max_sources)
                stats["sources_considered"] = len(sources)
                for source in sources:
                    for page_url in _source_entry_urls(source_conn, source)[: config.max_pages_per_source]:
                        try:
                            result = selected_fetcher.fetch(page_url)
                        except Exception as exc:
                            _append_error(config.data_dir, run_id, f"fetch failed {page_url}: {exc}")
                            continue
                        stats["pages_fetched"] += 1
                        snapshot_path = save_snapshot(
                            config.data_dir,
                            run_id,
                            source["source_id"],
                            result.url,
                            result.body,
                            result.content_type,
                        )
                        if "html" not in result.content_type.lower() and not result.url.endswith((".html", ".htm", "/")):
                            doc = _document_for_fetched_resource(source, result, snapshot_path)
                            _, is_new = upsert_document(content_conn, doc, run_id)
                            stats["documents_discovered"] += 1
                            stats["new_documents"] += int(is_new)
                            continue

                        html = result.text
                        for doc in discover_documents(source, result.url, html, config.max_links_per_page):
                            if doc["url"] == result.url:
                                doc["snapshot_path"] = snapshot_path
                            _, is_new = upsert_document(content_conn, doc, run_id)
                            stats["documents_discovered"] += 1
                            stats["new_documents"] += int(is_new)

                sync_report_queue(
                    content_conn,
                    source_conn,
                    run_id,
                    target_analysis_mode,
                    industry_config_path=config.industry_priority_file,
                    document_since=config.document_since,
                )
                queue_before = queue_preview(content_conn, target_analysis_mode, limit=30)
                stats["queued_reports"] = len(queue_before)
                active_industry_rank = _active_industry_rank(queue_before)
                active_industry_name = _active_industry_name(queue_before, active_industry_rank)
                stats["active_industry_rank"] = active_industry_rank if active_industry_rank is not None else 0
                target_queue_item = None
                analysis_candidates = []
                interpretation_items = []
                if config.interpretation_source_file and config.interpretation_source_file.exists():
                    seed_interpretation_sources(content_conn, config.interpretation_source_file)
                candidates = _next_generation_candidates(queue_before)
                selected_candidate = None
                selected_items: list[dict[str, Any]] = []
                selected_reference_count = 0
                selected_platform_count = 0
                for candidate in candidates:
                    document = document_by_id(content_conn, candidate["document_id"])
                    document = _enrich_document_detail(
                        content_conn,
                        selected_fetcher,
                        config.data_dir,
                        run_id,
                        document,
                    )
                    if document.get("document_type") == "attachment":
                        if document.get("text_excerpt"):
                            stats["attachments_parsed"] += 1
                        else:
                            stats["attachment_parse_failures"] += 1
                    candidate_items: list[dict[str, Any]] = []
                    if config.interpretation_source_file and config.interpretation_source_file.exists():
                        candidate_items = collect_interpretation_items(
                            content_conn,
                            run_id,
                            [document],
                            max_documents=1,
                            min_reference_items=config.min_external_references_per_report,
                            fetch_online=config.fetch_interpretation_results,
                            allow_insecure_tls=config.allow_insecure_tls,
                            bilibili_cookie_file=config.bilibili_cookie_file,
                            search_secrets_file=config.search_secrets_file,
                            platform_auth_file=config.platform_auth_file,
                            fetch_search_result_pages=config.fetch_search_result_pages,
                            request_timeout=config.interpretation_request_timeout,
                            request_retries=config.interpretation_request_retries,
                            request_delay_seconds=config.interpretation_request_delay_seconds,
                        )
                    reference_count = count_reference_items(candidate_items)
                    platform_count = len(reference_platforms(candidate_items))
                    selected_candidate = (candidate, document)
                    selected_items = candidate_items
                    selected_reference_count = reference_count
                    selected_platform_count = platform_count

                if selected_candidate:
                    target_queue_item, target_document = selected_candidate
                    analysis_candidates.append(target_document)
                    interpretation_items = selected_items
                    if active_industry_name:
                        stats["active_industry_name"] = active_industry_name
                    stats["interpretation_items"] = len(interpretation_items)
                    stats.update(interpretation_health_stats(interpretation_items))
                    reference_gaps = external_reference_gaps_for_items(interpretation_items)
                    upsert_external_reference_gaps(content_conn, reference_gaps)
                    gap_summary = external_reference_gap_summary_for_items(interpretation_items)
                    stats["external_reference_gaps"] = int(gap_summary.get("pending_count", 0) or 0)
                    stats["external_reference_count"] = max(0, selected_reference_count)
                    stats["external_platform_count"] = max(0, selected_platform_count)
                    stats["external_reference_deficit"] = max(
                        0,
                        config.min_external_references_per_report
                        - stats["external_reference_count"],
                    )
                    stats["external_platform_deficit"] = max(
                        0,
                        config.min_external_platforms_per_report
                        - stats["external_platform_count"],
                    )
                    stats["quality_gate_met"] = int(
                        stats["external_reference_deficit"] == 0
                        and stats["external_platform_deficit"] == 0
                    )

                interpretation_map = interpretation_context_by_document(interpretation_items)
                report_documents = []
                for document in analysis_candidates:
                    related_items = interpretation_map.get(str(document["document_id"]), [])
                    analysis = (
                        codex_analysis(document, related_items)
                        if config.analysis_mode == "codex"
                        else template_analysis(document, related_items)
                    )
                    upsert_analysis(content_conn, analysis, run_id)
                    stats["analyzed_documents"] += 1
                    report_documents.append(
                        document_with_analysis(
                            content_conn,
                            document["document_id"],
                            target_analysis_mode,
                        )
                    )

                if report_documents:
                    target_document_id = str(report_documents[0]["document_id"])
                    quality_gate_met = bool(stats.get("quality_gate_met"))
                    pending_after_current = (
                        [item for item in queue_before if item["document_id"] != target_document_id]
                        if quality_gate_met
                        else queue_before
                    )[:12]
                    report_path_candidate = _unique_report_path(
                        config.report_dir / report_file_name(run_id, report_documents)
                    )
                    current_timeline_event = {
                        "event_type": "generated" if quality_gate_met else "quality_gap",
                        "run_id": run_id,
                        "document_id": target_document_id,
                        "report_path": str(report_path_candidate),
                        "title": report_documents[0].get("title"),
                        "source_name": report_documents[0].get("source_name"),
                        "primary_industry": target_queue_item.get("primary_industry")
                        if target_queue_item
                        else None,
                        "administrative_level": target_queue_item.get("administrative_level")
                        if target_queue_item
                        else None,
                    }
                    timeline_items = [current_timeline_event] + report_timeline(content_conn, limit=12)
                else:
                    pending_after_current = queue_before[:12]
                    report_path_candidate = _unique_report_path(
                        config.report_dir / report_file_name(run_id, [])
                    )
                    timeline_items = report_timeline(content_conn, limit=12)

                report_artifacts = write_policy_report(
                    report_path_candidate,
                    run_id,
                    stats,
                    report_documents,
                    interpretation_items,
                    queue_items=pending_after_current,
                    timeline_items=timeline_items,
                )
                report_path = report_artifacts["pdf_path"]
                if report_documents:
                    target_document_id = str(report_documents[0]["document_id"])
                    quality_gate_met = bool(stats.get("quality_gate_met"))
                    if quality_gate_met:
                        mark_report_generated(
                            content_conn,
                            target_document_id,
                            target_analysis_mode,
                            run_id,
                            report_path,
                        )
                    append_report_timeline(
                        content_conn,
                        {
                            "run_id": run_id,
                            "document_id": target_document_id,
                            "event_type": "generated" if quality_gate_met else "quality_gap",
                            "report_path": report_path,
                            "primary_industry": target_queue_item.get("primary_industry")
                            if target_queue_item
                            else None,
                            "administrative_level": target_queue_item.get("administrative_level")
                            if target_queue_item
                            else None,
                            "details": {
                                "title": report_documents[0].get("title"),
                                "source_name": report_documents[0].get("source_name"),
                                "external_reference_count": stats["external_reference_count"],
                            },
                        },
                    )
                queue_after = queue_preview(content_conn, target_analysis_mode, limit=12)
                complete_run(content_conn, run_id, "completed", report_path, stats)
                monitor_status = write_monitor_status(
                    content_conn,
                    config.data_dir,
                    target_analysis_mode,
                    min_external_references=config.min_external_references_per_report,
                    min_external_platforms=config.min_external_platforms_per_report,
                    quality_rules_file=config.quality_rules_file,
                )
                return {
                    "run_id": run_id,
                    "status": "completed",
                    "report_path": report_path,
                    "report_artifacts": report_artifacts,
                    "monitor_status_path": monitor_status.get("status_path"),
                    "stats": stats,
                    "queue_preview": _public_queue_preview(queue_after),
                    "timeline_preview": _public_timeline_preview(report_timeline(content_conn, limit=10)),
                }
            except Exception as exc:
                complete_run(content_conn, run_id, "failed", report_path, stats, str(exc))
                write_monitor_status(
                    content_conn,
                    config.data_dir,
                    target_analysis_mode,
                    min_external_references=config.min_external_references_per_report,
                    min_external_platforms=config.min_external_platforms_per_report,
                    quality_rules_file=config.quality_rules_file,
                )
                raise
        finally:
            if source_conn is not None:
                source_conn.close()
            if content_conn is not None:
                content_conn.close()


def _source_entry_urls(conn, source: dict) -> list[str]:
    urls = [source["official_url"]]
    rows = conn.execute(
        """
        SELECT alias_url
        FROM source_aliases
        WHERE source_id = ? AND alias_type = 'column_url' AND alias_url != ''
        ORDER BY alias_id
        """,
        (source["source_id"],),
    ).fetchall()
    urls.extend(row["alias_url"] for row in rows)
    seen: set[str] = set()
    deduped: list[str] = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            deduped.append(url)
    return deduped


def _crawl_sources(conn, min_authority_score: int, limit: int) -> list[dict]:
    rows = conn.execute(
        """
        SELECT *
        FROM source_authority_current
        WHERE crawl_enabled = 1
          AND effective_score >= ?
        ORDER BY crawl_priority ASC, effective_score DESC, name ASC
        LIMIT ?
        """,
        (min_authority_score, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def _document_for_fetched_resource(source: dict, result, snapshot_path: str) -> dict:
    title = Path(result.url).name or result.url
    parsed = extract_attachment_text(result.url, result.content_type, result.body)
    return {
        "source_id": source["source_id"],
        "source_name": source["name"],
        "source_url": source["official_url"],
        "authority_tier_snapshot": source.get("effective_tier"),
        "authority_score_snapshot": source.get("effective_score"),
        "title": clean_title(title),
        "url": result.url,
        "document_type": "attachment",
        "content_hash": content_hash(result.body),
        "snapshot_path": snapshot_path,
        "text_excerpt": parsed.text or None,
        "status": "fetched",
    }


def _enrich_document_detail(conn, fetcher, data_dir: Path, run_id: str, document: dict) -> dict:
    if document.get("text_excerpt") and not _noisy_excerpt(str(document.get("text_excerpt") or "")):
        return document
    try:
        result = fetcher.fetch(document["canonical_url"])
    except Exception as exc:
        _append_error(data_dir, run_id, f"detail fetch failed {document['canonical_url']}: {exc}")
        return document
    snapshot_path = save_snapshot(
        data_dir,
        run_id,
        document["source_id"],
        result.url,
        result.body,
        result.content_type,
    )
    if document.get("document_type") == "attachment" or "html" not in result.content_type.lower():
        parsed = extract_attachment_text(result.url, result.content_type, result.body)
        if not parsed.text:
            _append_error(data_dir, run_id, f"attachment parse {parsed.status} {document['canonical_url']}")
        updated_doc = {
            **document,
            "url": document["canonical_url"],
            "content_hash": content_hash(result.body),
            "snapshot_path": snapshot_path,
            "text_excerpt": parsed.text[:6000] if parsed.text else None,
            "status": "fetched",
        }
        upsert_document(conn, updated_doc, run_id)
        return document_by_id(conn, document["document_id"])
    parser = parse_html(result.text)
    text_excerpt = " ".join(parser.text_parts)[:1800]
    updated_doc = {
        **document,
        "title": clean_title(parser.title or document["title"]),
        "url": document["canonical_url"],
        "content_hash": content_hash(result.body),
        "snapshot_path": snapshot_path,
        "text_excerpt": text_excerpt,
        "status": "fetched",
    }
    upsert_document(conn, updated_doc, run_id)
    return document_by_id(conn, document["document_id"])


def _noisy_excerpt(value: str) -> bool:
    markers = (
        "font-size",
        "header_toolbar",
        "window.open",
        "encodeURIComponent",
        "currUrl",
        "big5.www",
        "var INFO_FLAG",
        "@media",
        "无障碍",
    )
    return any(marker in value for marker in markers)


class _pipeline_lock:
    def __init__(self, path: Path):
        self.path = path
        self.fd: int | None = None

    def __enter__(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(self.fd, str(os.getpid()).encode("utf-8"))
        except FileExistsError as exc:
            if self._remove_stale_lock():
                self.fd = os.open(str(self.path), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.write(self.fd, str(os.getpid()).encode("utf-8"))
                return self
            raise RuntimeError(f"pipeline lock exists: {self.path}") from exc
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.fd is not None:
            os.close(self.fd)
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass

    def _remove_stale_lock(self) -> bool:
        try:
            raw_pid = self.path.read_text(encoding="utf-8").strip()
            pid = int(raw_pid)
        except (OSError, ValueError):
            return False
        try:
            os.kill(pid, 0)
            return False
        except ProcessLookupError:
            try:
                self.path.unlink()
            except FileNotFoundError:
                pass
            return True
        except PermissionError:
            return False


def _append_error(data_dir: Path, run_id: str, line: str) -> None:
    path = data_dir / "run_logs" / f"{run_id}.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text((path.read_text(encoding="utf-8") if path.exists() else "") + line + "\n", encoding="utf-8")


def _public_queue_preview(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "document_id": item.get("document_id"),
            "title": item.get("title"),
            "source_name": item.get("source_name"),
            "industry": item.get("primary_industry"),
            "industry_rank": item.get("industry_rank"),
            "sort_time": item.get("sort_time") or item.get("published_date") or item.get("discovered_at"),
            "administrative_level": item.get("administrative_level"),
            "priority_score": item.get("priority_score"),
        }
        for item in items
    ]


def _active_industry_rank(items: list[dict[str, Any]]) -> int | None:
    ranks = [
        int(item.get("industry_rank"))
        for item in items
        if item.get("industry_rank") is not None
    ]
    return min(ranks) if ranks else None


def _active_industry_name(items: list[dict[str, Any]], rank: int | None) -> str | None:
    if rank is None:
        return None
    for item in items:
        if item.get("industry_rank") == rank:
            return str(item.get("primary_industry") or item.get("industry") or "")
    return None


def _next_generation_candidates(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return items[:1]


def _public_timeline_preview(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "event_type": item.get("event_type"),
            "created_at": item.get("created_at"),
            "document_id": item.get("document_id"),
            "title": item.get("title"),
            "source_name": item.get("source_name"),
            "report_path": item.get("report_path"),
            "industry": item.get("primary_industry"),
            "administrative_level": item.get("administrative_level"),
        }
        for item in items
    ]


def _unique_report_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.stem
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = path.with_name(f"{stem}_{index}{suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"could not allocate unique report path for {path}")
