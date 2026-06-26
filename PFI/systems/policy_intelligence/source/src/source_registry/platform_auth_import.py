from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping

from .config_setup import build_config_setup
from .platform_auth import DEFAULT_CAPABILITIES
from .readiness import CORE_PLATFORMS


COOKIE_HINTS = {
    "bilibili": ("SESSDATA", "DedeUserID", "bili_jct"),
    "douyin": ("sessionid", "sid_guard", "passport_csrf_token"),
    "kuaishou": ("kuaishou", "did", "userId"),
    "weibo": ("SUB", "SUBP", "ALF"),
    "zhihu": ("z_c0", "_xsrf"),
    "wechat": ("suid", "SUV", "SNUID"),
    "xiaohongshu": ("web_session", "a1", "xsecappid"),
    "toutiao": ("sessionid", "tt_webid", "s_v_web_id"),
}

SESSION_BUNDLE_KEYS = ("chrome_session_file", "session_file", "chrome_profile_dir", "chrome_user_data_dir")


def import_platform_auth_cookie(
    platform: str,
    *,
    source_file: str | Path | None = None,
    cookie_env: str | None = None,
    cookie_text: str | None = None,
    secure_dir: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    target_file: str | Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    platform_key = _platform_key(platform)
    if platform_key not in CORE_PLATFORMS:
        raise ValueError(f"unsupported platform: {platform}")
    raw_cookie = _cookie_text(source_file=source_file, cookie_env=cookie_env, cookie_text=cookie_text)
    if not raw_cookie.strip():
        raise ValueError("cookie content is empty; export the logged-in browser cookie to a local file first.")
    if len(raw_cookie.strip()) < 12:
        raise ValueError("cookie content is too short to be useful.")

    setup = build_config_setup(secure_dir=secure_dir, platform_auth_path=platform_auth_file)
    auth_path = Path(str(platform_auth_file or setup["platform_auth_path"])).expanduser()
    cookie_dir = Path(str(setup["cookie_dir"])).expanduser()
    target = Path(target_file).expanduser() if target_file else cookie_dir / f"{platform_key}_cookie.txt"
    marker_status = _marker_status(platform_key, raw_cookie)
    target_exists = target.exists()
    if target_exists and not force and not dry_run:
        raise ValueError(f"target cookie file already exists; rerun with --force to overwrite: {_path_label(target)}")

    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        _chmod_private_dir(target.parent)
        _chmod_private_dir(Path(str(setup["secure_dir"])).expanduser())
        target.write_text(raw_cookie.strip() + "\n", encoding="utf-8")
        _chmod_private_file(target)
        _upsert_platform_auth(auth_path, platform_key, target)

    return {
        "platform": platform_key,
        "status": "dry_run" if dry_run else "imported",
        "target_file": _path_label(target),
        "platform_auth_file": _path_label(auth_path),
        "target_exists_before": target_exists,
        "overwritten": bool(target_exists and force and not dry_run),
        "cookie_size_bytes": len(raw_cookie.strip().encode("utf-8")),
        "marker_status": marker_status,
        "allowed_capabilities": DEFAULT_CAPABILITIES.get(platform_key, []),
        "next_commands": [
            (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite credential-doctor "
                f"--platform-auth-file {_command_path(auth_path)}"
            ),
            (
                "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate "
                f"--platform-auth-file {_command_path(auth_path)} --platform {platform_key}"
            ),
        ],
        "security_boundary": (
            "cookie 内容已写入本地私有文件；命令输出、dashboard、报告和数据库只展示脱敏状态，"
            "不展示 cookie、session、账号密码或完整敏感路径。"
        ),
    }


def import_platform_auth_cookie_directory(
    source_dir: str | Path,
    *,
    platforms: list[str] | None = None,
    secure_dir: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    directory = Path(source_dir).expanduser()
    if not directory.exists() or not directory.is_dir():
        raise ValueError("source cookie directory does not exist.")
    requested = [_platform_key(item) for item in (platforms or CORE_PLATFORMS)]
    unsupported = [item for item in requested if item not in CORE_PLATFORMS]
    if unsupported:
        raise ValueError(f"unsupported platform: {unsupported[0]}")
    results = []
    missing = []
    for platform in requested:
        source = _cookie_source_for_platform(directory, platform)
        if not source:
            missing.append(platform)
            continue
        results.append(
            import_platform_auth_cookie(
                platform,
                source_file=source,
                secure_dir=secure_dir,
                platform_auth_file=platform_auth_file,
                force=force,
                dry_run=dry_run,
            )
        )
    return {
        "status": "dry_run" if dry_run else "imported",
        "source_dir": "<cookie_source_dir>",
        "requested_count": len(requested),
        "imported_count": len(results),
        "missing_count": len(missing),
        "missing_platforms": missing,
        "results": results,
        "next_commands": _bulk_next_commands(platform_auth_file=platform_auth_file, secure_dir=secure_dir),
        "security_boundary": (
            "批量导入只读取本地目录中按平台命名的 cookie 文件；输出只展示平台、状态、脱敏目标路径和 marker 状态，"
            "不展示 cookie、session、账号密码或完整本地敏感路径。"
        ),
    }


def import_platform_auth_session_reference(
    platform: str,
    *,
    session_file: str | Path,
    secure_dir: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    auth_method: str | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    platform_key = _platform_key(platform)
    if platform_key not in CORE_PLATFORMS:
        raise ValueError(f"unsupported platform: {platform}")
    session_path = Path(session_file).expanduser()
    if not session_path.exists():
        raise ValueError("Chrome/session reference path does not exist.")

    setup = build_config_setup(secure_dir=secure_dir, platform_auth_path=platform_auth_file)
    auth_path = Path(str(platform_auth_file or setup["platform_auth_path"])).expanduser()
    method = auth_method or ("chrome_profile_reference" if session_path.is_dir() else "chrome_session")
    if not dry_run:
        _upsert_platform_auth_session(auth_path, platform_key, session_path, auth_method=method)

    return {
        "platform": platform_key,
        "status": "dry_run" if dry_run else "session_reference_imported",
        "auth_method": method,
        "session_reference_type": "directory" if session_path.is_dir() else "file",
        "session_reference": _session_path_label(session_path),
        "platform_auth_file": _path_label(auth_path),
        "collector_ready": False,
        "allowed_capabilities": DEFAULT_CAPABILITIES.get(platform_key, []),
        "next_commands": _bulk_next_commands(platform_auth_file=platform_auth_file, secure_dir=secure_dir),
        "security_boundary": (
            "Chrome/session 引用只登记本地路径状态，用于后续授权验收或人工交接；"
            "不会读取、复制、展示浏览器 cookie、session、账号密码或完整敏感路径。"
        ),
    }


def import_platform_auth_cookie_bundle(
    source_file: str | Path,
    *,
    platforms: list[str] | None = None,
    secure_dir: str | Path | None = None,
    platform_auth_file: str | Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    bundle_path = Path(source_file).expanduser()
    if not bundle_path.exists():
        raise ValueError("platform auth bundle file does not exist.")
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"platform auth bundle JSON is invalid: {exc.msg}") from exc
    if not isinstance(bundle, Mapping):
        raise ValueError("platform auth bundle JSON must be an object.")
    requested = [_platform_key(item) for item in (platforms or CORE_PLATFORMS)]
    unsupported = [item for item in requested if item not in CORE_PLATFORMS]
    if unsupported:
        raise ValueError(f"unsupported platform: {unsupported[0]}")
    results = []
    missing = []
    for platform in requested:
        source = _bundle_cookie_source(bundle, platform)
        session_source, session_key = _bundle_session_source(bundle, platform)
        if not source and not session_source:
            missing.append(platform)
            continue
        if source:
            results.append(
                import_platform_auth_cookie(
                    platform,
                    source_file=source,
                    secure_dir=secure_dir,
                    platform_auth_file=platform_auth_file,
                    force=force,
                    dry_run=dry_run,
                )
            )
        else:
            results.append(
                import_platform_auth_session_reference(
                    platform,
                    session_file=session_source,
                    secure_dir=secure_dir,
                    platform_auth_file=platform_auth_file,
                    auth_method="chrome_profile_reference" if session_key in {"chrome_profile_dir", "chrome_user_data_dir"} else "chrome_session",
                    dry_run=dry_run,
                )
            )
    return {
        "status": "dry_run" if dry_run else "imported",
        "source_file": "<platform_auth_bundle>",
        "requested_count": len(requested),
        "imported_count": len(results),
        "missing_count": len(missing),
        "missing_platforms": missing,
        "results": results,
        "next_commands": _bulk_next_commands(platform_auth_file=platform_auth_file, secure_dir=secure_dir),
        "security_boundary": (
            "bundle 导入只读取你指定的本地 cookie 文件路径并复制到私有目录；输出只展示平台、状态、"
            "脱敏目标路径和 marker/session 状态，不展示 cookie、session、账号密码、bundle 内容或完整敏感路径。"
        ),
    }


def _bundle_cookie_source(bundle: Mapping[str, Any], platform: str) -> str:
    raw = bundle.get(platform)
    if raw is None:
        raw = bundle.get(platform.upper())
    if isinstance(raw, str):
        return raw.strip()
    if isinstance(raw, Mapping):
        for key in ("cookie_file", "source_file", "path", "file"):
            value = raw.get(key)
            if value:
                return str(value).strip()
    platforms = bundle.get("platforms")
    if isinstance(platforms, Mapping):
        nested = platforms.get(platform) or platforms.get(platform.upper())
        if isinstance(nested, str):
            return nested.strip()
        if isinstance(nested, Mapping):
            for key in ("cookie_file", "source_file", "path", "file"):
                value = nested.get(key)
                if value:
                    return str(value).strip()
    return ""


def _bundle_session_source(bundle: Mapping[str, Any], platform: str) -> tuple[str, str]:
    raw = bundle.get(platform)
    if raw is None:
        raw = bundle.get(platform.upper())
    source, key = _session_source_from_mapping(raw)
    if source:
        return source, key
    platforms = bundle.get("platforms")
    if isinstance(platforms, Mapping):
        nested = platforms.get(platform) or platforms.get(platform.upper())
        return _session_source_from_mapping(nested)
    return "", ""


def _session_source_from_mapping(raw: Any) -> tuple[str, str]:
    if not isinstance(raw, Mapping):
        return "", ""
    for key in SESSION_BUNDLE_KEYS:
        value = raw.get(key)
        if value:
            return str(value).strip(), key
    return "", ""


def _cookie_source_for_platform(directory: Path, platform: str) -> Path | None:
    candidates = [
        directory / f"{platform}_cookie.txt",
        directory / f"{platform}.cookie",
        directory / f"{platform}.txt",
        directory / f"cookie_{platform}.txt",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate
    return None


def _bulk_next_commands(
    *,
    platform_auth_file: str | Path | None,
    secure_dir: str | Path | None,
) -> list[str]:
    setup = build_config_setup(secure_dir=secure_dir, platform_auth_path=platform_auth_file)
    auth_path = Path(str(platform_auth_file or setup["platform_auth_path"])).expanduser()
    return [
        (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite credential-doctor "
            f"--platform-auth-file {_command_path(auth_path)}"
        ),
        (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-auth-validate "
            f"--platform-auth-file {_command_path(auth_path)}"
        ),
        (
            "PYTHONPATH=src python3 -m source_registry --db data/source_registry.sqlite platform-parser-validate "
            f"--platform-auth-file {_command_path(auth_path)}"
        ),
    ]


def _cookie_text(
    *,
    source_file: str | Path | None,
    cookie_env: str | None,
    cookie_text: str | None,
) -> str:
    supplied = sum(1 for item in [source_file, cookie_env, cookie_text] if item)
    if supplied != 1:
        raise ValueError("provide exactly one cookie source: --source-file, --cookie-env, or internal cookie_text.")
    if cookie_text is not None:
        return cookie_text
    if cookie_env:
        return os.environ.get(cookie_env, "")
    if source_file:
        path = Path(source_file).expanduser()
        if not path.exists():
            raise ValueError("source cookie file does not exist.")
        return path.read_text(encoding="utf-8", errors="replace")
    return ""


def _upsert_platform_auth(auth_path: Path, platform: str, cookie_file: Path) -> None:
    payload = _load_json(auth_path)
    platforms = payload.setdefault("platforms", {})
    if not isinstance(platforms, dict):
        platforms = {}
        payload["platforms"] = platforms
    current = platforms.get(platform)
    config = current if isinstance(current, dict) else {}
    config["auth_method"] = "cookie_file"
    config["cookie_file"] = str(cookie_file)
    config.pop("chrome_session_file", None)
    config.pop("session_file", None)
    config.pop("chrome_profile_dir", None)
    config.pop("chrome_user_data_dir", None)
    config.setdefault("allowed_capabilities", DEFAULT_CAPABILITIES.get(platform, []))
    platforms[platform] = config
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _chmod_private_file(auth_path)


def _upsert_platform_auth_session(auth_path: Path, platform: str, session_path: Path, *, auth_method: str) -> None:
    payload = _load_json(auth_path)
    platforms = payload.setdefault("platforms", {})
    if not isinstance(platforms, dict):
        platforms = {}
        payload["platforms"] = platforms
    current = platforms.get(platform)
    config = current if isinstance(current, dict) else {}
    config["auth_method"] = auth_method
    config.pop("cookie_file", None)
    if session_path.is_dir():
        config["chrome_profile_dir"] = str(session_path)
        config.pop("chrome_session_file", None)
        config.pop("session_file", None)
    else:
        config["chrome_session_file"] = str(session_path)
        config.pop("chrome_profile_dir", None)
        config.pop("chrome_user_data_dir", None)
    config.setdefault("allowed_capabilities", DEFAULT_CAPABILITIES.get(platform, []))
    platforms[platform] = config
    auth_path.parent.mkdir(parents=True, exist_ok=True)
    auth_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    _chmod_private_file(auth_path)


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"platforms": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"platform auth JSON is invalid: {exc.msg}") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("platform auth JSON must be an object.")
    return dict(payload)


def _marker_status(platform: str, cookie: str) -> str:
    hints = COOKIE_HINTS.get(platform, ())
    if not hints:
        return "not_checked"
    return "expected_marker_found" if any(hint in cookie for hint in hints) else "expected_marker_missing"


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


def _platform_key(platform: str) -> str:
    value = platform.strip().lower()
    aliases = {
        "b站": "bilibili",
        "哔哩哔哩": "bilibili",
        "weixin": "wechat",
        "微信": "wechat",
        "微信公众号": "wechat",
        "小红书": "xiaohongshu",
        "今日头条": "toutiao",
    }
    return aliases.get(value, value)


def _path_label(path: Path) -> str:
    value = str(path)
    home = str(Path.home())
    if value.startswith(home):
        value = "~" + value[len(home) :]
    if ".policy-intelligence/cookies/" in value:
        return "~/.policy-intelligence/cookies/" + Path(value).name
    if Path(value).parent.name == "cookies":
        return "<cookie_dir>/" + Path(value).name
    if Path(value).name == "policy-platform-auth.json":
        return "<secure_dir>/policy-platform-auth.json"
    if ".policy-intelligence/" in value:
        return "~/.policy-intelligence/" + Path(value).name
    return value


def _session_path_label(path: Path) -> str:
    if path.is_dir():
        return "<chrome_profile_dir>"
    return "<chrome_session_file>"


def _tilde(path: str | Path) -> str:
    value = str(path)
    home = str(Path.home())
    if value.startswith(home):
        return "~" + value[len(home) :]
    return value


def _command_path(path: Path) -> str:
    value = str(path)
    if ".policy-intelligence/" in value or value.startswith(str(Path.home())):
        return _tilde(path)
    return _path_label(path)
