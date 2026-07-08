#!/usr/bin/env python3
"""Generate private OCR sidecar plans for screenshot evidence.

The tool never writes OCR text into Git-tracked paths and never creates empty
OCR sidecars. Dry-run is the default; `--apply` is required to write private
runtime sidecar text when a real local OCR engine returns non-empty text.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


DEFAULT_INPUT_DIR = "/Users/linzezhang/Library/CloudStorage/OneDrive-Personal/DWS_Outputs/付款请示群"
PRIVATE_OCR_ROOT = Path("KMFA/metadata/fund_weekly_analysis/private_runtime/ocr_sidecars")
PLAN_FIELDS = [
    "ocr_generation_id",
    "evidence_id",
    "source_image_relative_path",
    "engine",
    "generation_status",
    "ocr_text_private_relative_path",
    "text_length",
    "text_sha256",
    "apply_performed",
    "financial_fact_promoted",
    "review_status",
    "reason",
]


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_relative_path(value: str) -> Path:
    if not value.strip():
        raise ValueError("unsafe relative path: empty value")
    path = Path(value)
    if path.is_absolute() or path == Path(".") or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError(f"unsafe relative path: {value}")
    return path


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PLAN_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def normalize_engine_text(stdout: str) -> str:
    text = stdout.strip()
    if not text or text == "(null)":
        return ""
    return text


def read_text_with_mdls(image_path: Path, timeout_seconds: int) -> tuple[str, str]:
    mdls = shutil.which("mdls") or "/usr/bin/mdls"
    if not Path(mdls).exists():
        return "", "ocr_engine_unavailable"
    try:
        result = subprocess.run(
            [mdls, "-raw", "-name", "kMDItemTextContent", str(image_path)],
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired:
        return "", "ocr_engine_timeout"
    if result.returncode != 0:
        return "", "ocr_engine_error"
    text = normalize_engine_text(result.stdout)
    if not text:
        return "", "no_text_from_engine"
    return text, "ocr_text_available"


def vision_command(repo_root: Path) -> list[str] | None:
    configured = os.environ.get("KMFA_FUND_VISION_OCR_COMMAND", "").strip()
    if configured:
        return shlex.split(configured)
    swift = shutil.which("swift") or "/usr/bin/swift"
    helper = repo_root / "KMFA" / "fund-weekly-analysis-skill" / "tools" / "ocr_with_vision.swift"
    if not Path(swift).exists() or not helper.exists():
        return None
    return [swift, str(helper)]


def read_text_with_vision_batch(
    *,
    repo_root: Path,
    image_paths: list[Path],
    timeout_seconds: int,
    batch_size: int,
) -> dict[str, tuple[str, str, str]]:
    command = vision_command(repo_root)
    if command is None:
        return {str(path): ("", "ocr_engine_unavailable", "Swift Vision OCR command is unavailable") for path in image_paths}
    if not image_paths:
        return {}
    batch_size = max(1, batch_size)
    parsed: dict[str, tuple[str, str, str]] = {}
    for start in range(0, len(image_paths), batch_size):
        batch = image_paths[start:start + batch_size]
        try:
            result = subprocess.run(
                [*command, *[str(path) for path in batch]],
                text=True,
                capture_output=True,
                check=False,
                timeout=timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            for path in batch:
                parsed[str(path)] = ("", "ocr_engine_timeout", "vision OCR command timed out")
            continue
        if result.returncode != 0:
            reason = (result.stderr or result.stdout or "vision OCR command failed").strip().splitlines()[:1]
            for path in batch:
                parsed[str(path)] = ("", "ocr_engine_error", reason[0] if reason else "vision OCR command failed")
            continue
        for line in result.stdout.splitlines():
            if not line.strip():
                continue
            try:
                item = json.loads(line)
            except json.JSONDecodeError:
                continue
            path = str(Path(item.get("path", "")).expanduser())
            status = item.get("status") or "ocr_engine_error"
            text = normalize_engine_text(item.get("text", ""))
            if status == "ocr_text_available" and not text:
                status = "no_text_from_engine"
            reason = item.get("reason", "")
            parsed[path] = (text, status, reason)
        for path in batch:
            parsed.setdefault(str(path), ("", "ocr_engine_error", "vision OCR command returned no result"))
    for path in image_paths:
        parsed.setdefault(str(path), ("", "ocr_engine_error", "vision OCR command returned no result"))
    return parsed


def private_sidecar_relative_path(run_id: str, generation_id: str) -> Path:
    return PRIVATE_OCR_ROOT / run_id / f"{generation_id}.ocr.txt"


def build_generation_plan(
    *,
    repo_root: Path,
    input_dir: Path,
    run_dir: Path,
    engine: str,
    apply: bool,
    timeout_seconds: int,
    vision_batch_size: int,
    limit: int | None = None,
) -> list[dict]:
    coverage_path = run_dir / "screenshot_ocr_coverage.csv"
    coverage_rows = read_csv(coverage_path)
    missing_rows = [row for row in coverage_rows if row.get("ocr_coverage_status") == "ocr_text_sidecar_missing"]
    if limit is not None:
        missing_rows = missing_rows[:limit]

    source_image_by_index: dict[int, Path] = {}
    if engine == "vision":
        for index, coverage in enumerate(missing_rows):
            try:
                source_relative = safe_relative_path(coverage["source_image_relative_path"])
            except (KeyError, ValueError):
                continue
            source_image_path = input_dir / source_relative
            if source_image_path.exists():
                source_image_by_index[index] = source_image_path
        vision_results = read_text_with_vision_batch(
            repo_root=repo_root,
            image_paths=list(source_image_by_index.values()),
            timeout_seconds=timeout_seconds,
            batch_size=vision_batch_size,
        )
    else:
        vision_results = {}

    rows: list[dict] = []
    for index, coverage in enumerate(missing_rows):
        generation_id = f"OCRGEN-{run_dir.name}-{len(rows) + 1:05d}"
        reason = ""
        text = ""
        private_rel = Path()
        try:
            source_relative = safe_relative_path(coverage["source_image_relative_path"])
        except ValueError as exc:
            source_relative = Path("")
            status = "unsafe_source_image_path"
            reason = str(exc)
        else:
            source_image_path = input_dir / source_relative
            if not source_image_path.exists():
                status = "source_image_missing"
                reason = "source image path does not exist"
            elif engine == "none":
                status = "ocr_engine_unavailable"
                reason = "no OCR engine selected"
            elif engine == "mdls":
                text, engine_status = read_text_with_mdls(source_image_path, timeout_seconds)
                status = engine_status if not text else "ocr_text_generated_pending_review"
                if not text:
                    reason = f"{engine} returned no OCR text"
            elif engine == "vision":
                text, engine_status, engine_reason = vision_results.get(
                    str(source_image_path),
                    ("", "ocr_engine_error", "vision OCR result missing"),
                )
                status = engine_status if not text else "ocr_text_generated_pending_review"
                if not text:
                    reason = engine_reason or f"{engine} returned no OCR text"
            else:
                status = "ocr_engine_unavailable"
                reason = f"unsupported OCR engine: {engine}"

        text_length = str(len(text)) if text else "0"
        text_hash = sha256_text(text) if text else ""
        apply_performed = "false"
        if text:
            private_rel = private_sidecar_relative_path(run_dir.name, generation_id)
            if apply:
                private_path = repo_root / private_rel
                private_path.parent.mkdir(parents=True, exist_ok=True)
                private_path.write_text(text.rstrip() + "\n", encoding="utf-8")
                apply_performed = "true"
            else:
                reason = "dry_run_no_sidecar_written"

        rows.append({
            "ocr_generation_id": generation_id,
            "evidence_id": coverage.get("evidence_id", ""),
            "source_image_relative_path": coverage.get("source_image_relative_path", ""),
            "engine": engine,
            "generation_status": status,
            "ocr_text_private_relative_path": str(private_rel) if text else "",
            "text_length": text_length,
            "text_sha256": text_hash,
            "apply_performed": apply_performed,
            "financial_fact_promoted": "false",
            "review_status": "pending_human_review" if text else "pending_ocr_extraction",
            "reason": reason,
        })
    return rows


def summarize(rows: list[dict], engine: str, apply: bool) -> dict:
    return {
        "engine": engine,
        "apply": apply,
        "planned_count": len(rows),
        "generated_sidecar_count": sum(1 for row in rows if row["apply_performed"] == "true"),
        "text_available_count": sum(1 for row in rows if row["generation_status"] == "ocr_text_generated_pending_review"),
        "engine_unavailable_count": sum(1 for row in rows if row["generation_status"] == "ocr_engine_unavailable"),
        "no_text_from_engine_count": sum(1 for row in rows if row["generation_status"] == "no_text_from_engine"),
        "financial_fact_promoted": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=os.environ.get("KMFA_REPO_ROOT", "."))
    parser.add_argument("--input-dir", default=os.environ.get("KMFA_FUND_INPUT_DIR", DEFAULT_INPUT_DIR))
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--engine", choices=["vision", "mdls", "none"], default=os.environ.get("KMFA_FUND_OCR_ENGINE", "vision"))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--timeout-seconds", type=int, default=10)
    parser.add_argument("--vision-batch-size", type=int, default=int(os.environ.get("KMFA_FUND_VISION_BATCH_SIZE", "8")))
    parser.add_argument("--limit", type=int, default=None)
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    input_dir = Path(args.input_dir).expanduser().resolve()
    run_dir = Path(args.run_dir).expanduser()
    if not run_dir.is_absolute():
        run_dir = repo_root / run_dir
    run_dir = run_dir.resolve()

    coverage_path = run_dir / "screenshot_ocr_coverage.csv"
    if not coverage_path.exists():
        print(json.dumps({"status": "OCR_COVERAGE_MISSING", "coverage_path": str(coverage_path)}, ensure_ascii=False))
        return 2

    rows = build_generation_plan(
        repo_root=repo_root,
        input_dir=input_dir,
        run_dir=run_dir,
        engine=args.engine,
        apply=args.apply,
        timeout_seconds=args.timeout_seconds,
        vision_batch_size=args.vision_batch_size,
        limit=args.limit,
    )
    plan_path = run_dir / "screenshot_ocr_sidecar_generation_plan.csv"
    summary_path = run_dir / "screenshot_ocr_sidecar_generation_summary.json"
    write_csv(plan_path, rows)
    summary = summarize(rows, args.engine, args.apply)
    summary.update({
        "status": "OCR_SIDECAR_GENERATION_PLANNED",
        "run_dir": str(run_dir),
        "plan_path": str(plan_path),
        "summary_path": str(summary_path),
    })
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
