from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from .platform_auth import DEFAULT_CAPABILITIES
from .readiness import CORE_PLATFORMS


SEARCH_SECRET_KEYS = [
    "SERPAPI_API_KEY",
    "BING_SEARCH_API_KEY",
    "GOOGLE_SEARCH_API_KEY",
    "GOOGLE_CSE_ID",
]

PLATFORM_VALIDATION_HINTS = {
    "douyin": {
        "validation_url": "https://www.douyin.com/user/self",
        "success_markers": ["关注", "获赞"],
        "login_required_markers": ["登录", "验证码"],
        "captcha_markers": ["安全验证", "captcha"],
    },
    "kuaishou": {
        "validation_url": "https://www.kuaishou.com/",
        "success_markers": ["快手", "关注"],
        "login_required_markers": ["登录", "注册"],
        "captcha_markers": ["安全验证", "验证码"],
    },
    "weibo": {
        "validation_url": "https://weibo.com/",
        "success_markers": ["微博", "首页"],
        "login_required_markers": ["登录", "账号"],
        "captcha_markers": ["安全验证", "验证码"],
    },
    "zhihu": {
        "validation_url": "https://www.zhihu.com/",
        "success_markers": ["知乎", "首页"],
        "login_required_markers": ["登录", "注册"],
        "captcha_markers": ["captcha", "验证码"],
    },
    "wechat": {
        "validation_url": "https://weixin.sogou.com/",
        "success_markers": ["微信", "公众号"],
        "login_required_markers": ["登录", "账号"],
        "captcha_markers": ["安全验证", "验证码"],
    },
    "xiaohongshu": {
        "validation_url": "https://www.xiaohongshu.com/",
        "success_markers": ["小红书", "发现"],
        "login_required_markers": ["登录", "注册"],
        "captcha_markers": ["安全验证", "验证码"],
    },
    "toutiao": {
        "validation_url": "https://www.toutiao.com/",
        "success_markers": ["今日头条", "头条"],
        "login_required_markers": ["登录", "注册"],
        "captcha_markers": ["安全验证", "验证码"],
    },
}


def build_config_setup(
    *,
    secure_dir: str | Path | None = None,
    search_secrets_path: str | Path | None = None,
    platform_auth_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(secure_dir or "~/.policy-intelligence").expanduser()
    search_path = Path(search_secrets_path).expanduser() if search_secrets_path else root / "policy-search-secrets.json"
    auth_path = Path(platform_auth_path).expanduser() if platform_auth_path else root / "policy-platform-auth.json"
    cookie_dir = root / "cookies"
    search_bundle_path = root / "search_api_bundle.example.json"
    platform_bundle_path = root / "platform_auth_bundle.example.json"
    search_payload = {key: "" for key in SEARCH_SECRET_KEYS}
    platform_payload = {
        "platforms": {
            platform: _platform_auth_template(platform, cookie_dir)
            for platform in CORE_PLATFORMS
        }
    }
    search_bundle_payload = _search_api_bundle_template()
    platform_bundle_payload = _platform_auth_bundle_template(cookie_dir)
    return {
        "secure_dir": str(root),
        "search_secrets_path": str(search_path),
        "platform_auth_path": str(auth_path),
        "cookie_dir": str(cookie_dir),
        "search_api_bundle_example_path": str(search_bundle_path),
        "platform_auth_bundle_example_path": str(platform_bundle_path),
        "search_template": search_payload,
        "platform_auth_template": platform_payload,
        "search_api_bundle_template": search_bundle_payload,
        "platform_auth_bundle_template": platform_bundle_payload,
        "env_exports": {
            "SEARCH_SECRETS_FILE": str(search_path),
            "PLATFORM_AUTH_FILE": str(auth_path),
        },
        "shell_exports": [
            f"export SEARCH_SECRETS_FILE={_shell_quote(str(search_path))}",
            f"export PLATFORM_AUTH_FILE={_shell_quote(str(auth_path))}",
        ],
        "next_steps": [
            "Edit search_api_bundle.example.json, then run search-secret-bulk-import.",
            "Edit platform_auth_bundle.example.json with a Bilibili cookie or Chrome/session reference, then run platform-auth-bundle-import or platform-auth-session-import.",
            "Run access-readiness with both file paths; do not paste secrets into chat.",
            "Run the pipeline only after readiness shows the expected keys/auth files are available.",
        ],
    }


def write_config_setup(
    *,
    secure_dir: str | Path | None = None,
    search_secrets_path: str | Path | None = None,
    platform_auth_path: str | Path | None = None,
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    setup = build_config_setup(
        secure_dir=secure_dir,
        search_secrets_path=search_secrets_path,
        platform_auth_path=platform_auth_path,
    )
    writes = []
    for key, payload_key in [
        ("search_secrets_path", "search_template"),
        ("platform_auth_path", "platform_auth_template"),
        ("search_api_bundle_example_path", "search_api_bundle_template"),
        ("platform_auth_bundle_example_path", "platform_auth_bundle_template"),
    ]:
        path = Path(str(setup[key])).expanduser()
        action = _planned_action(path, force)
        writes.append({"path": str(path), "action": action})
        if dry_run or action == "skip_exists":
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(setup[payload_key], ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        _chmod_private(path)
    cookie_dir = Path(str(setup["cookie_dir"])).expanduser()
    if not dry_run:
        cookie_dir.mkdir(parents=True, exist_ok=True)
        _chmod_private_dir(Path(str(setup["secure_dir"])).expanduser())
        _chmod_private_dir(cookie_dir)
    setup["writes"] = writes
    setup["dry_run"] = dry_run
    setup["force"] = force
    setup["security_note"] = (
        "Templates contain empty key fields, placeholder bundle values, and cookie/session paths only. "
        "The command does not create cookie files, does not read browser profiles, and does not store account passwords."
    )
    return setup


def _planned_action(path: Path, force: bool) -> str:
    if path.exists() and not force:
        return "skip_exists"
    if path.exists() and force:
        return "overwrite"
    return "create"


def _chmod_private(path: Path) -> None:
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass


def _chmod_private_dir(path: Path) -> None:
    try:
        os.chmod(path, 0o700)
    except OSError:
        pass


def _platform_auth_template(platform: str, cookie_dir: Path) -> dict[str, Any]:
    template: dict[str, Any] = {
        "auth_method": "cookie_file",
        "cookie_file": str(cookie_dir / f"{platform}_cookie.txt"),
    }
    template.update(PLATFORM_VALIDATION_HINTS.get(platform, {}))
    template["allowed_capabilities"] = DEFAULT_CAPABILITIES.get(platform, [])
    return template


def _search_api_bundle_template() -> dict[str, Any]:
    return {
        "SERPAPI_API_KEY": "",
        "bing": {"api_key": ""},
        "google": {"api_key": "", "cse_id": ""},
    }


def _platform_auth_bundle_template(cookie_dir: Path) -> dict[str, Any]:
    return {
        "platforms": {
            "bilibili": {
                "cookie_file": str(cookie_dir / "bilibili_cookie.txt"),
                "chrome_profile_dir": "/path/to/chrome/profile/or/leave_empty",
            },
            "wechat": {"cookie_file": str(cookie_dir / "wechat_cookie.txt")},
            "zhihu": {"cookie_file": str(cookie_dir / "zhihu_cookie.txt")},
            "weibo": {"cookie_file": str(cookie_dir / "weibo_cookie.txt")},
            "douyin": {"chrome_profile_dir": "/path/to/chrome/profile/or/leave_empty"},
            "kuaishou": {"chrome_profile_dir": "/path/to/chrome/profile/or/leave_empty"},
            "xiaohongshu": {"chrome_profile_dir": "/path/to/chrome/profile/or/leave_empty"},
            "toutiao": {"cookie_file": str(cookie_dir / "toutiao_cookie.txt")},
        }
    }


def _shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"
