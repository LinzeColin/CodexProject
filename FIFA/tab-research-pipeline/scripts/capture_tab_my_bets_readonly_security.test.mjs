#!/usr/bin/env node

import assert from "node:assert/strict";
import fs from "node:fs/promises";
import os from "node:os";
import path from "node:path";

import {
  assertPrivateOutputDir,
  assertPrivateProfileDir,
  chromeUserDataDir,
  classifyMyBetsPage,
  captureDiagnosticsFileName,
  hasPrivatePathSegment,
  isAllowedLoginBootstrapRequest,
  isBlockedMyBetsRequest,
  validateMyBetsText,
} from "./capture_tab_my_bets_readonly.mjs";

assert.equal(isBlockedMyBetsRequest("POST", "https://www.tab.com.au/accounts/my-bets/bets"), true);
assert.equal(isBlockedMyBetsRequest("GET", "https://www.tab.com.au/betslip"), true);
assert.equal(isBlockedMyBetsRequest("GET", "https://www.tab.com.au/accounts/profile"), true);
assert.equal(isBlockedMyBetsRequest("GET", "https://www.tab.com.au/accounts/my-bets/bets"), false);
assert.equal(isBlockedMyBetsRequest("GET", "https://api.beta.tab.com.au/accounts/bets?status=PENDING"), false);
assert.equal(isBlockedMyBetsRequest("GET", "https://api.beta.tab.com.au/accounts/bet-history"), false);
assert.equal(isBlockedMyBetsRequest("GET", "https://api.beta.tab.com.au/accounts/balance"), true);
assert.equal(isAllowedLoginBootstrapRequest("POST", "https://login.tab.com.au/oauth/authorize"), true);
assert.equal(isBlockedMyBetsRequest("POST", "https://login.tab.com.au/oauth/authorize"), true);
assert.equal(isBlockedMyBetsRequest("POST", "https://login.tab.com.au/oauth/authorize", { allowLoginBootstrap: true }), false);
assert.equal(isBlockedMyBetsRequest("POST", "https://www.tab.com.au/betslip/add-selection", { allowLoginBootstrap: true }), true);
assert.equal(isBlockedMyBetsRequest("POST", "https://www.tab.com.au/accounts/profile", { allowLoginBootstrap: true }), true);
assert.equal(isBlockedMyBetsRequest("POST", "https://evil.example/oauth/authorize", { allowLoginBootstrap: true }), true);

assert.equal(validateMyBetsText("Login\nSign in").ready, false);
assert.equal(
  validateMyBetsText("", "https://login.tab.com.au/login?state=secret-oauth-state").reason,
  "TAB My Bets page appears unauthenticated",
);
assert.equal(validateMyBetsText("My Bets\nPending\nStake\n$100.00\nEstimated Return\n$108.00").ready, true);
assert.equal(
  classifyMyBetsPage("", "https://login.tab.com.au/login?state=secret-oauth-state").finalUrlPublic,
  "https://login.tab.com.au/login",
);
assert.equal(
  validateMyBetsText("Reference #18", "https://www.tab.com.au/accounts/my-bets/bets", "Access Denied").authStatus,
  "access_denied",
);
assert.equal(captureDiagnosticsFileName("01012026"), "tab_my_bets_capture_diagnostics_01012026.json");
assert.equal(path.basename(chromeUserDataDir()), path.basename(process.env.TAB_FIFA_CHROME_USER_DATA_DIR || "tab_chrome_profile"));
assert.equal(chromeUserDataDir("/tmp/private/custom-profile"), "/tmp/private/custom-profile");
assert.equal(hasPrivatePathSegment("/private/tmp/public"), false);
assert.equal(hasPrivatePathSegment("/private/tmp/example/private/tab_fifa"), true);
assert.equal(hasPrivatePathSegment("/Users/example/work/private/tab_fifa"), true);

const tmp = await fs.mkdtemp(path.join(os.tmpdir(), "tab-fifa-my-bets-private-"));
try {
  const privateDir = path.join(tmp, "private", "tab_fifa");
  const profileDir = path.join(tmp, "private", "tab_profile");
  await fs.mkdir(privateDir, { recursive: true });
  await assert.doesNotReject(() => assertPrivateOutputDir(privateDir));
  await assert.doesNotReject(() => assertPrivateProfileDir(profileDir));
  await assert.rejects(() => assertPrivateOutputDir(path.join(tmp, "public")), /private path/);
  await assert.rejects(() => assertPrivateProfileDir(path.join(tmp, "public_profile")), /private path/);
} finally {
  await fs.rm(tmp, { recursive: true, force: true });
}

console.log("OK: capture_tab_my_bets_readonly security tests passed");
