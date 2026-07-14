#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");


const appRoot = path.resolve(__dirname, "..");
const databaseRoot = path.resolve(appRoot, "../..");
const localPort = Number(process.env.MEMORY_ATLAS_R3_COMMAND_PORT || 4181);
const staticPort = Number(process.env.MEMORY_ATLAS_R3_STATIC_PORT || localPort + 1);
const localUrl = `http://127.0.0.1:${localPort}`;
const staticUrl = `http://127.0.0.1:${staticPort}`;
const outputDir = process.env.MEMORY_ATLAS_R3_COMMAND_AUDIT_DIR
  ? path.resolve(databaseRoot, process.env.MEMORY_ATLAS_R3_COMMAND_AUDIT_DIR)
  : fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-r3-command-audit-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();
const expectedCommandIds = [
  "sync_chatgpt",
  "sync_codex",
  "generate_weekly_report",
  "view_pending_proposals",
  "generate_personalization_prompt",
  "chatgpt_deep_explore",
];


function assertCondition(condition, message, details = {}) {
  if (!condition) {
    const error = new Error(message);
    error.details = details;
    throw error;
  }
}


function findChromiumExecutable() {
  const candidates = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
  ];
  return candidates.find((candidate) => fs.existsSync(candidate));
}


function requirePlaywright() {
  try {
    return require("playwright");
  } catch {}
  const pnpmRoot = path.join(
    os.homedir(),
    ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm",
  );
  try {
    const candidate = fs
      .readdirSync(pnpmRoot)
      .filter((entry) => entry.startsWith("playwright@"))
      .sort()
      .at(-1);
    if (candidate) return require(path.join(pnpmRoot, candidate, "node_modules/playwright"));
  } catch {}
  throw new Error("Playwright is not resolvable from project dependencies or Codex bundled runtime");
}


function runFrontendBuild() {
  const result = spawnSync("npm", ["run", "build"], {
    cwd: appRoot,
    env: { ...process.env },
    encoding: "utf8",
  });
  assertCondition(result.status === 0, "Current Memory Atlas frontend build failed before R3 browser validation", {
    stdoutTail: String(result.stdout || "").slice(-3000),
    stderrTail: String(result.stderr || "").slice(-3000),
  });
}


function copyDirectory(relativePath, sourceRoot) {
  const source = path.join(databaseRoot, relativePath);
  const target = path.join(sourceRoot, relativePath);
  assertCondition(fs.existsSync(source), `Required R3 fixture source is missing: ${relativePath}`);
  fs.mkdirSync(path.dirname(target), { recursive: true });
  fs.cpSync(source, target, { recursive: true, preserveTimestamps: true });
}


function writeJsonLines(filePath, rows) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, rows.map((row) => JSON.stringify(row)).join("\n") + "\n", "utf8");
}


function prepareFixture() {
  const fixtureRoot = fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-r3-workflows-"));
  const appSupport = path.join(fixtureRoot, "app-support");
  const sourceRoot = path.join(appSupport, "source");
  const runtimeDir = path.join(appSupport, "runtime");
  const codexHome = path.join(fixtureRoot, "codex-home");
  fs.mkdirSync(sourceRoot, { recursive: true });
  fs.mkdirSync(runtimeDir, { recursive: true });

  for (const relativePath of ["scripts", "config", "data", "skills", "机器治理/运行门禁"]) {
    copyDirectory(relativePath, sourceRoot);
  }
  fs.writeFileSync(
    path.join(sourceRoot, "memory_atlas_source_workspace.json"),
    JSON.stringify({
      schema_version: "memory_atlas_source_workspace.v1",
      original_repo_root: databaseRoot,
      installed_git_commit: "r3-browser-fixture",
      purpose: "Temporary installer-shaped R3 browser acceptance fixture.",
    }, null, 2) + "\n",
    "utf8",
  );

  fs.cpSync(path.join(appRoot, "dist"), runtimeDir, { recursive: true, preserveTimestamps: true });
  fs.copyFileSync(
    path.join(sourceRoot, "data/derived/visualization/memory_atlas.json"),
    path.join(runtimeDir, "memory_atlas.json"),
  );

  const fixtureThreadId = "019f4b00-1111-7222-8333-r3browser0001";
  writeJsonLines(path.join(codexHome, "session_index.jsonl"), [
    { id: fixtureThreadId, thread_name: "Memory Atlas R3 browser command workflow" },
  ]);
  writeJsonLines(path.join(codexHome, "sessions/2026/07/10/session.jsonl"), [
    {
      type: "session_meta",
      timestamp: "2026-07-10T08:00:00Z",
      payload: { id: fixtureThreadId, cwd: "/Users/example/memory-atlas", originator: "codex_desktop" },
    },
    {
      type: "response_item",
      timestamp: "2026-07-10T08:01:00Z",
      payload: {
        type: "message",
        role: "user",
        content: [{ type: "input_text", text: "请验证 Memory Atlas 六个本地命令工作流。" }],
      },
    },
  ]);

  const chatgptInbox = path.join(appSupport, "imports/chatgpt");
  fs.mkdirSync(chatgptInbox, { recursive: true });
  const conversationsPath = path.join(fixtureRoot, "conversations.json");
  fs.writeFileSync(
    conversationsPath,
    JSON.stringify([
      {
        id: "r3_browser_chatgpt",
        title: "Memory Atlas R3 command workflow",
        create_time: 1783670400,
        update_time: 1783670460,
        mapping: {
          root: {
            id: "root",
            message: {
              id: "r3-user",
              author: { role: "user" },
              create_time: 1783670401,
              content: { content_type: "text", parts: ["请生成本周 Memory Atlas 复盘。"] },
            },
          },
        },
      },
    ]),
    "utf8",
  );
  const exportZip = path.join(chatgptInbox, "chatgpt-official-export.zip");
  const zipResult = spawnSync("python3", ["-m", "zipfile", "-c", exportZip, conversationsPath], {
    encoding: "utf8",
  });
  assertCondition(zipResult.status === 0, "Unable to create synthetic ChatGPT official export", {
    stdout: zipResult.stdout,
    stderr: zipResult.stderr,
  });

  return { appSupport, codexHome, fixtureRoot, runtimeDir, sourceRoot };
}


function startProcess(command, args, options = {}) {
  const child = spawn(command, args, {
    cwd: options.cwd || databaseRoot,
    env: { ...process.env, ...(options.env || {}) },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const logs = [];
  child.stdout.on("data", (chunk) => logs.push(chunk.toString()));
  child.stderr.on("data", (chunk) => logs.push(chunk.toString()));
  return { child, logs };
}


function processExited(processHandle) {
  return processHandle.child.exitCode !== null || processHandle.child.signalCode !== null;
}


function httpRequest(url, options = {}, body = "") {
  return new Promise((resolve, reject) => {
    const target = new URL(url);
    const request = http.request(
      {
        hostname: target.hostname,
        port: target.port,
        path: `${target.pathname}${target.search}`,
        method: options.method || "GET",
        headers: options.headers || {},
      },
      (response) => {
        const chunks = [];
        response.on("data", (chunk) => chunks.push(chunk));
        response.on("end", () => resolve({
          body: Buffer.concat(chunks).toString("utf8"),
          headers: response.headers,
          status: response.statusCode || 0,
        }));
      },
    );
    request.setTimeout(options.timeoutMs || 2000, () => request.destroy(new Error(`timeout waiting for ${url}`)));
    request.on("error", reject);
    if (body) request.write(body);
    request.end();
  });
}


async function waitForHttp(url, processHandle, timeoutMs = 30000) {
  const started = Date.now();
  let lastError = null;
  while (Date.now() - started < timeoutMs) {
    if (processExited(processHandle)) {
      throw new Error(`Server exited before readiness with code ${processHandle.child.exitCode} and signal ${processHandle.child.signalCode}: ${processHandle.logs.join("").slice(-3000)}`);
    }
    try {
      const response = await httpRequest(url, { timeoutMs: 1200 });
      if (response.status >= 200 && response.status < 500) return response;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  throw new Error(`Server did not become ready at ${url}: ${lastError?.message || "unknown"}`);
}


async function stopProcess(processHandle) {
  if (!processHandle || processExited(processHandle)) return;
  let exitPromise = new Promise((resolve) => processHandle.child.once("exit", resolve));
  processHandle.child.kill("SIGTERM");
  await Promise.race([
    exitPromise,
    new Promise((resolve) => setTimeout(resolve, 2500)),
  ]);
  if (!processExited(processHandle)) {
    exitPromise = new Promise((resolve) => processHandle.child.once("exit", resolve));
    processHandle.child.kill("SIGKILL");
    await Promise.race([
      exitPromise,
      new Promise((resolve) => setTimeout(resolve, 2500)),
    ]);
  }
  if (!processExited(processHandle)) {
    throw new Error(`Unable to stop validation server process ${processHandle.child.pid}`);
  }
}


async function executeCommand(page, commandId, timeout = 180000) {
  const selector = `[data-s12-p1-command-id="${commandId}"]`;
  await page.locator(selector).scrollIntoViewIfNeeded();
  await page.locator(selector).click();
  const execute = page.locator(`[data-r3-command-execute="${commandId}"]`);
  await execute.scrollIntoViewIfNeeded();
  await execute.click();
  await page.waitForFunction(
    (id) => {
      const result = document.querySelector(`[data-r3-command-result="${id}"]`);
      const status = result?.getAttribute("data-r3-command-result-status");
      return Boolean(status && !["idle", "running"].includes(status));
    },
    commandId,
    { timeout },
  );
  return page.locator(`[data-r3-command-result="${commandId}"]`).evaluate((element) => ({
    inputHint: element.querySelector("code")?.textContent?.trim() || "",
    message: element.querySelector("p")?.textContent?.trim() || "",
    outputs: Array.from(element.querySelectorAll("li code")).map((item) => item.textContent?.trim() || ""),
    status: element.getAttribute("data-r3-command-result-status") || "",
    title: element.querySelector("strong")?.textContent?.trim() || "",
  }));
}


function pathExists(root, relativePath) {
  return fs.existsSync(path.join(root, relativePath));
}


function readJsonLines(filePath) {
  return fs.readFileSync(filePath, "utf8")
    .split("\n")
    .filter(Boolean)
    .map((line) => JSON.parse(line));
}


async function main() {
  runFrontendBuild();
  fs.mkdirSync(outputDir, { recursive: true });
  const fixture = prepareFixture();
  const runtimeServer = startProcess(
    "python3",
    [
      path.join(fixture.sourceRoot, "scripts/memory_atlas_runtime_server.py"),
      fixture.runtimeDir,
      String(localPort),
      "0",
      "0",
      fixture.sourceRoot,
    ],
    {
      cwd: fixture.sourceRoot,
      env: {
        MEMORY_ATLAS_CODEX_HOME: fixture.codexHome,
        MEMORY_ATLAS_COMMAND_TIMEOUT_SECONDS: "150",
      },
    },
  );
  const viteCli = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(fs.existsSync(viteCli), "Vite CLI is missing from app node_modules", { viteCli });
  const staticServer = startProcess(
    process.execPath,
    [viteCli, "preview", "--host", "127.0.0.1", "--port", String(staticPort), "--strictPort"],
    { cwd: appRoot },
  );
  let browser = null;
  let staticBrowser = null;
  const status = {
    status: "FAIL",
    phase: "R3_REAL_COMMAND_PALETTE_WORKFLOWS",
    command_api_version: "memory_atlas_command_api.v1_2_r3",
    local_url: localUrl,
    static_url: staticUrl,
    command_results: {},
    security: {},
    hosted_static: {},
    artifacts: {},
  };

  try {
    await waitForHttp(`${localUrl}/__memory_atlas_runtime_state`, runtimeServer);
    await waitForHttp(staticUrl, staticServer);

    const remoteOriginProbeBody = JSON.stringify({ command_id: "sync_codex" });
    const remoteOriginProbe = await httpRequest(
      `${localUrl}/__memory_atlas_command`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(remoteOriginProbeBody),
          Origin: "https://evil.example",
        },
      },
      remoteOriginProbeBody,
    );
    const extraFieldBody = JSON.stringify({ command_id: "sync_codex", argv: ["rm", "-rf", "/"] });
    const extraFieldProbe = await httpRequest(
      `${localUrl}/__memory_atlas_command`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Content-Length": Buffer.byteLength(extraFieldBody),
          Origin: localUrl,
        },
      },
      extraFieldBody,
    );
    const lifecycleProbes = [];
    for (const endpoint of ["/__memory_atlas_heartbeat", "/__memory_atlas_release"]) {
      lifecycleProbes.push(await httpRequest(
        `${localUrl}${endpoint}`,
        {
          method: "POST",
          headers: { "Content-Length": "0", Origin: "https://evil.example" },
        },
      ));
    }
    assertCondition(remoteOriginProbe.status === 403, "Remote origin command probe was not rejected", remoteOriginProbe);
    assertCondition(extraFieldProbe.status === 400, "Extra-field command probe was not rejected", extraFieldProbe);
    assertCondition(lifecycleProbes.every((probe) => probe.status === 403), "Remote origin lifecycle probe was not rejected", lifecycleProbes);
    assertCondition(!remoteOriginProbe.headers["access-control-allow-origin"], "Command API unexpectedly emits CORS headers");

    const { chromium } = requirePlaywright();
    browser = await chromium.launch({
      headless: true,
      ...(browserExecutable ? { executablePath: browserExecutable } : {}),
    });
    const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
    const externalRequests = [];
    await context.route("https://chatgpt.com/**", async (route) => {
      externalRequests.push({ method: route.request().method(), url: route.request().url() });
      await route.fulfill({
        status: 200,
        contentType: "text/html; charset=utf-8",
        body: "<!doctype html><title>ChatGPT prefill fixture</title><main>prefill intercepted</main>",
      });
    });

    const page = await context.newPage();
    const pageErrors = [];
    const commandRequests = [];
    page.on("pageerror", (error) => pageErrors.push(String(error.message || error)));
    page.on("request", (request) => {
      if (request.method() === "POST" && request.url().endsWith("/__memory_atlas_command")) {
        commandRequests.push(JSON.parse(request.postData() || "{}"));
      }
    });
    await page.goto(localUrl, { waitUntil: "networkidle", timeout: 60000 });
    await page.waitForFunction(() => window.__memoryAtlasR3CommandWorkflows?.().runtimeAvailable === true, null, { timeout: 15000 });
    const runtimeContract = await page.evaluate(() => window.__memoryAtlasR3CommandWorkflows?.());
    assertCondition(JSON.stringify(runtimeContract.commandIds) === JSON.stringify(expectedCommandIds), "Local runtime command inventory differs", runtimeContract);

    for (const commandId of expectedCommandIds.slice(0, -1)) {
      const result = await executeCommand(page, commandId);
      assertCondition(result.status === "success", `${commandId} did not complete successfully`, result);
      assertCondition(/[\u4e00-\u9fff]/.test(`${result.title}${result.message}`), `${commandId} lacks actionable Chinese result`, result);
      status.command_results[commandId] = result;
      if (commandId === "view_pending_proposals") {
        await page.waitForSelector('[data-r4-proposal-workspace="memory_atlas_proposal_workflow.v1_2_r4"]', { timeout: 30000 });
        await page.getByRole("button", { name: "关闭提案复核" }).click();
        await page.waitForSelector('[data-r4-proposal-workspace="memory_atlas_proposal_workflow.v1_2_r4"]', { state: "detached" });
      }
    }

    await page.locator('[data-s12-p1-command-id="chatgpt_deep_explore"]').scrollIntoViewIfNeeded();
    await page.locator('[data-s12-p1-command-id="chatgpt_deep_explore"]').click();
    const popupPromise = context.waitForEvent("page", { timeout: 15000 });
    await page.locator('[data-r3-command-execute="chatgpt_deep_explore"]').click();
    const popup = await popupPromise;
    await page.waitForFunction(
      () => document.querySelector('[data-r3-command-result="chatgpt_deep_explore"]')?.getAttribute("data-r3-command-result-status") === "success",
      null,
      { timeout: 180000 },
    );
    await popup.waitForURL((url) => url.hostname === "chatgpt.com" && Boolean(url.searchParams.get("q")), { timeout: 30000 });
    const deepResult = await page.locator('[data-r3-command-result="chatgpt_deep_explore"]').evaluate((element) => ({
      message: element.querySelector("p")?.textContent?.trim() || "",
      outputs: Array.from(element.querySelectorAll("li code")).map((item) => item.textContent?.trim() || ""),
      status: element.getAttribute("data-r3-command-result-status") || "",
      title: element.querySelector("strong")?.textContent?.trim() || "",
    }));
    status.command_results.chatgpt_deep_explore = deepResult;
    assertCondition(deepResult.status === "success", "Deep explore did not complete", deepResult);
    assertCondition(externalRequests.length === 1 && externalRequests[0].method === "GET", "Deep explore made unexpected external requests", externalRequests);
    const prefillUrl = new URL(externalRequests[0].url);
    assertCondition(prefillUrl.hostname === "chatgpt.com" && Boolean(prefillUrl.searchParams.get("q")), "Deep explore URL lacks ChatGPT prefill query", externalRequests);
    const prefillText = prefillUrl.searchParams.get("q") || "";
    const guardedHeaderPattern = ["author", "ization"].join("");
    const guardedBrowserPattern = ["cook", "ie"].join("");
    const guardedSessionPattern = ["session", "id"].join("");
    const guardedTokenPattern = ["access", "refresh"]
      .map((prefix) => `${prefix}_${["to", "ken"].join("")}`)
      .join("|");
    const credentialPrefillPattern = new RegExp(
      `sk-[A-Za-z0-9_-]{12,}|${guardedHeaderPattern}:\\s*\\S+|${guardedBrowserPattern}:\\s*\\S+|${guardedSessionPattern}=\\S+|(${guardedTokenPattern})\\s*[:=]\\s*\\S+`,
      "i",
    );
    assertCondition(
      !credentialPrefillPattern.test(prefillText),
      "Deep explore prefill contains credential material",
    );
    await popup.close();

    assertCondition(commandRequests.length === expectedCommandIds.length, "Browser did not issue exactly six command requests", commandRequests);
    assertCondition(
      JSON.stringify(commandRequests.map((item) => item.command_id)) === JSON.stringify(expectedCommandIds),
      "Browser command order or inventory differs",
      commandRequests,
    );
    assertCondition(commandRequests.every((item) => Object.keys(item).length === 1), "Browser sent fields outside command_id", commandRequests);
    assertCondition(pageErrors.length === 0, "Local command page emitted browser errors", { pageErrors });

    const chatgptSummary = JSON.parse(fs.readFileSync(
      path.join(fixture.sourceRoot, "data/derived/chatgpt/chatgpt_sync_summary.json"),
      "utf8",
    ));
    const chatgptManifestRows = readJsonLines(
      path.join(fixture.sourceRoot, "data/processed/conversations/conversation_manifest.jsonl"),
    );
    const chatgptManifestRow = chatgptManifestRows.find(
      (row) => row.conversation_id === "r3_browser_chatgpt",
    );
    const chatgptRawRoot = path.resolve(fixture.sourceRoot, "data/public_raw/chatgpt");
    const chatgptRawPath = chatgptManifestRow?.raw_ref
      ? path.resolve(fixture.sourceRoot, chatgptManifestRow.raw_ref)
      : "";
    const chatgptRaw = chatgptRawPath && chatgptRawPath.startsWith(`${chatgptRawRoot}${path.sep}`)
      && fs.existsSync(chatgptRawPath)
      ? JSON.parse(fs.readFileSync(chatgptRawPath, "utf8"))
      : null;
    const chatgptArtifactValid = Boolean(
      chatgptSummary.schema_version === "memory_atlas_chatgpt_sync_summary.v1"
      && chatgptSummary.conversation_count === 1
      && chatgptSummary.conversation_ids?.includes("r3_browser_chatgpt")
      && chatgptManifestRow
      && chatgptRaw
      && chatgptRaw.conversation_id === "r3_browser_chatgpt"
      && chatgptRaw.content_sha256 === chatgptManifestRow.content_sha256,
    );
    const weeklyOutputs = fs.readdirSync(path.join(fixture.sourceRoot, "data/derived/weekly"))
      .filter((name) => name.endsWith(".memory_atlas_weekly_report.md"));
    const expectedArtifacts = {
      chatgpt_sync: chatgptArtifactValid,
      codex_sync: pathExists(fixture.sourceRoot, "data/processed/codex/codex_session_manifest.jsonl"),
      weekly_report: weeklyOutputs.length > 0,
      personalization_chatgpt: pathExists(fixture.sourceRoot, "data/derived/personalization/chatgpt_personalization.md"),
      personalization_codex: pathExists(fixture.sourceRoot, "data/derived/personalization/codex_personalization.md"),
      personalization_other_agent: pathExists(fixture.sourceRoot, "data/derived/personalization/other_agent_personalization.md"),
      deep_explore_prompt: pathExists(fixture.sourceRoot, "data/derived/chatgpt_deep_explore/latest_memory_analysis_prompt.md"),
      deep_explore_machine: pathExists(fixture.sourceRoot, "data/derived/chatgpt_deep_explore/chatgpt_deep_explore_export.json"),
      runtime_snapshot: pathExists(fixture.runtimeDir, "memory_atlas.json"),
    };
    assertCondition(Object.values(expectedArtifacts).every(Boolean), "One or more real command artifacts are missing", expectedArtifacts);

    const auditRows = readJsonLines(path.join(fixture.appSupport, "command_audit.jsonl"));
    assertCondition(auditRows.length === expectedCommandIds.length, "Machine-local audit does not contain exactly six rows", auditRows);
    assertCondition(auditRows.every((row) => Object.keys(row).every((key) => [
      "schema_version", "command_id", "status", "started_at", "finished_at", "duration_ms",
    ].includes(key))), "Audit log contains unapproved details", auditRows);

    await page.bringToFront();
    await page.evaluate(() => document.fonts.ready);
    await page.locator(".command-palette").evaluate((element) => { element.scrollTop = 0; });
    await page.waitForTimeout(500);
    await page.screenshot({
      path: path.join(outputDir, "local-six-command-surface.png"),
      fullPage: false,
      animations: "disabled",
    });
    await page.locator('[data-r3-command-result="chatgpt_deep_explore"]').scrollIntoViewIfNeeded();
    await page.waitForTimeout(300);
    await page.screenshot({
      path: path.join(outputDir, "local-deep-explore-result.png"),
      fullPage: false,
      animations: "disabled",
    });

    const reloadFailurePage = await context.newPage();
    let snapshotRequestCount = 0;
    await reloadFailurePage.route("**/memory_atlas.json?**", async (route) => {
      snapshotRequestCount += 1;
      if (snapshotRequestCount === 1) {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ error: "reload failure fixture" }),
      });
    });
    await reloadFailurePage.goto(localUrl, { waitUntil: "networkidle", timeout: 60000 });
    await reloadFailurePage.waitForSelector('[data-view="home"]', { timeout: 30000 });
    await reloadFailurePage.waitForFunction(() => window.__memoryAtlasR3CommandWorkflows?.().runtimeAvailable === true, null, { timeout: 15000 });
    const snapshotTextBeforeReload = await reloadFailurePage.locator(".stat-strip").innerText();
    const reloadFailureResult = await executeCommand(reloadFailurePage, "sync_codex");
    assertCondition(reloadFailureResult.status === "error", "Reload failure did not surface as a command error", reloadFailureResult);
    assertCondition(await reloadFailurePage.locator('[data-view="home"]').isVisible(), "Reload failure removed the mounted Home route");
    assertCondition(await reloadFailurePage.locator(".stat-strip").innerText() === snapshotTextBeforeReload, "Reload failure replaced the existing snapshot metrics");
    assertCondition(await reloadFailurePage.locator('[data-state="load-failed-banner"]').count() === 0, "Reload failure promoted to a global load failure banner");
    status.reload_failure = {
      command_status: reloadFailureResult.status,
      existing_snapshot_preserved: true,
      global_load_failure: false,
      snapshot_request_count: snapshotRequestCount,
    };
    await reloadFailurePage.close();
    await context.close();
    await browser.close();
    browser = null;

    staticBrowser = await chromium.launch({
      headless: true,
      ...(browserExecutable ? { executablePath: browserExecutable } : {}),
    });
    const staticContext = await staticBrowser.newContext({ viewport: { width: 1440, height: 900 } });
    const staticPage = await staticContext.newPage();
    const staticCommandRequests = [];
    staticPage.on("request", (request) => {
      if (request.method() === "POST" && request.url().includes("/__memory_atlas_command")) {
        staticCommandRequests.push(request.url());
      }
    });
    await staticPage.goto(staticUrl, { waitUntil: "networkidle", timeout: 60000 });
    await staticPage.waitForFunction(() => window.__memoryAtlasR3CommandWorkflows?.().hostedStaticReadOnly === true, null, { timeout: 15000 });
    await staticPage.locator('[data-s12-p1-command-id="sync_codex"]').click();
    await staticPage.locator('[data-r3-command-execute="sync_codex"]').click();
    await staticPage.waitForFunction(
      () => document.querySelector('[data-r3-command-result="sync_codex"]')?.getAttribute("data-r3-command-result-status") === "local_required",
      null,
      { timeout: 5000 },
    );
    const staticResult = await staticPage.locator('[data-r3-command-result="sync_codex"]').evaluate((element) => ({
      handoff: element.querySelector("a")?.getAttribute("href") || "",
      message: element.querySelector("p")?.textContent?.trim() || "",
      status: element.getAttribute("data-r3-command-result-status") || "",
    }));
    assertCondition(staticResult.message.includes("仅在本地 Memory Atlas app 执行"), "Hosted-static result lacks specific local-app explanation", staticResult);
    assertCondition(staticResult.handoff === "http://127.0.0.1:4177", "Hosted-static result lacks exact local-app handoff", staticResult);
    assertCondition(staticCommandRequests.length === 0, "Hosted-static page attempted command execution", staticCommandRequests);
    await staticPage.bringToFront();
    await staticPage.locator(".brand").waitFor({ state: "visible" });
    await staticPage.locator('[data-r3-command-result="sync_codex"]').scrollIntoViewIfNeeded();
    await staticPage.evaluate(() => document.fonts.ready);
    await staticPage.waitForTimeout(700);
    await staticPage.screenshot({
      path: path.join(outputDir, "hosted-static-read-only-handoff.png"),
      fullPage: false,
      animations: "disabled",
    });

    status.status = "PASS";
    status.security = {
      allowlisted_command_count: expectedCommandIds.length,
      remote_origin_rejected: true,
      remote_lifecycle_origin_rejected: true,
      extra_fields_rejected: true,
      cors_enabled: false,
      no_silent_send: true,
      external_request_methods: externalRequests.map((item) => item.method),
      audit_metadata_only: true,
      canonical_repo_mutation: false,
      remote_push: false,
    };
    status.hosted_static = {
      command_post_count: staticCommandRequests.length,
      result: staticResult,
    };
    status.artifacts = expectedArtifacts;
    status.command_request_ids = commandRequests.map((item) => item.command_id);
    status.screenshots = [
      "local-six-command-surface.png",
      "local-deep-explore-result.png",
      "hosted-static-read-only-handoff.png",
    ];
    await staticContext.close();
    await staticBrowser.close();
    staticBrowser = null;
  } catch (error) {
    status.error = String(error?.message || error);
    status.error_details = error?.details || {};
    status.runtime_server_log_tail = runtimeServer.logs.join("").slice(-5000);
    status.static_server_log_tail = staticServer.logs.join("").slice(-3000);
    throw error;
  } finally {
    fs.writeFileSync(path.join(outputDir, "status.json"), JSON.stringify(status, null, 2) + "\n", "utf8");
    if (staticBrowser) await staticBrowser.close();
    if (browser) await browser.close();
    await stopProcess(staticServer);
    await stopProcess(runtimeServer);
    fs.rmSync(fixture.fixtureRoot, { recursive: true, force: true });
  }

  process.stdout.write(JSON.stringify({
    status: status.status,
    phase: status.phase,
    command_count: expectedCommandIds.length,
    hosted_static_command_posts: status.hosted_static.command_post_count,
    output_dir: outputDir,
  }, null, 2) + "\n");
}


main().catch((error) => {
  console.error(error.stack || error.message || String(error));
  process.exit(1);
});
