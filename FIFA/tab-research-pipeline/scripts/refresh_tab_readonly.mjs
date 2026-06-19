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
let chromiumModule = null;
const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const WORKSPACE_ROOT = resolveWorkspaceRoot(SCRIPT_DIR);
const CANONICAL_OUTPUT_DIR = path.resolve(process.env.TAB_FIFA_OUTPUT_DIR || path.join(WORKSPACE_ROOT, "outputs"));
const IS_CLI = process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url);

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

const BOARDS = {
  matches: {
    board: "2026 World Cup Matches",
    url: "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Matches",
    output: "tab_fifa_matches_main_markets_raw_v0_9.json",
    mode: "match_details",
  },
  futures: {
    board: "2026 World Cup Futures",
    url: "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Futures",
    output: "tab_fifa_world_cup_futures_raw_v0_13.json",
    mode: "page_text",
  },
  group_betting: {
    board: "2026 World Cup Group Betting",
    url: "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Group%20Betting",
    output: "tab_fifa_world_cup_group_betting_raw_v0_14.json",
    mode: "page_text",
  },
  australia_markets: {
    board: "2026 World Cup Australia Markets",
    url: "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Australia%20Markets",
    output: "tab_fifa_world_cup_australia_markets_expanded_raw_v0_17.json",
    mode: "australia_expanded",
  },
  team_futures_multi: {
    board: "2026 World Cup Team Futures Multi",
    url: "https://www.tab.com.au/sports/betting/Soccer/competitions/2026%20World%20Cup%20Team%20Futures%20Multi",
    output: "tab_fifa_world_cup_team_futures_multi_raw_v0_16.json",
    mode: "page_text",
  },
};

function envKeyForBoardUrl(boardId) {
  return `TAB_FIFA_BOARD_URL_${String(boardId || "").toUpperCase()}`;
}

function boardUrl(boardId, config) {
  return process.env[envKeyForBoardUrl(boardId)] || config.url;
}

const EXPECTED_MATCHES = [
  "Mexico v South Africa",
  "South Korea v Czechia",
  "Canada v Bosn-Herzegovina",
  "USA v Paraguay",
  "Qatar v Switzerland",
  "Brazil v Morocco",
  "Haiti v Scotland",
  "Australia v Turkiye",
  "Germany v Curacao",
  "Netherlands v Japan",
  "Cote d Ivoire v Ecuador",
  "Sweden v Tunisia",
  "Spain v Cabo Verde",
  "Belgium v Egypt",
  "Saudi Arabia v Uruguay",
  "Iran v New Zealand",
  "France v Senegal",
  "Iraq v Norway",
  "Argentina v Algeria",
  "Austria v Jordan",
  "Portugal v DR Congo",
  "England v Croatia",
  "Ghana v Panama",
  "Uzbekistan v Colombia",
  "USA v Australia",
  "Paraguay v Australia",
];

const MARKET_BOUNDARIES = [
  "Result",
  "Double Chance",
  "Handicap",
  "Correct Score",
  "Total Goals Over/Under",
  "Both Teams to Score",
  "Result Over/Under Double",
  "Draw No Bet",
  "Half/Full Double",
  "1st Half Result",
  "Team To Score",
  "Goals",
  "Margin",
  "Doubles",
  "Correct Score",
  "Half",
  "Team",
  "Others",
  "Language:",
];

const CORE_MARKETS = [
  "Result",
  "Double Chance",
  "Handicap",
  "Total Goals Over/Under",
  "Both Teams to Score",
  "Draw No Bet",
];
const FUTURES_EXPECTED_TEAM_COUNT = 48;
const FUTURES_DETAIL_MARKETS = [
  "Stage of Elimination",
  "Team Tournament Goals O/U",
  "Player Tournament Goals OU",
];

const AUSTRALIA_MARKET_IDS = [
  "team_group_match_wins",
  "team_to_win_a_group_match",
  "team_to_win_all_3_group_matches",
  "team_total_group_goals_scored_o_u",
  "team_total_group_goals_scored_exact",
  "aus_score_in_every_group_match",
  "team_total_group_goals_conceded_o_u",
  "aus_concede_in_every_group_match",
  "aus_group_exact_finishing_position",
  "aus_group_point_o_u",
  "aus_exact_group_points",
  "to_score_a_goal_in_tournament",
  "team_total_goals_scored_bands",
  "top_australian_goalscorer",
];
const AUSTRALIA_BOARD_MARKERS = [
  /2026 World Cup Australia Markets/i,
  /\bAustralia Markets\b/i,
  /\bAUS Group\b/i,
  /Top Australian Goalscorer/i,
];
const AUSTRALIA_ROUTE_FALLBACK_MARKERS = [
  /2026 World Cup Matches/i,
  /World Cup Matches - Betting Odds/i,
];
const PUBLIC_RAW_REMOVE_LINE_PATTERNS = [
  /Active Session/i,
  /My Bets/i,
  /Bet Slip/i,
  /Pending Bets/i,
  /My Offers/i,
  /Account/i,
  /\/accounts\//i,
];

function headlessMode() {
  return true;
}

function parseArgs(argv) {
  const args = {
    board: "all",
    outputDir: "",
    outputDirExplicit: false,
    dryRun: false,
    smoke: false,
    limit: 0,
    offset: 0,
    match: "",
    refreshId: "",
    timeoutMs: 45000,
  };
  for (let idx = 2; idx < argv.length; idx += 1) {
    const arg = argv[idx];
    if (arg === "--dry-run") args.dryRun = true;
    else if (arg === "--smoke") args.smoke = true;
    else if (arg === "--board") args.board = argv[++idx];
    else if (arg === "--output-dir") {
      args.outputDir = path.resolve(argv[++idx]);
      args.outputDirExplicit = true;
    }
    else if (arg === "--limit") args.limit = Number(argv[++idx]);
    else if (arg === "--offset") args.offset = Number(argv[++idx]);
    else if (arg === "--match") args.match = argv[++idx];
    else if (arg === "--refresh-id") args.refreshId = argv[++idx];
    else if (arg === "--timeout-ms") args.timeoutMs = Number(argv[++idx]);
    else throw new Error(`unknown argument: ${arg}`);
  }
  return args;
}

function selectedBoards(name) {
  if (name === "all") return Object.entries(BOARDS);
  if (!BOARDS[name]) throw new Error(`unknown board: ${name}`);
  return [[name, BOARDS[name]]];
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

async function captureBoard(page, boardId, config, timeoutMs) {
  if (config.mode === "match_details") return captureMatches(page, boardId, config, timeoutMs);
  if (config.mode === "australia_expanded") return captureAustraliaMarkets(page, boardId, config, timeoutMs);
  return capturePageText(page, boardId, config, timeoutMs);
}

async function capturePageText(page, boardId, config, timeoutMs) {
  const url = boardUrl(boardId, config);
  await gotoReadOnly(page, url, timeoutMs);
  await waitBrieflyForNetwork(page, timeoutMs);
  await page.waitForTimeout(2500);
  const pageTextCaptureNotes = [];
  if (isWorldCupFuturesBoard(config.board)) {
    const detail = await navigateToFuturesDetailIfAvailable(page, url, timeoutMs);
    pageTextCaptureNotes.push(detail);
    const expansion = await expandFuturesWinnerSelections(page);
    pageTextCaptureNotes.push(expansion);
    const detailExpansions = await expandFuturesDetailMarkets(page);
    pageTextCaptureNotes.push(...detailExpansions);
  }
  const payload = await page.evaluate(({ board, url }) => {
    const links = Array.from(document.querySelectorAll("a[href]")).map((node) => ({
      text: (node.textContent || "").trim(),
      href: node.href,
    }));
    return {
      generated_at: new Date().toISOString(),
      source: "playwright_read_only_public_tab_page",
      board,
      url,
      title: document.title,
      text: document.body ? document.body.innerText : "",
      links,
    };
  }, { board: config.board, url });
  if (pageTextCaptureNotes.length) {
    payload.capture_notes = pageTextCaptureNotes;
    payload.landed_url = await page.evaluate(() => window.location.href).catch(() => "");
  }
  if (isWorldCupFuturesBoard(config.board)) {
    payload.futures_market_coverage = futuresMarketCoverage(payload.text || "");
  }
  return { boardId, output: config.output, payload };
}

async function navigateToFuturesDetailIfAvailable(page, sourceUrl, timeoutMs) {
  const beforeState = await readOnlyWagerState(page);
  const href = await page.evaluate(() => {
    const links = Array.from(document.querySelectorAll("a[href]"));
    const match = links.find((node) => /\/sports\/betting\/Soccer\/competitions\/2026%20World%20Cup%20Futures\/matches\/2026%20World%20Cup/i.test(node.href || ""));
    return match ? match.href : "";
  }).catch(() => "");
  const target = href || `${String(sourceUrl || "").replace(/\/$/, "")}/matches/2026%20World%20Cup`;
  if (!target || /\/matches\/2026%20World%20Cup/i.test(page.url())) {
    return { action: "futures_detail_navigation", attempted: false, reason: "already_on_detail_or_no_target" };
  }
  await gotoReadOnly(page, target, timeoutMs);
  await waitBrieflyForNetwork(page, timeoutMs);
  await waitForFuturesWinnerSelections(page, FUTURES_EXPECTED_TEAM_COUNT, Math.min(timeoutMs, 10000));
  assertReadOnlyWagerUnchanged(beforeState, await readOnlyWagerState(page), "Futures detail navigation");
  return {
    action: "futures_detail_navigation",
    attempted: true,
    target_host: routeHost(target),
    landed_url_path: await page.evaluate(() => window.location.pathname).catch(() => ""),
  };
}

async function expandFuturesWinnerSelections(page) {
  const beforeState = await readOnlyWagerState(page);
  const before = futuresMarketCoverage(await page.evaluate(() => document.body ? document.body.innerText || "" : "").catch(() => ""));
  if (before.winner_selection_count >= FUTURES_EXPECTED_TEAM_COUNT) {
    return {
      action: "futures_show_all_selections",
      attempted: false,
      reason: "winner_selection_count_already_complete",
      before_count: before.winner_selection_count,
    };
  }
  const attempt = await dispatchReadOnlyHeaderActivation(page, "Show All Selections");
  if (!attempt.found || attempt.forbidden || !attempt.dispatched) {
    return {
      action: "futures_show_all_selections",
      attempted: Boolean(attempt.found),
      expanded: false,
      before_count: before.winner_selection_count,
      reason: attempt.reason || (attempt.forbidden ? "forbidden_target" : "show_all_selection_not_found"),
    };
  }
  await page.waitForTimeout(1800);
  await waitForFuturesWinnerSelections(page, FUTURES_EXPECTED_TEAM_COUNT, 6000);
  assertReadOnlyWagerUnchanged(beforeState, await readOnlyWagerState(page), "Futures Show All Selections");
  const after = futuresMarketCoverage(await page.evaluate(() => document.body ? document.body.innerText || "" : "").catch(() => ""));
  return {
    action: "futures_show_all_selections",
    attempted: true,
    expanded: after.winner_selection_count > before.winner_selection_count,
    before_count: before.winner_selection_count,
    after_count: after.winner_selection_count,
    target_class: attempt.target_class,
    target_tag: attempt.target_tag,
  };
}

async function expandFuturesDetailMarkets(page) {
  const notes = [];
  for (const market of FUTURES_DETAIL_MARKETS) {
    const beforeState = await readOnlyWagerState(page);
    const beforeText = await page.evaluate(() => document.body ? document.body.innerText || "" : "").catch(() => "");
    const beforeLength = beforeText.length;
    const attempt = await dispatchReadOnlyHeaderActivation(page, market);
    if (!attempt.found || attempt.forbidden || !attempt.dispatched) {
      notes.push({
        action: "futures_detail_market_expansion",
        market,
        attempted: Boolean(attempt.found),
        expanded: false,
        before_text_length: beforeLength,
        reason: attempt.reason || (attempt.forbidden ? "forbidden_target" : "market_header_not_found"),
        target_class: attempt.target_class || "",
        target_tag: attempt.target_tag || "",
      });
      continue;
    }
    await page.waitForTimeout(1400);
    assertReadOnlyWagerUnchanged(beforeState, await readOnlyWagerState(page), `Futures ${market}`);
    const afterText = await page.evaluate(() => document.body ? document.body.innerText || "" : "").catch(() => "");
    notes.push({
      action: "futures_detail_market_expansion",
      market,
      attempted: true,
      expanded: afterText.length > beforeLength,
      before_text_length: beforeLength,
      after_text_length: afterText.length,
      target_class: attempt.target_class,
      target_tag: attempt.target_tag,
    });
  }
  return notes;
}

async function waitForFuturesWinnerSelections(page, minCount, timeoutMs) {
  const deadline = Date.now() + Math.max(1000, timeoutMs);
  let latest = futuresMarketCoverage(await page.evaluate(() => document.body ? document.body.innerText || "" : "").catch(() => ""));
  while (Date.now() < deadline && latest.winner_selection_count < minCount) {
    await page.waitForTimeout(500);
    latest = futuresMarketCoverage(await page.evaluate(() => document.body ? document.body.innerText || "" : "").catch(() => ""));
  }
  return latest;
}

async function captureMatches(page, boardId, config, timeoutMs, limit = 0, matchFilter = "", offset = 0) {
  const matches = [];
  const start = Math.max(0, offset);
  const liveTargets = liveMatchTargetsFromEnv();
  const baseTargets = liveTargets.length
    ? liveTargets
    : EXPECTED_MATCHES.map((match) => ({ match, href: "" }));
  const filteredTargets = matchFilter
    ? baseTargets.filter((target) => target.match === matchFilter)
    : baseTargets;
  const targetMatches = limit > 0 ? filteredTargets.slice(start, start + limit) : filteredTargets.slice(start);
  if (matchFilter && !targetMatches.length) throw new Error(`unknown match: ${matchFilter}`);
  for (const target of targetMatches) {
    matches.push(await captureMatchWithRetry(page, config, target, timeoutMs));
  }
  return {
    boardId,
    output: config.output,
    payload: {
      generated_at: new Date().toISOString(),
      source: "playwright_read_only_match_detail",
      scope: "2026 World Cup Matches main markets",
      count: matches.length,
      target_source: liveTargets.length ? "live_board_discovery" : "configured_expected_matches",
      available_match_count: baseTargets.length,
      target_matches: baseTargets.map((target) => target.match),
      matches,
    },
  };
}

async function captureMatchWithRetry(page, config, target, timeoutMs) {
  let lastError = null;
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const record = await captureSingleMatch(page, config, target, timeoutMs);
      if (attempt > 1) record.navigation_retry_count = attempt - 1;
      return record;
    } catch (error) {
      lastError = error;
      await page.waitForTimeout(1200 * attempt);
    }
  }
  throw new Error(`match detail navigation failed for ${target.match} after 3 attempts: ${lastError?.message || String(lastError)}`);
}

async function captureSingleMatch(page, config, target, timeoutMs) {
  const match = target.match;
  const href = target.href || `${boardUrl("matches", config)}/matches/${encodeURIComponent(match)}`;
  await gotoReadOnly(page, href, timeoutMs);
  await waitBrieflyForNetwork(page, timeoutMs);
  await page.waitForTimeout(1200);
  const initialDetail = await page.evaluate(() => ({
    title: document.title,
    text: document.body ? document.body.innerText : "",
  }));
  if (isAccessDenied(initialDetail.title, initialDetail.text)) {
    return {
      match,
      href,
      title: initialDetail.title,
      markets: {},
      expansion_attempts: [],
      errors: [`Access Denied while loading match detail for ${match}`],
      scrape_note: "playwright_read_only_match_detail",
      partial_core_only: true,
      market_availability: "access_denied",
      access_status: "access_denied",
      target_source: target.href ? "live_board_discovery" : "configured_expected_matches",
    };
  }
  const expansionAttempts = await expandMatchCoreMarkets(page);
  const detail = await page.evaluate(() => ({
    title: document.title,
    text: document.body ? document.body.innerText : "",
  }));
  const accessDenied = isAccessDenied(detail.title, detail.text);
  const sections = extractMarketSections(detail.text);
  const hasFullCore = CORE_MARKETS.every((name) => Object.prototype.hasOwnProperty.call(sections, name));
  const sectionNames = Object.keys(sections);
  const record = {
    match,
    href,
    title: detail.title,
    markets: sections,
    expansion_attempts: expansionAttempts,
    errors: expansionAttempts
      .filter((attempt) => attempt.error)
      .map((attempt) => `Market header expansion failed for ${attempt.market}: ${attempt.error}`),
    scrape_note: "playwright_read_only_match_detail",
    partial_core_only: !hasFullCore,
    access_status: accessDenied ? "access_denied" : "ok",
    target_source: target.href ? "live_board_discovery" : "configured_expected_matches",
  };
  if (accessDenied) {
    record.access_denied = true;
    record.errors.push(`Access Denied while loading match detail for ${match}`);
  }
  if (!hasFullCore) {
    record.market_availability = sectionNames.length === 1 && sectionNames[0] === "Result" ? "tab_only_result" : "partial_core";
  }
  return record;
}

function liveMatchTargetsFromEnv() {
  const raw = process.env.TAB_FIFA_MATCH_TARGETS_JSON || "";
  if (!raw.trim()) return [];
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    return [];
  }
  if (!Array.isArray(parsed)) return [];
  const seen = new Set();
  const targets = [];
  for (const item of parsed) {
    const match = compactWhitespace(String(item?.match || ""));
    const href = String(item?.href || "").trim();
    if (!isUsableMatchHref(href) || !/ v /.test(match)) continue;
    const key = `${match}|${href}`;
    if (seen.has(key)) continue;
    seen.add(key);
    targets.push({ match, href });
  }
  return targets;
}

function isUsableMatchHref(href) {
  return /^https:\/\/www\.tab\.com\.au\/sports\/betting\/Soccer\/competitions\/2026%20World%20Cup%20Matches\/matches\//i.test(String(href || ""));
}

function compactWhitespace(value) {
  return String(value || "").replace(/\s+/g, " ").trim();
}

async function expandMatchCoreMarkets(page) {
  const attempts = [];
  for (const name of ["Double Chance", "Handicap", "Total Goals Over/Under", "Both Teams to Score", "Draw No Bet"]) {
    const attempt = await safeReadOnlyHeaderClick(page, name).catch((error) => ({
      market: name,
      attempted: true,
      expanded: false,
      error: error.message || String(error),
    }));
    attempts.push(attempt);
    await page.waitForTimeout(250);
  }
  await page.waitForTimeout(1500);
  return attempts;
}

async function safeReadOnlyHeaderClick(page, name) {
  const beforeState = await readOnlyWagerState(page);
  const dispatch = await dispatchReadOnlyHeaderActivation(page, name);
  if (!dispatch.found) {
    return {
      market: name,
      attempted: false,
      expanded: false,
      missing: true,
      reason: dispatch.reason || "safe visible header target not found",
      locator_count: dispatch.locator_count || 0,
    };
  }
  if (dispatch.forbidden || isForbiddenHeaderTargetClass(dispatch.target_class)) {
    throw new Error(`refused to click non-header betting target for ${name}: ${dispatch.target_class}`);
  }
  if (!dispatch.dispatched) {
    throw new Error(`safe header dispatch failed for ${name}: ${dispatch.reason || "unknown"}`);
  }
  await page.waitForTimeout(150);
  assertReadOnlyWagerUnchanged(beforeState, await readOnlyWagerState(page), name);
  return {
    market: name,
    attempted: true,
    expanded: true,
    fallback: "visible_dom_dispatch",
    target_class: dispatch.target_class,
    target_tag: dispatch.target_tag,
  };
}

async function dispatchReadOnlyHeaderActivation(page, name) {
  return page.evaluate((marketName) => {
    const forbiddenPattern = /price|selection|runner|bet|betslip|proposition/i;
    const normalize = (value) => String(value || "").replace(/\s+/g, " ").trim();
    const visible = (node) => {
      if (!node || !node.getBoundingClientRect) return false;
      const style = window.getComputedStyle(node);
      if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity || 1) === 0) return false;
      const rect = node.getBoundingClientRect();
      return rect.width > 0 && rect.height > 0;
    };
    const targetFor = (node) => node.closest("button,a,[role='button'],[data-testid],.template-header,[class*='header']") || node;
    const walker = document.createTreeWalker(document.body || document.documentElement, NodeFilter.SHOW_TEXT);
    let locatorCount = 0;
    let candidate = null;
    while (walker.nextNode()) {
      const textNode = walker.currentNode;
      if (normalize(textNode.nodeValue) !== marketName) continue;
      locatorCount += 1;
      const element = textNode.parentElement;
      const target = targetFor(element);
      if (!visible(target)) continue;
      const targetClass = String(target.className || target.getAttribute("data-testid") || "");
      const targetText = normalize(target.textContent);
      if (forbiddenPattern.test(targetClass)) {
        return {
          found: true,
          forbidden: true,
          dispatched: false,
          target_class: targetClass,
          target_tag: target.tagName,
          target_text: targetText,
          locator_count: locatorCount,
        };
      }
      candidate = { target, targetClass, targetText };
      break;
    }
    if (!candidate) {
      return {
        found: false,
        dispatched: false,
        locator_count: locatorCount,
        reason: locatorCount ? "only hidden or unsafe exact text targets found" : "exact market text not found",
      };
    }
    candidate.target.scrollIntoView({ block: "center" });
    for (const type of ["mousedown", "mouseup", "click"]) {
      candidate.target.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
    }
    return {
      found: true,
      forbidden: false,
      dispatched: true,
      target_class: candidate.targetClass,
      target_tag: candidate.target.tagName,
      target_text: candidate.targetText,
      locator_count: locatorCount,
    };
  }, name);
}

function isForbiddenHeaderTargetClass(value) {
  return /price|selection|runner|bet|betslip|proposition/i.test(String(value || ""));
}

async function readOnlyWagerState(page) {
  return page.evaluate(() => {
    const text = document.body ? document.body.innerText || "" : "";
    const slipMatch = text.match(/Bet Slip\s*(\d{1,3})/i);
    const count = slipMatch ? Number(slipMatch[1]) : null;
    return {
      count: Number.isFinite(count) ? count : null,
      emptyPrompt: /Click a price to add a bet|Add more selections to start a multi/i.test(text),
      hasSelectionDetail: /Estimated Return|Remove Selection|Stake\s*\$/i.test(text),
    };
  }).catch(() => ({ count: null, emptyPrompt: false, hasSelectionDetail: false }));
}

function assertReadOnlyWagerUnchanged(before, after, marketName) {
  if (before.count !== null && after.count !== null && before.count !== after.count) {
    throw new Error(`read-only expansion changed wager selection count for ${marketName}: ${before.count} -> ${after.count}`);
  }
  if (before.emptyPrompt && !after.emptyPrompt) {
    throw new Error(`read-only expansion removed empty wager prompt for ${marketName}`);
  }
  if (!before.hasSelectionDetail && after.hasSelectionDetail) {
    throw new Error(`read-only expansion created wager selection detail for ${marketName}`);
  }
  if ((before.count === 0 || before.count === null) && after.count !== null && after.count > 0) {
    throw new Error(`read-only expansion created wager selections for ${marketName}: ${after.count}`);
  }
}

async function captureAustraliaMarkets(page, boardId, config, timeoutMs) {
  const url = boardUrl(boardId, config);
  await gotoReadOnly(page, url, timeoutMs);
  await waitBrieflyForNetwork(page, timeoutMs);
  await page.waitForTimeout(2500);
  const wagerStateBefore = await readOnlyWagerState(page);
  const before = await page.evaluate((ids) => ids.map((id) => {
    const root = document.getElementById(id);
    return {
      id,
      className: root ? String(root.className || "") : "",
      text: root ? root.innerText || "" : "",
    };
  }), AUSTRALIA_MARKET_IDS);
  await page.evaluate((ids) => {
    for (const id of ids) {
      const root = document.getElementById(id);
      if (!root) continue;
      const header = root.querySelector(".template-header") || root.querySelector("[class*='header']") || root;
      if (!header || !String(root.className || "").includes("collapsed")) continue;
      header.scrollIntoView({ block: "center" });
      for (const type of ["mousedown", "mouseup", "click"]) {
        header.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
      }
    }
  }, AUSTRALIA_MARKET_IDS);
  await page.waitForTimeout(3500);
  assertReadOnlyWagerUnchanged(wagerStateBefore, await readOnlyWagerState(page), config.board);
  const after = await page.evaluate((ids) => ids.map((id) => {
    const root = document.getElementById(id);
    return {
      id,
      className: root ? String(root.className || "") : "",
      text: root ? root.innerText || "" : "",
    };
  }), AUSTRALIA_MARKET_IDS);
  const byId = new Map(before.map((block) => [block.id, block]));
  const markets = after.map((block) => ({
    id: block.id,
    beforeClass: byId.get(block.id)?.className || "",
    beforeText: byId.get(block.id)?.text || "",
    afterClass: block.className,
    afterText: block.text,
    ok: Boolean(block.text && block.text.length > 0),
  }));
  const payload = await page.evaluate(({ board, url, markets }) => ({
    board,
    url,
    landed_url: window.location.href,
    title: document.title,
    captured_at: new Date().toISOString(),
    expansion_method: "playwright_read_only_header_dispatch",
    market_ids: markets.map((market) => market.id),
    markets,
    text: document.body ? document.body.innerText : "",
  }), { board: config.board, url, markets });
  const missingMarketIds = markets
    .filter((market) => !market.beforeClass && !market.beforeText && !market.afterClass && !market.afterText)
    .map((market) => market.id);
  payload.missing_market_ids = missingMarketIds;
  if (isAustraliaMarketsRouteMismatch(payload)) {
    payload.route_status = "route_mismatch_to_matches";
    payload.route_error = `${config.board} route mismatch: landed on 2026 World Cup Matches; TAB live soccer nav may not list this board`;
  } else {
    payload.route_status = "ok";
  }
  return { boardId, output: config.output, payload };
}

function extractMarketSections(text) {
  const lines = text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
  const starts = [];
  for (let index = 0; index < lines.length; index += 1) {
    if (MARKET_BOUNDARIES.includes(lines[index])) starts.push([index, lines[index]]);
  }
  const sections = {};
  for (let pos = 0; pos < starts.length; pos += 1) {
    const [start, name] = starts[pos];
    if (!CORE_MARKETS.includes(name) || Object.prototype.hasOwnProperty.call(sections, name)) continue;
    let end = lines.length;
    for (const [nextStart, nextName] of starts.slice(pos + 1)) {
      if (nextStart > start && MARKET_BOUNDARIES.includes(nextName)) {
        end = nextStart;
        break;
      }
    }
    const value = lines.slice(start, end).join("\n").trim();
    if (value.split(/\r?\n/).length > 2) sections[name] = value;
  }
  return sections;
}

async function atomicWriteJson(outputPath, payload) {
  const tmpPath = `${outputPath}.${process.pid}.tmp`;
  await fs.writeFile(tmpPath, JSON.stringify(payload, null, 2), { encoding: "utf8", mode: 0o600 });
  await fs.rename(tmpPath, outputPath);
}

async function waitBrieflyForNetwork(page, timeoutMs) {
  await page.waitForLoadState("networkidle", { timeout: Math.min(timeoutMs, 6000) }).catch(() => {});
}

async function gotoReadOnly(page, url, timeoutMs) {
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: timeoutMs });
    return { strategy: "domcontentloaded" };
  } catch (error) {
    const firstError = error.message || String(error);
    await page.goto(url, { waitUntil: "commit", timeout: Math.max(timeoutMs, 45000) });
    return { strategy: "commit_after_domcontentloaded_timeout", first_error: firstError };
  }
}

async function main() {
  const args = parseArgs(process.argv);
  const targets = selectedBoards(args.board);
  const refreshId = args.refreshId || `manual-${new Date().toISOString().replace(/[:.]/g, "")}`;
  const summary = {
    generated_at: new Date().toISOString(),
    refresh_id: refreshId,
    dry_run: args.dryRun,
    smoke: args.smoke,
    limit: args.limit,
    offset: args.offset,
    match: args.match,
    headless: headlessMode(),
    output_dir: args.outputDir,
    node_module_hint: NODE_MODULE_HINT,
    executable_path: chromeExecutablePath(),
    boards: targets.map(([boardId, config]) => ({
      board_id: boardId,
      board: config.board,
      url: boardUrl(boardId, config),
      output: path.join(args.outputDir, config.output),
    })),
  };
  if (args.dryRun) {
    console.log(JSON.stringify(summary, null, 2));
    return;
  }
  if (!args.outputDirExplicit) {
    throw new Error("live raw refresh requires an explicit --output-dir staging directory");
  }
  await assertStagingOutputDir(args.outputDir);

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
    await fs.mkdir(args.outputDir, { recursive: true });
    const capturedResults = [];
    for (const [boardId, config] of targets) {
      const result = config.mode === "match_details"
        ? await captureMatches(page, boardId, config, args.timeoutMs, args.limit, args.match, args.offset)
        : await captureBoard(page, boardId, config, args.timeoutMs);
      result.payload.refresh_id = refreshId;
      result.payload = sanitizePayload(result.payload);
      const outputPath = path.join(args.outputDir, result.output);
      validatePayload(config, result.payload, args.smoke);
      capturedResults.push({ result, outputPath });
    }
    const results = [];
    for (const { result, outputPath } of capturedResults) {
      await atomicWriteJson(outputPath, result.payload);
      results.push({
        board_id: result.boardId,
        output: outputPath,
        text_length: result.payload.text?.length || 0,
        match_count: result.payload.matches?.length || 0,
        market_count: countCapturedMarkets(result.payload),
        error_count: countPayloadErrors(result.payload),
        link_count: result.payload.links?.length || 0,
      });
    }
    console.log(JSON.stringify({ ...summary, results }, null, 2));
  } finally {
    await browser.close().catch(() => {});
  }
}

async function assertStagingOutputDir(outputDir) {
  const resolved = path.resolve(outputDir);
  const canonical = await realpathClosest(CANONICAL_OUTPUT_DIR);
  const outputReal = await realpathClosest(resolved);
  if (
    isSameOrChildPath(resolved, CANONICAL_OUTPUT_DIR)
    || isSameOrChildPath(outputReal, canonical)
    || await pathUsesSymlinkToCanonical(resolved, CANONICAL_OUTPUT_DIR)
  ) {
    throw new Error("live raw refresh refuses to write directly to canonical outputs; use a staging directory");
  }
}

async function pathUsesSymlinkToCanonical(candidate, canonicalDir) {
  const resolved = path.resolve(candidate);
  const segments = path.relative(path.parse(resolved).root, resolved).split(path.sep).filter(Boolean);
  let current = path.parse(resolved).root;
  for (const segment of segments) {
    current = path.join(current, segment);
    let stat;
    try {
      stat = await fs.lstat(current);
    } catch {
      continue;
    }
    if (!stat.isSymbolicLink()) continue;
    const target = await fs.readlink(current);
    const targetResolved = path.resolve(path.dirname(current), target);
    if (isSameOrChildPath(targetResolved, canonicalDir)) return true;
  }
  return false;
}

async function realpathClosest(candidate) {
  let current = path.resolve(candidate);
  const suffix = [];
  while (true) {
    try {
      const real = await fs.realpath(current);
      return path.join(real, ...suffix);
    } catch (error) {
      if (error.code !== "ENOENT") return current;
      const parent = path.dirname(current);
      if (parent === current) return path.resolve(candidate);
      suffix.unshift(path.basename(current));
      current = parent;
    }
  }
}

function isSameOrChildPath(candidate, parent) {
  const relative = path.relative(path.resolve(parent), path.resolve(candidate));
  return relative === "" || (!!relative && !relative.startsWith("..") && !path.isAbsolute(relative));
}

function countCapturedMarkets(payload) {
  if (Array.isArray(payload.markets)) return payload.markets.length;
  if (Array.isArray(payload.matches)) {
    return payload.matches.reduce((count, match) => count + Object.keys(match.markets || {}).length, 0);
  }
  return 0;
}

function countPayloadErrors(payload) {
  if (Array.isArray(payload.matches)) {
    return payload.matches.reduce((count, match) => count + (match.errors || []).length, 0);
  }
  if (Array.isArray(payload.markets)) {
    return payload.markets.filter((market) => !market.ok).length;
  }
  return 0;
}

function validatePayload(config, payload, smoke = false) {
  const text = payload.text || "";
  const title = payload.title || "";
  if (isAccessDenied(title, text)) {
    throw new Error(`${config.board} refresh returned Access Denied`);
  }
  if (config.mode === "page_text") {
    if (smoke) {
      if (text.length < 200) throw new Error(`${config.board} smoke text is too short: ${text.length}`);
      return;
    }
    if (text.length < 1000) throw new Error(`${config.board} text is too short: ${text.length}`);
    if (isWorldCupFuturesBoard(config.board)) {
      const coverage = payload.futures_market_coverage || futuresMarketCoverage(text);
      payload.futures_market_coverage = coverage;
      if (!coverage.page_ready) {
        throw new Error(
          `${config.board} missing futures core table markers: ` +
          `status=${coverage.status}; winner_selections=${coverage.winner_selection_count}; ` +
          `markers=${coverage.visible_markets.join(",") || "none"}`
        );
      }
    }
    if (config.board.includes("Group Betting") && (!text.includes("World Cup Group A") || !text.includes("WC26 Group"))) {
      throw new Error(`${config.board} missing group betting markers`);
    }
    if (config.board.includes("Team Futures Multi") && (!text.includes("2026 SWC Futures Multi") || !text.includes("Reach Quarter Final"))) {
      throw new Error(`${config.board} missing team futures multi markers`);
    }
  }
  if (config.mode === "australia_expanded") {
    if (isAustraliaMarketsRouteMismatch(payload)) {
      throw new Error(
        payload.route_error ||
        `${config.board} route mismatch: landed on 2026 World Cup Matches; TAB live soccer nav may not list this board`
      );
    }
    const markets = payload.markets || [];
    if (smoke) {
      if (!markets.length) throw new Error(`${config.board} smoke did not capture market blocks`);
      return;
    }
    if (markets.length !== AUSTRALIA_MARKET_IDS.length) {
      throw new Error(`${config.board} market count ${markets.length} did not match expected ${AUSTRALIA_MARKET_IDS.length}`);
    }
    const incomplete = markets.filter((market) => !market.ok || !/\n\d+(\.\d+)?/.test(market.afterText || ""));
    if (incomplete.length) throw new Error(`${config.board} has ${incomplete.length} incomplete expanded markets`);
  }
  if (config.mode === "match_details") {
    const matches = payload.matches || [];
    const denied = matches.filter((match) => match.access_denied || match.access_status === "access_denied" || isAccessDenied(match.title || "", match.text || ""));
    if (denied.length) {
      throw new Error(`${config.board} match detail returned Access Denied for ${denied.map((match) => match.match || "unknown").join(", ")}`);
    }
    if (smoke) {
      if (!matches.length) throw new Error(`${config.board} smoke did not capture any matches`);
      const priced = matches.filter((match) => Object.keys(match.markets || {}).length > 0);
      if (!priced.length) {
        const first = matches[0] || {};
        throw new Error(
          `${config.board} smoke did not capture any priced market sections; ` +
          `first_match=${first.match || "unknown"} title=${first.title || "unknown"} ` +
          `access_status=${first.access_status || "unknown"} availability=${first.market_availability || "unknown"}`
        );
      }
      return;
    }
    const expectedCount = payload.count || EXPECTED_MATCHES.length;
    if (matches.length !== expectedCount) throw new Error(`${config.board} match count ${matches.length} did not match expected ${expectedCount}`);
    const fullCore = matches.filter((match) => !match.partial_core_only).length;
    const errorCount = matches.reduce((count, match) => count + (match.errors || []).length, 0);
    if (errorCount > 0) throw new Error(`${config.board} has ${errorCount} market expansion errors`);
    const threshold = Math.max(1, Math.floor(matches.length * 0.90));
    if (fullCore < threshold) throw new Error(`${config.board} full core coverage ${fullCore}/${matches.length} below threshold`);
  }
}

function isWorldCupFuturesBoard(board) {
  return String(board || "").includes("Futures") && !String(board || "").includes("Multi");
}

function futuresMarketCoverage(text) {
  const lines = String(text || "").split(/\r?\n/).map((line) => compactWhitespace(line)).filter(Boolean);
  const combined = lines.join("\n");
  const visibleMarkets = [];
  if (/Winner/i.test(combined)) visibleMarkets.push("Winner");
  if (/To Qualify for Final/i.test(combined)) visibleMarkets.push("To Qualify for Final");
  if (/To Qualify For Semi Final/i.test(combined)) visibleMarkets.push("To Qualify For Semi Final");
  if (/To Qualify for Quarter Final/i.test(combined)) visibleMarkets.push("To Qualify for Quarter Final");
  if (/Top Goal Scorer/i.test(combined)) visibleMarkets.push("Top Goal Scorer");
  if (/Reach Round of 16/i.test(combined)) visibleMarkets.push("Reach Round of 16");
  for (const market of FUTURES_DETAIL_MARKETS) {
    if (combined.includes(market)) visibleMarkets.push(market);
  }
  const legacyCoreVisible = (
    visibleMarkets.includes("Winner") &&
    visibleMarkets.includes("To Qualify for Final") &&
    visibleMarkets.includes("To Qualify For Semi Final") &&
    visibleMarkets.includes("To Qualify for Quarter Final")
  );
  const currentDetailVisible = FUTURES_DETAIL_MARKETS.every((market) => visibleMarkets.includes(market));
  const winnerSelections = extractFuturesWinnerSelections(lines);
  const titleReady = /2026 World Cup Futures/i.test(combined);
  const winnerMarketVisible = titleReady && winnerSelections.length >= 12;
  const winnerMarketComplete = titleReady && winnerSelections.length >= FUTURES_EXPECTED_TEAM_COUNT;
  return {
    status: legacyCoreVisible
      ? "legacy_core_table_visible"
      : winnerMarketComplete && currentDetailVisible
        ? "current_detail_markets_visible"
        : winnerMarketComplete
          ? "winner_market_complete"
          : winnerMarketVisible
            ? "winner_market_partial"
            : "insufficient_futures_markers",
    page_ready: legacyCoreVisible || winnerMarketComplete,
    full_core_markets_visible: legacyCoreVisible,
    current_detail_markets_visible: currentDetailVisible,
    partial_winner_market_visible: winnerMarketVisible && !winnerMarketComplete && !legacyCoreVisible,
    winner_market_complete: winnerMarketComplete,
    visible_markets: visibleMarkets,
    winner_selection_count: winnerSelections.length,
    expected_winner_selection_count: FUTURES_EXPECTED_TEAM_COUNT,
    winner_selection_preview: winnerSelections.slice(0, 12),
    coverage_note: legacyCoreVisible
      ? "Legacy four-column Futures core table is visible."
      : winnerMarketComplete && currentDetailVisible
        ? "TAB currently exposes the Futures detail page with a complete 48-team Winner market and current detail markets for Stage of Elimination, Team Tournament Goals O/U, and Player Tournament Goals OU."
        : winnerMarketComplete
          ? "TAB currently exposes the Futures detail page with a complete 48-team Winner market; downstream full automation gate remains blocked until non-Winner futures markets are parsed or explicitly marked unavailable."
      : winnerMarketVisible
        ? "TAB currently exposes a partial Futures Winner market; capture must navigate to the detail page or expand Show All Selections before the raw snapshot is safe."
        : "Futures page did not expose enough World Cup winner selections for a safe research snapshot.",
  };
}

function routeHost(href) {
  try {
    return new URL(href).host;
  } catch (_error) {
    return String(href || "").slice(0, 80);
  }
}

function extractFuturesWinnerSelections(lines) {
  const start = lines.findIndex((line) => /2026 World Cup Winner/i.test(line));
  if (start < 0) return [];
  const end = lines.findIndex((line, index) =>
    index > start &&
    (/^Show All Selections$/i.test(line) ||
      /^Top Goal Scorer$/i.test(line) ||
      /^Reach Round of 16$/i.test(line) ||
      /^Stage of Elimination$/i.test(line) ||
      /^Team Tournament Goals O\/U$/i.test(line) ||
      /^Language:$/i.test(line))
  );
  const tokens = lines.slice(start + 1, end > start ? end : lines.length);
  const selections = [];
  for (let index = 0; index < tokens.length - 1; index += 1) {
    const name = tokens[index];
    const odds = tokens[index + 1];
    if (!isDecimalPrice(name) && isDecimalPrice(odds)) {
      selections.push({ selection: name, odds: Number(odds) });
      index += 1;
    }
  }
  return selections;
}

function isDecimalPrice(value) {
  const text = String(value || "").trim();
  if (!/^\d+(?:\.\d{1,2})?$/.test(text)) return false;
  const price = Number(text);
  return Number.isFinite(price) && price >= 1.01 && price <= 10000;
}

function isAustraliaMarketsRouteMismatch(payload) {
  const text = String(payload?.text || "");
  const title = String(payload?.title || "");
  const combined = `${title}\n${text}`;
  const hasAustraliaBoardMarker = AUSTRALIA_BOARD_MARKERS.some((pattern) => pattern.test(combined));
  const looksLikeMatchesBoard = AUSTRALIA_ROUTE_FALLBACK_MARKERS.some((pattern) => pattern.test(combined));
  const markets = Array.isArray(payload?.markets) ? payload.markets : [];
  const hasAnyDomMarket = markets.some((market) =>
    Boolean(market.beforeClass || market.beforeText || market.afterClass || market.afterText)
  );
  return !hasAustraliaBoardMarker && looksLikeMatchesBoard && !hasAnyDomMarket;
}

function isAccessDenied(title, text) {
  return /Access Denied/i.test(String(title || "")) || /Access Denied/i.test(String(text || ""));
}

function isBlockedRequest(method, url) {
  const upperMethod = method.toUpperCase();
  if (["POST", "PUT", "PATCH", "DELETE"].includes(upperMethod)) return true;
  return /\/accounts\/|betslip|bet-slip|placebet|place-bet|addselection|add-selection/i.test(url);
}

function sanitizePayload(payload) {
  const cleaned = sanitizeValue(payload);
  if (Array.isArray(payload?.links) && Array.isArray(cleaned.links)) {
    cleaned.links = payload.links
      .filter((link) => !isBlockedRequest("GET", link.href || ""))
      .map((link) => sanitizeValue({ ...link, text: sanitizeText(link.text || "") }));
  }
  return cleaned;
}

function sanitizeValue(value) {
  if (typeof value === "string") return sanitizeText(value);
  if (Array.isArray(value)) return value.map((item) => sanitizeValue(item));
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, child]) => [key, sanitizeValue(child)])
    );
  }
  return value;
}

function sanitizeText(text) {
  return String(text || "")
    .split(/\r?\n/)
    .filter((line) => !PUBLIC_RAW_REMOVE_LINE_PATTERNS.some((pattern) => pattern.test(line)))
    .join("\n");
}

export {
  BOARDS,
  CANONICAL_OUTPUT_DIR,
  assertReadOnlyWagerUnchanged,
  assertStagingOutputDir,
  isAccessDenied,
  isAustraliaMarketsRouteMismatch,
  isBlockedRequest,
  isForbiddenHeaderTargetClass,
  isUsableMatchHref,
  liveMatchTargetsFromEnv,
  sanitizePayload,
  sanitizeText,
  validatePayload,
};

if (IS_CLI) {
  main().catch((error) => {
    console.error(JSON.stringify({ error: error.message }, null, 2));
    process.exit(1);
  });
}
