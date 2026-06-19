from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from app.core.packaging import build_delivery_package
from tests.helpers import temp_settings


def _write(path: Path, text: str = "x") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def test_delivery_package_excludes_private_evidence_by_default(tmp_path: Path):
    settings = temp_settings(tmp_path)
    _write(settings.root_dir / "app" / "__init__.py")
    _write(settings.root_dir / "README.md", "readme")
    _write(settings.root_dir / "outputs" / "intake_pack" / "EVIDENCE_INTAKE_GUIDE.md", "guide")
    _write(settings.root_dir / "outputs" / "intake_pack" / "evidence" / "alipay.png", "private")
    _write(settings.root_dir / "evidence" / "manual.csv", "private")
    _write(settings.root_dir / "data" / "backups" / "intake_promotions" / "old.csv", "private")

    result = build_delivery_package(settings)

    assert result["status"] == "pass"
    assert Path(result["zip_path"]).exists()
    assert Path(result["manifest_path"]).exists()
    with zipfile.ZipFile(result["zip_path"]) as archive:
        names = set(archive.namelist())
    assert "README.md" in names
    assert "outputs/intake_pack/EVIDENCE_INTAKE_GUIDE.md" in names
    assert "outputs/package/package_latest.json" not in names
    assert "outputs/package/package_latest.md" not in names
    assert "outputs/intake_pack/evidence/alipay.png" not in names
    assert "evidence/manual.csv" not in names
    assert "data/backups/intake_promotions/old.csv" not in names
    assert result["included_private_like_members"] == []
    manifest_text = Path(result["manifest_path"]).read_text(encoding="utf-8")
    assert settings.root_dir.as_posix() not in manifest_text


def test_delivery_package_can_include_private_evidence_when_explicit(tmp_path: Path):
    settings = temp_settings(tmp_path)
    _write(settings.root_dir / "README.md", "readme")
    _write(settings.root_dir / "outputs" / "intake_pack" / "evidence" / "alipay.png", "private")

    result = build_delivery_package(settings, include_private_evidence=True)

    assert result["status"] == "pass"
    with zipfile.ZipFile(result["zip_path"]) as archive:
        names = set(archive.namelist())
    assert "outputs/intake_pack/evidence/alipay.png" in names
    assert result["included_private_like_members"] == ["outputs/intake_pack/evidence/alipay.png"]


def test_delivery_package_preserves_previous_zip_when_build_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    settings = temp_settings(tmp_path)
    _write(settings.root_dir / "README.md", "readme")
    zip_path = settings.root_dir / "outputs" / "package" / "serenity_daily_analysis_delivery.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    real_zipfile = zipfile.ZipFile
    with real_zipfile(zip_path, "w") as archive:
        archive.writestr("previous.txt", "still valid")

    class FailingZipFile:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("zip writer failed")

    monkeypatch.setattr("app.core.packaging.zipfile.ZipFile", FailingZipFile)

    with pytest.raises(RuntimeError, match="zip writer failed"):
        build_delivery_package(settings)

    with real_zipfile(zip_path) as archive:
        assert archive.read("previous.txt") == b"still valid"
    assert not list(zip_path.parent.glob("*.tmp"))
    assert not list(zip_path.parent.glob(".*.tmp"))
