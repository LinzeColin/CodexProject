from app.config import Settings


def test_opend_auto_start_and_cleanup_are_enabled_by_default(tmp_path, monkeypatch):
    monkeypatch.delenv("SERENITY_OPEND_AUTO_START", raising=False)
    monkeypatch.delenv("SERENITY_OPEND_KEEP_AUTO_STARTED", raising=False)

    settings = Settings.load(tmp_path)

    assert settings.opend_auto_start_enabled is True
    assert settings.opend_keep_auto_started is False


def test_opend_auto_start_and_cleanup_can_be_overridden(tmp_path, monkeypatch):
    monkeypatch.setenv("SERENITY_OPEND_AUTO_START", "false")
    monkeypatch.setenv("SERENITY_OPEND_KEEP_AUTO_STARTED", "true")

    settings = Settings.load(tmp_path)

    assert settings.opend_auto_start_enabled is False
    assert settings.opend_keep_auto_started is True
