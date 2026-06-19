import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LEGACY_PATTERNS = [
    re.compile(re.escape("E" + "VA" + "_OS")),
    re.compile(re.escape("E" + "VA" + " OS")),
    re.compile(re.escape("E" + "VA" + "_")),
    re.compile(re.escape("Quant" + "Lab")),
    re.compile(re.escape("quant" + "lab")),
    re.compile(re.escape("QUANT" + "LAB" + "_")),
]

EXTRA_LEGACY_PATTERNS = [
    re.compile(re.escape("E" + "VA" + "CommandCenter")),
    re.compile(re.escape("E" + "VA" + "CacheCleanupReport")),
    re.compile(re.escape("e" + "va" + "_os")),
    re.compile(re.escape("com.linze." + "e" + "va" + "-os")),
    re.compile(r"\b" + re.escape("E" + "VA") + r"\b"),
]

SKIPPED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    "data",
}

BINARY_SUFFIXES = {
    ".icns",
    ".pdf",
    ".png",
    ".pyc",
}


def _relative(path: Path) -> str:
    return path.relative_to(PROJECT_ROOT).as_posix()


def _iter_current_text_files():
    legacy_archive = PROJECT_ROOT / "docs" / "archive" / "legacy-migration.md"
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path == legacy_archive:
            continue
        if path.suffix in BINARY_SUFFIXES:
            continue
        if any(part in SKIPPED_DIRS for part in path.relative_to(PROJECT_ROOT).parts):
            continue
        yield path


def test_current_text_surface_does_not_reintroduce_legacy_identity_terms():
    violations = []

    for path in _iter_current_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for pattern in LEGACY_PATTERNS:
            if pattern.search(text):
                violations.append(f"{_relative(path)}: {pattern.pattern}")

    assert violations == []


def test_current_text_surface_does_not_keep_common_legacy_artifact_terms():
    violations = []

    for path in _iter_current_text_files():
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        for pattern in EXTRA_LEGACY_PATTERNS:
            if pattern.search(text):
                violations.append(f"{_relative(path)}: {pattern.pattern}")

    assert violations == []
