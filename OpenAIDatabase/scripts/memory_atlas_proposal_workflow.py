#!/usr/bin/env python3
"""Controlled proposal approval, apply, validation and rollback for Memory Atlas."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Callable


PROPOSAL_API_VERSION = "memory_atlas_proposal_api.v1_2_r4"
PROPOSAL_BUNDLE_VERSION = "memory_atlas_apply_ready_proposal.v1_2_r4"
PROPOSAL_REVIEW_VERSION = "memory_atlas_proposal_review.v1_2_r4"
PROPOSAL_RESULT_VERSION = "memory_atlas_proposal_result.v1_2_r4"
TRANSACTION_VERSION = "memory_atlas_proposal_transaction.v1_2_r4"
AUDIT_VERSION = "memory_atlas_proposal_audit.v1_2_r4"

APPLY_READY_DIR = Path("data/derived/proposals/apply_ready")
STATE_REPORT_PATH = Path("data/derived/proposals/proposal_state_machine_report.json")
DIFF_REPORT_PATH = Path("data/derived/proposals/diff_narrator_report.json")
REQUIRED_NARRATOR_FIELDS = (
    "what_changed_zh",
    "why_changed_zh",
    "affected_surfaces_zh",
    "how_to_verify_zh",
    "how_to_rollback_zh",
)
SUPPORTED_TARGET_TYPES = {
    "memory",
    "agents_rule",
    "config",
    "formula",
    "ui_text",
    "taxonomy",
    "report_template",
}
ALLOWED_VALIDATION_IDS = {"utf8_nonempty", "json_document"}
TARGET_PREFIXES: dict[str, tuple[str, ...]] = {
    "memory": (".codex/memories/extensions/ad_hoc/notes/",),
    "agents_rule": (".agents/",),
    "config": ("config/", "机器治理/运行门禁/"),
    "formula": ("机器治理/参数与公式/",),
    "ui_text": ("人类可读/",),
    "taxonomy": ("config/taxonomy/", "data/derived/taxonomy/"),
    "report_template": ("人类可读/", "config/report_templates/"),
}
TARGET_EXACT: dict[str, tuple[str, ...]] = {"agents_rule": ("AGENTS.md",)}
FORBIDDEN_PATH_FRAGMENTS = (
    "data/public_raw/",
    "data/raw/",
    "data/private_imports/",
    "raw_encrypted",
    "raw_archive",
    "transcript_archive",
    "credential",
    "cookies",
    "tokens",
    "secrets",
    "sessions/",
    ".git",
)
EXECUTABLE_SUFFIXES = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".sh", ".command"}
PROPOSAL_ID_PATTERN = re.compile(r"^proposal_[a-z0-9][a-z0-9_-]{5,55}$")
TRANSACTION_ID_PATTERN = re.compile(r"^txn_[a-f0-9]{20}$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")
MAX_BUNDLE_BYTES = 1_048_576
MAX_CONTENT_BYTES = 524_288
MAX_OPERATIONS = 8
MAX_VALIDATORS = 4


class ProposalWorkflowError(RuntimeError):
    """Base error for a rejected or failed proposal workflow operation."""


class ProposalBundleError(ProposalWorkflowError):
    """A proposal bundle is invalid or outside the target contract."""


class ProposalAuthorizationError(ProposalWorkflowError):
    """Human review proof is missing, stale, replayed or inconsistent."""


class ProposalValidationError(ProposalWorkflowError):
    """Post-apply validation did not pass."""


class ProposalRollbackError(ProposalWorkflowError):
    """A rollback cannot safely restore the recorded target state."""


@dataclass(frozen=True)
class ProposalWorkflowContext:
    source_root: Path
    app_support: Path
    token_ttl_seconds: int = 600


@dataclass(frozen=True)
class ParsedOperation:
    target_file: str
    target_path: Path
    expected_sha256: str
    content: bytes


@dataclass(frozen=True)
class ParsedBundle:
    path: Path
    digest: str
    proposal_id: str
    target_type: str
    risk_level: str
    expires_at: str
    action_half_life: str
    human_reason_zh: str
    narrator: dict[str, str]
    operations: tuple[ParsedOperation, ...]
    validation_ids: tuple[str, ...]
    rollback_plan_zh: str


def utc_iso(epoch: float | None = None) -> str:
    value = datetime.fromtimestamp(epoch if epoch is not None else time.time(), timezone.utc)
    return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ProposalBundleError(f"提案资料缺失或 JSON 无效：{path.name}。") from exc
    if not isinstance(payload, dict):
        raise ProposalBundleError(f"提案资料必须是 JSON object：{path.name}。")
    return payload


def parse_iso_epoch(value: str) -> float:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except (AttributeError, ValueError) as exc:
        raise ProposalBundleError("proposal expires_at 不是有效 ISO datetime。") from exc


def contains_chinese(value: str) -> bool:
    return any("\u4e00" <= character <= "\u9fff" for character in value)


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    staged = path.with_name(f".{path.name}.{os.getpid()}.{secrets.token_hex(4)}.next")
    try:
        staged.write_bytes(content)
        os.replace(staged, path)
    finally:
        if staged.exists():
            staged.unlink()


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    content = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n"
    atomic_write(path, content)


class ProposalWorkflow:
    def __init__(
        self,
        context: ProposalWorkflowContext,
        *,
        now_fn: Callable[[], float] = time.time,
        token_factory: Callable[[], str] = lambda: secrets.token_urlsafe(32),
    ) -> None:
        self.context = self._validate_workspace(context)
        self.now_fn = now_fn
        self.token_factory = token_factory
        self._review_tokens: dict[str, dict[str, Any]] = {}
        self._rollback_tokens: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _validate_workspace(context: ProposalWorkflowContext) -> ProposalWorkflowContext:
        app_support_raw = Path(os.path.abspath(context.app_support.expanduser()))
        source_raw = Path(os.path.abspath(context.source_root.expanduser()))
        if source_raw != app_support_raw / "source":
            raise ProposalBundleError("proposal 只能在 Memory Atlas Application Support 安装副本中执行。")
        if app_support_raw.is_symlink() or source_raw.is_symlink():
            raise ProposalBundleError("proposal source 不能是符号链接。")
        app_support = app_support_raw.resolve()
        source_root = source_raw.resolve()
        if source_root.parent != app_support or (source_root / ".git").exists():
            raise ProposalBundleError("proposal source 已逃逸安装副本或包含 Git worktree。")
        manifest = read_json(source_root / "memory_atlas_source_workspace.json")
        if manifest.get("schema_version") != "memory_atlas_source_workspace.v1":
            raise ProposalBundleError("Memory Atlas source manifest 版本无效。")
        original = manifest.get("original_repo_root")
        if not isinstance(original, str) or not original.strip() or Path(original).expanduser().resolve() == source_root:
            raise ProposalBundleError("proposal source manifest 未证明安装副本边界。")
        return ProposalWorkflowContext(
            source_root=source_root,
            app_support=app_support,
            token_ttl_seconds=max(1, int(context.token_ttl_seconds)),
        )

    def review(self) -> dict[str, Any]:
        now = self.now_fn()
        self._prune_tokens(now)
        state_items = self._state_items()
        narrator_items = self._narrator_items()
        indexed: dict[str, dict[str, Any]] = {}
        for proposal_id, state in state_items.items():
            narration = narrator_items.get(proposal_id, {})
            indexed[proposal_id] = {
                "proposal_id": proposal_id,
                "current_state": str(state.get("current_state") or "pending_human_review"),
                "target_type": str(state.get("target_type") or narration.get("target_type") or "unknown"),
                "target_files": [str(item) for item in state.get("target_files") or narration.get("target_files") or []],
                "risk_level": str(narration.get("risk_level") or "unknown"),
                "expires_at": str(state.get("expires_at") or ""),
                "action_half_life": str(state.get("action_half_life") or ""),
                "human_reason_zh": "当前提案可复核，但尚未提供可安全应用的精确文件内容。",
                "narrator": {field: str(narration.get(field) or "") for field in REQUIRED_NARRATOR_FIELDS},
                "validation_ids": [],
                "rollback_plan_zh": str(state.get("rollback_plan_zh") or narration.get("how_to_rollback_zh") or ""),
                "apply_ready": False,
                "blocked_reason_zh": "缺少 apply-ready bundle 的精确内容、目标 hash 或固定 validation ID。",
            }

        apply_ready_dir = self.context.source_root / APPLY_READY_DIR
        if apply_ready_dir.exists() and (apply_ready_dir.is_symlink() or not apply_ready_dir.is_dir()):
            raise ProposalBundleError("apply-ready proposal 目录必须是普通目录。")
        if apply_ready_dir.is_dir():
            for path in sorted(apply_ready_dir.glob("*.json")):
                fallback_id = path.stem if PROPOSAL_ID_PATTERN.fullmatch(path.stem) else f"proposal_invalid_{sha256_bytes(path.name.encode())[:8]}"
                try:
                    bundle = self._parse_bundle(path, now=now, verify_current_hash=True)
                except ProposalBundleError as exc:
                    indexed[fallback_id] = {
                        "proposal_id": fallback_id,
                        "current_state": "pending_human_review",
                        "target_type": "unknown",
                        "target_files": [],
                        "risk_level": "unknown",
                        "expires_at": "",
                        "action_half_life": "",
                        "human_reason_zh": "该 apply-ready bundle 未通过安全预检。",
                        "narrator": {field: "" for field in REQUIRED_NARRATOR_FIELDS},
                        "validation_ids": [],
                        "rollback_plan_zh": "没有执行写入，因此不需要回滚。",
                        "apply_ready": False,
                        "blocked_reason_zh": str(exc),
                    }
                    continue
                token = self.token_factory()
                self._review_tokens[token] = {
                    "proposal_id": bundle.proposal_id,
                    "bundle_path": str(bundle.path.relative_to(self.context.source_root)),
                    "bundle_digest": bundle.digest,
                    "expires_epoch": now + self.context.token_ttl_seconds,
                }
                indexed[bundle.proposal_id] = self._review_bundle(bundle, token)

        transactions = self._review_transactions(now)
        proposals = sorted(indexed.values(), key=lambda item: (not bool(item["apply_ready"]), item["proposal_id"]))
        return {
            "schema_version": PROPOSAL_REVIEW_VERSION,
            "status": "success",
            "proposal_api_version": PROPOSAL_API_VERSION,
            "proposals": proposals,
            "transactions": transactions,
            "summary": {
                "proposal_count": len(proposals),
                "apply_ready_count": sum(1 for item in proposals if item["apply_ready"]),
                "review_only_count": sum(1 for item in proposals if not item["apply_ready"]),
                "rollback_available_count": len(transactions),
            },
            "safety": {
                "raw_mutation": False,
                "canonical_repo_mutation": False,
                "remote_push": False,
                "operation_content_returned": False,
            },
        }

    def approve_and_apply(self, *, proposal_id: str, review_token: str, confirmation: str) -> dict[str, Any]:
        self._validate_proposal_id(proposal_id)
        if confirmation != f"授权应用 {proposal_id}":
            raise ProposalAuthorizationError("授权确认文本不匹配，未执行 apply。")
        now = self.now_fn()
        token = self._review_tokens.get(review_token)
        if not token or token.get("proposal_id") != proposal_id or float(token.get("expires_epoch", 0)) < now:
            raise ProposalAuthorizationError("proposal review token 缺失、过期或已使用，请重新打开提案复核。")
        relative_bundle = Path(str(token["bundle_path"]))
        bundle_path = self.context.source_root / relative_bundle
        bundle = self._parse_bundle(bundle_path, now=now, verify_current_hash=True)
        if bundle.digest != token.get("bundle_digest"):
            raise ProposalAuthorizationError("proposal 在复核后已变化，请重新核对后授权。")
        self._review_tokens.pop(review_token, None)
        return self._apply_bundle(bundle, now=now)

    def rollback(self, *, transaction_id: str, rollback_token: str, confirmation: str) -> dict[str, Any]:
        if not TRANSACTION_ID_PATTERN.fullmatch(transaction_id):
            raise ProposalAuthorizationError("rollback transaction ID 无效。")
        if confirmation != f"确认回滚 {transaction_id}":
            raise ProposalAuthorizationError("回滚确认文本不匹配，未执行 rollback。")
        now = self.now_fn()
        token = self._rollback_tokens.get(rollback_token)
        if not token or token.get("transaction_id") != transaction_id or float(token.get("expires_epoch", 0)) < now:
            raise ProposalAuthorizationError("rollback token 缺失、过期或已使用，请重新打开提案复核。")
        transaction_dir = self.context.app_support / "proposal_transactions" / transaction_id
        transaction = read_json(transaction_dir / "transaction.json")
        if transaction.get("schema_version") != TRANSACTION_VERSION or transaction.get("state") != "committed":
            raise ProposalRollbackError("该 transaction 当前不允许人工回滚。")
        targets = transaction.get("targets") if isinstance(transaction.get("targets"), list) else []
        for target in targets:
            relative = str(target.get("target_file") or "")
            target_path = self._resolve_target(str(transaction.get("target_type") or ""), relative)
            current = target_path.read_bytes() if target_path.exists() else b""
            if (target_path.exists() is not True) or sha256_bytes(current) != target.get("after_sha256"):
                raise ProposalRollbackError("目标文件在 apply 后又发生变化，已停止自动覆盖。")
        self._rollback_tokens.pop(rollback_token, None)
        restored = self._restore_transaction(transaction_dir, transaction)
        transaction["state"] = "rolled_back_by_human"
        transaction.setdefault("state_history", []).append("rolled_back_by_human")
        transaction["rolled_back_at"] = utc_iso(now)
        write_json_atomic(transaction_dir / "transaction.json", transaction)
        self._append_audit(
            action="rollback",
            proposal_id=str(transaction.get("proposal_id") or ""),
            status="success",
            transaction_id=transaction_id,
            target_files=sorted(restored),
        )
        return {
            "schema_version": PROPOSAL_RESULT_VERSION,
            "action": "rollback",
            "status": "success",
            "state": "rolled_back_by_human",
            "proposal_id": transaction.get("proposal_id"),
            "transaction_id": transaction_id,
            "message_zh": "本次 proposal 变更已按事务快照完整回滚。",
            "restored_sha256": restored,
            "safety": self._safety(proposal_apply_execution=False),
        }

    def _apply_bundle(self, bundle: ParsedBundle, *, now: float) -> dict[str, Any]:
        transaction_id = self._new_transaction_id(now)
        transaction_dir = self.context.app_support / "proposal_transactions" / transaction_id
        if transaction_dir.exists() or transaction_dir.is_symlink():
            raise ProposalWorkflowError("proposal transaction ID 冲突，未执行写入。")
        snapshots_dir = transaction_dir / "snapshots"
        snapshots_dir.mkdir(parents=True, exist_ok=False)
        state_history = ["pending_human_review", "approved_by_human", "applying"]
        targets: list[dict[str, Any]] = []
        for index, operation in enumerate(bundle.operations):
            before_exists = operation.target_path.exists()
            before = operation.target_path.read_bytes() if before_exists else b""
            snapshot_relative = f"snapshots/{index:03d}.bin"
            (transaction_dir / snapshot_relative).write_bytes(before)
            targets.append(
                {
                    "target_file": operation.target_file,
                    "before_exists": before_exists,
                    "before_sha256": sha256_bytes(before) if before_exists else "missing",
                    "after_sha256": sha256_bytes(operation.content),
                    "snapshot_file": snapshot_relative,
                }
            )
        transaction = {
            "schema_version": TRANSACTION_VERSION,
            "transaction_id": transaction_id,
            "proposal_id": bundle.proposal_id,
            "target_type": bundle.target_type,
            "state": "applying",
            "state_history": state_history,
            "started_at": utc_iso(now),
            "targets": targets,
            "validation_ids": list(bundle.validation_ids),
            "rollback_plan_zh": bundle.rollback_plan_zh,
            "raw_mutation": False,
            "canonical_repo_mutation": False,
            "remote_push": False,
        }
        write_json_atomic(transaction_dir / "transaction.json", transaction)
        try:
            for operation in bundle.operations:
                atomic_write(operation.target_path, operation.content)
            state_history.append("applied")
            transaction["state"] = "applied"
            write_json_atomic(transaction_dir / "transaction.json", transaction)
            self._run_validations(bundle)
            state_history.extend(["validated", "committed"])
            transaction["state"] = "committed"
            transaction["committed_at"] = utc_iso(self.now_fn())
            write_json_atomic(transaction_dir / "transaction.json", transaction)
        except Exception as exc:
            state_history.append("failed_validation")
            transaction["state"] = "failed_validation"
            transaction["failure_type"] = exc.__class__.__name__
            write_json_atomic(transaction_dir / "transaction.json", transaction)
            try:
                restored = self._restore_transaction(transaction_dir, transaction)
            except Exception as rollback_exc:
                transaction["state"] = "manual_rollback_required"
                transaction["state_history"].append("manual_rollback_required")
                transaction["rollback_failure_type"] = rollback_exc.__class__.__name__
                write_json_atomic(transaction_dir / "transaction.json", transaction)
                raise ProposalRollbackError("validation 失败且自动回滚未完成；请保留 transaction 证据并停止后续操作。") from rollback_exc
            transaction["state"] = "rollback_or_needs_revision"
            transaction["state_history"].append("rollback_or_needs_revision")
            transaction["rolled_back_at"] = utc_iso(self.now_fn())
            write_json_atomic(transaction_dir / "transaction.json", transaction)
            self._append_audit(
                action="approve_apply",
                proposal_id=bundle.proposal_id,
                status="validation_failed_rolled_back",
                transaction_id=transaction_id,
                target_files=[item.target_file for item in bundle.operations],
            )
            return {
                "schema_version": PROPOSAL_RESULT_VERSION,
                "action": "approve_apply",
                "status": "validation_failed_rolled_back",
                "state": "rollback_or_needs_revision",
                "proposal_id": bundle.proposal_id,
                "transaction_id": transaction_id,
                "message_zh": "apply 后 validation 未通过，所有目标已按事务快照自动恢复。",
                "state_history": list(transaction["state_history"]),
                "validation_ids": list(bundle.validation_ids),
                "validation_results": [{"validation_id": item, "status": "FAIL"} for item in bundle.validation_ids],
                "automatic_rollback": True,
                "rollback_available": False,
                "restored_sha256": restored,
                "safety": self._safety(proposal_apply_execution=True),
            }

        rollback_token = self.token_factory()
        self._rollback_tokens[rollback_token] = {
            "transaction_id": transaction_id,
            "expires_epoch": self.now_fn() + self.context.token_ttl_seconds,
        }
        self._append_audit(
            action="approve_apply",
            proposal_id=bundle.proposal_id,
            status="success",
            transaction_id=transaction_id,
            target_files=[item.target_file for item in bundle.operations],
        )
        return {
            "schema_version": PROPOSAL_RESULT_VERSION,
            "action": "approve_apply",
            "status": "success",
            "state": "committed",
            "proposal_id": bundle.proposal_id,
            "transaction_id": transaction_id,
            "message_zh": "proposal 已获本次人类授权，精确目标已应用并通过固定 validation。",
            "state_history": list(transaction["state_history"]),
            "validation_ids": list(bundle.validation_ids),
            "validation_results": [{"validation_id": item, "status": "PASS"} for item in bundle.validation_ids],
            "automatic_rollback": False,
            "rollback_available": True,
            "rollback_token": rollback_token,
            "safety": self._safety(proposal_apply_execution=True),
        }

    def _parse_bundle(self, path: Path, *, now: float, verify_current_hash: bool) -> ParsedBundle:
        if path.is_symlink() or not path.is_file():
            raise ProposalBundleError("apply-ready bundle 必须是普通非 symlink 文件。")
        raw = path.read_bytes()
        if not raw or len(raw) > MAX_BUNDLE_BYTES:
            raise ProposalBundleError("apply-ready bundle 为空或超过大小限制。")
        try:
            payload = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProposalBundleError("apply-ready bundle 不是有效 UTF-8 JSON。") from exc
        if not isinstance(payload, dict) or payload.get("schema_version") != PROPOSAL_BUNDLE_VERSION:
            raise ProposalBundleError("apply-ready bundle schema_version 无效。")
        proposal_id = str(payload.get("proposal_id") or "")
        self._validate_proposal_id(proposal_id)
        if path.stem != proposal_id:
            raise ProposalBundleError("apply-ready bundle 文件名必须等于 proposal_id。")
        if payload.get("current_state") != "pending_human_review":
            raise ProposalBundleError("apply-ready proposal 必须处于 pending_human_review。")
        target_type = str(payload.get("target_type") or "")
        if target_type not in SUPPORTED_TARGET_TYPES:
            raise ProposalBundleError("proposal target_type 不在固定支持列表。")
        risk_level = str(payload.get("risk_level") or "")
        if risk_level not in {"low", "medium", "high"}:
            raise ProposalBundleError("proposal risk_level 无效。")
        expires_at = str(payload.get("expires_at") or "")
        if parse_iso_epoch(expires_at) <= now:
            raise ProposalBundleError("proposal 已过期，必须重新生成后再授权。")
        action_half_life = str(payload.get("action_half_life") or "")
        if action_half_life not in {"today", "this_week", "this_month", "long_term", "expired"}:
            raise ProposalBundleError("proposal action_half_life 无效。")
        human_reason_zh = str(payload.get("human_reason_zh") or "").strip()
        if not human_reason_zh or not contains_chinese(human_reason_zh):
            raise ProposalBundleError("proposal human_reason_zh 必须是中文可读说明。")
        narrator_payload = payload.get("narrator") if isinstance(payload.get("narrator"), dict) else {}
        narrator: dict[str, str] = {}
        for field in REQUIRED_NARRATOR_FIELDS:
            value = str(narrator_payload.get(field) or "").strip()
            if not value or not contains_chinese(value):
                raise ProposalBundleError(f"proposal narrator 缺少中文字段：{field}。")
            narrator[field] = value
        operations_payload = payload.get("operations") if isinstance(payload.get("operations"), list) else []
        if not 1 <= len(operations_payload) <= MAX_OPERATIONS:
            raise ProposalBundleError("proposal operations 数量超出限制。")
        operations: list[ParsedOperation] = []
        seen_targets: set[str] = set()
        for operation in operations_payload:
            if not isinstance(operation, dict) or set(operation) != {"operation", "target_file", "expected_sha256", "content"}:
                raise ProposalBundleError("proposal operation 字段不符合固定合同。")
            if operation.get("operation") != "replace_text":
                raise ProposalBundleError("proposal 只允许 replace_text 全文件替换。")
            target_file = str(operation.get("target_file") or "")
            if target_file in seen_targets:
                raise ProposalBundleError("proposal 不能重复写同一个目标文件。")
            seen_targets.add(target_file)
            target_path = self._resolve_target(target_type, target_file)
            expected = str(operation.get("expected_sha256") or "")
            if expected != "missing" and not SHA256_PATTERN.fullmatch(expected):
                raise ProposalBundleError("proposal expected_sha256 无效。")
            content_text = operation.get("content")
            if not isinstance(content_text, str):
                raise ProposalBundleError("proposal operation content 必须是 UTF-8 text。")
            content = content_text.encode("utf-8")
            if len(content) > MAX_CONTENT_BYTES:
                raise ProposalBundleError("proposal operation content 超过大小限制。")
            if verify_current_hash:
                current = target_path.read_bytes() if target_path.exists() else None
                current_sha = sha256_bytes(current) if current is not None else "missing"
                if current_sha != expected:
                    raise ProposalBundleError("proposal 目标文件已变化，expected_sha256 不匹配。")
            operations.append(ParsedOperation(target_file, target_path, expected, content))
        validation_ids_payload = payload.get("validation_ids") if isinstance(payload.get("validation_ids"), list) else []
        validation_ids = tuple(str(item) for item in validation_ids_payload)
        if not 1 <= len(validation_ids) <= MAX_VALIDATORS or any(item not in ALLOWED_VALIDATION_IDS for item in validation_ids):
            raise ProposalBundleError("proposal validation_ids 不在固定允许列表。")
        if len(set(validation_ids)) != len(validation_ids):
            raise ProposalBundleError("proposal validation_ids 不能重复。")
        rollback_plan_zh = str(payload.get("rollback_plan_zh") or "").strip()
        if not rollback_plan_zh or not contains_chinese(rollback_plan_zh):
            raise ProposalBundleError("proposal rollback_plan_zh 必须是中文可执行说明。")
        return ParsedBundle(
            path=path,
            digest=sha256_bytes(raw),
            proposal_id=proposal_id,
            target_type=target_type,
            risk_level=risk_level,
            expires_at=expires_at,
            action_half_life=action_half_life,
            human_reason_zh=human_reason_zh,
            narrator=narrator,
            operations=tuple(operations),
            validation_ids=validation_ids,
            rollback_plan_zh=rollback_plan_zh,
        )

    def _resolve_target(self, target_type: str, target_file: str) -> Path:
        if not target_file or "\\" in target_file or "//" in target_file:
            raise ProposalBundleError("proposal target_file 格式无效。")
        pure = PurePosixPath(target_file)
        if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
            raise ProposalBundleError("proposal target_file 必须是无 traversal 的相对路径。")
        normalized = pure.as_posix()
        folded = normalized.casefold()
        if any(fragment.casefold() in folded for fragment in FORBIDDEN_PATH_FRAGMENTS):
            raise ProposalBundleError("proposal target_file 命中 raw/private/credential 禁止范围。")
        if pure.suffix.lower() in EXECUTABLE_SUFFIXES:
            raise ProposalBundleError("proposal workflow 不允许写入可执行源码。")
        prefixes = TARGET_PREFIXES.get(target_type, ())
        exact = TARGET_EXACT.get(target_type, ())
        if normalized not in exact and not any(normalized.startswith(prefix) and len(normalized) > len(prefix) for prefix in prefixes):
            raise ProposalBundleError("proposal target_file 不在 target_type 固定目录中。")
        target_path = self.context.source_root.joinpath(*pure.parts)
        current = self.context.source_root
        for part in pure.parts[:-1]:
            current = current / part
            if current.exists() and (current.is_symlink() or not current.is_dir()):
                raise ProposalBundleError("proposal target_file 父目录含 symlink 或非目录节点。")
        if target_path.exists() and (target_path.is_symlink() or not target_path.is_file()):
            raise ProposalBundleError("proposal target_file 必须是普通文件或尚不存在。")
        resolved = target_path.resolve(strict=False)
        try:
            resolved.relative_to(self.context.source_root)
        except ValueError as exc:
            raise ProposalBundleError("proposal target_file 已逃逸安装副本。") from exc
        return target_path

    def _run_validations(self, bundle: ParsedBundle) -> None:
        targets = [operation.target_path for operation in bundle.operations]
        for validation_id in bundle.validation_ids:
            if validation_id == "utf8_nonempty":
                for target in targets:
                    try:
                        value = target.read_text(encoding="utf-8")
                    except (OSError, UnicodeDecodeError) as exc:
                        raise ProposalValidationError("目标不是有效 UTF-8 文件。") from exc
                    if not value.strip():
                        raise ProposalValidationError("目标文件为空，未通过 utf8_nonempty。")
            elif validation_id == "json_document":
                for target in targets:
                    if target.suffix.lower() != ".json":
                        raise ProposalValidationError("json_document 只能验证 .json 目标。")
                    try:
                        json.loads(target.read_text(encoding="utf-8"))
                    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise ProposalValidationError("目标未通过固定 JSON document 验证。") from exc
            else:
                raise ProposalValidationError("validation ID 不在固定允许列表。")

    def _restore_transaction(self, transaction_dir: Path, transaction: dict[str, Any]) -> dict[str, str]:
        restored: dict[str, str] = {}
        target_type = str(transaction.get("target_type") or "")
        targets = transaction.get("targets") if isinstance(transaction.get("targets"), list) else []
        for target in targets:
            relative = str(target.get("target_file") or "")
            target_path = self._resolve_target(target_type, relative)
            snapshot_relative = str(target.get("snapshot_file") or "")
            snapshot_path = transaction_dir / snapshot_relative
            try:
                snapshot_path.resolve().relative_to(transaction_dir.resolve())
            except ValueError as exc:
                raise ProposalRollbackError("transaction snapshot 路径已逃逸。") from exc
            if snapshot_path.is_symlink() or not snapshot_path.is_file():
                raise ProposalRollbackError("transaction snapshot 缺失或不是普通文件。")
            before = snapshot_path.read_bytes()
            if target.get("before_exists") is True:
                if sha256_bytes(before) != target.get("before_sha256"):
                    raise ProposalRollbackError("transaction snapshot hash 不匹配。")
                atomic_write(target_path, before)
                restored[relative] = sha256_bytes(target_path.read_bytes())
            else:
                if before:
                    raise ProposalRollbackError("新文件 transaction snapshot 必须为空。")
                if target_path.exists():
                    target_path.unlink()
                restored[relative] = "missing"
            if restored[relative] != target.get("before_sha256"):
                raise ProposalRollbackError("目标文件未恢复到事务前 hash。")
        return restored

    def _state_items(self) -> dict[str, dict[str, Any]]:
        path = self.context.source_root / STATE_REPORT_PATH
        if not path.is_file():
            return {}
        payload = read_json(path)
        result: dict[str, dict[str, Any]] = {}
        for item in payload.get("proposals") or []:
            if isinstance(item, dict) and isinstance(item.get("proposal_id"), str):
                result[str(item["proposal_id"])] = item
        return result

    def _narrator_items(self) -> dict[str, dict[str, Any]]:
        path = self.context.source_root / DIFF_REPORT_PATH
        if not path.is_file():
            return {}
        payload = read_json(path)
        result: dict[str, dict[str, Any]] = {}
        for item in payload.get("narrations") or []:
            if isinstance(item, dict) and isinstance(item.get("proposal_id"), str):
                result[str(item["proposal_id"])] = item
        return result

    def _review_bundle(self, bundle: ParsedBundle, token: str) -> dict[str, Any]:
        return {
            "proposal_id": bundle.proposal_id,
            "current_state": "pending_human_review",
            "target_type": bundle.target_type,
            "target_files": [item.target_file for item in bundle.operations],
            "risk_level": bundle.risk_level,
            "expires_at": bundle.expires_at,
            "action_half_life": bundle.action_half_life,
            "human_reason_zh": bundle.human_reason_zh,
            "narrator": dict(bundle.narrator),
            "validation_ids": list(bundle.validation_ids),
            "rollback_plan_zh": bundle.rollback_plan_zh,
            "apply_ready": True,
            "blocked_reason_zh": "",
            "review_token": token,
        }

    def _review_transactions(self, now: float) -> list[dict[str, Any]]:
        root = self.context.app_support / "proposal_transactions"
        if not root.is_dir() or root.is_symlink():
            return []
        result: list[dict[str, Any]] = []
        for path in sorted(root.glob("txn_*/transaction.json")):
            try:
                transaction = read_json(path)
            except ProposalBundleError:
                continue
            transaction_id = str(transaction.get("transaction_id") or "")
            if transaction.get("schema_version") != TRANSACTION_VERSION or transaction.get("state") != "committed" or not TRANSACTION_ID_PATTERN.fullmatch(transaction_id):
                continue
            token = self.token_factory()
            self._rollback_tokens[token] = {
                "transaction_id": transaction_id,
                "expires_epoch": now + self.context.token_ttl_seconds,
            }
            result.append(
                {
                    "transaction_id": transaction_id,
                    "proposal_id": transaction.get("proposal_id"),
                    "state": "committed",
                    "target_files": [str(item.get("target_file") or "") for item in transaction.get("targets") or []],
                    "rollback_token": token,
                }
            )
        return result

    def _new_transaction_id(self, now: float) -> str:
        material = f"{now}:{self.token_factory()}".encode("utf-8")
        return f"txn_{sha256_bytes(material)[:20]}"

    def _prune_tokens(self, now: float) -> None:
        self._review_tokens = {key: value for key, value in self._review_tokens.items() if float(value.get("expires_epoch", 0)) >= now}
        self._rollback_tokens = {key: value for key, value in self._rollback_tokens.items() if float(value.get("expires_epoch", 0)) >= now}
        if len(self._review_tokens) > 256:
            self._review_tokens.clear()
        if len(self._rollback_tokens) > 256:
            self._rollback_tokens.clear()

    @staticmethod
    def _validate_proposal_id(proposal_id: str) -> None:
        if not PROPOSAL_ID_PATTERN.fullmatch(proposal_id):
            raise ProposalBundleError("proposal_id 格式无效。")

    @staticmethod
    def _safety(*, proposal_apply_execution: bool) -> dict[str, bool]:
        return {
            "human_approval_required": True,
            "proposal_apply_execution": proposal_apply_execution,
            "raw_mutation": False,
            "canonical_repo_mutation": False,
            "remote_push": False,
            "arbitrary_path_input": False,
            "arbitrary_argv_input": False,
        }

    def _append_audit(
        self,
        *,
        action: str,
        proposal_id: str,
        status: str,
        transaction_id: str,
        target_files: list[str],
    ) -> None:
        path = self.context.app_support / "proposal_audit.jsonl"
        path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "schema_version": AUDIT_VERSION,
            "action": action,
            "proposal_id": proposal_id,
            "status": status,
            "transaction_id": transaction_id,
            "target_files": target_files,
            "recorded_at": utc_iso(self.now_fn()),
        }
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


__all__ = [
    "ALLOWED_VALIDATION_IDS",
    "PROPOSAL_API_VERSION",
    "PROPOSAL_BUNDLE_VERSION",
    "PROPOSAL_RESULT_VERSION",
    "REQUIRED_NARRATOR_FIELDS",
    "ProposalAuthorizationError",
    "ProposalBundleError",
    "ProposalRollbackError",
    "ProposalValidationError",
    "ProposalWorkflow",
    "ProposalWorkflowContext",
    "ProposalWorkflowError",
]
