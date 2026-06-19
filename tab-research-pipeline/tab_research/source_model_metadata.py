from __future__ import annotations

import json
import ssl
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .io import atomic_write_json


SOURCE_MODEL_GITHUB_METADATA_JSON_LATEST = "source_model_github_metadata_latest.json"
REPORT_TZ = ZoneInfo("Australia/Sydney")
GITHUB_API_BASE = "https://api.github.com/repos"
GITHUB_METADATA_FRESHNESS_SLA_HOURS = 4


def write_source_model_github_metadata(
    output_dir: Path,
    references: list[dict[str, Any]] | None = None,
    timeout_seconds: float = 8.0,
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    if references is None:
        from .model_compare import OPEN_SOURCE_REFERENCES

        references = OPEN_SOURCE_REFERENCES
    payload = refresh_source_model_github_metadata(references, timeout_seconds=timeout_seconds)
    atomic_write_json(output_dir / SOURCE_MODEL_GITHUB_METADATA_JSON_LATEST, payload)
    return payload


def refresh_source_model_github_metadata(
    references: list[dict[str, Any]],
    timeout_seconds: float = 8.0,
) -> dict[str, Any]:
    generated_at = datetime.now(REPORT_TZ).isoformat()
    rows: list[dict[str, Any]] = []
    for ref in references:
        rows.append(fetch_reference_metadata(ref, generated_at, timeout_seconds=timeout_seconds))
    ready_rows = [row for row in rows if row.get("fetch_status") == "ready"]
    failed_rows = [row for row in rows if row.get("fetch_status") not in {"ready", "skipped"}]
    skipped_rows = [row for row in rows if row.get("fetch_status") == "skipped"]
    status = "ready" if len(ready_rows) == len(rows) else "partial" if ready_rows else "failed"
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": status,
        "freshness_sla_hours": GITHUB_METADATA_FRESHNESS_SLA_HOURS,
        "freshness_status": "fresh_4h",
        "source_count": len(rows),
        "fetched_count": len(ready_rows),
        "failed_count": len(failed_rows),
        "skipped_count": len(skipped_rows),
        "stars_total": sum(int(row.get("stargazers_count") or 0) for row in ready_rows),
        "forks_total": sum(int(row.get("forks_count") or 0) for row in ready_rows),
        "open_issues_total": sum(int(row.get("open_issues_count") or 0) for row in ready_rows),
        "rows": rows,
        "truthfulness_note": "GitHub metadata comes from the public repository API. If a fetch fails, the registry falls back to cached/static source evidence.",
    }


def fetch_reference_metadata(ref: dict[str, Any], generated_at: str, timeout_seconds: float = 8.0) -> dict[str, Any]:
    source = str(ref.get("name") or "")
    url = str(ref.get("url") or "")
    slug = github_repo_slug(url)
    base = {
        "source": source,
        "display_name": str(ref.get("display_name") or source),
        "url": url,
        "repo_slug": slug,
        "api_url": f"{GITHUB_API_BASE}/{slug}" if slug else "",
        "fetched_at": generated_at,
    }
    if not slug:
        return {
            **base,
            "fetch_status": "skipped",
            "error_type": "not_github_repo",
            "error_message": "source URL is not a GitHub repository",
        }
    try:
        repo = fetch_github_repo(slug, timeout_seconds=timeout_seconds)
    except urllib.error.HTTPError as exc:
        return failed_row(base, "http_error", f"HTTP {exc.code}")
    except urllib.error.URLError as exc:
        reason = exc.reason.__class__.__name__ if getattr(exc, "reason", None) is not None else "url_error"
        return failed_row(base, "url_error", reason)
    except (TimeoutError, OSError, json.JSONDecodeError) as exc:
        return failed_row(base, exc.__class__.__name__, public_error_message(exc))
    return {
        **base,
        "fetch_status": "ready",
        "stargazers_count": int(repo.get("stargazers_count") or 0),
        "forks_count": int(repo.get("forks_count") or 0),
        "open_issues_count": int(repo.get("open_issues_count") or 0),
        "watchers_count": int(repo.get("watchers_count") or 0),
        "default_branch": str(repo.get("default_branch") or ""),
        "pushed_at": str(repo.get("pushed_at") or ""),
        "updated_at": str(repo.get("updated_at") or ""),
        "archived": bool(repo.get("archived")),
        "disabled": bool(repo.get("disabled")),
        "visibility": str(repo.get("visibility") or ""),
        "license_key": str((repo.get("license") or {}).get("key") or ""),
        "license_name": str((repo.get("license") or {}).get("name") or ""),
        "language": str(repo.get("language") or ""),
        "homepage": str(repo.get("homepage") or ""),
        "html_url": str(repo.get("html_url") or url),
    }


def fetch_github_repo(slug: str, timeout_seconds: float = 8.0) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{GITHUB_API_BASE}/{slug}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "tab-fifa-research/1.0",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    errors: list[str] = []
    for method, context in github_ssl_attempts():
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds, context=context) as response:
                payload = json.loads(response.read().decode("utf-8"))
            return payload if isinstance(payload, dict) else {}
        except urllib.error.HTTPError:
            raise
        except Exception as exc:
            errors.append(f"{method}: {exc.__class__.__name__}: {public_error_message(exc)}")
    try:
        result = subprocess.run(
            [
                "curl",
                "-fsSL",
                "--max-time",
                str(int(max(timeout_seconds, 1))),
                "-H",
                "Accept: application/vnd.github+json",
                "-H",
                "X-GitHub-Api-Version: 2022-11-28",
                f"{GITHUB_API_BASE}/{slug}",
            ],
            text=True,
            capture_output=True,
            timeout=timeout_seconds + 3,
            check=False,
        )
        if result.returncode == 0 and result.stdout.strip():
            payload = json.loads(result.stdout)
            return payload if isinstance(payload, dict) else {}
        errors.append(f"curl: exit {result.returncode}: {result.stderr.strip()[:160]}")
    except Exception as exc:
        errors.append(f"curl: {exc.__class__.__name__}: {public_error_message(exc)}")
    raise urllib.error.URLError("; ".join(errors)[:360])


def github_ssl_attempts() -> list[tuple[str, ssl.SSLContext | None]]:
    attempts: list[tuple[str, ssl.SSLContext | None]] = [("urllib_default_ssl", None)]
    try:
        import certifi  # type: ignore

        attempts.append(("urllib_certifi_ssl", ssl.create_default_context(cafile=certifi.where())))
    except Exception:
        pass
    return attempts


def github_repo_slug(url: str) -> str:
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return ""
    if parsed.netloc.lower() not in {"github.com", "www.github.com"}:
        return ""
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        return ""
    owner = parts[0]
    repo = parts[1][:-4] if parts[1].endswith(".git") else parts[1]
    if not owner or not repo:
        return ""
    return f"{owner}/{repo}"


def failed_row(base: dict[str, Any], error_type: str, error_message: str) -> dict[str, Any]:
    return {
        **base,
        "fetch_status": "failed",
        "error_type": error_type,
        "error_message": error_message,
        "stargazers_count": 0,
        "forks_count": 0,
        "open_issues_count": 0,
    }


def load_source_model_github_metadata(output_dir: Path) -> dict[str, Any]:
    path = Path(output_dir) / SOURCE_MODEL_GITHUB_METADATA_JSON_LATEST
    try:
        if not path.exists():
            return {}
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def github_metadata_by_source(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        str(row.get("source") or ""): row
        for row in payload.get("rows", [])
        if isinstance(row, dict) and row.get("source")
    }


def public_error_message(exc: BaseException) -> str:
    message = str(exc).replace(str(Path.home()), "~")
    if len(message) > 120:
        message = message[:117] + "..."
    return message
