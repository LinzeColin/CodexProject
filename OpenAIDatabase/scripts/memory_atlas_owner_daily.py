#!/usr/bin/env python3
"""Fixed, no-write Owner Daily runner shared by the CLI and local app."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable


OWNER_DAILY_API_VERSION = "memory_atlas_owner_daily_api.v1_2_r5"
OWNER_DAILY_RESULT_VERSION = "memory_atlas_owner_daily_result.v1_2_r5"
OWNER_DAILY_STEP_IDS = (
    "sync",
    "analyze",
    "build-atlas",
    "audit",
    "push",
    "proposals",
    "generate-personalization-prompt",
    "deep-explore",
)
MAX_CHILD_OUTPUT_BYTES = 1024 * 1024
MAX_RESULT_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 60
SAFE_ENV_KEYS = ("PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR")


class OwnerDailyRequestError(ValueError):
    """The caller requested behavior outside the fixed profile contract."""


class OwnerDailyWorkspaceError(RuntimeError):
    """The fixed profile cannot run from the supplied source root."""


class OwnerDailyOutputError(RuntimeError):
    """A child exceeded the bounded output contract."""


@dataclass(frozen=True)
class OwnerDailyContext:
    source_root: Path
    python_executable: str = sys.executable
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    max_output_bytes: int = MAX_CHILD_OUTPUT_BYTES


@dataclass(frozen=True)
class OwnerDailyStep:
    step_id: str
    label_zh: str
    purpose_zh: str
    args: tuple[str, ...]

    @property
    def display_invocation(self) -> list[str]:
        return ["python3", "scripts/atlasctl.py", *self.args]


OWNER_DAILY_STEPS = (
    OwnerDailyStep("sync", "同步入口", "检查 ChatGPT 同步入口合同，不写文件。", ("sync", "--source", "chatgpt", "--dry-run")),
    OwnerDailyStep("analyze", "行为分析", "检查行为智能 facet 分析 dry-run。", ("analyze", "--stage", "facets", "--dry-run")),
    OwnerDailyStep("build-atlas", "Atlas 构建", "检查可视化 atlas 构建计划，不写派生文件。", ("build-atlas", "--dry-run")),
    OwnerDailyStep("audit", "质量审计", "检查轻量 audit 命令面，不执行 R8 总门禁。", ("audit", "--dry-run")),
    OwnerDailyStep("push", "备份范围", "检查 GitHub 备份范围，不上传远端 main。", ("push", "--dry-run")),
    OwnerDailyStep("proposals", "提案状态", "检查 proposal 状态机，不执行 apply。", ("proposals", "--dry-run")),
    OwnerDailyStep(
        "generate-personalization-prompt",
        "个性化提示",
        "检查 personalization prompt 合同，不发送到 ChatGPT。",
        ("generate-personalization-prompt", "--dry-run"),
    ),
    OwnerDailyStep("deep-explore", "深度探索", "检查深度探索提示合同，不打开浏览器、不自动提交。", ("deep-explore", "--dry-run")),
)
_STEP_BY_ID = {step.step_id: step for step in OWNER_DAILY_STEPS}

_METRIC_FIELDS: dict[str, tuple[str, ...]] = {
    "sync": ("source_id", "input_required_for_apply"),
    "analyze": ("stage", "task_id", "event_count", "source_count"),
    "build-atlas": ("output", "node_count", "edge_count"),
    "audit": ("check", "task_id", "gate_count", "failed_gate_count"),
    "push": ("changed_file_count", "tracked_change_count", "backup_scope_check"),
    "proposals": ("proposal_count", "phase_status"),
    "generate-personalization-prompt": ("targets", "task_id"),
    "deep-explore": ("mode", "task_id"),
}


ProcessRunner = Callable[..., subprocess.CompletedProcess[str]]


def build_child_environment(base_env: dict[str, str] | None = None) -> dict[str, str]:
    source = base_env if base_env is not None else dict(os.environ)
    child = {key: source[key] for key in SAFE_ENV_KEYS if source.get(key)}
    child.setdefault("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
    child.setdefault("HOME", str(Path.home()))
    child.setdefault("LANG", "en_US.UTF-8")
    child["PYTHONIOENCODING"] = "utf-8"
    child["PYTHONDONTWRITEBYTECODE"] = "1"
    return child


def _terminate_process(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
    else:
        process.terminate()
    try:
        process.wait(timeout=2)
        return
    except subprocess.TimeoutExpired:
        pass
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            return
    else:
        process.kill()
    process.wait()


def default_process_runner(
    argv: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    timeout_seconds: int,
    shell: bool,
    max_output_bytes: int,
) -> subprocess.CompletedProcess[str]:
    if shell:
        raise OwnerDailyRequestError("Owner Daily 禁止使用 shell。")
    with tempfile.TemporaryFile() as stdout_file, tempfile.TemporaryFile() as stderr_file:
        process = subprocess.Popen(
            argv,
            cwd=str(cwd),
            env=env,
            stdout=stdout_file,
            stderr=stderr_file,
            shell=False,
            start_new_session=os.name == "posix",
        )
        deadline = time.monotonic() + timeout_seconds
        while process.poll() is None:
            output_size = os.fstat(stdout_file.fileno()).st_size + os.fstat(stderr_file.fileno()).st_size
            if output_size > max_output_bytes:
                _terminate_process(process)
                raise OwnerDailyOutputError("Owner Daily 子步骤输出超过安全上限。")
            if time.monotonic() >= deadline:
                _terminate_process(process)
                raise subprocess.TimeoutExpired(argv, timeout_seconds)
            time.sleep(0.02)
        output_size = os.fstat(stdout_file.fileno()).st_size + os.fstat(stderr_file.fileno()).st_size
        if output_size > max_output_bytes:
            raise OwnerDailyOutputError("Owner Daily 子步骤输出超过安全上限。")
        stdout_file.seek(0)
        stderr_file.seek(0)
        stdout = stdout_file.read(max_output_bytes + 1).decode("utf-8", errors="replace")
        stderr = stderr_file.read(max_output_bytes + 1).decode("utf-8", errors="replace")
        return subprocess.CompletedProcess(argv, int(process.returncode or 0), stdout, stderr)


def owner_daily_profile_contract() -> dict[str, Any]:
    commands = [
        {
            "command_id": step.step_id,
            "dry_run": True,
            "invocation": step.display_invocation,
            "purpose_zh": step.purpose_zh,
        }
        for step in OWNER_DAILY_STEPS
    ]
    return {
        "status": "PASS",
        "command": "run",
        "profile": "owner-daily",
        "task_id": "MA-V12-S14P1",
        "acceptance_id": "ACC-MA-V12-S14P1",
        "contract_version": "atlasctl_unified_cli.v1_2_s14_p1",
        "phase_status": "phase_s14_p1_unified_cli_completed_pending_s14_p2",
        "dry_run": True,
        "writes_files": False,
        "remote_push": False,
        "github_main_upload": False,
        "app_reinstall": False,
        "local_deep_clean": False,
        "commands": commands,
        "phase_boundary": {
            "does_not_run_final_audit": True,
            "does_not_upload_github_main": True,
            "does_not_reinstall_app": True,
            "does_not_clean_local_computer": True,
            "stage_review_deferred_to": "S14 Review",
            "next_phase": "S14 P2",
        },
        "中文说明": "owner-daily 串行执行八个固定 no-write dry-run；结果不代表 R8 总审计或发布完成。",
    }


def _safe_metric_value(value: Any) -> Any | None:
    if isinstance(value, bool) or isinstance(value, (int, float)):
        return value
    if isinstance(value, str):
        text = value.strip()
        return text[:240] if text else None
    if isinstance(value, list):
        values = []
        for item in value[:8]:
            safe = _safe_metric_value(item)
            if isinstance(safe, (str, int, float, bool)):
                values.append(safe)
        return values
    return None


def _extract_metrics(step_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    source = dict(payload)
    if isinstance(payload.get("gates"), list):
        source["gate_count"] = len(payload["gates"])
    if isinstance(payload.get("changed_files"), list):
        source["changed_file_count"] = len(payload["changed_files"])
    metrics: dict[str, Any] = {}
    for field in _METRIC_FIELDS[step_id]:
        safe = _safe_metric_value(source.get(field))
        if safe is not None:
            metrics[field] = safe
    return metrics


def _nested_false(payload: dict[str, Any], field: str) -> bool:
    if payload.get(field) is False:
        return True
    for container_name in ("safety", "boundary", "scope_boundary", "phase_boundary"):
        container = payload.get(container_name)
        if isinstance(container, dict) and container.get(field) is False:
            return True
    return False


def _validate_safe_payload(step_id: str, payload: dict[str, Any]) -> None:
    payload_status = payload.get("status")
    historical_phase_pass = (
        isinstance(payload_status, str)
        and payload_status.startswith("phase_")
        and "completed" in payload_status
    )
    if payload_status not in {"PASS", "ok", "success"} and not historical_phase_pass:
        raise ValueError("status")
    if payload.get("dry_run") is not True or payload.get("writes_files") is not False:
        raise ValueError("dry_run")
    if step_id in {"analyze", "audit", "proposals", "generate-personalization-prompt", "deep-explore"}:
        phase_boundary = payload.get("phase_boundary")
        does_not_modify_raw = isinstance(phase_boundary, dict) and phase_boundary.get("does_not_modify_raw") is True
        if not _nested_false(payload, "raw_mutation") and not (step_id == "analyze" and does_not_modify_raw):
            raise ValueError("raw_mutation")
    if step_id == "push" and payload.get("remote_push") is not False:
        raise ValueError("remote_push")
    if step_id in {"generate-personalization-prompt", "deep-explore"} and payload.get("sends_to_chatgpt") is not False:
        raise ValueError("sends_to_chatgpt")
    if step_id == "deep-explore" and payload.get("opens_browser") is not False:
        raise ValueError("opens_browser")


class OwnerDailyRunner:
    def __init__(
        self,
        context: OwnerDailyContext,
        *,
        process_runner: ProcessRunner = default_process_runner,
        base_env: dict[str, str] | None = None,
    ) -> None:
        raw_root = Path(os.path.abspath(context.source_root.expanduser()))
        if raw_root.is_symlink() or not raw_root.is_dir():
            raise OwnerDailyWorkspaceError("Owner Daily source root 缺失或是符号链接。")
        source_root = raw_root.resolve()
        atlasctl = source_root / "scripts" / "atlasctl.py"
        if not atlasctl.is_file() or atlasctl.is_symlink():
            raise OwnerDailyWorkspaceError("Owner Daily 固定 atlasctl.py 缺失或无效。")
        self.context = OwnerDailyContext(
            source_root=source_root,
            python_executable=str(context.python_executable),
            timeout_seconds=max(1, int(context.timeout_seconds)),
            max_output_bytes=max(1024, min(int(context.max_output_bytes), MAX_CHILD_OUTPUT_BYTES)),
        )
        self.process_runner = process_runner
        self.child_env = build_child_environment(base_env)

    def run(self) -> dict[str, Any]:
        return self._execute("run", OWNER_DAILY_STEPS)

    def retry(self, step_id: str) -> dict[str, Any]:
        if not isinstance(step_id, str) or step_id not in _STEP_BY_ID:
            raise OwnerDailyRequestError("Owner Daily retry step 不在固定允许列表中。")
        return self._execute("retry", (_STEP_BY_ID[step_id],), requested_step_id=step_id)

    def _execute(
        self,
        action: str,
        steps: tuple[OwnerDailyStep, ...],
        *,
        requested_step_id: str | None = None,
    ) -> dict[str, Any]:
        results = [self._execute_step(step) for step in steps]
        failed_ids = [step["step_id"] for step in results if step["status"] == "failed"]
        completed_count = len(results) - len(failed_ids)
        contract = owner_daily_profile_contract()
        contract.update(
            {
                "schema_version": OWNER_DAILY_RESULT_VERSION,
                "api_version": OWNER_DAILY_API_VERSION,
                "action": action,
                "status": "PASS" if not failed_ids else "PARTIAL_FAILURE",
                "conclusion_zh": (
                    f"Owner Daily 已完成 {completed_count} 项 no-write 检查，没有发现步骤失败。"
                    if not failed_ids
                    else f"Owner Daily 已完成 {completed_count} 项，{len(failed_ids)} 项未通过；可只重试失败步骤。"
                ),
                "completed_count": completed_count,
                "failed_count": len(failed_ids),
                "retryable_step_ids": failed_ids,
                "steps": results,
                "safety": {
                    "writes_files": False,
                    "remote_push": False,
                    "raw_mutation": False,
                    "sends_to_chatgpt": False,
                    "proposal_apply_execution": False,
                    "canonical_repo_mutation": False,
                },
            }
        )
        if requested_step_id:
            contract["requested_step_id"] = requested_step_id
        if len(json.dumps(contract, ensure_ascii=False).encode("utf-8")) > MAX_RESULT_BYTES:
            raise OwnerDailyOutputError("Owner Daily 汇总结果超过安全上限。")
        return contract

    def _execute_step(self, step: OwnerDailyStep) -> dict[str, Any]:
        started = time.monotonic()
        argv = [
            self.context.python_executable,
            str(self.context.source_root / "scripts" / "atlasctl.py"),
            *step.args,
        ]
        status = "failed"
        metrics: dict[str, Any] = {}
        failure_zh = ""
        try:
            result = self.process_runner(
                argv,
                cwd=self.context.source_root,
                env=dict(self.child_env),
                timeout_seconds=self.context.timeout_seconds,
                shell=False,
                max_output_bytes=self.context.max_output_bytes,
            )
            stdout = str(getattr(result, "stdout", "") or "")
            stderr = str(getattr(result, "stderr", "") or "")
            if len(stdout.encode("utf-8")) + len(stderr.encode("utf-8")) > self.context.max_output_bytes:
                raise OwnerDailyOutputError("Owner Daily 子步骤输出超过安全上限。")
            if int(getattr(result, "returncode", 1)) != 0:
                raise RuntimeError("exit")
            payload = json.loads(stdout)
            if not isinstance(payload, dict):
                raise ValueError("payload")
            _validate_safe_payload(step.step_id, payload)
            metrics = _extract_metrics(step.step_id, payload)
            status = "pass"
        except subprocess.TimeoutExpired:
            failure_zh = f"{step.label_zh}超时并已停止；请检查本地依赖后只重试此步骤。"
        except OwnerDailyOutputError:
            failure_zh = f"{step.label_zh}输出超过安全上限并已停止；请检查本机日志后只重试此步骤。"
        except (json.JSONDecodeError, ValueError):
            failure_zh = f"{step.label_zh}返回格式或 no-write 安全字段无效；请修复后只重试此步骤。"
        except Exception:
            failure_zh = f"{step.label_zh}未通过；请检查对应本地数据或依赖后只重试此步骤。"
        return {
            "step_id": step.step_id,
            "order": OWNER_DAILY_STEP_IDS.index(step.step_id) + 1,
            "label_zh": step.label_zh,
            "status": status,
            "conclusion_zh": f"{step.label_zh} no-write 检查通过。" if status == "pass" else "",
            "failure_zh": failure_zh,
            "retryable": status == "failed",
            "duration_ms": max(0, round((time.monotonic() - started) * 1000)),
            "invocation": step.display_invocation,
            "metrics": metrics,
        }


__all__ = [
    "MAX_CHILD_OUTPUT_BYTES",
    "MAX_RESULT_BYTES",
    "OWNER_DAILY_API_VERSION",
    "OWNER_DAILY_RESULT_VERSION",
    "OWNER_DAILY_STEP_IDS",
    "OWNER_DAILY_STEPS",
    "OwnerDailyContext",
    "OwnerDailyOutputError",
    "OwnerDailyRequestError",
    "OwnerDailyRunner",
    "OwnerDailyWorkspaceError",
    "build_child_environment",
    "default_process_runner",
    "owner_daily_profile_contract",
]
