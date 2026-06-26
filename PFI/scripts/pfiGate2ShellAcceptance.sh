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
      echo "Unknown pfiGate2ShellAcceptance argument: $1" >&2
      exit 64
      ;;
  esac
done

cd "$PROJECT_DIR"
mkdir -p "$OUTPUT_DIR"

STAMP="$(date -u +"%Y%m%d_%H%M%S")"
JSON_PATH="$OUTPUT_DIR/PFIGate2ShellAcceptance_$STAMP.json"
LATEST_PATH="$OUTPUT_DIR/PFIGate2ShellAcceptance_latest.json"
SCREENSHOT_PATH="$OUTPUT_DIR/PFIGate2ShellAcceptance_$STAMP.png"
START_LOG="$OUTPUT_DIR/PFIGate2ShellAcceptance_streamlit_$STAMP.log"

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
    "schema": "PFIGate2ShellAcceptanceV1",
    "system": "PFI",
    "subsystem": "Gate2 Shell UAT",
    "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    "status": "Blocked",
    "summary": {"pass": 0, "fail": 1, "info": 0, "total": 1},
    "checks": [{"name": "Gate2ShellAcceptanceBlocked", "status": "Fail", "evidence": reason}],
    "outputs": {"json": str(json_path), "latest_json": str(latest_path)},
    "heavy_smoke_policy": "Does not run finalAcceptanceCheck, ciSmoke, full pytest, market refresh, broker connections, real orders, payments, or holdings writes.",
    "safety_boundary": "Starts local Streamlit only when no healthy PFI service is found, and stops only the service started by this acceptance run.",
    "next_action": "Install or expose a usable browser automation runtime, then rerun scripts/pfiGate2ShellAcceptance.sh --summary-json.",
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
    "performance_budget": payload.get("performance_budget"),
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
    "Gate2 Shell Acceptance: "
    f"{payload.get('status')} "
    f"pass={summary.get('pass')} fail={summary.get('fail')} "
    f"url={payload.get('url')}"
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
  write_blocked_payload "Node.js executable not found for Playwright Gate2 shell acceptance."
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

const PERFORMANCE_BUDGET = {
  shell_ready_ms: 20000,
  workspace_switch_ms: 1500,
  function_open_ms: 1500,
  drawer_toggle_ms: 1000,
  command_palette_ms: 1000,
};

const REQUIRED_WORKSPACES = [
  ['home', '首页'],
  ['market', '市场'],
  ['research', '研究'],
  ['portfolio', '持仓'],
  ['strategy', '策略实验室'],
  ['data', '数据与系统'],
];

const UAT_JOURNEYS = [
  {
    name: 'JOURNEY_HOME_TO_BACKTEST',
    workspace: 'home',
    view: 'single',
    title: '单标的回测',
    action: '运行回测',
    requiredText: ['收益', '回撤', '交易', '报告证据', '禁止实盘自动下单'],
  },
  {
    name: 'JOURNEY_STRATEGY_MARKET_FEEL',
    workspace: 'strategy',
    view: 'market_feel',
    title: '盘感训练',
    action: '生成盘感训练',
    requiredText: ['读图训练', '限时判断', '复盘记录', '不输出实盘信号'],
  },
  {
    name: 'JOURNEY_STRATEGY_PARAMETER_SCAN',
    workspace: 'strategy',
    view: 'scan',
    title: '参数扫描',
    action: '运行参数扫描',
    requiredText: ['参数网格', '样本内外表现', '稳定性', '过拟合风险'],
  },
  {
    name: 'JOURNEY_STRATEGY_SIMULATION',
    workspace: 'strategy',
    view: 'big_data',
    title: '模拟实验',
    action: '打开模拟实验',
    requiredText: ['组合策略', '情景压力', '假设实验', '不连接券商'],
  },
  {
    name: 'JOURNEY_MARKET_HOTSPOTS',
    workspace: 'market',
    view: 'hotspots',
    title: '热点分析',
    action: '生成热点分析',
    requiredText: ['指数', 'ETF', '主题', '热点不是交易信号'],
  },
  {
    name: 'JOURNEY_RESEARCH_REPORT_POLICY',
    workspace: 'research',
    view: 'report_manifest',
    title: '报告清单',
    action: '打开报告清单',
    requiredText: ['运行元数据', '缺失证据', '验证任务', '不修改报告'],
    followUpView: {
      view: 'policy',
      title: '政策雷达',
      action: '打开政策雷达',
      requiredText: ['政策来源', '官方', '监管来源', '政策线索'],
    },
  },
  {
    name: 'JOURNEY_PORTFOLIO_HOLDINGS_REVIEW',
    workspace: 'portfolio',
    view: 'holdings',
    title: '持仓复核',
    action: '同步持仓',
    requiredText: ['正式持仓', '候选持仓', '暴露', '不提交券商'],
  },
  {
    name: 'JOURNEY_DATA_SYSTEM_DIAGNOSTICS',
    workspace: 'data',
    view: 'tools',
    title: '数据中心',
    action: '检查数据源',
    requiredText: ['数据源', '代码格式', '质量报告', '缓存', '隐私边界'],
  },
];

function check(name, status, evidence, meta = {}) {
  return { name, status, evidence, ...meta };
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
    schema: 'PFIGate2ShellAcceptanceV1',
    system: 'PFI',
    subsystem: 'Gate2 Shell UAT',
    generated_at: generatedAt,
    status,
    url,
    started_by_acceptance: startedByAcceptance,
    required_workspaces: REQUIRED_WORKSPACES.map(([workspace]) => workspace),
    uat_journeys: UAT_JOURNEYS.map((journey) => journey.name),
    performance_budget: PERFORMANCE_BUDGET,
    summary: summarize(checks),
    checks,
    outputs: {
      json: jsonPath,
      latest_json: latestPath,
      screenshot: fs.existsSync(screenshotPath) ? screenshotPath : '',
    },
    heavy_smoke_policy: 'Does not run finalAcceptanceCheck, ciSmoke, full pytest, market refresh, broker connections, real orders, payments, or holdings writes.',
    safety_boundary: 'Browser-only verification against localhost. Research, backtest, simulation, review, report, and training surfaces only; no live automatic trading or broker submission.',
    next_action: status === 'Pass' ? 'Use this Gate2 evidence with visual acceptance and CI target gate.' : 'Fix failed checks before moving to the next PFI gate.',
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

let axeCore = null;
try {
  axeCore = require('axe-core');
} catch (_error) {
  axeCore = null;
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

async function timed(label, budget, checks, fn) {
  const started = Date.now();
  const result = await fn();
  const elapsed = Date.now() - started;
  checks.push(check(`Performance:${label}`, elapsed <= budget ? 'Pass' : 'Fail', `${elapsed}ms <= ${budget}ms`, { elapsed_ms: elapsed, budget_ms: budget }));
  return result;
}

async function switchWorkspace(frame, workspaceId, label, checks) {
  await timed(`WorkspaceSwitch:${workspaceId}`, PERFORMANCE_BUDGET.workspace_switch_ms, checks, async () => {
    await frame.locator(`[data-workspace="${workspaceId}"]`).click({ timeout: 10000 });
    await frame.waitForFunction(
      ([expectedId, expectedLabel]) => {
        const main = document.querySelector('#main-workspace');
        const title = document.querySelector('#workspace-title');
        return main && title && main.dataset.activeWorkspace === expectedId && title.textContent.includes(expectedLabel);
      },
      [workspaceId, label],
      { timeout: 10000 },
    );
  });
  const titleText = await frame.locator('#workspace-title').innerText({ timeout: 5000 });
  checks.push(check(`Workspace:${workspaceId}:ChinesePanel`, titleText.includes(label) ? 'Pass' : 'Fail', titleText));
}

async function openFunction(frame, view, title, action, requiredText, prefix, checks) {
  await timed(`${prefix}:FunctionOpen:${view}`, PERFORMANCE_BUDGET.function_open_ms, checks, async () => {
    const control = frame.locator(`[data-feature-view="${view}"]`).first();
    await control.waitFor({ state: 'visible', timeout: 10000 });
    const tagName = await control.evaluate((node) => node.tagName.toLowerCase());
    const href = await control.evaluate((node) => node.getAttribute('href') || '');
    checks.push(check(`${prefix}:${view}:ControlIsButton`, tagName === 'button' ? 'Pass' : 'Fail', `${tagName}; href=${href || 'none'}`));
    checks.push(check(`${prefix}:${view}:NoLegacyHref`, href === '' ? 'Pass' : 'Fail', href || 'none'));
    await control.click({ timeout: 10000 });
    await frame.waitForFunction(
      ([expectedTitle, expectedAction]) => {
        const panel = document.querySelector('[data-function-detail]');
        const titleNode = document.querySelector('[data-function-title]');
        const actionNode = document.querySelector('[data-function-action]');
        return panel && !panel.hidden && titleNode && actionNode
          && titleNode.textContent.includes(expectedTitle)
          && actionNode.textContent.includes(expectedAction);
      },
      [title, action],
      { timeout: 10000 },
    );
  });

  const detailText = await frame.locator('[data-function-detail]').innerText({ timeout: 5000 });
  checks.push(check(`${prefix}:${view}:PanelTitle`, detailText.includes(title) ? 'Pass' : 'Fail', title));
  checks.push(check(`${prefix}:${view}:PrimaryAction`, detailText.includes(action) ? 'Pass' : 'Fail', action));
  checks.push(check(`${prefix}:${view}:SafetyBoundary`, detailText.includes('禁止实盘自动下单') ? 'Pass' : 'Fail', detailText.slice(0, 220)));
  for (const text of requiredText) {
    checks.push(check(`${prefix}:${view}:RequiredText:${text}`, detailText.includes(text) ? 'Pass' : 'Fail', text));
  }
  const activeWorkspace = await frame.locator('#main-workspace').evaluate((node) => node.dataset.activeWorkspace);
  const urlAfterClick = frame.page().url();
  checks.push(check(`${prefix}:${view}:SameShellWorkspace`, activeWorkspace ? 'Pass' : 'Fail', activeWorkspace || 'missing'));
  checks.push(check(`${prefix}:${view}:NoLegacyPageNavigation`, urlAfterClick.includes('pfi_shell=0') ? 'Fail' : 'Pass', urlAfterClick));
  return detailText;
}

async function verifyPrimaryActionNavigation(page, baseUrl, route, checks) {
  await page.goto(baseUrl, { waitUntil: 'domcontentloaded', timeout: 60000 });
  const shellFrame = await findShellFrame(page);
  checks.push(check(`PrimaryActionNavigation:${route.view}:ShellFrame`, shellFrame ? 'Pass' : 'Fail', route.view));
  if (!shellFrame) return;
  await shellFrame.evaluate(() => localStorage.removeItem('pfi-context-v2')).catch(() => {});
  await switchWorkspace(shellFrame, route.workspace, route.workspaceLabel, checks);
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
    { timeout: 10000 },
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
    { timeout: 10000 },
  );
  const runnerText = await shellFrame.locator('[data-function-runner]').innerText({ timeout: 5000 });
  const afterPages = page.context().pages().length;
  checks.push(check(`PrimaryActionNavigation:${route.view}:SameShellRunner`, runnerText.includes('操作面板') ? 'Pass' : 'Fail', runnerText.slice(0, 220)));
  checks.push(check(`PrimaryActionNavigation:${route.view}:NoNewLegacyPage`, afterPages === beforePages ? 'Pass' : 'Fail', `before=${beforePages} after=${afterPages}`));
  checks.push(check(`PrimaryActionNavigation:${route.view}:NoLegacyQuery`, page.url().includes('pfi_shell=0') || page.url().includes('pfi_legacy=1') ? 'Fail' : 'Pass', page.url()));
  checks.push(check(`PrimaryActionNavigation:${route.view}:SafetyBoundary`, runnerText.includes('不连接券商') && runnerText.includes('不提交订单') ? 'Pass' : 'Fail', runnerText.slice(0, 220)));
}

async function runJourney(frame, journey, checks) {
  const label = REQUIRED_WORKSPACES.find(([id]) => id === journey.workspace)?.[1] || journey.workspace;
  await switchWorkspace(frame, journey.workspace, label, checks);
  const detailText = await openFunction(frame, journey.view, journey.title, journey.action, journey.requiredText, journey.name, checks);
  checks.push(check(`${journey.name}:ChineseUserSurface`, /[\u3400-\u9fff]/.test(detailText) ? 'Pass' : 'Fail', detailText.slice(0, 160)));
  if (journey.followUpView) {
    await openFunction(
      frame,
      journey.followUpView.view,
      journey.followUpView.title,
      journey.followUpView.action,
      journey.followUpView.requiredText,
      `${journey.name}:FOLLOW_UP`,
      checks,
    );
  }
}

async function verifyAllVisibleFeatureControls(page, frame, checks) {
  let total = 0;
  for (const [workspaceId, label] of REQUIRED_WORKSPACES) {
    await switchWorkspace(frame, workspaceId, label, checks);
    const count = await frame.locator('.workflow-card .workflow-open').count();
    checks.push(check(`AllFeatureControls:${workspaceId}:Count`, count > 0 ? 'Pass' : 'Fail', `count=${count}`));
    for (let index = 0; index < count; index += 1) {
      await switchWorkspace(frame, workspaceId, label, checks);
      const info = await frame.locator('.workflow-card').nth(index).evaluate((card) => {
        const title = (card.querySelector('.workflow-card-head strong')?.textContent || '').trim();
        const control = card.querySelector('.workflow-open');
        return {
          title,
          tagName: control ? control.tagName.toLowerCase() : '',
          text: control ? control.textContent.trim() : '',
          href: control ? control.getAttribute('href') || '' : '',
          view: control ? control.getAttribute('data-feature-view') || '' : '',
          workspace: control ? control.getAttribute('data-feature-workspace') || '' : '',
        };
      });
      const prefix = `AllFeatureControls:${workspaceId}:${index}:${info.title || 'untitled'}`;
      checks.push(check(`${prefix}:ControlExists`, info.tagName ? 'Pass' : 'Fail', JSON.stringify(info)));
      checks.push(check(`${prefix}:ControlIsButton`, info.tagName === 'button' ? 'Pass' : 'Fail', `${info.tagName}; href=${info.href || 'none'}`));
      checks.push(check(`${prefix}:HasFunctionView`, info.view ? 'Pass' : 'Fail', JSON.stringify(info)));
      checks.push(check(`${prefix}:NoLegacyHref`, info.href === '' ? 'Pass' : 'Fail', info.href || 'none'));
      if (!info.view) continue;
      const beforePages = page.context().pages().length;
      await timed(`${prefix}:OpenPanel`, PERFORMANCE_BUDGET.function_open_ms, checks, async () => {
        await frame.locator('.workflow-card .workflow-open').nth(index).click({ timeout: 10000 });
        await frame.waitForFunction(
          (expectedTitle) => {
            const panel = document.querySelector('[data-function-detail]');
            const titleNode = document.querySelector('[data-function-title]');
            const actionNode = document.querySelector('[data-function-action]');
            if (!panel || panel.hidden || !titleNode || !actionNode) return false;
            const titleText = titleNode.textContent || '';
            return titleText.includes(expectedTitle) || expectedTitle.includes(titleText) || titleText.length > 1;
          },
          info.title,
          { timeout: 10000 },
        );
      });
      const detailText = await frame.locator('[data-function-detail]').innerText({ timeout: 5000 });
      checks.push(check(`${prefix}:ChinesePanel`, /[\u3400-\u9fff]/.test(detailText) ? 'Pass' : 'Fail', detailText.slice(0, 180)));
      checks.push(check(`${prefix}:SafetyBoundary`, detailText.includes('禁止实盘自动下单') ? 'Pass' : 'Fail', detailText.slice(0, 220)));
      await frame.locator('[data-function-action]').click({ timeout: 10000 });
      await frame.waitForFunction(() => {
        const runner = document.querySelector('[data-function-runner]');
        return runner && !runner.hidden && runner.textContent.includes('操作面板');
      }, null, { timeout: 10000 });
      const runnerText = await frame.locator('[data-function-runner]').innerText({ timeout: 5000 });
      checks.push(check(`${prefix}:RunnerVisible`, runnerText.includes('操作面板') ? 'Pass' : 'Fail', runnerText.slice(0, 180)));
      checks.push(check(`${prefix}:RunnerSafety`, runnerText.includes('不连接券商') && runnerText.includes('不提交订单') ? 'Pass' : 'Fail', runnerText.slice(0, 220)));
      const afterPages = page.context().pages().length;
      checks.push(check(`${prefix}:NoNewPage`, afterPages === beforePages ? 'Pass' : 'Fail', `before=${beforePages} after=${afterPages}`));
      checks.push(check(`${prefix}:NoLegacyQuery`, page.url().includes('pfi_shell=0') || page.url().includes('pfi_legacy=1') ? 'Fail' : 'Pass', page.url()));
      total += 1;
    }
  }
  checks.push(check('AllFeatureControls:TotalPanelsOpened', total >= 40 ? 'Pass' : 'Fail', `opened=${total}`));
  return total;
}

async function accessibilityProof(frame, checks) {
  const structural = await frame.evaluate(() => {
    const selectors = {
      skip_link: '.skip-link',
      primary_nav: 'nav[aria-label="一级工作区"]',
      global_context: 'form[aria-label="全局上下文"]',
      evidence_drawer: 'aside[aria-label="证据抽屉"]',
      command_palette: 'dialog[aria-label="命令面板"]',
      polite_live_region: '[aria-live="polite"]',
      assertive_live_region: '[aria-live="assertive"]',
    };
    const presence = Object.fromEntries(Object.entries(selectors).map(([key, selector]) => [key, Boolean(document.querySelector(selector))]));
    const visibleEnough = (node) => {
      const style = window.getComputedStyle(node);
      const box = node.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && box.width > 1 && box.height > 1;
    };
    const accessibleName = (node) => (
      node.getAttribute('aria-label')
      || node.getAttribute('title')
      || node.getAttribute('placeholder')
      || node.textContent
      || ''
    ).trim();
    const unlabeled = [...document.querySelectorAll('button, a, input, select, textarea, [role="button"], [role="option"]')]
      .filter(visibleEnough)
      .filter((node) => !accessibleName(node))
      .map((node) => node.outerHTML.slice(0, 120));
    const tooSmall = [...document.querySelectorAll('button, a, input, select, textarea')]
      .filter(visibleEnough)
      .map((node) => ({ name: accessibleName(node), tag: node.tagName.toLowerCase(), box: node.getBoundingClientRect() }))
      .filter((item) => item.box.width < 44 || item.box.height < 44)
      .map((item) => `${item.tag}:${item.name}:${Math.round(item.box.width)}x${Math.round(item.box.height)}`);
    const targetVar = window.getComputedStyle(document.documentElement).getPropertyValue('--pfi-target').trim();
    const focusStyle = [...document.styleSheets].some((sheet) => {
      try {
        return [...sheet.cssRules].some((rule) => String(rule.selectorText || '').includes(':focus-visible'));
      } catch (_error) {
        return false;
      }
    });
    return { presence, unlabeled, tooSmall, targetVar, focusStyle };
  });

  for (const [key, present] of Object.entries(structural.presence)) {
    checks.push(check(`WCAGStructuralProof:${key}`, present ? 'Pass' : 'Fail', String(present)));
  }
  checks.push(check('WCAGStructuralProof:NoUnlabeledInteractive', structural.unlabeled.length === 0 ? 'Pass' : 'Fail', structural.unlabeled.join(' | ') || 'all labeled'));
  checks.push(check('WCAGStructuralProof:MinTarget44px', structural.tooSmall.length === 0 ? 'Pass' : 'Fail', structural.tooSmall.join(' | ') || 'all targets >= 44px'));
  checks.push(check('WCAGStructuralProof:TargetToken', structural.targetVar === '44px' ? 'Pass' : 'Fail', structural.targetVar));
  checks.push(check('WCAGStructuralProof:FocusVisible', structural.focusStyle ? 'Pass' : 'Fail', String(structural.focusStyle)));

  if (axeCore) {
    await frame.addScriptTag({ content: axeCore.source });
    const results = await frame.evaluate(async () => {
      return await window.axe.run(document, {
        runOnly: { type: 'tag', values: ['wcag2a', 'wcag2aa'] },
      });
    });
    checks.push(check('AxeWCAG2AA:Violations', results.violations.length === 0 ? 'Pass' : 'Fail', results.violations.map((item) => item.id).join(', ') || 'none'));
  } else {
    checks.push(check('AxeWCAG2AA:OptionalDependency', 'Info', 'axe-core not installed; WCAG structural proof executed locally without network.'));
  }
}

async function noLegacyAndNoGibberish(frame, page, checks) {
  const bodyText = await frameText(frame);
  const retiredText = ['E' + 'VA', 'Quant' + 'Lab', 'Token' + ' ROI', 'PFI_OS', 'PFIOS'];
  const forbiddenText = [
    'Traceback',
    'ModuleNotFoundError',
    'ImportError:',
    'Connection lost',
    'Global Search',
    'Task Center',
    'Workflow cards',
    'Operational evidence',
    'Fast Path Review',
    'legacy',
    '旧版',
    ...retiredText,
  ];
  for (const text of forbiddenText) {
    checks.push(check(`NoVisibleLegacyOrError:${text}`, bodyText.includes(text) ? 'Fail' : 'Pass', text));
  }
  const shellOnly = await frame.evaluate(() => {
    const featureAnchors = [...document.querySelectorAll('a[data-feature-view]')].map((node) => node.outerHTML.slice(0, 120));
    const legacyVisible = [...document.querySelectorAll('[data-function-legacy-link]')].some((node) => {
      const style = window.getComputedStyle(node);
      const box = node.getBoundingClientRect();
      return style.display !== 'none' && style.visibility !== 'hidden' && box.width > 1 && box.height > 1;
    });
    return { featureAnchors, legacyVisible };
  });
  checks.push(check('NoLegacyPageImport:FeatureControlsAreNotAnchors', shellOnly.featureAnchors.length === 0 ? 'Pass' : 'Fail', shellOnly.featureAnchors.join(' | ') || 'all feature controls are buttons'));
  checks.push(check('NoLegacyPageImport:DetailLinkNotPrimary', shellOnly.legacyVisible ? 'Fail' : 'Pass', shellOnly.legacyVisible ? '兼容详情入口不应在默认用户路径可见' : '核心 UAT 只暴露同壳操作面板'));
  checks.push(check('NoLegacyPageImport:ParentUrlStaysShell', page.url().includes('pfi_shell=0') ? 'Fail' : 'Pass', page.url()));
  checks.push(check('ChineseFirstSurface:BodyHasCJK', /[\u3400-\u9fff]/.test(bodyText) ? 'Pass' : 'Fail', `length=${bodyText.length}`));
  checks.push(check('ChineseFirstSurface:BodyLength', bodyText.length > 800 ? 'Pass' : 'Fail', `length=${bodyText.length}`));
}

(async () => {
  const checks = [
    check('BrowserExecutable', 'Pass', browserExecutable),
    check('AxeCoreResolved', axeCore ? 'Pass' : 'Info', axeCore ? 'axe-core local package available' : 'axe-core local package unavailable'),
  ];
  let browser;
  let shellReadyMs = 0;
  let screenshotBytes = 0;
  let allFeatureControlCount = 0;
  try {
    browser = await playwright.chromium.launch({ headless: true, executablePath: browserExecutable });
    const page = await browser.newPage({ viewport: { width: 1440, height: 1000 } });
    const pageStarted = Date.now();
    const response = await page.goto(url, { waitUntil: 'domcontentloaded', timeout: 60000 });
    checks.push(check('HTTPStatus', response && response.ok() ? 'Pass' : 'Fail', `status=${response ? response.status() : 'missing'}`));
    const shellFrame = await findShellFrame(page);
    shellReadyMs = Date.now() - pageStarted;
    checks.push(check('PFIWebShellFrame', shellFrame ? 'Pass' : 'Fail', shellFrame ? 'PFI Web Shell iframe rendered' : 'PFI Web Shell iframe missing'));
    checks.push(check('Performance:ShellReady', shellReadyMs <= PERFORMANCE_BUDGET.shell_ready_ms ? 'Pass' : 'Fail', `${shellReadyMs}ms <= ${PERFORMANCE_BUDGET.shell_ready_ms}ms`, { elapsed_ms: shellReadyMs, budget_ms: PERFORMANCE_BUDGET.shell_ready_ms }));
    if (!shellFrame) {
      throw new Error('PFI Web Shell iframe did not render expected Chinese workspace text.');
    }

    await shellFrame.evaluate(() => localStorage.removeItem('pfi-context-v2'));
    await switchWorkspace(shellFrame, 'home', '首页', checks);

    for (const [workspaceId, label] of REQUIRED_WORKSPACES) {
      await switchWorkspace(shellFrame, workspaceId, label, checks);
    }

    for (const journey of UAT_JOURNEYS) {
      await runJourney(shellFrame, journey, checks);
    }

    allFeatureControlCount = await verifyAllVisibleFeatureControls(page, shellFrame, checks);

    await timed('EvidenceDrawerToggle', PERFORMANCE_BUDGET.drawer_toggle_ms, checks, async () => {
      await shellFrame.locator('[data-evidence-toggle]').first().click({ timeout: 10000 });
      await shellFrame.waitForFunction(() => {
        const drawer = document.querySelector('[data-evidence-drawer]');
        return drawer && drawer.getAttribute('aria-expanded') === 'true';
      }, null, { timeout: 5000 });
    });

    await timed('CommandPaletteOpen', PERFORMANCE_BUDGET.command_palette_ms, checks, async () => {
      await shellFrame.locator('[data-command-open]').click({ timeout: 10000 });
      await shellFrame.waitForFunction(() => {
        const dialog = document.querySelector('[data-command-palette]');
        return dialog && (dialog.open || dialog.hasAttribute('open'));
      }, null, { timeout: 5000 });
    });

    await accessibilityProof(shellFrame, checks);
    await noLegacyAndNoGibberish(shellFrame, page, checks);

    await page.screenshot({ path: screenshotPath, fullPage: true });
    screenshotBytes = fs.existsSync(screenshotPath) ? fs.statSync(screenshotPath).size : 0;
    checks.push(check('ScreenshotCaptured', screenshotBytes > 10000 ? 'Pass' : 'Fail', `bytes=${screenshotBytes}`));

    const primaryActionRoutes = [
      { workspace: 'home', workspaceLabel: '首页', view: 'single', panelTitle: '单标的回测', expectedView: 'single', expectedTitle: '单标的回测' },
      { workspace: 'strategy', workspaceLabel: '策略实验室', view: 'market_feel', panelTitle: '盘感训练', expectedView: 'market_feel', expectedTitle: '盘感训练' },
      { workspace: 'market', workspaceLabel: '市场', view: 'market_slice', panelTitle: '市场垂直切片', expectedView: 'hotspots', expectedTitle: '热点分析' },
      { workspace: 'research', workspaceLabel: '研究', view: 'research_policy_slice', panelTitle: '研究与政策垂直切片', expectedView: 'policy', expectedTitle: '政策雷达' },
      { workspace: 'research', workspaceLabel: '研究', view: 'report_manifest', panelTitle: '报告清单', expectedView: 'reports', expectedTitle: '报告中心' },
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
          shell_ready_ms: shellReadyMs,
          screenshot_bytes: screenshotBytes,
          viewport: '1440x1000',
          all_feature_control_panels_opened: allFeatureControlCount,
        },
      }),
      status === 'Pass' ? 0 : 2,
    );
  } catch (error) {
    if (browser) {
      await browser.close().catch(() => {});
    }
    checks.push(check('Gate2BrowserProbe', 'Fail', String(error && error.stack || error)));
    writePayload(basePayload('Fail', checks, { browser: { executable: browserExecutable } }), 2);
  }
})();
JS
NODE_STATUS="$?"
set -e

print_payload
exit "$NODE_STATUS"
