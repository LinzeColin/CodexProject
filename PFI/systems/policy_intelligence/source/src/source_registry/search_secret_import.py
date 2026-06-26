from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from .config_setup import SEARCH_SECRET_KEYS, build_config_setup
from .web_search import search_provider_status


PROVIDER_FIELDS = {
    "serpapi": ("SERPAPI_API_KEY",),
    "bing": ("BING_SEARCH_API_KEY",),
    "google": ("GOOGLE_SEARCH_API_KEY", "GOOGLE_CSE_ID"),
}

PLACEHOLDERS = {"", "todo", "change_me", "changeme", "your_key_here", "your-api-key", "xxx", "xxxx"}

BULK_FIELD_ALIASES = {
    "serpapi": {
        "SERPAPI_API_KEY": ("SERPAPI_API_KEY", "SERPAPI_KEY", "api_key", "key"),
    },
    "bing": {
        "BING_SEARCH_API_KEY": ("BING_SEARCH_API_KEY", "AZURE_BING_SEARCH_KEY", "api_key", "key"),
    },
    "google": {
        "GOOGLE_SEARCH_API_KEY": ("GOOGLE_SEARCH_API_KEY", "GOOGLE_API_KEY", "api_key", "key"),
        "GOOGLE_CSE_ID": ("GOOGLE_CSE_ID", "GOOGLE_CUSTOM_SEARCH_ENGINE_ID", "cse_id", "engine_id"),
    },
}


def import_search_secret(
    provider: str,
    *,
    value_file: str | Path | None = None,
    value_env: str | None = None,
    value_text: str | None = None,
    engine_id_file: str | Path | None = None,
    engine_id_env: str | None = None,
    engine_id_text: str | None = None,
    secure_dir: str | Path | None = None,
    search_secrets_file: str | Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    provider_key = provider.strip().lower()
    if provider_key not in PROVIDER_FIELDS:
        raise ValueError(f"unsupported search provider: {provider}")
    setup = build_config_setup(secure_dir=secure_dir, search_secrets_path=search_secrets_file)
    target = Path(str(search_secrets_file or setup["search_secrets_path"])).expanduser()
    payload = _load_payload(target)
    key_name = PROVIDER_FIELDS[provider_key][0]
    key_value = _secret_text(value_file=value_file, value_env=value_env, value_text=value_text, label="api key")
    _validate_secret_value(key_value, label="api key")
    updates = {key_name: key_value.strip()}

    if provider_key == "google":
        current_engine = str(payload.get("GOOGLE_CSE_ID") or "").strip()
        engine_value = _optional_secret_text(
            value_file=engine_id_file,
            value_env=engine_id_env,
            value_text=engine_id_text,
        )
        if engine_value:
            _validate_secret_value(engine_value, label="Google CSE ID")
            updates["GOOGLE_CSE_ID"] = engine_value.strip()
        elif _is_placeholder(current_engine):
            raise ValueError("google provider requires --engine-id-file or --engine-id-env unless GOOGLE_CSE_ID already exists.")

    existing_conflicts = [
        name
        for name, value in updates.items()
        if not _is_placeholder(str(payload.get(name) or "")) and str(payload.get(name) or "") != value
    ]
    if existing_conflicts and not force:
        raise ValueError("target search secret already has values; rerun with --force to overwrite.")

    if not dry_run:
        for name in SEARCH_SECRET_KEYS:
            payload.setdefault(name, "")
        payload.update(updates)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _chmod_private_file(target)
        _chmod_private_dir(target.parent)

    status_payload = dict(payload)
    status_payload.update(updates)
    status = _provider_status(provider_key, status_payload)
    return {
        "provider": provider_key,
        "status": "dry_run" if dry_run else "imported",
        "search_secrets_file": _path_label(target),
        "updated_fields": list(updates),
        "overwritten_fields": existing_conflicts if force else [],
        "provider_ready_after_import": bool(status.get("ready")),
        "provider_status_after_import": status.get("status"),
        "next_commands": [
            (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-validate "
                f"--search-secrets-file {_command_path(target)} --offline"
            ),
            (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-validate "
                f"--search-secrets-file {_command_path(target)}"
            ),
        ],
        "security_boundary": (
            "API key 已写入本地私有文件；命令输出、dashboard、报告和数据库只展示脱敏状态，"
            "不展示 key、secret 或完整敏感路径。"
        ),
    }


def import_search_secret_bundle(
    source_file: str | Path,
    *,
    secure_dir: str | Path | None = None,
    search_secrets_file: str | Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    source = Path(source_file).expanduser()
    if not source.exists():
        raise ValueError("search secret bundle file does not exist.")
    try:
        bundle = json.loads(source.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"search secret bundle JSON is invalid: {exc.msg}") from exc
    if not isinstance(bundle, Mapping):
        raise ValueError("search secret bundle JSON must be an object.")

    setup = build_config_setup(secure_dir=secure_dir, search_secrets_path=search_secrets_file)
    target = Path(str(search_secrets_file or setup["search_secrets_path"])).expanduser()
    payload = _load_payload(target)
    updates: dict[str, str] = {}
    results: list[dict[str, Any]] = []
    for provider in ("serpapi", "bing", "google"):
        provider_updates, missing, invalid = _bundle_updates_for_provider(provider, bundle)
        if invalid:
            results.append(
                {
                    "provider": provider,
                    "status": "invalid",
                    "updated_fields": [],
                    "missing_fields": missing,
                    "error": invalid,
                    "provider_ready_after_import": False,
                }
            )
            continue
        if missing:
            results.append(
                {
                    "provider": provider,
                    "status": "skipped_missing",
                    "updated_fields": [],
                    "missing_fields": missing,
                    "provider_ready_after_import": False,
                }
            )
            continue
        updates.update(provider_updates)
        status_payload = dict(payload)
        status_payload.update(updates)
        provider_status = _provider_status(provider, status_payload)
        results.append(
            {
                "provider": provider,
                "status": "dry_run" if dry_run else "imported",
                "updated_fields": list(provider_updates),
                "missing_fields": [],
                "provider_ready_after_import": bool(provider_status.get("ready")),
                "provider_status_after_import": provider_status.get("status"),
            }
        )

    existing_conflicts = [
        name
        for name, value in updates.items()
        if not _is_placeholder(str(payload.get(name) or "")) and str(payload.get(name) or "") != value
    ]
    if existing_conflicts and not force:
        raise ValueError("target search secret already has values; rerun with --force to overwrite.")

    if updates and not dry_run:
        for name in SEARCH_SECRET_KEYS:
            payload.setdefault(name, "")
        payload.update(updates)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        _chmod_private_file(target)
        _chmod_private_dir(target.parent)

    status_payload = dict(payload)
    status_payload.update(updates)
    provider_statuses = search_provider_status_from_payload(status_payload)
    ready_count = sum(1 for item in provider_statuses if item.get("ready"))
    return {
        "status": "dry_run" if dry_run else "imported",
        "search_secrets_file": _path_label(target),
        "imported_count": sum(1 for item in results if item.get("status") in {"imported", "dry_run"}),
        "skipped_count": sum(1 for item in results if item.get("status") == "skipped_missing"),
        "invalid_count": sum(1 for item in results if item.get("status") == "invalid"),
        "ready_count_after_import": ready_count,
        "total_provider_count": len(provider_statuses),
        "updated_fields": list(updates),
        "overwritten_fields": existing_conflicts if force else [],
        "results": results,
        "next_commands": [
            (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-validate "
                f"--search-secrets-file {_command_path(target)} --offline"
            ),
            (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite search-validate "
                f"--search-secrets-file {_command_path(target)}"
            ),
            (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite credential-doctor "
                f"--search-secrets-file {_command_path(target)}"
            ),
        ],
        "security_boundary": (
            "批量导入只写入本地私有 search secret 文件；输出只包含 provider 状态、字段名和验收命令，"
            "不展示 API key、secret、bundle 内容或完整敏感路径。"
        ),
    }


def _bundle_updates_for_provider(provider: str, bundle: Mapping[str, Any]) -> tuple[dict[str, str], list[str], str]:
    updates: dict[str, str] = {}
    missing: list[str] = []
    for field, aliases in BULK_FIELD_ALIASES[provider].items():
        value = _bundle_value(bundle, provider, aliases)
        if not value:
            missing.append(field)
            continue
        try:
            _validate_secret_value(value, label=field)
        except ValueError as exc:
            return {}, [field], str(exc)
        updates[field] = value.strip()
    return updates, missing, ""


def _bundle_value(bundle: Mapping[str, Any], provider: str, aliases: tuple[str, ...]) -> str:
    nested = bundle.get(provider) or bundle.get(provider.upper())
    if isinstance(nested, Mapping):
        for alias in aliases:
            raw = nested.get(alias)
            if raw:
                return str(raw).strip()
    for alias in aliases:
        raw = bundle.get(alias)
        if raw:
            return str(raw).strip()
    return ""


def _secret_text(
    *,
    value_file: str | Path | None,
    value_env: str | None,
    value_text: str | None,
    label: str,
) -> str:
    supplied = sum(1 for item in [value_file, value_env, value_text] if item)
    if supplied != 1:
        raise ValueError(f"provide exactly one {label} source: --value-file or --value-env.")
    return _optional_secret_text(value_file=value_file, value_env=value_env, value_text=value_text)


def _optional_secret_text(
    *,
    value_file: str | Path | None,
    value_env: str | None,
    value_text: str | None,
) -> str:
    supplied = sum(1 for item in [value_file, value_env, value_text] if item)
    if supplied > 1:
        raise ValueError("provide only one source for each secret value.")
    if value_text is not None:
        return value_text.strip()
    if value_env:
        return os.environ.get(value_env, "").strip()
    if value_file:
        path = Path(value_file).expanduser()
        if not path.exists():
            raise ValueError("secret value file does not exist.")
        return path.read_text(encoding="utf-8", errors="replace").strip()
    return ""


def _validate_secret_value(value: str, *, label: str) -> None:
    clean = value.strip()
    if _is_placeholder(clean):
        raise ValueError(f"{label} is empty or placeholder.")
    if len(clean) < 8:
        raise ValueError(f"{label} is too short to be useful.")


def _load_payload(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {key: "" for key in SEARCH_SECRET_KEYS}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"search secrets JSON is invalid: {exc.msg}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("search secrets JSON must be an object.")
    return dict(payload)


def _provider_status(provider: str, payload: Mapping[str, Any]) -> dict[str, Any]:
    for item in search_provider_status_from_payload(payload):
        if item.get("provider") == provider:
            return item
    return {"provider": provider, "ready": False, "status": "missing_secret"}


def search_provider_status_from_payload(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    temp_path = None
    try:
        import tempfile

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
            json.dump(dict(payload), handle)
            temp_path = handle.name
        return search_provider_status(temp_path)
    finally:
        if temp_path:
            try:
                Path(temp_path).unlink()
            except OSError:
                pass


def _is_placeholder(value: str) -> bool:
    return value.strip().lower() in PLACEHOLDERS


def _chmod_private_file(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _chmod_private_dir(path: Path) -> None:
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass


def _path_label(path: Path) -> str:
    value = str(path)
    home = str(Path.home())
    if value.startswith(home):
        value = "~" + value[len(home) :]
    if Path(value).name == "policy-search-secrets.json":
        return "~/.policy-intelligence/policy-search-secrets.json" if ".policy-intelligence/" in value else "<secure_dir>/policy-search-secrets.json"
    return value


def _command_path(path: Path) -> str:
    value = str(path)
    home = str(Path.home())
    if value.startswith(home):
        return "~" + value[len(home) :]
    if Path(value).name == "policy-search-secrets.json":
        return _path_label(path)
    return value
