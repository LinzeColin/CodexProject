from pathlib import Path

from app.core.path_display import display_path, redact_text_for_markdown


def test_display_path_uses_relative_project_paths(tmp_path: Path):
    root = tmp_path / "workspace"
    project_file = root / "outputs" / "preflight" / "report.md"

    assert display_path(root, project_file) == "outputs/preflight/report.md"


def test_display_path_hides_external_local_directories(tmp_path: Path):
    root = tmp_path / "workspace"
    external_file = tmp_path / "Downloads" / "alipay_export.csv"

    assert display_path(root, external_file) == "external:alipay_export.csv"


def test_redact_text_for_markdown_redacts_embedded_local_paths(tmp_path: Path):
    root = tmp_path / "workspace"
    text = (
        f"run python {root / 'outputs' / 'moomoo-api-workbench' / 'quote_smoke_test.py'} "
        "and review /Users/test/Documents/Codex/private/alipay.csv."
    )

    redacted = redact_text_for_markdown(root, text)

    assert "/Users/" not in redacted
    assert "outputs/moomoo-api-workbench/quote_smoke_test.py" in redacted
    assert "external:alipay.csv" in redacted
