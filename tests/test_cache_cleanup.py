from pathlib import Path

from quantlab.system.cache_cleanup import build_cache_cleanup_report


def test_cache_cleanup_dry_run_counts_disposable_artifacts(tmp_path: Path) -> None:
    (tmp_path / "src" / "pkg" / "__pycache__").mkdir(parents=True)
    (tmp_path / "src" / "pkg" / "__pycache__" / "mod.pyc").write_bytes(b"bytecode")
    (tmp_path / ".pytest_cache").mkdir()
    (tmp_path / ".pytest_cache" / "README.md").write_text("cache", encoding="utf-8")
    (tmp_path / "data" / "cache").mkdir(parents=True)
    (tmp_path / "data" / "cache" / "quantlab_macos_app.log").write_text("log", encoding="utf-8")
    (tmp_path / "data" / "cache" / ".gitkeep").write_text("", encoding="utf-8")
    (tmp_path / "data" / "cache" / "US").mkdir()
    (tmp_path / "data" / "cache" / "US" / "AAPL.csv").write_text("market cache", encoding="utf-8")
    (tmp_path / "report.docx").write_bytes(b"keep")

    report = build_cache_cleanup_report(tmp_path, dry_run=True)

    assert report["schema"] == "EVACacheCleanupReportV1"
    assert report["mode"] == "dry_run"
    assert report["candidate_count"] == 3
    assert report["candidate_file_count"] == 3
    assert report["removed_count"] == 0
    assert "data/cache/US/AAPL.csv" not in str(report)
    assert "report.docx" not in str(report)
    assert "SQLite databases, and market bar caches are not deleted" in report["safety_boundary"]


def test_cache_cleanup_delete_preserves_reports_and_market_cache(tmp_path: Path) -> None:
    pycache = tmp_path / "tests" / "__pycache__"
    pycache.mkdir(parents=True)
    (pycache / "test_mod.pyc").write_bytes(b"bytecode")
    (tmp_path / ".DS_Store").write_text("finder", encoding="utf-8")
    market_cache = tmp_path / "data" / "cache" / "US" / "AAPL.csv"
    market_cache.parent.mkdir(parents=True)
    market_cache.write_text("market cache", encoding="utf-8")
    report_file = tmp_path / "outputs" / "report.pdf"
    report_file.parent.mkdir()
    report_file.write_bytes(b"pdf")

    report = build_cache_cleanup_report(tmp_path, dry_run=False)

    assert report["mode"] == "delete"
    assert report["removed_count"] == 2
    assert not pycache.exists()
    assert not (tmp_path / ".DS_Store").exists()
    assert market_cache.exists()
    assert report_file.exists()
