#!/usr/bin/env zsh
set -euo pipefail
setopt NO_BG_NICE

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
    "schema": "PFIOSUIVisualAcceptanceV1",
    "system": "PFI",
    "subsystem": "UI Visual Acceptance",
    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    "status": "Blocked",
    "summary": {"pass": 0, "fail": 1, "info": 0, "total": 1},
    "checks": [{"name": "VisualAcceptanceBlocked", "status": "Fail", "evidence": reason}],
    "outputs": {"json": str(json_path), "latest_json": str(latest_path)},
    "heavy_smoke_policy": "Does not run scripts/finalAcceptanceCheck.sh, scripts/ciSmoke.sh, full pytest, market refresh, broker connections, orders, payments, or holdings writes.",
    "safety_boundary": "Starts local Streamlit only when no healthy PFI service is found, and stops only the service started by this acceptance run.",
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
    "$PROJECT_DIR/scripts/stopPFI.sh" >/dev/null 2>&1 || true
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
  "$PROJECT_DIR/scripts/startPFI.sh" > "$START_LOG" 2>&1 &
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
  write_blocked_payload "No healthy local PFI service found within ${START_TIMEOUT}s."
  print_payload
  exit 3
fi

NODE_BIN="${PFI_PLAYWRIGHT_NODE:-}"
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
if [[ -n "${PFI_PLAYWRIGHT_NODE_PATH:-}" ]]; then
  NODE_MODULE_CANDIDATES+=("$PFI_PLAYWRIGHT_NODE_PATH")
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
    schema: 'PFIOSUIVisualAcceptanceV1',
    system: 'PFI',
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
  process.env.PFI_BROWSER_EXECUTABLE || '',
  '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
  '/Applications/Chromium.app/Contents/MacOS/Chromium',
  '/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge',
].filter(Boolean);
const browserExecutable = browserCandidates.find((candidate) => fs.existsSync(candidate));
if (!browserExecutable) {
  const checks = [check('BrowserExecutable', 'Fail', `No executable found in ${browserCandidates.join(', ')}`)];
  writePayload(basePayload('Blocked', checks), 3);
}

async function findShellFrame(page) {
  for (let attempt = 0; attempt < 90; attempt += 1) {
    for (const frame of page.frames()) {
      const text = await frame.locator('body').innerText({ timeout: 1000 }).catch(() => '');
      if (text.includes('PFI') && text.includes('策略实验室') && text.includes('数据与系统')) {
        return frame;
      }
    }
    await page.waitForTimeout(1000);
  }
  return null;
}

async function frameText(frame) {
  return frame.locator('body').innerText({ timeout: 10000 }).catch(() => '');
}

async function verifyPrimaryActionNavigation(page, baseUrl, route, checks) {
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const shellFrame = await findShellFrame(page);
  checks.push(check(`PrimaryActionNavigation:${route.view}:ShellFrame`, shellFrame ? 'Pass' : 'Fail', route.view));
  if (!shellFrame) return;
  await shellFrame.evaluate(() => localStorage.removeItem('pfi-context-v2')).catch(() => {});
  await shellFrame.locator(`[data-workspace="${route.workspace}"]`).click({ timeout: 10000 });
  await shellFrame.waitForFunction(
    (expectedWorkspace) => {
      const main = document.querySelector('#main-workspace');
      return main && main.dataset.activeWorkspace === expectedWorkspace;
    },
    route.workspace,
    { timeout: 10000 }
  );
  const control = shellFrame.locator(`[data-feature-view="${route.view}"]`).first();
  const visible = await control.isVisible({ timeout: 10000 }).catch(() => false);
  checks.push(check(`PrimaryActionNavigation:${route.view}:ControlVisible`, visible ? 'Pass' : 'Fail', route.view));
  if (!visible) return;
  await control.click({ timeout: 10000 });
  await shellFrame.waitForFunction(
    (expectedTitle) => {
      const panel = document.querySelector('[data-function-detail]');
      const title = document.querySelector('[data-function-title]');
      return panel && !panel.hidden && title && title.textContent.includes(expectedTitle);
    },
    route.panelTitle,
    { timeout: 10000 }
  );
  const beforePages = page.context().pages().length;
  await shellFrame.locator('[data-function-action]').click({ timeout: 10000 });
  await shellFrame.waitForFunction(
    (expectedTitle) => {
      const runner = document.querySelector('[data-function-runner]');
      const title = document.querySelector('[data-function-run-title]');
      return runner && !runner.hidden && title && title.textContent.includes(expectedTitle);
    },
    route.panelTitle,
    { timeout: 10000 }
  );
  const runnerText = await shellFrame.locator('[data-function-runner]').innerText({ timeout: 5000 });
  const afterPages = page.context().pages().length;
  checks.push(check(`PrimaryActionNavigation:${route.view}:SameShellRunner`, runnerText.includes('操作面板') ? 'Pass' : 'Fail', runnerText.slice(0, 220)));
  checks.push(check(`PrimaryActionNavigation:${route.view}:NoNewLegacyPage`, afterPages === beforePages ? 'Pass' : 'Fail', `before=${beforePages} after=${afterPages}`));
  checks.push(check(`PrimaryActionNavigation:${route.view}:NoLegacyQuery`, page.url().includes('pfi_shell=0') || page.url().includes('pfi_legacy=1') ? 'Fail' : 'Pass', page.url()));
  checks.push(check(`PrimaryActionNavigation:${route.view}:SafetyBoundary`, runnerText.includes('不连接券商') && runnerText.includes('不提交订单') ? 'Pass' : 'Fail', runnerText.slice(0, 220)));
}

(async () => {
  const checks = [check('BrowserExecutable', 'Pass', browserExecutable)];
  let browser;
  try {
    browser = await playwright.chromium.launch({ headless: true, executablePath: browserExecutable });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    checks.push(check('HTTPStatus', response && response.ok() ? 'Pass' : 'Fail', `status=${response ? response.status() : 'missing'}`));
    const shellFrame = await findShellFrame(page);
    checks.push(check('PFIWebShellFrame', shellFrame ? 'Pass' : 'Fail', shellFrame ? 'PFI Web Shell iframe rendered' : 'PFI Web Shell iframe missing'));
    if (!shellFrame) {
      throw new Error('PFI Web Shell iframe did not render expected Chinese workspace text.');
    }
    await page.waitForTimeout(1200);
    let bodyText = await frameText(shellFrame);
    const requiredText = [
      'PFI',
      '首页',
      '市场',
      '研究',
      '持仓',
      '策略实验室',
      '数据与系统',
      '功能板块',
      '盘感训练',
    ];
    for (const text of requiredText) {
      checks.push(check(`VisibleText:${text}`, bodyText.includes(text) ? 'Pass' : 'Fail', text));
    }

    const workspaceLabels = [
      ['home', '首页'],
      ['market', '市场'],
      ['research', '研究'],
      ['portfolio', '持仓'],
      ['strategy', '策略实验室'],
      ['data', '数据与系统'],
    ];
    for (const [workspaceId, label] of workspaceLabels) {
      await shellFrame.locator(`[data-workspace="${workspaceId}"]`).click({ timeout: 10000 });
      await shellFrame.waitForFunction(
        ([expectedId, expectedLabel]) => {
          const main = document.querySelector('#main-workspace');
          const title = document.querySelector('#workspace-title');
          return main && title && main.dataset.activeWorkspace === expectedId && title.textContent.includes(expectedLabel);
        },
        [workspaceId, label],
        { timeout: 10000 }
      );
      const activeTitle = await shellFrame.locator('#workspace-title').innerText({ timeout: 5000 });
      checks.push(check(`WorkspaceSwitch:${workspaceId}`, activeTitle.includes(label) ? 'Pass' : 'Fail', activeTitle));
    }

    await shellFrame.locator('[data-workspace="home"]').click({ timeout: 10000 });
    await shellFrame.waitForFunction(
      () => {
        const main = document.querySelector('#main-workspace');
        const title = document.querySelector('#workspace-title');
        return main && title && main.dataset.activeWorkspace === 'home' && title.textContent.includes('首页');
      },
      null,
      { timeout: 10000 }
    );

    const featureLinks = [
      ['single', '单标的回测', '运行回测'],
      ['scan', '参数扫描', '运行参数扫描'],
      ['market_feel', '盘感训练', '生成盘感训练'],
      ['hotspots', '热点分析', '生成热点分析'],
      ['reports', '报告中心', '打开报告列表'],
      ['holdings', '持仓复核', '同步持仓'],
      ['policy', '政策雷达', '打开政策雷达'],
      ['tools', '数据中心', '检查数据源'],
    ];
    for (const [view, title, actionLabel] of featureLinks) {
      await shellFrame.locator('[data-workspace="home"]').click({ timeout: 10000 });
      await shellFrame.waitForFunction(
        () => {
          const main = document.querySelector('#main-workspace');
          const titleNode = document.querySelector('#workspace-title');
          return main && titleNode && main.dataset.activeWorkspace === 'home' && titleNode.textContent.includes('首页');
        },
        null,
        { timeout: 10000 }
      );
      const locator = shellFrame.locator(`[data-feature-view="${view}"]`).first();
      const visible = await locator.isVisible({ timeout: 10000 }).catch(() => false);
      checks.push(check(`FeatureOpen:${view}:ControlVisible`, visible ? 'Pass' : 'Fail', `${title}; ${actionLabel}`));
      if (!visible) continue;
      await locator.click({ timeout: 10000 });
      await shellFrame.waitForFunction(
        ([expectedTitle, expectedAction]) => {
          const panel = document.querySelector('[data-function-detail]');
          const titleNode = document.querySelector('[data-function-title]');
          const actionNode = document.querySelector('[data-function-action]');
          return panel && !panel.hidden && titleNode && actionNode
            && titleNode.textContent.includes(expectedTitle)
            && actionNode.textContent.includes(expectedAction);
        },
        [title, actionLabel],
        { timeout: 10000 }
      );
      const detailText = await shellFrame.locator('[data-function-detail]').innerText({ timeout: 5000 });
      checks.push(check(`FeatureOpen:${view}:PanelTitle`, detailText.includes(title) ? 'Pass' : 'Fail', title));
      checks.push(check(`FeatureOpen:${view}:PrimaryAction`, detailText.includes(actionLabel) ? 'Pass' : 'Fail', actionLabel));
      checks.push(check(`FeatureOpen:${view}:SafetyBoundary`, detailText.includes('禁止实盘自动下单') ? 'Pass' : 'Fail', detailText.slice(0, 180)));
      checks.push(check(`FeatureOpen:${view}:NoEnglishSchema`, /PFIOS[A-Za-z0-9]+V\\d/.test(detailText) ? 'Fail' : 'Pass', view));
    }
    bodyText = await frameText(shellFrame);
    const retiredIdentityText = ['E' + 'VA', 'Quant' + 'Lab', 'Token' + ' ROI', 'PFI', 'PFIOS', 'DisabledProvider', 'Deep Path', 'Provider ', 'QA '];
    const forbiddenText = ['Traceback', 'ModuleNotFoundError', 'ImportError:', 'Connection lost', ...retiredIdentityText, 'Global Search'];
    for (const text of forbiddenText) {
      checks.push(check(`NoVisibleError:${text}`, bodyText.includes(text) ? 'Fail' : 'Pass', text));
    }
    checks.push(check('BodyTextLength', bodyText.length > 600 ? 'Pass' : 'Fail', `length=${bodyText.length}`));
    await page.screenshot({ path: screenshotPath, fullPage: true });
    const screenshotBytes = fs.existsSync(screenshotPath) ? fs.statSync(screenshotPath).size : 0;
    checks.push(check('ScreenshotCaptured', screenshotBytes > 10000 ? 'Pass' : 'Fail', `bytes=${screenshotBytes}`));

    const functionPages = [
      ['single', '单标的回测', '运行回测'],
      ['scan', '参数扫描', '参数网格'],
      ['market_feel', '盘感训练', '生成盘感训练'],
      ['hotspots', '热点分析', '生成热点分析'],
      ['reports', '报告中心', '报告列表'],
      ['holdings', '持仓', '同步持仓'],
    ];
    for (const [view, title, actionText] of functionPages) {
      const targetUrl = new URL(url);
      targetUrl.searchParams.delete('pfi_shell');
      targetUrl.searchParams.delete('pfi_legacy');
      targetUrl.searchParams.set('view', view);
      await page.goto(targetUrl.toString(), { waitUntil: 'domcontentloaded', timeout: 60000 });
      const directShellFrame = await findShellFrame(page);
      checks.push(check(`FunctionPage:${view}:ShellFrame`, directShellFrame ? 'Pass' : 'Fail', title));
      if (!directShellFrame) continue;
      await directShellFrame.waitForFunction(
        ([expectedTitle, expectedAction]) => {
          const panel = document.querySelector('[data-function-detail]');
          const titleNode = document.querySelector('[data-function-title]');
          const actionNode = document.querySelector('[data-function-action]');
          return panel && !panel.hidden && titleNode && actionNode
            && titleNode.textContent.includes(expectedTitle)
            && actionNode.textContent.includes(expectedAction);
        },
        [title, actionText],
        { timeout: 25000 }
      ).catch(() => {});
      const pageText = await frameText(directShellFrame);
      checks.push(check(`FunctionPage:${view}:Title`, pageText.includes(title) ? 'Pass' : 'Fail', title));
      checks.push(check(`FunctionPage:${view}:Action`, pageText.includes(actionText) ? 'Pass' : 'Fail', actionText));
      checks.push(check(`FunctionPage:${view}:NoLegacyQuery`, page.url().includes('pfi_shell=0') || page.url().includes('pfi_legacy=1') ? 'Fail' : 'Pass', page.url()));
      checks.push(check(`FunctionPage:${view}:NoTraceback`, pageText.includes('Traceback') || pageText.includes('ModuleNotFoundError') || pageText.includes('ImportError:') ? 'Fail' : 'Pass', view));
      checks.push(check(`FunctionPage:${view}:NoRetiredIdentity`, retiredIdentityText.some((fragment) => pageText.includes(fragment)) ? 'Fail' : 'Pass', view));
      checks.push(check(`FunctionPage:${view}:NoStreamlitChrome`, pageText.includes('Deploy') || pageText.includes('Stop') ? 'Fail' : 'Pass', view));
    }
    const primaryActionRoutes = [
      { workspace: 'home', view: 'single', panelTitle: '单标的回测', expectedView: 'single', expectedTitle: '单标的回测' },
      { workspace: 'home', view: 'market_feel', panelTitle: '盘感训练', expectedView: 'market_feel', expectedTitle: '盘感训练' },
      { workspace: 'market', view: 'market_slice', panelTitle: '市场垂直切片', expectedView: 'hotspots', expectedTitle: '热点分析' },
      { workspace: 'research', view: 'research_policy_slice', panelTitle: '研究与政策垂直切片', expectedView: 'policy', expectedTitle: '政策雷达' },
      { workspace: 'research', view: 'report_manifest', panelTitle: '报告清单', expectedView: 'reports', expectedTitle: '报告中心' },
    ];
    for (const route of primaryActionRoutes) {
      await verifyPrimaryActionNavigation(page, url, route, checks);
    }
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
