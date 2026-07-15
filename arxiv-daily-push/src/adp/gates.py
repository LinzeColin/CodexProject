"""5 资格硬门（R1-1）—— 布尔先淘汰，不参与打分；每条拦截一句人话原因.

纯函数：输入候选与上下文 dict，输出 GateResult。测试保护见 tests/test_adp_selection.py。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from urllib.parse import urlparse

OFFICIAL_HOSTS = {"arxiv.org", "export.arxiv.org", "www.arxiv.org",
                  "biorxiv.org", "www.biorxiv.org", "medrxiv.org", "www.medrxiv.org"}


@dataclass(frozen=True)
class GateResult:
    passed: bool
    results: Mapping[str, bool]
    reject_reason: str  # 人话，一句；通过时为空


def run_gates(candidate: Mapping[str, Any], context: Mapping[str, Any]) -> GateResult:
    """context: source_health(str), seen_version_ids(set[str]), license_usage_allowlist(set[str])."""
    meta = (candidate.get("metadata") or {}).get("arxiv") or {}
    checks: dict[str, bool] = {}
    reasons: dict[str, str] = {}

    summary = (meta.get("summary") or "").strip()
    url = candidate.get("canonical_url") or ""
    checks["evidence_traceable"] = bool(summary) and bool(url)
    reasons["evidence_traceable"] = "关键声明缺少可定位原文（无摘要或无原文链接）"

    parsed = urlparse(url)
    checks["official_https_source"] = parsed.scheme == "https" and parsed.hostname in OFFICIAL_HOSTS
    reasons["official_https_source"] = f"来源不是官方 HTTPS 渠道（{parsed.hostname or '无主机'}）"

    versioned_id = meta.get("versioned_id") or ""
    seen: set[str] = set(context.get("seen_version_ids") or set())
    checks["dedup_version_unique"] = bool(versioned_id) and versioned_id not in seen
    reasons["dedup_version_unique"] = f"重复条目：版本 {versioned_id or '未知'} 此前已入选或已生成讲义"

    health = str(context.get("source_health") or "active")
    checks["source_health_ok"] = health in {"active", "degraded"}
    reasons["source_health_ok"] = f"来源健康状态为 {health}（连续失败已自动停用）"

    usage = str(((candidate.get("license") or {}).get("usage")) or "")
    allow = set(context.get("license_usage_allowlist") or {"private_learning_link_only"})
    checks["license_policy_ok"] = usage in allow
    reasons["license_policy_ok"] = f"许可用途 {usage or '未知'} 不在私人学习白名单内"

    failed = [key for key, ok in checks.items() if not ok]
    return GateResult(
        passed=not failed,
        results=checks,
        reject_reason="" if not failed else reasons[failed[0]],
    )
