#!/usr/bin/env python3
"""Allowlisted local command workflows for the Memory Atlas macOS app."""

from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import parse_qs, urlparse


SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from memory_atlas_proposal_workflow import (  # noqa: E402
    PROPOSAL_API_VERSION,
    ProposalWorkflow,
    ProposalWorkflowContext,
)


COMMAND_API_VERSION = "memory_atlas_command_api.v1_2_r3"
COMMAND_RESULT_VERSION = "memory_atlas_command_result.v1_2_r3"
COMMAND_IDS = (
    "sync_chatgpt",
    "sync_codex",
    "generate_weekly_report",
    "view_pending_proposals",
    "generate_personalization_prompt",
    "chatgpt_deep_explore",
)
MAX_OUTPUT_PATHS = 12
DEFAULT_TIMEOUT_SECONDS = 180
SAFE_ENV_KEYS = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR")


class CommandRequestError(ValueError):
    """The request is outside the fixed command contract."""


class CommandWorkspaceError(RuntimeError):
    """The command target is not an installer-created local source workspace."""


class CommandBusyError(RuntimeError):
    """A command is already executing."""


class CommandExecutionError(RuntimeError):
    """A fixed command failed to complete."""


@dataclass(frozen=True)
class CommandContext:
    source_root: Path
    runtime_dir: Path
    app_support: Path
    codex_home: Path | None = None
    python_executable: str = sys.executable
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS


ProcessRunner = Callable[..., Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def build_child_environment(base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Return the minimum environment needed by fixed local Python commands."""

    source = base_env if base_env is not None else dict(os.environ)
    child = {key: source[key] for key in SAFE_ENV_KEYS if source.get(key)}
    child.setdefault("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
    child.setdefault("HOME", str(Path.home()))
    child.setdefault("LANG", "en_US.UTF-8")
    child["PYTHONIOENCODING"] = "utf-8"
    child["PYTHONDONTWRITEBYTECODE"] = "1"
    return child


def default_process_runner(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
    shell: bool,
) -> subprocess.CompletedProcess[str]:
    if shell:
        raise CommandRequestError("Memory Atlas 本地命令禁止使用 shell。")
    process = subprocess.Popen(
        argv,
        cwd=str(cwd),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        start_new_session=os.name == "posix",
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired as exc:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        else:
            process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(
            exc.cmd,
            exc.timeout,
            output=stdout,
            stderr=stderr,
        ) from None
    return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr)


def validate_chatgpt_prefill_url(value: str) -> str:
    if not isinstance(value, str) or not value or len(value) > 24_000:
        raise CommandExecutionError("ChatGPT 预填充地址缺失或长度异常，已停止打开外部页面。")
    parsed = urlparse(value)
    query = parse_qs(parsed.query, keep_blank_values=True)
    if (
        parsed.scheme != "https"
        or parsed.hostname != "chatgpt.com"
        or parsed.port is not None
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in {"", "/"}
        or parsed.fragment
        or not query.get("q")
        or not str(query["q"][0]).strip()
    ):
        raise CommandExecutionError("ChatGPT 预填充地址未通过安全校验，已停止打开外部页面。")
    return value


def validate_workspace(context: CommandContext) -> CommandContext:
    raw_app_support = Path(os.path.abspath(context.app_support.expanduser()))
    raw_source_root = Path(os.path.abspath(context.source_root.expanduser()))
    raw_runtime_dir = Path(os.path.abspath(context.runtime_dir.expanduser()))
    if raw_source_root != raw_app_support / "source" or raw_runtime_dir != raw_app_support / "runtime":
        raise CommandWorkspaceError("命令只能在 Memory Atlas 的 Application Support 安装副本中执行。")
    if raw_app_support.is_symlink() or raw_source_root.is_symlink() or raw_runtime_dir.is_symlink():
        raise CommandWorkspaceError("Memory Atlas 本地 source/runtime 不能是符号链接，拒绝执行命令。")

    app_support = raw_app_support.resolve()
    source_root = raw_source_root.resolve()
    runtime_dir = raw_runtime_dir.resolve()
    if source_root.parent != app_support or runtime_dir.parent != app_support:
        raise CommandWorkspaceError("Memory Atlas 本地 source/runtime 已逃逸 Application Support，拒绝执行命令。")
    if (source_root / ".git").exists():
        raise CommandWorkspaceError("Memory Atlas 本地 source 含 Git worktree 元数据，拒绝执行命令。")

    manifest_path = source_root / "memory_atlas_source_workspace.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CommandWorkspaceError("Memory Atlas 本地 source manifest 缺失或损坏，拒绝执行命令。") from exc
    if manifest.get("schema_version") != "memory_atlas_source_workspace.v1":
        raise CommandWorkspaceError("Memory Atlas 本地 source manifest 版本无效，拒绝执行命令。")
    original_repo_value = manifest.get("original_repo_root")
    if not isinstance(original_repo_value, str) or not original_repo_value.strip():
        raise CommandWorkspaceError("Memory Atlas 本地 source manifest 缺少原始仓库边界，拒绝执行命令。")
    original_repo_root = Path(original_repo_value).expanduser().resolve()
    if original_repo_root == source_root:
        raise CommandWorkspaceError("Memory Atlas 命令不能在原始仓库路径执行。")
    if not runtime_dir.is_dir():
        raise CommandWorkspaceError("Memory Atlas 本地 runtime 目录缺失，拒绝执行命令。")
    return CommandContext(
        source_root=source_root,
        runtime_dir=runtime_dir,
        app_support=app_support,
        codex_home=context.codex_home.expanduser().resolve() if context.codex_home else None,
        python_executable=context.python_executable,
        timeout_seconds=max(1, int(context.timeout_seconds)),
    )


def parse_json_output(stdout: str) -> dict[str, Any]:
    text = (stdout or "").strip()
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise CommandExecutionError("本地命令返回了无法解析的结果，请查看 Memory Atlas 本机日志。") from exc
    if not isinstance(payload, dict):
        raise CommandExecutionError("本地命令返回格式不正确，请查看 Memory Atlas 本机日志。")
    return payload


def relative_output_paths(payload: dict[str, Any], source_root: Path) -> list[str]:
    raw_outputs: list[Any] = []
    if isinstance(payload.get("outputs"), list):
        raw_outputs.extend(payload["outputs"])
    if payload.get("output"):
        raw_outputs.append(payload["output"])
    outputs: list[str] = []
    for raw in raw_outputs:
        if not isinstance(raw, str) or not raw.strip():
            continue
        candidate = Path(raw)
        if candidate.is_absolute():
            try:
                candidate = candidate.resolve().relative_to(source_root)
            except ValueError:
                continue
        normalized = candidate.as_posix().lstrip("/")
        if normalized.startswith("../") or normalized == "..":
            continue
        if normalized not in outputs:
            outputs.append(normalized)
        if len(outputs) >= MAX_OUTPUT_PATHS:
            break
    return outputs


class CommandBridge:
    command_ids = COMMAND_IDS

    def __init__(
        self,
        context: CommandContext,
        *,
        runner: ProcessRunner = default_process_runner,
        base_env: dict[str, str] | None = None,
        proposal_workflow: Any | None = None,
    ) -> None:
        self.context = validate_workspace(context)
        self.runner = runner
        self.child_env = build_child_environment(base_env)
        self.proposal_workflow = proposal_workflow or ProposalWorkflow(
            ProposalWorkflowContext(
                source_root=self.context.source_root,
                app_support=self.context.app_support,
            )
        )
        self._lock = threading.Lock()

    def execute(self, command_id: str) -> dict[str, Any]:
        if not isinstance(command_id, str) or command_id not in COMMAND_IDS:
            raise CommandRequestError("命令不在 Memory Atlas 固定允许列表中。")
        if not self._lock.acquire(blocking=False):
            raise CommandBusyError("另一个 Memory Atlas 本地操作正在运行，请完成后重试。")

        started_at = utc_now()
        started = time.monotonic()
        try:
            try:
                result = self._execute_allowed(command_id)
            except CommandExecutionError as exc:
                result = self._result(
                    command_id,
                    status="error",
                    title_zh="操作未完成",
                    message_zh=str(exc),
                )
            except subprocess.TimeoutExpired:
                result = self._result(
                    command_id,
                    status="error",
                    title_zh="操作超时",
                    message_zh="本地操作超过安全时限，已停止；请检查数据源状态后重试。",
                )
            except Exception:
                result = self._result(
                    command_id,
                    status="error",
                    title_zh="操作未完成",
                    message_zh="本地操作出现未预期错误；请查看 Memory Atlas 本机日志后重试。",
                )
            result["started_at"] = started_at
            result["finished_at"] = utc_now()
            result["duration_ms"] = max(0, round((time.monotonic() - started) * 1000))
            self._append_audit(result)
            return result
        finally:
            self._lock.release()

    def execute_proposal_action(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise CommandRequestError("proposal action 请求格式无效。")
        action = payload.get("action")
        if action == "approve_apply":
            expected = {"action", "proposal_id", "review_token", "confirmation"}
        elif action == "rollback":
            expected = {"action", "transaction_id", "rollback_token", "confirmation"}
        else:
            raise CommandRequestError("proposal action 不在固定允许列表中。")
        if set(payload) != expected or any(not isinstance(payload.get(key), str) or not payload.get(key) for key in expected):
            raise CommandRequestError("proposal action 字段不符合固定合同。")
        if not self._lock.acquire(blocking=False):
            raise CommandBusyError("另一个 Memory Atlas 本地操作正在运行，请完成后重试。")
        try:
            if action == "approve_apply":
                return self.proposal_workflow.approve_and_apply(
                    proposal_id=payload["proposal_id"],
                    review_token=payload["review_token"],
                    confirmation=payload["confirmation"],
                )
            return self.proposal_workflow.rollback(
                transaction_id=payload["transaction_id"],
                rollback_token=payload["rollback_token"],
                confirmation=payload["confirmation"],
            )
        finally:
            self._lock.release()

    def _execute_allowed(self, command_id: str) -> dict[str, Any]:
        handlers = {
            "sync_chatgpt": self._sync_chatgpt,
            "sync_codex": self._sync_codex,
            "generate_weekly_report": self._generate_weekly_report,
            "view_pending_proposals": self._view_pending_proposals,
            "generate_personalization_prompt": self._generate_personalization_prompt,
            "chatgpt_deep_explore": self._chatgpt_deep_explore,
        }
        return handlers[command_id]()

    def _run(self, argv: list[str], failure_message_zh: str) -> dict[str, Any]:
        result = self.runner(
            list(argv),
            cwd=self.context.source_root,
            env=dict(self.child_env),
            timeout_seconds=self.context.timeout_seconds,
            shell=False,
        )
        if int(getattr(result, "returncode", 1)) != 0:
            raise CommandExecutionError(failure_message_zh)
        payload = parse_json_output(str(getattr(result, "stdout", "")))
        if payload.get("status") not in {"PASS", "ok", "success"}:
            raise CommandExecutionError(failure_message_zh)
        return payload

    def _atlasctl(self, *args: str) -> list[str]:
        return [
            self.context.python_executable,
            str(self.context.source_root / "scripts" / "atlasctl.py"),
            *args,
        ]

    def _sync_chatgpt(self) -> dict[str, Any]:
        inbox = self.context.app_support / "imports" / "chatgpt"
        inbox.mkdir(parents=True, exist_ok=True)
        try:
            inbox.chmod(0o700)
        except OSError:
            pass
        candidates = sorted(
            path
            for path in inbox.iterdir()
            if path.suffix.lower() == ".zip" and path.is_file() and not path.is_symlink()
        )
        if not candidates:
            return self._result(
                "sync_chatgpt",
                status="needs_input",
                title_zh="需要 ChatGPT 官方导出",
                message_zh="请把一个 ChatGPT 官方导出 ZIP 放入本地导入箱后重试；不会读取浏览器 cookie、token 或登录状态。",
                input_hint_zh="~/Library/Application Support/OpenAIDatabase/MemoryAtlas/imports/chatgpt",
            )
        if len(candidates) != 1:
            return self._result(
                "sync_chatgpt",
                status="needs_input",
                title_zh="导入箱存在多个文件",
                message_zh="请在 ChatGPT 本地导入箱中只保留一个官方导出 ZIP，然后重试。",
                input_hint_zh="~/Library/Application Support/OpenAIDatabase/MemoryAtlas/imports/chatgpt",
            )
        export_path = candidates[0].resolve()
        if export_path.parent != inbox.resolve():
            raise CommandExecutionError("ChatGPT 导出文件不在固定本地导入箱中，已拒绝执行。")
        sync_payload = self._run(
            self._atlasctl("sync", "--source", "chatgpt", "--official-export", str(export_path)),
            "ChatGPT 同步失败：请确认 ZIP 来自官方导出且不含明文凭据，再重试。",
        )
        snapshot = self._rebuild_and_publish()
        return self._result(
            "sync_chatgpt",
            status="success",
            title_zh="ChatGPT 同步完成",
            message_zh="官方导出已在本地安装副本中完成脱敏同步，页面数据已刷新。",
            action={"type": "reload_atlas"},
            metrics={
                "conversation_count": sync_payload.get("conversation_count", 0),
                "node_count": snapshot.get("node_count", 0),
            },
        )

    def _sync_codex(self) -> dict[str, Any]:
        codex_home = self.context.codex_home or (Path(self.child_env["HOME"]) / ".codex")
        if not codex_home.is_dir():
            return self._result(
                "sync_codex",
                status="needs_input",
                title_zh="未找到 Codex 本地资料",
                message_zh="请确认本机 Codex 数据目录可读后重试；不会读取 auth、cookie 或明文凭据文件。",
            )
        sync_payload = self._run(
            self._atlasctl("sync", "--source", "codex", "--codex-home", str(codex_home)),
            "Codex 同步失败：请确认本机 Codex sessions 可读，并查看本机日志中的脱敏校验结果。",
        )
        snapshot = self._rebuild_and_publish()
        return self._result(
            "sync_codex",
            status="success",
            title_zh="Codex 同步完成",
            message_zh="Codex sessions 已在内存中脱敏汇总，本地页面数据已刷新。",
            action={"type": "reload_atlas"},
            metrics={
                "session_count": sync_payload.get("session_count", 0),
                "node_count": snapshot.get("node_count", 0),
            },
        )

    def _rebuild_and_publish(self) -> dict[str, Any]:
        self._run(
            self._atlasctl("build-atlas"),
            "Memory Atlas 派生快照构建失败；旧的本地页面快照保持不变。",
        )
        source_snapshot = self.context.source_root / "data" / "derived" / "visualization" / "memory_atlas.json"
        try:
            payload = json.loads(source_snapshot.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise CommandExecutionError("新快照缺失或 JSON 无效；旧的本地页面快照保持不变。") from exc
        source_contract = payload.get("source_contract")
        writeback_policy = source_contract.get("writeback_policy") if isinstance(source_contract, dict) else None
        contribution = payload.get("contribution")
        if (
            payload.get("schema_version") != "memory_atlas.v1"
            or not isinstance(payload.get("nodes"), list)
            or not isinstance(payload.get("edges"), list)
            or not isinstance(payload.get("timeline"), list)
            or not isinstance(payload.get("overview"), dict)
            or not isinstance(payload.get("metrics"), list)
            or not isinstance(contribution, dict)
            or not isinstance(contribution.get("daily"), list)
            or not isinstance(source_contract, dict)
            or source_contract.get("mode") != "public_redacted_read_only_visualization"
            or not isinstance(writeback_policy, dict)
            or writeback_policy.get("direct_frontend_mutation_of_active_memory") is not False
        ):
            raise CommandExecutionError("新快照结构无效；旧的本地页面快照保持不变。")
        target = self.context.runtime_dir / "memory_atlas.json"
        staged = target.with_name(f".{target.name}.{os.getpid()}.next")
        try:
            shutil.copy2(source_snapshot, staged)
            os.replace(staged, target)
        finally:
            if staged.exists():
                staged.unlink()
        return {
            "node_count": len(payload["nodes"]),
            "generated_at": payload["overview"].get("generated_at", ""),
        }

    def _generate_weekly_report(self) -> dict[str, Any]:
        payload = self._run(
            [
                self.context.python_executable,
                str(self.context.source_root / "scripts" / "build_memory_atlas_weekly_report.py"),
                "--database-dir",
                str(self.context.source_root),
            ],
            "本周报告生成失败：请先确认当前脱敏 Memory Atlas 快照可读。",
        )
        return self._result(
            "generate_weekly_report",
            status="success",
            title_zh="本周报告已生成",
            message_zh="已从当前脱敏派生快照生成本周报告，并保存在本地安装副本。",
            action={"type": "navigate_view", "view": "summary"},
            outputs=relative_output_paths(payload, self.context.source_root),
        )

    def _view_pending_proposals(self) -> dict[str, Any]:
        review = self.proposal_workflow.review()
        summary = review.get("summary") if isinstance(review.get("summary"), dict) else {}
        count = summary.get("proposal_count", 0)
        return self._result(
            "view_pending_proposals",
            status="success",
            title_zh="待授权提案已读取",
            message_zh=f"已读取 {int(count or 0)} 条提案状态；请核对中文 diff、精确目标、验证与回滚范围后再决定是否授权。",
            action={"type": "navigate_view", "view": "summary"},
            metrics={"proposal_count": int(count or 0)},
            proposal_review=review,
        )

    def _generate_personalization_prompt(self) -> dict[str, Any]:
        payload = self._run(
            self._atlasctl(
                "generate-personalization-prompt",
                "--database-dir",
                str(self.context.source_root),
                "--target",
                "all",
            ),
            "个性化提示生成失败：请先修复最新 memory、behavior、latent 或 self-iteration 派生报告。",
        )
        outputs = relative_output_paths(payload, self.context.source_root)
        return self._result(
            "generate_personalization_prompt",
            status="success",
            title_zh="个性化提示已生成",
            message_zh="ChatGPT、Codex 和其他 agent 的最新提示已生成；没有自动发送。",
            action={"type": "navigate_view", "view": "summary"},
            outputs=outputs,
        )

    def _chatgpt_deep_explore(self) -> dict[str, Any]:
        payload = self._run(
            self._atlasctl(
                "chatgpt-deep-explore",
                "--database-dir",
                str(self.context.source_root),
                "--mode",
                "prefill_only",
            ),
            "ChatGPT 深度探索准备失败：请先修复本地派生报告；不会静默发送任何内容。",
        )
        if payload.get("mode") != "prefill_only" or payload.get("sends_to_chatgpt") is not False:
            raise CommandExecutionError("ChatGPT 深度探索未满足仅预填、零自动发送边界，已停止。")
        launch_url = validate_chatgpt_prefill_url(str(payload.get("launch_url") or ""))
        return self._result(
            "chatgpt_deep_explore",
            status="success",
            title_zh="ChatGPT 深度探索已准备",
            message_zh="已打开仅预填的 ChatGPT 页面；请检查内容后由你决定是否发送。",
            action={"type": "open_url", "url": launch_url},
            outputs=relative_output_paths(payload, self.context.source_root),
        )

    def _result(
        self,
        command_id: str,
        *,
        status: str,
        title_zh: str,
        message_zh: str,
        action: dict[str, Any] | None = None,
        outputs: list[str] | None = None,
        metrics: dict[str, Any] | None = None,
        input_hint_zh: str | None = None,
        proposal_review: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {
            "schema_version": COMMAND_RESULT_VERSION,
            "command_id": command_id,
            "status": status,
            "title_zh": title_zh,
            "message_zh": message_zh,
            "outputs": outputs or [],
            "safety": {
                "user_trigger_required": True,
                "canonical_repo_mutation": False,
                "remote_push": False,
                "proposal_apply_execution": False,
                "sends_to_chatgpt": False,
                "auto_submit": False,
                "cookie_token_secret_export": False,
            },
        }
        if action:
            result["action"] = action
        if metrics:
            result["metrics"] = metrics
        if input_hint_zh:
            result["input_hint_zh"] = input_hint_zh
        if proposal_review:
            result["proposal_review"] = proposal_review
        return result

    def _append_audit(self, result: dict[str, Any]) -> None:
        audit_path = self.context.app_support / "command_audit.jsonl"
        audit_path.parent.mkdir(parents=True, exist_ok=True)
        row = {
            "schema_version": "memory_atlas_command_audit.v1_2_r3",
            "command_id": result.get("command_id"),
            "status": result.get("status"),
            "started_at": result.get("started_at"),
            "finished_at": result.get("finished_at"),
            "duration_ms": result.get("duration_ms"),
        }
        with audit_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


__all__ = [
    "COMMAND_API_VERSION",
    "COMMAND_IDS",
    "PROPOSAL_API_VERSION",
    "CommandBridge",
    "CommandBusyError",
    "CommandContext",
    "CommandExecutionError",
    "CommandRequestError",
    "CommandWorkspaceError",
    "build_child_environment",
    "validate_chatgpt_prefill_url",
    "validate_workspace",
]
