#!/usr/bin/env node

import fs from "node:fs/promises";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

import { BOARDS, isBlockedRequest, sanitizePayload } from "./refresh_tab_readonly.mjs";

const NODE_MODULE_HINT =
  process.env.TAB_FIFA_NODE_MODULES ||
  "/Users/linzezhang/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules";
const require = createRequire(import.meta.url);
let chromiumModule = null;
const IS_CLI = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);
const SOCCER_URL = "https://www.tab.com.au/sports/betting/Soccer";
const OUTPUT_NAME = "tab_fifa_live_board_discovery_raw_latest.json";

function parseArgs(argv) {
  const args = {
    outputDir: "",
    outputDirExplicit: false,
    dryRun: false,
    timeoutMs: 45000,
  };
  for (let idx = 2; idx < argv.length; idx += 1) {
    const arg = argv[idx];
    if (arg === "--dry-run") args.dryRun = true;
    else if (arg === "--output-dir") {
      args.outputDir = path.resolve(argv[++idx]);
      args.outputDirExplicit = true;
    } else if (arg === "--timeout-ms") args.timeoutMs = Number(argv[++idx]);
    else throw new Error(`unknown argument: ${arg}`);
  }
  return args;
}

function headlessMode() {
  return true;
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

async function main() {
  const args = parseArgs(process.argv);
  const expectedBoards = expectedBoardRows([]);
  const summary = {
    generated_at: new Date().toISOString(),
    source: "playwright_read_only_tab_soccer_live_nav",
    url: SOCCER_URL,
    dry_run: args.dryRun,
    headless: headlessMode(),
    output_dir: args.outputDir,
    output: args.outputDir ? path.join(args.outputDir, OUTPUT_NAME) : OUTPUT_NAME,
    expected_boards: expectedBoards,
  };
  if (args.dryRun) {
    console.log(JSON.stringify(summary, null, 2));
    return;
  }
  if (!args.outputDirExplicit) {
    throw new Error("live board discovery requires an explicit --output-dir");
  }
  const browser = await loadChromium().launch({
    executablePath: chromeExecutablePath(),
    headless: headlessMode(),
    args: ["--disable-gpu", "--no-first-run", "--no-default-browser-check"],
  });
  try {
    const context = await browser.newContext({
      viewport: { width: 1440, height: 1400 },
      locale: "en-AU",
      serviceWorkers: "block",
    });
    await context.route("**/*", async (route) => {
      const request = route.request();
      if (isBlockedRequest(request.method(), request.url())) {
        await route.abort();
        return;
      }
      await route.continue();
    });
    const page = await context.newPage();
    await page.goto(SOCCER_URL, { waitUntil: "domcontentloaded", timeout: args.timeoutMs });
    await page.waitForLoadState("networkidle", { timeout: Math.min(args.timeoutMs, 6000) }).catch(() => {});
    await page.waitForFunction(
      () => /Soccer - Betting Odds|2026 World Cup|Competitions/i.test(document.body?.innerText || ""),
      { timeout: Math.min(args.timeoutMs, 12000) }
    ).catch(() => {});
    await page.waitForTimeout(2500);
    const live = await page.evaluate((url) => {
      const links = Array.from(document.querySelectorAll("a[href]")).map((node) => ({
        text: (node.textContent || "").trim(),
        href: node.href,
      }));
      return {
        generated_at: new Date().toISOString(),
        source: "playwright_read_only_tab_soccer_live_nav",
        url,
        landed_url: window.location.href,
        title: document.title,
        text: document.body ? document.body.innerText : "",
        links,
      };
    }, SOCCER_URL);
    const payload = buildPayload(live, args);
    await fs.mkdir(args.outputDir, { recursive: true });
    const outputPath = path.join(args.outputDir, OUTPUT_NAME);
    await atomicWriteJson(outputPath, payload);
    console.log(JSON.stringify({
      ...summary,
      output: outputPath,
      expected_boards: payload.expected_boards,
      listed_expected_count: payload.summary.listed_expected_count,
      missing_expected_count: payload.summary.missing_expected_count,
      observed_world_cup_link_count: payload.summary.observed_world_cup_link_count,
    }, null, 2));
  } finally {
    await browser.close().catch(() => {});
  }
}

function buildPayload(live, args) {
  const sanitized = sanitizePayload(live);
  const links = (sanitized.links || []).filter((link) => link.href && !isBlockedRequest("GET", link.href));
  const text = sanitized.text || "";
  const markers = pageMarkers(sanitized, links, text);
  const quality = discoveryQuality(markers, sanitized, text);
  const observed = observedWorldCupLinks(links, text);
  const expected = expectedBoardRows(links, text, quality.discoveryReady);
  const listed = expected.filter((row) => row.live_nav_status === "listed").length;
  return sanitizePayload({
    generated_at: sanitized.generated_at,
    source: sanitized.source,
    url: sanitized.url,
    landed_url: sanitized.landed_url,
    title: sanitized.title,
    headless: headlessMode(),
    timeout_ms: args.timeoutMs,
    page_markers: markers,
    expected_boards: expected,
    observed_world_cup_links: observed,
    summary: {
      expected_board_count: expected.length,
      listed_expected_count: listed,
      missing_expected_count: expected.length - listed,
      observed_world_cup_link_count: observed.length,
      discovery_ready: quality.discoveryReady,
      quality_status: quality.status,
      quality_issues: quality.issues,
      access_denied: quality.accessDenied,
      full_expected_nav_ready: listed === expected.length,
    },
    truthfulness_note: "本文件只反映 TAB Soccer live 导航中可见的公开链接；缺失板块不得用旧盘口生成下注建议。",
  });
}

function pageMarkers(sanitized, links, text) {
  return {
    text_length: text.length,
    link_count: links.length,
    has_soccer: /Soccer - Betting Odds|Home\s+Soccer/i.test(text) || /Soccer Betting/i.test(sanitized.title || ""),
    has_world_cup: /2026 World Cup|World Cup Group|WC26|SWC/i.test(text),
    access_denied: /Access Denied/i.test(`${sanitized.title || ""}\n${text}`),
  };
}

function discoveryQuality(markers, sanitized, text) {
  const issues = [];
  const accessDenied = Boolean(markers.access_denied);
  if (accessDenied) issues.push("access_denied");
  if (!markers.has_soccer) issues.push("soccer_page_marker_missing");
  if (markers.link_count === 0) issues.push("link_count_zero");
  const discoveryReady = !accessDenied && Boolean(markers.has_soccer) && markers.link_count > 0;
  return {
    discoveryReady,
    accessDenied,
    status: discoveryReady ? "ready" : accessDenied ? "blocked_access_denied" : "blocked_low_quality_page",
    issues,
  };
}

function expectedBoardRows(links, text = "", discoveryReady = true) {
  return Object.entries(BOARDS).map(([refreshBoardId, config]) => {
    const matches = links.filter((link) => linkMatchesBoard(link, config));
    const textListed = normalizedTextHasBoard(text, config.board);
    const listed = matches.length > 0 || textListed;
    if (!discoveryReady) {
      return {
        refresh_board_id: refreshBoardId,
        board: config.board,
        expected_url: config.url,
        live_nav_status: "discovery_blocked",
        matched_link_count: matches.length,
        matched_text_marker: textListed,
        matched_links: matchedLinksForBoard(refreshBoardId, matches),
        automation_decision: "discovery_retry_required",
      };
    }
    return {
      refresh_board_id: refreshBoardId,
      board: config.board,
      expected_url: config.url,
      live_nav_status: listed ? "listed" : "missing_from_live_nav",
      matched_link_count: matches.length,
      matched_text_marker: textListed,
      matched_links: matchedLinksForBoard(refreshBoardId, matches),
      automation_decision: listed ? "refresh_allowed" : "temporarily_unavailable_review",
    };
  });
}

function matchedLinksForBoard(refreshBoardId, matches) {
  const limit = refreshBoardId === "matches" ? 80 : 5;
  return matches.slice(0, limit).map((link) => ({
    text: link.text,
    href: link.href,
  }));
}

function observedWorldCupLinks(links, text = "") {
  const seen = new Set();
  const rows = [];
  for (const link of links) {
    const label = compactWhitespace(link.text || "");
    const href = link.href || "";
    if (!/World Cup|WC26|SWC/i.test(`${label} ${href}`)) continue;
    const key = `${label}|${href}`;
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push({ text: label, href });
  }
  for (const label of observedWorldCupTextMarkers(text)) {
    const key = `${label}|page_text`;
    if (seen.has(key)) continue;
    seen.add(key);
    rows.push({ text: label, href: "" });
  }
  return rows.slice(0, 80);
}

function observedWorldCupTextMarkers(text) {
  const lines = String(text || "")
    .split(/\r?\n/)
    .map((line) => compactWhitespace(line))
    .filter((line) => /2026 World Cup|World Cup Group|WC26|SWC/i.test(line));
  return Array.from(new Set(lines)).slice(0, 40);
}

function linkMatchesBoard(link, config) {
  const label = normalize(link.text || "");
  const href = normalize(decodeURIComponent(link.href || ""));
  const board = normalize(config.board);
  const expected = normalize(decodeURIComponent(config.url));
  return label.includes(board) || href.includes(expected) || href.includes(board);
}

function normalizedTextHasBoard(text, board) {
  return normalize(text).includes(normalize(board));
}

function normalize(value) {
  return compactWhitespace(String(value || "")).toLowerCase();
}

function compactWhitespace(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

async function atomicWriteJson(outputPath, payload) {
  const tmpPath = `${outputPath}.${process.pid}.tmp`;
  await fs.writeFile(tmpPath, JSON.stringify(payload, null, 2), { encoding: "utf8", mode: 0o600 });
  await fs.rename(tmpPath, outputPath);
}

export {
  expectedBoardRows,
  matchedLinksForBoard,
};

if (IS_CLI) {
  main().catch((error) => {
    console.error(JSON.stringify({ error: error.message }, null, 2));
    process.exit(1);
  });
}
