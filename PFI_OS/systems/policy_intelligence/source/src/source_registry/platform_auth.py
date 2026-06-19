from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


COOKIE_ENV_BY_PLATFORM = {
    "bilibili": "BILIBILI_COOKIE_FILE",
    "douyin": "DOUYIN_COOKIE_FILE",
    "kuaishou": "KUAISHOU_COOKIE_FILE",
    "weibo": "WEIBO_COOKIE_FILE",
    "zhihu": "ZHIHU_COOKIE_FILE",
    "wechat": "WECHAT_COOKIE_FILE",
    "xiaohongshu": "XIAOHONGSHU_COOKIE_FILE",
    "toutiao": "TOUTIAO_COOKIE_FILE",
}

DEFAULT_CAPABILITIES = {
    "bilibili": ["video_detail", "public_subtitle"],
    "douyin": ["search", "video_detail", "comments", "author_profile"],
    "kuaishou": ["search", "video_detail", "comments", "author_profile"],
    "weibo": ["search", "post_detail", "comments", "author_profile"],
    "zhihu": ["search", "article_detail", "answer_detail", "author_profile"],
    "wechat": ["article_detail", "author_profile"],
    "xiaohongshu": ["search", "note_detail", "comments", "author_profile"],
    "toutiao": ["search", "article_detail", "comments", "author_profile"],
}


@dataclass(frozen=True)
class PlatformAuthState:
    platform: str
    configured: bool
    available: bool
    status: str
    auth_method: str = ""
    cookie_file: str = ""
    session_file: str = ""
    allowed_capabilities: tuple[str, ...] = ()
    validation_url: str = ""
    success_markers: tuple[str, ...] = ()
    login_required_markers: tuple[str, ...] = ()
    captcha_markers: tuple[str, ...] = ()
    note: str = ""

    def as_metadata(self) -> dict[str, Any]:
        return {
            "platform": self.platform,
            "configured": self.configured,
            "available": self.available,
            "status": self.status,
            "auth_method": self.auth_method,
            "cookie_file_configured": bool(self.cookie_file),
            "session_file_configured": bool(self.session_file),
            "collector_ready": bool(self.available and self.cookie_file),
            "allowed_capabilities": list(self.allowed_capabilities),
            "validation_url_configured": bool(self.validation_url),
            "success_marker_count": len(self.success_markers),
            "login_required_marker_count": len(self.login_required_markers),
            "captcha_marker_count": len(self.captcha_markers),
            "note": self.note,
        }


def platform_auth_state(
    platform: str,
    auth_file: str | Path | None = None,
    extra_cookie_file: str | Path | None = None,
) -> PlatformAuthState:
    platform_key = _platform_key(platform)
    config = _platform_config(platform_key, auth_file)
    cookie_file = str(extra_cookie_file or config.get("cookie_file") or "").strip()
    session_file = _session_path(config)
    auth_method = str(config.get("auth_method") or "").strip()
    capabilities = tuple(
        str(item)
        for item in (
            config.get("allowed_capabilities")
            or DEFAULT_CAPABILITIES.get(platform_key, [])
        )
        if str(item).strip()
    )
    validation_url = str(config.get("validation_url") or "").strip()
    success_markers = _string_tuple(config.get("success_markers"))
    login_required_markers = _string_tuple(config.get("login_required_markers"))
    captcha_markers = _string_tuple(config.get("captcha_markers"))
    if not cookie_file:
        env_name = COOKIE_ENV_BY_PLATFORM.get(platform_key)
        cookie_file = os.environ.get(env_name, "").strip() if env_name else ""
    configured = bool(cookie_file or session_file or auth_method)
    if cookie_file:
        cookie_path = Path(cookie_file).expanduser()
        if cookie_path.exists():
            return PlatformAuthState(
                platform=platform_key,
                configured=True,
                available=True,
                status="auth_cookie_file_available",
                auth_method=auth_method or "cookie_file",
                cookie_file=str(cookie_path),
                session_file=session_file,
                allowed_capabilities=capabilities,
                validation_url=validation_url,
                success_markers=success_markers,
                login_required_markers=login_required_markers,
                captcha_markers=captcha_markers,
                note="本地 cookie 文件存在；系统不会在报告或日志中输出 cookie 内容。",
            )
        return PlatformAuthState(
            platform=platform_key,
            configured=True,
            available=False,
            status="auth_cookie_file_missing",
            auth_method=auth_method or "cookie_file",
            cookie_file=str(cookie_path),
            session_file=session_file,
            allowed_capabilities=capabilities,
            validation_url=validation_url,
            success_markers=success_markers,
            login_required_markers=login_required_markers,
            captcha_markers=captcha_markers,
            note="已配置 cookie 文件路径，但文件不存在或当前用户不可读。",
        )
    if session_file:
        session_path = Path(session_file).expanduser()
        if session_path.exists():
            return PlatformAuthState(
                platform=platform_key,
                configured=True,
                available=True,
                status="auth_session_file_available",
                auth_method=auth_method or _session_auth_method(config),
                session_file=str(session_path),
                allowed_capabilities=capabilities,
                validation_url=validation_url,
                success_markers=success_markers,
                login_required_markers=login_required_markers,
                captcha_markers=captcha_markers,
                note="本地 Chrome/session 引用存在；仅作为授权状态，直接采集仍优先需要 cookie 文件，不绕过验证码或访问控制。",
            )
        return PlatformAuthState(
            platform=platform_key,
            configured=True,
            available=False,
            status="auth_session_file_missing",
            auth_method=auth_method or _session_auth_method(config),
            session_file=str(session_path),
            allowed_capabilities=capabilities,
            validation_url=validation_url,
            success_markers=success_markers,
            login_required_markers=login_required_markers,
            captcha_markers=captcha_markers,
            note="已配置 Chrome/session 文件路径，但文件不存在或当前用户不可读。",
        )
    return PlatformAuthState(
        platform=platform_key,
        configured=False,
        available=False,
        status="auth_not_configured",
        allowed_capabilities=capabilities,
        validation_url=validation_url,
        success_markers=success_markers,
        login_required_markers=login_required_markers,
        captcha_markers=captcha_markers,
        note="未配置本地授权文件；只能保留公开搜索入口或开放 API 结果。",
    )


def bilibili_cookie_file_from_auth(
    auth_file: str | Path | None,
    explicit_cookie_file: str | Path | None = None,
) -> str | None:
    state = platform_auth_state("bilibili", auth_file, explicit_cookie_file)
    if state.available and state.cookie_file:
        return state.cookie_file
    return str(explicit_cookie_file) if explicit_cookie_file else None


def _platform_config(platform: str, auth_file: str | Path | None) -> Mapping[str, Any]:
    config = _load_auth_config(auth_file)
    platforms = config.get("platforms") if isinstance(config, Mapping) else {}
    if not isinstance(platforms, Mapping):
        return {}
    raw = platforms.get(platform) or {}
    return raw if isinstance(raw, Mapping) else {}


def _load_auth_config(auth_file: str | Path | None) -> Mapping[str, Any]:
    if not auth_file:
        auth_file = os.environ.get("PLATFORM_AUTH_FILE")
    if not auth_file:
        return {}
    path = Path(auth_file).expanduser()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


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


def _string_tuple(value: Any) -> tuple[str, ...]:
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        values = []
    return tuple(str(item).strip() for item in values if str(item).strip())


def _session_path(config: Mapping[str, Any]) -> str:
    for key in ("chrome_session_file", "session_file", "chrome_profile_dir", "chrome_user_data_dir"):
        value = str(config.get(key) or "").strip()
        if value:
            return value
    return ""


def _session_auth_method(config: Mapping[str, Any]) -> str:
    if str(config.get("chrome_profile_dir") or config.get("chrome_user_data_dir") or "").strip():
        return "chrome_profile_reference"
    return "chrome_session"
