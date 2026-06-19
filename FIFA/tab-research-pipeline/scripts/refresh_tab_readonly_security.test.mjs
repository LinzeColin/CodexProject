#!/usr/bin/env node

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import {
  CANONICAL_OUTPUT_DIR,
  assertReadOnlyWagerUnchanged,
  assertStagingOutputDir,
  isForbiddenHeaderTargetClass,
  isBlockedRequest,
  sanitizePayload,
  validatePayload,
} from "./refresh_tab_readonly.mjs";

await testBlockedRequests();
await testPayloadSanitizer();
await testPayloadValidation();
await testReadOnlyWagerGuard();
await testReadOnlyHeaderTargetGuard();
await testCanonicalOutputRealpathGuard();

console.log("OK: refresh_tab_readonly security tests passed");

async function testBlockedRequests() {
  assert.equal(isBlockedRequest("POST", "https://www.tab.com.au/sports/betting/Soccer"), true);
  assert.equal(isBlockedRequest("GET", "https://www.tab.com.au/accounts/profile"), true);
  assert.equal(isBlockedRequest("GET", "https://www.tab.com.au/sports/betting/Soccer/competitions/2026"), false);
}

async function testPayloadSanitizer() {
  const sanitized = sanitizePayload({
    text: "Markets\nMy Bets 9\nBet Slip 0\nResult",
    nested: { label: "Pending Bets\nWorld Cup" },
    links: [
      { text: "Account", href: "https://www.tab.com.au/accounts/profile" },
      { text: "My Bets\nMexico v South Africa", href: "https://www.tab.com.au/sports/betting/Soccer" },
    ],
  });
  const serialized = JSON.stringify(sanitized);
  assert.equal(sanitized.links.length, 1);
  assert.match(sanitized.links[0].text, /Mexico v South Africa/);
  assert.doesNotMatch(serialized, /My Bets|Bet Slip|Pending Bets|\/accounts\//i);
}

async function testPayloadValidation() {
  assert.throws(
    () => validatePayload({ board: "2026 World Cup Futures", mode: "page_text" }, { title: "Access Denied", text: "" }, true),
    /Access Denied/
  );
  assert.throws(
    () => validatePayload({ board: "2026 World Cup Matches", mode: "match_details" }, { matches: [] }, true),
    /did not capture any matches/
  );
  assert.throws(
    () => validatePayload(
      { board: "2026 World Cup Matches", mode: "match_details" },
      { matches: [{ match: "A v B", markets: {}, errors: [] }] },
      true
    ),
    /priced market sections/
  );
  assert.doesNotThrow(() => validatePayload(
    { board: "2026 World Cup Matches", mode: "match_details" },
    { matches: [{ match: "A v B", markets: { Result: "Result\nA\n2.00" }, errors: [] }] },
    true
  ));
  assert.doesNotThrow(() => validatePayload(
    { board: "2026 World Cup Futures", mode: "page_text" },
    { title: "OK", text: "Winner ".repeat(40) },
    true
  ));
  const collapsedFutures = {
    title: "2026 World Cup Futures Betting & Odds 2026 - TAB.com.au",
    text: [
      "Home",
      "Soccer",
      "2026 World Cup Futures",
      "2026 World Cup Futures - Betting Odds",
      "TAB public market navigation ".repeat(45),
      "2026 World Cup",
      "102 Markets",
      "2026 World Cup WinnerMon 20 Jul 5:00Bet live",
      "Australia",
      "401.00",
      "Spain",
      "5.50",
      "France",
      "5.50",
      "Portugal",
      "8.50",
      "England",
      "9.00",
      "Brazil",
      "10.00",
      "Argentina",
      "11.00",
      "Germany",
      "15.00",
      "Netherlands",
      "17.00",
      "Norway",
      "34.00",
      "Belgium",
      "41.00",
      "Colombia",
      "41.00",
      "Japan",
      "41.00",
      "Morocco",
      "51.00",
      "Mexico",
      "51.00",
      "USA",
      "67.00",
      "Switzerland",
      "67.00",
      "Show All Selections",
      "Top Goal Scorer",
    ].join("\n"),
  };
  assert.throws(() => validatePayload(
    { board: "2026 World Cup Futures", mode: "page_text" },
    collapsedFutures,
    false
  ), /winner_selections=17/);
  assert.equal(collapsedFutures.futures_market_coverage.partial_winner_market_visible, true);
  assert.equal(collapsedFutures.futures_market_coverage.winner_selection_count, 17);
  const completeFutures = {
    title: "OK",
    text: [
      "2026 World Cup Futures",
      "Winner",
      "2026 World Cup Winner",
      ...[
        "Australia", "Spain", "France", "Portugal", "England", "Brazil", "Argentina", "Germany",
        "Netherlands", "Norway", "Belgium", "Colombia", "Japan", "Morocco", "Mexico", "USA",
        "Switzerland", "Ecuador", "Turkiye", "Uruguay", "Croatia", "Senegal", "Austria", "Sweden",
        "Cote d Ivoire", "Canada", "Korea Republic", "Paraguay", "Scotland", "Egypt", "Algeria",
        "Bosnia Herzegovina", "Czechia", "Ghana", "Congo DR", "Iran", "Iraq", "Tunisia",
        "New Zealand", "Panama", "Qatar", "Saudi Arabia", "South Africa", "Cabo Verde",
        "Uzbekistan", "Jordan", "Curacao", "Haiti",
      ].flatMap((team, index) => [team, `${2 + index}.00`]),
      "Stage of Elimination",
      "Team Tournament Goals O/U",
      "Player Tournament Goals OU",
      "Language:",
      "English",
      "TracksidePromotionsNoticesHelp Center",
      "Click a price to add a bet.",
      "Add more selections to start a multi",
      "This fixture pads the public page text to satisfy the live raw text length guard while keeping only read-only market text.",
      "This fixture pads the public page text to satisfy the live raw text length guard while keeping only read-only market text.",
      "This fixture pads the public page text to satisfy the live raw text length guard while keeping only read-only market text.",
      "This fixture pads the public page text to satisfy the live raw text length guard while keeping only read-only market text.",
    ].join("\n"),
  };
  assert.doesNotThrow(() => validatePayload(
    { board: "2026 World Cup Futures", mode: "page_text" },
    completeFutures,
    false
  ));
  assert.equal(completeFutures.futures_market_coverage.winner_market_complete, true);
  assert.equal(completeFutures.futures_market_coverage.status, "current_detail_markets_visible");
  assert.equal(completeFutures.futures_market_coverage.current_detail_markets_visible, true);
  assert.equal(completeFutures.futures_market_coverage.winner_selection_count, 48);
  assert.equal(
    ["Stage of Elimination", "Team Tournament Goals O/U", "Player Tournament Goals OU"]
      .every((market) => completeFutures.futures_market_coverage.visible_markets.includes(market)),
    true
  );
  assert.throws(
    () => validatePayload(
      { board: "2026 World Cup Futures", mode: "page_text" },
      { title: "OK", text: "2026 World Cup Futures\nWinner\nAustralia\n401.00" },
      false
    ),
    /text is too short|missing futures core table markers/
  );
}

async function testReadOnlyWagerGuard() {
  assert.doesNotThrow(() => assertReadOnlyWagerUnchanged(
    { count: 0, emptyPrompt: true, hasSelectionDetail: false },
    { count: 0, emptyPrompt: true, hasSelectionDetail: false },
    "Result"
  ));
  assert.throws(
    () => assertReadOnlyWagerUnchanged(
      { count: 0, emptyPrompt: true, hasSelectionDetail: false },
      { count: 1, emptyPrompt: false, hasSelectionDetail: true },
      "Result"
    ),
    /read-only expansion changed wager selection count/
  );
}

async function testReadOnlyHeaderTargetGuard() {
  assert.equal(isForbiddenHeaderTargetClass("template-header collapsed"), false);
  assert.equal(isForbiddenHeaderTargetClass("accordion-header"), false);
  assert.equal(isForbiddenHeaderTargetClass("price-button runner-selection"), true);
  assert.equal(isForbiddenHeaderTargetClass("betslip proposition"), true);
}

async function testCanonicalOutputRealpathGuard() {
  await assert.rejects(
    () => assertStagingOutputDir(CANONICAL_OUTPUT_DIR),
    /refuses to write directly to canonical outputs/
  );
  await assert.rejects(
    () => assertStagingOutputDir(path.join(CANONICAL_OUTPUT_DIR, "nested")),
    /refuses to write directly to canonical outputs/
  );

  const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "tab-fifa-refresh-security-"));
  try {
    const staging = path.join(tmp, "staging");
    await fs.mkdir(staging);
    await assert.doesNotReject(() => assertStagingOutputDir(staging));

    const symlink = path.join(tmp, "outputs-link");
    await fs.symlink(CANONICAL_OUTPUT_DIR, symlink, "dir");
    await assert.rejects(
      () => assertStagingOutputDir(symlink),
      /refuses to write directly to canonical outputs/
    );
  } finally {
    await fs.rm(tmp, { recursive: true, force: true });
  }
}
