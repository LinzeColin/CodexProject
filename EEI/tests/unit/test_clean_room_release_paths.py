from __future__ import annotations

import hashlib

from scripts import manage_clean_room_release as release
from scripts import manage_release_artifacts as release_artifacts


def test_tracked_paths_decode_non_ascii_paths_without_git_quoting(monkeypatch) -> None:
    def fake_run_git_bytes(*args: str) -> bytes:
        assert args == ("-c", "core.quotePath=false", "ls-files", "-z")
        return "README.md\0功能清单\0开发记录\0模型参数文件\0".encode()

    monkeypatch.setattr(release, "run_git_bytes", fake_run_git_bytes)

    paths = release.tracked_paths()

    assert {"功能清单", "开发记录", "模型参数文件"}.issubset(paths)
    assert not any(path.startswith('"\\') for path in paths)


def test_release_artifact_paths_are_posix_for_cross_platform_governance() -> None:
    assert release.path_id(release.EVIDENCE) == "artifacts/tests/a200/t1215_clean_room_release.json"
    assert release.path_id(release.PACKAGE) in release.EXCLUDED_FROM_PACKAGE


def test_t1211_release_paths_decode_non_ascii_paths_without_git_quoting(monkeypatch) -> None:
    def fake_run_git_bytes(*args: str) -> bytes:
        assert args == ("-c", "core.quotePath=false", "ls-files", "-z")
        return "README.md\0功能清单\0开发记录\0模型参数文件\0".encode()

    monkeypatch.setattr(release_artifacts, "run_git_bytes", fake_run_git_bytes)

    paths = release_artifacts.tracked_paths()

    assert {"功能清单", "开发记录", "模型参数文件"}.issubset(paths)
    assert not any(path.startswith('"\\') for path in paths)


def test_t1211_release_artifact_paths_are_posix_for_cross_platform_governance() -> None:
    assert (
        release_artifacts.path_id(release_artifacts.RELEASE_EVIDENCE)
        == "artifacts/release_evidence_t1211.json"
    )
    assert "artifacts/release_evidence_t1211.json" in release_artifacts.REQUIRED_RELEASE_PATHS
    assert (
        release_artifacts.path_id(release_artifacts.CHECKSUMS)
        in release_artifacts.CHECKSUM_EXCLUDES
    )


def test_t1211_release_checksum_uses_raw_file_bytes(tmp_path) -> None:
    sample = tmp_path / "sample.txt"
    payload = b"alpha\r\nbeta\r\n"
    sample.write_bytes(payload)

    assert release_artifacts.raw_file_bytes(sample) == payload
    assert release_artifacts.sha256_file(sample) == hashlib.sha256(payload).hexdigest()


def test_canonical_file_bytes_normalize_crlf_text(tmp_path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_bytes(b"alpha\r\nbeta\r\n")

    assert release.canonical_file_bytes(sample) == b"alpha\nbeta\n"
