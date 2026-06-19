#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:A:h}"
PROJECT_DIR="${SCRIPT_DIR:h}"
OUTPUT_DIR="$PROJECT_DIR/data/systemAudit"
URL=""
START_TIMEOUT=120
JSON_OUTPUT=0
SUMMARY_JSON=0

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --url)
      URL="$2"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="$2"
      shift 2
      ;;
    --start-timeout)
      START_TIMEOUT="$2"
      shift 2
      ;;
    --json)
      JSON_OUTPUT=1
      shift
      ;;
    --summary-json)
      SUMMARY_JSON=1
      shift
      ;;
    *)
      echo "Unknown uiVisualAcceptance argument: $1" >&2
      exit 64
      ;;
  esac
done

cd "$PROJECT_DIR"
mkdir -p "$OUTPUT_DIR"

STAMP="$(date -u +"%Y%m%d_%H%M%S")"
JSON_PATH="$OUTPUT_DIR/UIVisualAcceptance_$STAMP.json"
LATEST_PATH="$OUTPUT_DIR/UIVisualAcceptance_latest.json"
SCREENSHOT_PATH="$OUTPUT_DIR/UIVisualAcceptance_$STAMP.png"
START_LOG="$OUTPUT_DIR/UIVisualAcceptance_streamlit_$STAMP.log"

find_healthy_url() {
  local port code
  for port in {8501..8510}; do
    code="$(curl -s -o /dev/null -w "%{http_code}" "http://127.0.0.1:$port/_stcore/health" 2>/dev/null || true)"
    if [[ "$code" == "200" ]]; then
      printf "http://127.0.0.1:%s\n" "$port"
      return 0
    fi
  done
  return 1
}

write_blocked_payload() {
  local reason="$1"
  PYTHONDONTWRITEBYTECODE=1 python3 - "$JSON_PATH" "$LATEST_PATH" "$reason" <<'PY'
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

json_path = Path(sys.argv[1])
latest_path = Path(sys.argv[2])
reason = sys.argv[3]
payload = {
    "schema": "EVAOSUIVisualAcceptanceV1",
    "system": "EVA_OS",
    "subsystem": "UI Visual Acceptance",
    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    "status": "Blocked",
    "summary": {"pass": 0, "fail": 1, "info": 0, "total": 1},
    "checks": [{"name": "VisualAcceptanceBlocked", "status": "Fail", "evidence": reason}],
    "outputs": {"json": str(json_path), "latest_json": str(latest_path)},
    "heavy_smoke_policy": "Does not run scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, market refresh, broker connections, orders, payments, or holdings writes.",
    "safety_boundary": "Starts local Streamlit only when no healthy EVA_OS service is found, and stops only the service started by this acceptance run.",
    "next_action": "Install or expose a usable browser automation runtime, then rerun scripts/uiVisualAcceptance.sh --summary-json.",
}
json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copyfile(json_path, latest_path)
print(json.dumps({"schema": payload["schema"], "status": payload["status"], "summary": payload["summary"], "reason": reason}, ensure_ascii=False))
PY
}

print_payload() {
  if [[ "$JSON_OUTPUT" == "1" ]]; then
    cat "$JSON_PATH"
    return
  fi
  if [[ "$SUMMARY_JSON" == "1" ]]; then
    PYTHONDONTWRITEBYTECODE=1 python3 - "$JSON_PATH" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
summary = {
    "schema": payload.get("schema"),
    "status": payload.get("status"),
    "summary": payload.get("summary"),
    "url": payload.get("url"),
    "started_by_acceptance": payload.get("started_by_acceptance"),
    "browser": payload.get("browser", {}).get("executable"),
    "screenshot_bytes": payload.get("visual_metrics", {}).get("screenshot_bytes"),
    "failed_checks": [row.get("name") for row in payload.get("checks", []) if row.get("status") == "Fail"],
}
print(json.dumps(summary, ensure_ascii=False, indent=2))
PY
    return
  fi
  PYTHONDONTWRITEBYTECODE=1 python3 - "$JSON_PATH" <<'PY'
import json
import sys
from pathlib import Path

payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
summary = payload.get("summary", {})
print(
    "UI Visual Acceptance: "
    f"{payload.get('status')} "
    f"pass={summary.get('pass')} fail={summary.get('fail')} "
    f"url={payload.get('url')} screenshot_bytes={payload.get('visual_metrics', {}).get('screenshot_bytes')}"
)
PY
}

STARTED_BY_ACCEPTANCE=0
SERVER_PID=""

cleanup() {
  if [[ "$STARTED_BY_ACCEPTANCE" == "1" ]]; then
    "$PROJECT_DIR/scripts/stopQuantLab.sh" >/dev/null 2>&1 || true
    if [[ -n "$SERVER_PID" ]]; then
      wait "$SERVER_PID" >/dev/null 2>&1 || true
    fi
  fi
}
trap cleanup EXIT

if [[ -z "$URL" ]]; then
  URL="$(find_healthy_url || true)"
fi

if [[ -z "$URL" ]]; then
  "$PROJECT_DIR/scripts/startQuantLab.sh" > "$START_LOG" 2>&1 &
  SERVER_PID="$!"
  STARTED_BY_ACCEPTANCE=1
  for _ in $(seq 1 "$START_TIMEOUT"); do
    URL="$(find_healthy_url || true)"
    if [[ -n "$URL" ]]; then
      break
    fi
    if ! kill -0 "$SERVER_PID" >/dev/null 2>&1; then
      write_blocked_payload "Streamlit exited before health became available. See $START_LOG."
      print_payload
      exit 3
    fi
    sleep 1
  done
fi

if [[ -z "$URL" ]]; then
  write_blocked_payload "No healthy local EVA_OS service found within ${START_TIMEOUT}s."
  print_payload
  exit 3
fi

NODE_BIN="${EVA_OS_PLAYWRIGHT_NODE:-}"
if [[ -z "$NODE_BIN" ]]; then
  for candidate in \
    "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node" \
    "$(command -v node 2>/dev/null || true)"; do
    if [[ -n "$candidate" && -x "$candidate" ]]; then
      NODE_BIN="$candidate"
      break
    fi
  done
fi

if [[ -z "$NODE_BIN" || ! -x "$NODE_BIN" ]]; then
  write_blocked_payload "Node.js executable not found for Playwright UI acceptance."
  print_payload
  exit 3
fi

NODE_MODULE_CANDIDATES=()
if [[ -n "${EVA_OS_PLAYWRIGHT_NODE_PATH:-}" ]]; then
  NODE_MODULE_CANDIDATES+=("$EVA_OS_PLAYWRIGHT_NODE_PATH")
fi
NODE_MODULE_CANDIDATES+=(
  "$PROJECT_DIR/node_modules"
  "$HOME/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
)
NODE_PATH_VALUE=""
for candidate in "${NODE_MODULE_CANDIDATES[@]}"; do
  if [[ -d "$candidate" ]]; then
    NODE_PATH_VALUE="${NODE_PATH_VALUE:+$NODE_PATH_VALUE:}$candidate"
  fi
done

set +e
NODE_PATH="$NODE_PATH_VALUE" "$NODE_BIN" - "$URL" "$JSON_PATH" "$LATEST_PATH" "$SCREENSHOT_PATH" "$STARTED_BY_ACCEPTANCE" <<'JS'
const fs = require('fs');
const path = require('path');

const [url, jsonPath, latestPath, screenshotPath, startedRaw] = process.argv.slice(2);
const generatedAt = new Date().toISOString();
const startedByAcceptance = startedRaw === '1';

function check(name, status, evidence) {
  return { name, status, evidence };
}

function summarize(checks) {
  const pass = checks.filter((row) => row.status === 'Pass').length;
  const fail = checks.filter((row) => row.status === 'Fail').length;
  const info = checks.filter((row) => row.status === 'Info').length;
  return { pass, fail, info, total: checks.length };
}

function writePayload(payload, exitCode) {
  fs.mkdirSync(path.dirname(jsonPath), { recursive: true });
  fs.writeFileSync(jsonPath, JSON.stringify(payload, null, 2), 'utf8');
  fs.copyFileSync(jsonPath, latestPath);
  process.exit(exitCode);
}

function basePayload(status, checks, extra = {}) {
  return {
    schema: 'EVAOSUIVisualAcceptanceV1',
    system: 'EVA_OS',
    subsystem: 'UI Visual Acceptance',
    generated_at: generatedAt,
    status,
    url,
    started_by_acceptance: startedByAcceptance,
    summary: summarize(checks),
    checks,
    outputs: {
      json: jsonPath,
      latest_json: latestPath,
      screenshot: fs.existsSync(screenshotPath) ? screenshotPath : '',
    },
    heavy_smoke_policy: 'Does not run scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, market refresh, broker connections, orders, payments, or holdings writes.',
    safety_boundary: 'Browser-only visual verification against localhost. It starts Streamlit only when needed and stops only the service it started.',
    next_action: status === 'Pass' ? 'Use this evidence with macOS runtime acceptance for real local UI acceptance.' : 'Inspect failed checks and rerun after fixing UI/runtime readiness.',
    ...extra,
  };
}

let playwright;
try {
  playwright = require('playwright');
} catch (error) {
  const checks = [check('PlaywrightAvailable', 'Fail', String(error && error.message || error))];
  writePayload(basePayload('Blocked', checks), 3);
}

const browserCandidates = [
  process.env.EVA_OS_BROWSER_EXECUTABLE || '',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
].filter(Boolean);
const browserExecutable = browserCandidates.find((candidate) => fs.existsSync(candidate));
if (!browserExecutable) {
  const checks = [check('BrowserExecutable', 'Fail', `No executable found in ${browserCandidates.join(', ')}`)];
  writePayload(basePayload('Blocked', checks), 3);
}

(async () => {
  const checks = [check('BrowserExecutable', 'Pass', browserExecutable)];
  let browser;
  try {
    browser = await playwright.chromium.launch({ headless: true, executablePath: browserExecutable });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    checks.push(check('HTTPStatus', response && response.ok() ? 'Pass' : 'Fail', `status=${response ? response.status() : 'missing'}`));
    await page.waitForFunction(
      () => document.body && document.body.innerText && document.body.innerText.includes('工作台状态'),
      null,
      { timeout: 90000 }
    );
    let bodyText = '';
    for (let attempt = 0; attempt < 12; attempt += 1) {
      bodyText = await page.locator('body').innerText({ timeout: 10000 }).catch(() => '');
      if (bodyText.includes('macOS 生命周期')) {
        break;
      }
      await page.mouse.wheel(0, 1000);
      await page.waitForTimeout(1000);
    }
    if (!bodyText.includes('macOS 生命周期')) {
      await page.waitForFunction(
        () => document.body && document.body.innerText && document.body.innerText.includes('macOS 生命周期'),
        null,
        { timeout: 60000 }
      );
    }
    await page.waitForTimeout(1200);
    bodyText = await page.locator('body').innerText({ timeout: 10000 });
    const requiredText = [
      'EVA_OS',
      '工作台状态',
      'macOS 生命周期',
      '运行时验收证据',
      '缓存预览',
    ];
    for (const text of requiredText) {
      checks.push(check(`VisibleText:${text}`, bodyText.includes(text) ? 'Pass' : 'Fail', text));
    }
    const lifecycleHeading = page.getByText('macOS 生命周期').first();
    await lifecycleHeading.scrollIntoViewIfNeeded({ timeout: 30000 });
    await page.waitForTimeout(1200);
    const lifecycleButtons = ['开发检查', '轻量验收', '生命周期验收'];
    for (const name of lifecycleButtons) {
      const button = page.getByRole('button', { name }).first();
      const visible = await button.isVisible({ timeout: 10000 }).catch(() => false);
      checks.push(check(`LifecycleButton:${name}`, visible ? 'Pass' : 'Fail', name));
    }
    const forbiddenText = ['Traceback', 'ModuleNotFoundError', 'ImportError:', 'Connection lost'];
    for (const text of forbiddenText) {
      checks.push(check(`NoVisibleError:${text}`, bodyText.includes(text) ? 'Fail' : 'Pass', text));
    }
    checks.push(check('BodyTextLength', bodyText.length > 1000 ? 'Pass' : 'Fail', `length=${bodyText.length}`));
    await page.screenshot({ path: screenshotPath, fullPage: true });
    const screenshotBytes = fs.existsSync(screenshotPath) ? fs.statSync(screenshotPath).size : 0;
    checks.push(check('ScreenshotCaptured', screenshotBytes > 10000 ? 'Pass' : 'Fail', `bytes=${screenshotBytes}`));
    await browser.close();
    const summary = summarize(checks);
    const status = summary.fail === 0 ? 'Pass' : 'Fail';
    writePayload(
      basePayload(status, checks, {
        browser: { executable: browserExecutable },
        visual_metrics: {
          body_text_length: bodyText.length,
          screenshot_bytes: screenshotBytes,
          viewport: '1440x1000',
        },
      }),
      status === 'Pass' ? 0 : 2
    );
  } catch (error) {
    if (browser) {
      await browser.close().catch(() => {});
    }
    checks.push(check('BrowserVisualProbe', 'Fail', String(error && error.stack || error)));
    writePayload(basePayload('Fail', checks, { browser: { executable: browserExecutable } }), 2);
  }
})();
JS
NODE_STATUS="$?"
set -e

print_payload
exit "$NODE_STATUS"
