#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
APP_PY="$ROOT/.venv/bin/python"
LABEL="${ALPHA_PHASE6_OWNER_GATE_LABEL:-com.linze.alpha.phase6-owner-gate-sampler}"
AGENT_DIR="${ALPHA_LAUNCH_AGENT_DIR:-$HOME/Library/LaunchAgents}"
PLIST_PATH="$AGENT_DIR/${LABEL}.plist"
INTERVAL_SECONDS="${ALPHA_PHASE6_OWNER_GATE_INTERVAL_SECONDS:-300}"
EVIDENCE_ROOT="${ALPHA_PHASE6_OWNER_GATE_EVIDENCE_ROOT:-$ROOT/runtime/phase6_owner_gate_latest}"
LOG_DIR="${ALPHA_LAUNCH_AGENT_LOG_DIR:-$HOME/Library/Logs/Alpha}"
STDOUT_LOG="$LOG_DIR/phase6_owner_gate_sampler.out.log"
STDERR_LOG="$LOG_DIR/phase6_owner_gate_sampler.err.log"
DRY_RUN="${ALPHA_LAUNCH_AGENT_DRY_RUN:-0}"

mkdir -p "$ROOT/runtime" "$AGENT_DIR" "$LOG_DIR"

if [[ ! -x "$APP_PY" ]]; then
  "$PYTHON_BIN" -m venv "$ROOT/.venv"
  "$APP_PY" -m pip install -e "$ROOT"
fi

"$APP_PY" - "$PLIST_PATH" "$LABEL" "$ROOT" "$INTERVAL_SECONDS" "$STDOUT_LOG" "$STDERR_LOG" "$EVIDENCE_ROOT" <<'PY'
from __future__ import annotations

import os
import plistlib
import shlex
import sys
from pathlib import Path

plist_path, label, root, interval_seconds, stdout_log, stderr_log, evidence_root = sys.argv[1:]
home = str(Path.home())
path_env = os.environ.get("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
python_bin = str(Path(root) / ".venv" / "bin" / "python")
script = str(Path(root) / "scripts" / "build_phase6_owner_gate_evidence.py")
command = (
    f"cd {shlex.quote(root)} && "
    f"exec {shlex.quote(python_bin)} {shlex.quote(script)} "
    f"--sample-count 1 --evidence-root {shlex.quote(evidence_root)}"
)
payload = {
    "Label": label,
    "ProgramArguments": ["/bin/zsh", "-lc", command],
    "WorkingDirectory": root,
    "EnvironmentVariables": {
        "PYTHONPATH": root,
        "ALPHA_LAUNCHD": "1",
        "HOME": home,
        "PATH": path_env,
    },
    "RunAtLoad": True,
    "StartInterval": int(interval_seconds),
    "StandardOutPath": stdout_log,
    "StandardErrorPath": stderr_log,
}
path = Path(plist_path)
path.parent.mkdir(parents=True, exist_ok=True)
with path.open("wb") as handle:
    plistlib.dump(payload, handle, sort_keys=True)
PY

echo "Alpha Phase 6 OWNER-GATE sampler LaunchAgent 配置已写入：${PLIST_PATH}"
echo "安全边界：只生成 paper/shadow 证据，不写 LIVE_AUTHORIZATION.json，不提交真实 broker order。"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "干运行：未调用 launchctl。"
  exit 0
fi

DOMAIN="gui/$(id -u)"
launchctl bootout "$DOMAIN" "$PLIST_PATH" >/dev/null 2>&1 || true
launchctl bootstrap "$DOMAIN" "$PLIST_PATH"
launchctl enable "$DOMAIN/$LABEL" >/dev/null 2>&1 || true
launchctl kickstart -k "$DOMAIN/$LABEL" >/dev/null 2>&1 || true

echo "Alpha Phase 6 OWNER-GATE sampler LaunchAgent 已安装并启动：${LABEL}"
echo "stdout 日志：${STDOUT_LOG}"
echo "stderr 日志：${STDERR_LOG}"
