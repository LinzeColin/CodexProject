from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from typing import Any, Iterable

from .db import seed_sources


def load_seed_file(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if isinstance(data, dict):
        return list(data.get("sources", []))
    if isinstance(data, list):
        return data
    raise ValueError("seed file must contain a list or an object with a 'sources' list")


def seed_from_file(conn, path: str | Path) -> list[str]:
    return seed_sources(conn, load_seed_file(path))


def iter_csv_sources(path: str | Path) -> Iterable[dict[str, Any]]:
    file_path = Path(path)
    if file_path.suffix.lower() == ".zip":
        with zipfile.ZipFile(file_path) as archive:
            for name in archive.namelist():
                if name.lower().endswith(".csv"):
                    with archive.open(name) as fh:
                        text = fh.read().decode("utf-8-sig")
                    yield from _rows_to_sources(csv.DictReader(text.splitlines()))
        return

    with file_path.open("r", encoding="utf-8-sig", newline="") as fh:
        yield from _rows_to_sources(csv.DictReader(fh))


def import_official_csv(conn, path: str | Path) -> list[str]:
    return seed_sources(conn, iter_csv_sources(path))


def _rows_to_sources(rows: Iterable[dict[str, str]]) -> Iterable[dict[str, Any]]:
    for row in rows:
        name = _pick(row, "网站名称", "来源名称", "name", "Name")
        url = _pick(row, "首页网址", "网站首页网址", "网址", "url", "URL")
        if not name or not url:
            continue

        sponsor = _pick(row, "主办单位", "主办", "sponsor_unit")
        supervisor = _pick(row, "主管单位", "supervisor_unit")
        site_id = _pick(row, "政府网站标识码", "网站标识码", "government_site_id")
        icp = _pick(row, "ICP备案号", "ICP备案", "icp")
        police = _pick(row, "公安机关备案号", "公安备案号", "police")
        region = _pick(row, "地区", "区域", "省份", "region")
        site_type = _pick(row, "网站类型", "类型", "source_type")

        source_type = _infer_source_type(site_type, name)
        level = _infer_level(site_type, region, name)
        evidence = [
            {
                "type": "official_directory",
                "value": "中国政府网政府网站基本信息下载",
                "url": "https://zfwzzc.www.gov.cn/check_web/databaseInfo/download",
            }
        ]
        if site_id:
            evidence.append({"type": "government_site_id", "value": site_id})
        if sponsor:
            evidence.append({"type": "sponsor_unit", "value": sponsor})
        if supervisor:
            evidence.append({"type": "supervisor_unit", "value": supervisor})
        if icp:
            evidence.append({"type": "icp_registration", "value": icp})
        if police:
            evidence.append({"type": "police_registration", "value": police})

        yield {
            "name": name,
            "country_code": "CN",
            "country_name": "China",
            "region": region or "China",
            "administrative_level": level,
            "source_type": source_type,
            "sponsor_unit": sponsor,
            "supervisor_unit": supervisor,
            "official_url": url,
            "publishes_original_documents": True,
            "crawl_enabled": True,
            "crawl_priority": _priority_for(source_type, level),
            "status": "active",
            "review_status": "unreviewed",
            "evidence": evidence,
            "aliases": [],
        }


def _pick(row: dict[str, str], *keys: str) -> str:
    normalized = {str(k).strip(): (v or "").strip() for k, v in row.items()}
    for key in keys:
        if normalized.get(key):
            return normalized[key]
    return ""


def _infer_source_type(site_type: str, name: str) -> str:
    text = f"{site_type} {name}"
    if "部委" in text or "国务院" in text or "部" in name or "委" in name:
        return "ministry"
    if "省级门户" in text or "人民政府" in name:
        return "provincial_portal"
    if "所属网站" in text:
        return "subordinate_site"
    return "government_portal"


def _infer_level(site_type: str, region: str, name: str) -> str:
    text = f"{site_type} {region} {name}"
    if "国务院" in text or "部委" in text or "国家" in name or "中华人民共和国" in name:
        return "national"
    if "省" in text or "自治区" in text or "直辖市" in text or "省级" in text:
        return "provincial"
    return "unknown"


def _priority_for(source_type: str, level: str) -> int:
    if level == "national" and source_type in {"government_portal", "ministry"}:
        return 10
    if level == "provincial":
        return 20
    if source_type == "subordinate_site":
        return 30
    return 50
