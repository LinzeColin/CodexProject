#!/usr/bin/env node

import fs from "node:fs/promises";
import fsSync from "node:fs";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const NODE_MODULE_HINT =
  process.env.TAB_FIFA_NODE_MODULES ||
  "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const require = createRequire(import.meta.url);
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const PROJECT_ROOT = resolveWorkspaceRoot(SCRIPT_DIR);
const CANONICAL_OUTPUT_DIR = path.resolve(process.env.TAB_FIFA_OUTPUT_DIR || path.join(PROJECT_ROOT, "outputs"));
const DEFAULT_PRIVATE_DIR = path.resolve(process.env.TAB_FIFA_PRIVATE_DIR || path.join(PROJECT_ROOT, "work", "private", "tab_fifa"));
const DEFAULT_CHROME_PROFILE_DIR = path.join(DEFAULT_PRIVATE_DIR, "tab_chrome_profile");
const MY_BETS_URL = "https://www.tab.com.au/accounts/my-bets/bets";
const IS_CLI = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
let chromiumModule = null;

function parseArgs(argv) {
  const args = {
    outputDir: DEFAULT_PRIVATE_DIR,
    chromeUserDataDir: "",
    reportDate: "",
    timeoutMs: 45000,
    waitForLoginMs: 0,
    dryRun: false,
  };
  for (let idx = 2; idx < argv.length; idx += 1) {
    const arg = argv[idx];
    if (arg === "--dry-run") args.dryRun = true;
    else if (arg === "--output-dir") args.outputDir = path.resolve(argv[++idx]);
    else if (arg === "--chrome-user-data-dir") args.chromeUserDataDir = path.resolve(argv[++idx]);
    else if (arg === "--report-date") args.reportDate = argv[++idx];
    else if (arg === "--timeout-ms") args.timeoutMs = Number(argv[++idx]);
    else if (arg === "--wait-for-login-ms") args.waitForLoginMs = Number(argv[++idx]);
    else throw new Error(`unknown argument: ${arg}`);
  }
  if (!args.reportDate) args.reportDate = reportDateToday();
  if (!/^\d{8}$/.test(args.reportDate)) throw new Error("report date must use DDMMYYYY format");
  if (!Number.isFinite(args.timeoutMs) || args.timeoutMs <= 0) throw new Error("timeout-ms must be positive");
  if (!Number.isFinite(args.waitForLoginMs) || args.waitForLoginMs < 0) throw new Error("wait-for-login-ms must be zero or positive");
  return args;
}

function reportDateToday() {
  const formatter = new Intl.DateTimeFormat("en-AU", {
    timeZone: "Australia/Sydney",
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
  });
  return formatter.format(new Date()).replace(/\//g, "");
}

function headlessMode() {
  return !["0", "false", "no"].includes(String(process.env.TAB_FIFA_HEADLESS || "1").toLowerCase());
}

function chromeUserDataDir(cliValue = "", outputDir = DEFAULT_PRIVATE_DIR) {
  return cliValue || process.env.TAB_FIFA_CHROME_USER_DATA_DIR || path.join(outputDir || DEFAULT_PRIVATE_DIR, "tab_chrome_profile");
}

function resolveWorkspaceRoot(anchorDir) {
  if (process.env.TAB_FIFA_WORKSPACE_ROOT) return path.resolve(process.env.TAB_FIFA_WORKSPACE_ROOT);
  const candidates = [];
  let current = path.resolve(anchorDir);
  while (true) {
    candidates.push(current);
    const parent = path.dirname(current);
    if (parent === current) break;
    current = parent;
  }
  for (const candidate of candidates) {
    if (fsSync.existsSync(path.join(candidate, "outputs")) && fsSync.existsSync(path.join(candidate, "work", "tab-research-pipeline"))) {
      return candidate;
    }
  }
  for (const candidate of candidates) {
    if (fsSync.existsSync(path.join(candidate, "tab-research-pipeline")) && (fsSync.existsSync(path.join(candidate, "AGENTS.md")) || fsSync.existsSync(path.join(candidate, ".git")))) {
      return candidate;
    }
  }
  return path.resolve(anchorDir, "..");
}

function chromeExecutablePath() {
  const macChrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
  return process.env.CHROME_EXECUTABLE_PATH || macChrome;
}

function loadChromium() {
  if (!chromiumModule) {
    ({ chromium: chromiumModule } = require(path.join(NODE_MODULE_HINT, "playwright")));
  }
  return chromiumModule;
}

async function main(argv = process.argv) {
  const args = parseArgs(argv);
  const profileDir = chromeUserDataDir(args.chromeUserDataDir, args.outputDir);
  const rawFile = `tab_my_bets_raw_${args.reportDate}.txt`;
  const diagnosticsFile = captureDiagnosticsFileName(args.reportDate);
  const summary = {
    schema_version: 1,
    mode: args.dryRun ? "dry-run" : "live",
    url: "TAB My Bets",
    report_date: args.reportDate,
    output_dir: path.basename(args.outputDir),
    raw_text_file: rawFile,
    diagnostics_file: diagnosticsFile,
    headless: headlessMode(),
    auth_profile: path.basename(profileDir),
    wait_for_login_ms: args.waitForLoginMs,
    ready: false,
  };
  await assertPrivateOutputDir(args.outputDir);
  await assertPrivateProfileDir(profileDir);
  if (args.dryRun) {
    console.log(JSON.stringify({ ...summary, ready: true, path_guard_ready: true }, null, 2));
    return;
  }

  await fs.mkdir(args.outputDir, { recursive: true, mode: 0o700 });
  await fs.chmod(args.outputDir, 0o700).catch(() => {});

  const session = await openReadOnlyContext({ chromeUserDataDir: args.chromeUserDataDir, outputDir: args.outputDir });
  try {
    const context = session.context;
    const allowLoginBootstrap = !headlessMode() && args.waitForLoginMs > 0;
    await context.route("**/*", async (route) => {
      const request = route.request();
      if (isBlockedMyBetsRequest(request.method(), request.url(), { allowLoginBootstrap })) {
        await route.abort();
        return;
      }
      await route.continue();
    });
    const page = await context.newPage();
    await page.goto(MY_BETS_URL, { waitUntil: "domcontentloaded", timeout: args.timeoutMs });
    await page.waitForLoadState("networkidle", { timeout: args.timeoutMs }).catch(() => {});
    const captured = await captureValidatedPage(page, args);
    const { finalUrl, title, text, validation } = captured;
    const diagnostic = buildCaptureDiagnostic({
      ...summary,
      auth_mode: session.authMode,
      auth_profile: session.profileDirName,
      page_title: title,
      final_url: finalUrl,
      text,
      validation,
      wait_result: captured.waitResult,
    });
    await writePrivateJson(path.join(args.outputDir, diagnosticsFile), diagnostic);
    if (!validation.ready) {
      throw new Error(validation.reason);
    }
    const rawPath = path.join(args.outputDir, rawFile);
    await atomicWritePrivateText(rawPath, text);
    console.log(JSON.stringify({
      ...summary,
      auth_mode: session.authMode,
      auth_profile: session.profileDirName,
      ready: true,
      auth_status: validation.authStatus,
      text_length: text.length,
      line_count: text.split(/\r?\n/).filter((line) => line.trim()).length,
      raw_text_file: path.basename(rawPath),
      diagnostics_file: diagnosticsFile,
    }, null, 2));
  } finally {
    await session.close().catch(() => {});
  }
}

async function captureValidatedPage(page, args) {
  let captured = await readPageText(page, args.timeoutMs);
  if (captured.validation.ready || args.waitForLoginMs <= 0) {
    return { ...captured, waitResult: args.waitForLoginMs > 0 ? "already_ready" : "not_requested" };
  }
  const deadline = Date.now() + args.waitForLoginMs;
  while (Date.now() < deadline) {
    await page.waitForTimeout(Math.min(2000, Math.max(250, deadline - Date.now())));
    captured = await readPageText(page, Math.min(args.timeoutMs, 5000));
    if (captured.validation.ready) {
      return { ...captured, waitResult: "became_ready" };
    }
  }
  return { ...captured, waitResult: "timed_out" };
}

async function readPageText(page, timeoutMs) {
  const finalUrl = page.url();
  const title = await page.title().catch(() => "");
  const text = await page.locator("body").innerText({ timeout: timeoutMs }).catch(() => "");
  const validation = validateMyBetsText(text, finalUrl, title);
  return { finalUrl, title, text, validation };
}

async function openReadOnlyContext(options = {}) {
  const chromium = loadChromium();
  const userDataDir = chromeUserDataDir(options.chromeUserDataDir || "", options.outputDir || DEFAULT_PRIVATE_DIR);
  if (userDataDir) {
    await fs.mkdir(userDataDir, { recursive: true, mode: 0o700 });
    await fs.chmod(userDataDir, 0o700).catch(() => {});
    const context = await chromium.launchPersistentContext(path.resolve(userDataDir), {
      executablePath: chromeExecutablePath(),
      headless: headlessMode(),
      viewport: { width: 1280, height: 1400 },
      locale: "en-AU",
      serviceWorkers: "block",
      args: ["--disable-gpu", "--no-first-run", "--no-default-browser-check"],
    });
    return {
      context,
      authMode: "persistent-profile",
      profileDirName: path.basename(userDataDir),
      close: () => context.close(),
    };
  }
  const browser = await chromium.launch({
    executablePath: chromeExecutablePath(),
    headless: headlessMode(),
    args: ["--disable-gpu", "--no-first-run", "--no-default-browser-check"],
  });
  const context = await browser.newContext({
    viewport: { width: 1280, height: 1400 },
    locale: "en-AU",
    serviceWorkers: "block",
  });
  return {
    context,
    authMode: "fresh-context",
    profileDirName: "",
    close: () => browser.close(),
  };
}

async function assertPrivateOutputDir(outputDir) {
  const resolved = path.resolve(outputDir);
  if (isSameOrChildPath(resolved, CANONICAL_OUTPUT_DIR)) {
    throw new Error("My Bets capture refuses to write into public outputs");
  }
  if (!hasPrivatePathSegment(resolved)) {
    throw new Error("My Bets capture requires an output directory under a private path");
  }
}

async function assertPrivateProfileDir(profileDir) {
  const resolved = path.resolve(profileDir);
  if (isSameOrChildPath(resolved, CANONICAL_OUTPUT_DIR)) {
    throw new Error("My Bets capture refuses to use a Chrome profile under public outputs");
  }
  if (!hasPrivatePathSegment(resolved)) {
    throw new Error("My Bets capture requires the Chrome profile under a private path");
  }
}

function isSameOrChildPath(candidate, parent) {
  const relative = path.relative(path.resolve(parent), path.resolve(candidate));
  return relative === "" || (!!relative && !relative.startsWith("..") && !path.isAbsolute(relative));
}

function hasPrivatePathSegment(candidate) {
  let parts = path.resolve(candidate).split(path.sep).filter(Boolean);
  if (parts[0] === "private" && (parts[1] === "tmp" || parts[1] === "var")) {
    parts = parts.slice(2);
  }
  return parts.includes("private");
}

function isBlockedMyBetsRequest(method, url, options = {}) {
  const upperMethod = String(method || "").toUpperCase();
  if (/betslip|bet-slip|placebet|place-bet|addselection|add-selection/i.test(url)) return true;
  if (/\/accounts\//i.test(url) && !isReadOnlyMyBetsUrl(url)) return true;
  if (options.allowLoginBootstrap && isAllowedLoginBootstrapRequest(upperMethod, url)) return false;
  if (["POST", "PUT", "PATCH", "DELETE"].includes(upperMethod)) return true;
  return false;
}

function isAllowedLoginBootstrapRequest(method, url) {
  if (!["POST", "GET"].includes(String(method || "").toUpperCase())) return false;
  try {
    const parsed = new URL(String(url || ""));
    const host = parsed.hostname.toLowerCase();
    const isTabHost = host === "tab.com.au" || host.endsWith(".tab.com.au");
    if (!isTabHost) return false;
    const value = `${host}\n${parsed.pathname}\n${parsed.search}`.toLowerCase();
    return /login|oauth|authorize|identity|authentication|session|signin|sign-in/.test(value);
  } catch {
    return false;
  }
}

function isReadOnlyMyBetsUrl(url) {
  try {
    const parsed = new URL(String(url || ""));
    const value = `${parsed.pathname}\n${parsed.search}`.toLowerCase();
    return /my-bets|mybets|bet-history/.test(value) || /\bbets?\b/.test(value);
  } catch {
    const value = String(url || "").toLowerCase();
    return /my-bets|mybets|bet-history/.test(value) || /\bbets?\b/.test(value);
  }
}

function validateMyBetsText(text, finalUrl = "", pageTitle = "") {
  const page = classifyMyBetsPage(text, finalUrl, pageTitle);
  if (page.authStatus === "access_denied") {
    return { ready: false, reason: "TAB My Bets page access denied", authStatus: page.authStatus };
  }
  if (page.authStatus === "login_required") {
    return { ready: false, reason: "TAB My Bets page appears unauthenticated", authStatus: page.authStatus };
  }
  if (!page.hasRecognizableBetMarkers) {
    return { ready: false, reason: "TAB My Bets text did not contain recognizable bet markers", authStatus: page.authStatus };
  }
  return { ready: true, reason: "", authStatus: page.authStatus };
}

function classifyMyBetsPage(text, finalUrl = "", pageTitle = "") {
  const value = String(text || "");
  const url = String(finalUrl || "");
  const title = String(pageTitle || "");
  const isLoginUrl = /^https:\/\/login\.tab\.com\.au\/login/i.test(url) || /\/login\b/i.test(url);
  const hasLoginText = /log in|login|sign in|password|username|mobile/i.test(value);
  const hasAccessDenied = /access denied|akamai|reference #|not have permission/i.test(`${title}\n${value}`);
  const hasMyBetsText = /My Bets/i.test(value);
  const hasRecognizableBetMarkers = /My Bets|Pending|Won|Lost|Stake|Estimated Return/i.test(value);
  return {
    authStatus: hasAccessDenied
      ? "access_denied"
      : ((isLoginUrl || (hasLoginText && !hasMyBetsText)) ? "login_required" : "session_page_loaded"),
    hasLoginText,
    hasAccessDenied,
    hasMyBetsText,
    hasRecognizableBetMarkers,
    textLength: value.length,
    finalUrlPublic: publicUrlPart(url),
  };
}

function captureDiagnosticsFileName(reportDate) {
  return `tab_my_bets_capture_diagnostics_${reportDate}.json`;
}

function buildCaptureDiagnostic({ report_date, mode, auth_mode, auth_profile, page_title, final_url, text, validation, wait_result }) {
  const page = classifyMyBetsPage(text, final_url, page_title);
  return {
    schema_version: 1,
    private_diagnostic: true,
    report_date,
    mode,
    capture_target: "TAB My Bets",
    auth_mode,
    auth_profile: auth_profile || "",
    ready: Boolean(validation.ready),
    auth_status: validation.authStatus || page.authStatus,
    reason: validation.reason || "ready",
    wait_result: wait_result || "",
    page_title: String(page_title || "").slice(0, 120),
    final_url_public: page.finalUrlPublic,
    text_length: page.textLength,
    markers: {
      has_login_text: page.hasLoginText,
      has_access_denied: page.hasAccessDenied,
      has_my_bets_text: page.hasMyBetsText,
      has_recognizable_bet_markers: page.hasRecognizableBetMarkers,
    },
    raw_text_stored: Boolean(validation.ready),
    note: "Private diagnostic only; no raw My Bets text, no query string, no account identifiers.",
  };
}

function publicUrlPart(url) {
  try {
    const parsed = new URL(String(url || ""));
    return `${parsed.origin}${parsed.pathname}`;
  } catch {
    return "";
  }
}

async function atomicWritePrivateText(filePath, text) {
  const tmp = `${filePath}.${process.pid}.tmp`;
  await fs.writeFile(tmp, text, { encoding: "utf-8", mode: 0o600 });
  await fs.chmod(tmp, 0o600).catch(() => {});
  await fs.rename(tmp, filePath);
  await fs.chmod(filePath, 0o600).catch(() => {});
}

async function writePrivateJson(filePath, payload) {
  const tmp = `${filePath}.${process.pid}.tmp`;
  await fs.writeFile(tmp, `${JSON.stringify(payload, null, 2)}\n`, { encoding: "utf-8", mode: 0o600 });
  await fs.chmod(tmp, 0o600).catch(() => {});
  await fs.rename(tmp, filePath);
  await fs.chmod(filePath, 0o600).catch(() => {});
}

if (IS_CLI) {
  main().catch((error) => {
    console.error(error.message);
    process.exitCode = 1;
  });
}

export {
  assertPrivateOutputDir,
  assertPrivateProfileDir,
  chromeUserDataDir,
  hasPrivatePathSegment,
  classifyMyBetsPage,
  captureDiagnosticsFileName,
  isAllowedLoginBootstrapRequest,
  isBlockedMyBetsRequest,
  openReadOnlyContext,
  validateMyBetsText,
};
