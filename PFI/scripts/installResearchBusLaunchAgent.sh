#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.pfi.researchbus.sync"
PLIST_PATH="${HOME}/Library/LaunchAgents/${LABEL}.plist"
INTERVAL_SECONDS="${RESEARCH_BUS_LAUNCH_INTERVAL_SECONDS:-60}"
RUNNER_DIR="${HOME}/Library/Application Support/PFI"
RUNNER_PATH="${RUNNER_DIR}/researchBusSyncRunner.sh"
RUNNER_LOG_DIR="${RUNNER_DIR}/logs"
OUT_LOG="${RUNNER_LOG_DIR}/research_bus_launchd.out.log"
ERR_LOG="${RUNNER_LOG_DIR}/research_bus_launchd.err.log"
ACTION="${1:-install}"

mkdir -p "${HOME}/Library/LaunchAgents" "$RUNNER_DIR" "$RUNNER_LOG_DIR"

write_runner() {
  cat > "$RUNNER_PATH" <<RUNNER
#!/usr/bin/env bash
set -uo pipefail

PROJECT_ROOT="${ROOT_DIR}"
AI_ROOT="\${RESEARCH_BUS_AI_ROOT:-$PFI_AI_RESEARCH_ROOT}"
LOG_DIR="${RUNNER_LOG_DIR}"
LOG_FILE="${RUNNER_LOG_DIR}/research_bus_system_sync.log"
LOCK_DIR="${RUNNER_LOG_DIR}/research_bus_system_sync.lockdir"

mkdir -p "\$LOG_DIR"

timestamp() {
  date "+%Y-%m-%dT%H:%M:%S%z"
}

log_line() {
  printf "%s %s\\n" "\$(timestamp)" "\$*" >> "\$LOG_FILE"
}

run_step() {
  local label="\$1"
  shift
  local step_timeout="\${RESEARCH_BUS_STEP_TIMEOUT_SECONDS:-45}"
  "\$@" >> "\$LOG_FILE" 2>&1 &
  local child_pid=\$!
  local waited=0
  while kill -0 "\$child_pid" 2>/dev/null; do
    if [[ "\$waited" -ge "\$step_timeout" ]]; then
      kill "\$child_pid" 2>/dev/null || true
      sleep 1
      kill -9 "\$child_pid" 2>/dev/null || true
      wait "\$child_pid" 2>/dev/null || true
      log_line "WARN \${label} timed out after \${step_timeout}s"
      return 0
    fi
    sleep 1
    waited=\$((waited + 1))
  done
  if wait "\$child_pid"; then
    log_line "OK \${label}"
  else
    local status=\$?
    log_line "WARN \${label} exited with status \${status}"
  fi
}

if ! mkdir "\$LOCK_DIR" 2>/dev/null; then
  log_line "SKIP another research bus sync is already running"
  exit 0
fi
trap 'rmdir "\$LOCK_DIR" 2>/dev/null || true' EXIT

cd "\$PROJECT_ROOT" || {
  log_line "ERROR cannot access PROJECT_ROOT=\$PROJECT_ROOT"
  exit 1
}

RUNTIME_PYTHON="~/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3.12"
if [[ -x "\$RUNTIME_PYTHON" ]]; then
  PYTHON_BIN="\$RUNTIME_PYTHON"
elif [[ -x "\${PROJECT_ROOT}/.venv/bin/python" ]]; then
  PYTHON_BIN="\${PROJECT_ROOT}/.venv/bin/python"
else
  PYTHON_BIN="/usr/bin/python3"
fi
export PYTHONDONTWRITEBYTECODE=1
VENV_SITE_PACKAGES="\${PROJECT_ROOT}/.venv/lib/python3.12/site-packages"
if [[ -d "\$VENV_SITE_PACKAGES" ]]; then
  export PYTHONPATH="\${PROJECT_ROOT}/src:\${VENV_SITE_PACKAGES}\${PYTHONPATH:+:\$PYTHONPATH}"
else
  export PYTHONPATH="\${PROJECT_ROOT}/src\${PYTHONPATH:+:\$PYTHONPATH}"
fi

log_line "START research system sync runner"
log_line "Python=\$PYTHON_BIN"
run_step "PFI chat dropbox" "\$PYTHON_BIN" -m pfi_os.examples.research_bus_api process-dropbox --min-age-seconds 0 --limit 100 --json
run_step "PFI heartbeat" "\$PYTHON_BIN" -m pfi_os.examples.research_bus_api heartbeat --system-name ResearchBus --status Ready --capability sync_all --capability chat_input --capability chat_dropbox --capability independent_validation --capability local_webhook
run_step "PFI request processing" "\$PYTHON_BIN" -m pfi_os.examples.research_bus_api process --system-name ResearchBus --limit 100 --json
run_step "PFI research bus sync" "\$PYTHON_BIN" -m pfi_os.examples.sync_research_bus --json

if [[ -d "\$AI_ROOT" ]]; then
  run_step "AI research heartbeat" /bin/bash -lc "cd '\$AI_ROOT' && PYTHONDONTWRITEBYTECODE=1 python3 -m src.cli research-bus-heartbeat --system-name AI-Research-System --status Ready --capability publish_reports --capability pull_pfi_os_results --capability pull_validation_tasks --capability pull_independent_validation --capability pull_consumer_behavior_state"
  run_step "AI research request processing" /bin/bash -lc "cd '\$AI_ROOT' && PYTHONDONTWRITEBYTECODE=1 python3 -m src.cli research-bus-process --system-name AI-Research-System --limit 100 --json"
  run_step "AI research bus sync" /bin/bash -lc "cd '\$AI_ROOT' && PYTHONDONTWRITEBYTECODE=1 python3 -m src.cli research-bus-sync --json"
else
  log_line "WARN AI_ROOT not found: \$AI_ROOT"
fi

log_line "END research system sync runner"
RUNNER
  chmod +x "$RUNNER_PATH"
}

write_plist() {
  write_runner
  cat > "$PLIST_PATH" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${LABEL}</string>
  <key>ProgramArguments</key>
  <array>
    <string>/bin/bash</string>
    <string>${RUNNER_PATH}</string>
  </array>
  <key>WorkingDirectory</key>
  <string>${HOME}</string>
  <key>RunAtLoad</key>
  <true/>
  <key>StartInterval</key>
  <integer>${INTERVAL_SECONDS}</integer>
  <key>StandardOutPath</key>
  <string>${OUT_LOG}</string>
  <key>StandardErrorPath</key>
  <string>${ERR_LOG}</string>
  <key>ProcessType</key>
  <string>Background</string>
</dict>
</plist>
PLIST
}

load_agent() {
  launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$PLIST_PATH"
  launchctl enable "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true
  launchctl kickstart -k "gui/$(id -u)/${LABEL}" >/dev/null 2>&1 || true
}

case "$ACTION" in
  install)
    write_plist
    echo "$PLIST_PATH"
    echo "$RUNNER_PATH"
    ;;
  load)
    write_plist
    load_agent
    echo "loaded ${LABEL}"
    ;;
  unload)
    launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
    echo "unloaded ${LABEL}"
    ;;
  remove)
    launchctl bootout "gui/$(id -u)" "$PLIST_PATH" >/dev/null 2>&1 || true
    rm -f "$PLIST_PATH"
    echo "removed ${LABEL}"
    ;;
  status)
    launchctl print "gui/$(id -u)/${LABEL}" 2>/dev/null || {
      echo "${LABEL} is not loaded"
      exit 1
    }
    ;;
  *)
    echo "Usage: $0 install|load|unload|remove|status" >&2
    exit 2
    ;;
esac
