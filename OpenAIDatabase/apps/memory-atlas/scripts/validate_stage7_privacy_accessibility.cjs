#!/usr/bin/env node
"use strict";

const fs = require("node:fs");
const http = require("node:http");
const os = require("node:os");
const path = require("node:path");
const { spawn, spawnSync } = require("node:child_process");

const appRoot = path.resolve(__dirname, "..");
const repoRoot = path.resolve(appRoot, "../..");
const publishDir = path.join(appRoot, "dist");
const port = Number(process.env.MEMORY_ATLAS_STAGE7_PRIVACY_PORT || 4177);
const targetUrl = `http://127.0.0.1:${port}`;
const outputDir = process.env.MEMORY_ATLAS_PRIVACY_ACCESSIBILITY_AUDIT_DIR
  || fs.mkdtempSync(path.join(os.tmpdir(), "memory-atlas-stage7-privacy-accessibility-"));
const browserExecutable = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || findChromiumExecutable();

const FEEDBACK_STORAGE_KEY = "memory-atlas.timeline.feedback";
const FORBIDDEN_ARTIFACT_TEXT_PATTERNS = [
  /PRIVATE CORE DETAIL/i,
  /SECRET DETAIL/i,
  /sk-[A-Za-z0-9_-]{20,}/,
  /-----BEGIN (?:RSA |EC |OPENSSH |PRIVATE )?PRIVATE KEY-----/i,
  /OpenAI-export\.zip/i,
  /chatgpt_memory_vault/i,
  /\.local_keys/i,
  /\/Users\/[A-Za-z0-9_.-]+\//,
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
  const pnpmRoot = path.join(os.homedir(), ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/.pnpm");
  try {
    const candidate = fs
      .readdirSync(pnpmRoot)
      .filter((entry) => entry.startsWith("playwright@"))
      .sort()
      .at(-1);
    if (candidate) {
      return require(path.join(pnpmRoot, candidate, "node_modules/playwright"));
    }
  } catch {}
  throw new Error("Playwright is not resolvable from project dependencies or Codex bundled runtime");
}

function httpGet(url, timeoutMs = 2000) {
  return new Promise((resolve, reject) => {
    const request = http.get(url, (response) => {
      response.resume();
      response.on("end", () => resolve(response.statusCode || 0));
    });
    request.setTimeout(timeoutMs, () => {
      request.destroy(new Error(`timeout waiting for ${url}`));
    });
    request.on("error", reject);
  });
}

async function waitForHttp(url, timeoutMs = 20000) {
  const started = Date.now();
  let lastError = null;
  while (Date.now() - started < timeoutMs) {
    try {
      const status = await httpGet(url, 1200);
      if (status >= 200 && status < 500) return status;
    } catch (error) {
      lastError = error;
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(`Vite preview did not become ready at ${url}: ${lastError?.message || "unknown"}`);
}

function startPreviewServer() {
  const viteCli = path.join(appRoot, "node_modules/vite/bin/vite.js");
  assertCondition(fs.existsSync(viteCli), "Vite CLI is missing from app node_modules", { viteCli });
  const server = spawn(process.execPath, [viteCli, "preview", "--host", "127.0.0.1", "--port", String(port), "--strictPort"], {
    cwd: appRoot,
    env: { ...process.env },
    stdio: ["ignore", "pipe", "pipe"],
  });
  const logs = [];
  server.stdout.on("data", (chunk) => logs.push(chunk.toString()));
  server.stderr.on("data", (chunk) => logs.push(chunk.toString()));
  return { server, logs };
}

async function stopPreviewServer(server) {
  if (!server || server.exitCode !== null) return;
  server.kill("SIGTERM");
  await Promise.race([
    new Promise((resolve) => server.once("exit", resolve)),
    new Promise((resolve) => setTimeout(resolve, 2500)),
  ]);
  if (server.exitCode === null) {
    server.kill("SIGKILL");
    await new Promise((resolve) => server.once("exit", resolve));
  }
}

async function assertPortClosed() {
  try {
    await httpGet(targetUrl, 600);
    throw new Error(`preview server still responds on ${targetUrl}`);
  } catch (error) {
    if (String(error.message || "").includes("still responds")) throw error;
  }
}

function isIgnoredRuntimeProbe(response) {
  try {
    const pathname = new URL(response.url).pathname;
    return response.status === 404 && ["/__memory_atlas_heartbeat", "/__memory_atlas_release"].includes(pathname);
  } catch {
    return false;
  }
}

function runReleasePrivacyAudit() {
  const auditScript = path.join(repoRoot, "scripts/audit_memory_atlas_release.py");
  const result = spawnSync("python3", [auditScript, "--repo-root", repoRoot, "--publish-dir", publishDir], {
    cwd: repoRoot,
    encoding: "utf8",
  });
  if (result.status !== 0) {
    throw Object.assign(new Error("release privacy audit failed"), {
      details: { stdout: result.stdout, stderr: result.stderr, status: result.status },
    });
  }
  return JSON.parse(result.stdout);
}

function collectFiles(root) {
  const result = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const fullPath = path.join(root, entry.name);
    if (entry.isDirectory()) {
      result.push(...collectFiles(fullPath));
    } else if (entry.isFile()) {
      result.push(fullPath);
    }
  }
  return result;
}

function inspectPublishArtifact() {
  assertCondition(fs.existsSync(publishDir), "publish directory is missing; run build first", { publishDir });
  const files = collectFiles(publishDir);
  const relativeFiles = files.map((file) => path.relative(publishDir, file).split(path.sep).join("/")).sort();
  assertCondition(relativeFiles.length > 0, "publish directory is empty", { publishDir });
  assertCondition(!relativeFiles.some((file) => file.endsWith(".map")), "publish artifact contains sourcemap files", { relativeFiles });
  assertCondition(relativeFiles.includes("memory_atlas.json"), "publish artifact is missing memory_atlas.json", { relativeFiles });

  const atlasPath = path.join(publishDir, "memory_atlas.json");
  const atlas = JSON.parse(fs.readFileSync(atlasPath, "utf8"));
  const sourceContract = atlas.source_contract || {};
  assertCondition(atlas.schema_version === "memory_atlas.v1", "memory_atlas.json schema version is unexpected", { schema: atlas.schema_version });
  assertCondition(
    sourceContract.mode === "public_redacted_read_only_visualization",
    "memory_atlas.json is not a public redacted read-only visualization snapshot",
    { sourceContract },
  );
  assertCondition(
    sourceContract.writeback_policy?.direct_frontend_mutation_of_active_memory === false,
    "frontend active-memory mutation is not locked off in source contract",
    { writebackPolicy: sourceContract.writeback_policy },
  );

  const artifactText = files
    .filter((file) => [".html", ".css", ".js", ".json", ".svg", ".txt", ".webmanifest"].includes(path.extname(file).toLowerCase()))
    .map((file) => fs.readFileSync(file, "utf8"))
    .join("\n");
  const matchedPatterns = FORBIDDEN_ARTIFACT_TEXT_PATTERNS
    .filter((pattern) => pattern.test(artifactText))
    .map((pattern) => pattern.toString());
  assertCondition(matchedPatterns.length === 0, "publish artifact contains forbidden private/secret text patterns", { matchedPatterns });

  return {
    publishDir,
    fileCount: relativeFiles.length,
    files: relativeFiles,
    sourceContractMode: sourceContract.mode,
    exportProfile: sourceContract.export_profile || "",
    directFrontendMutation: sourceContract.writeback_policy?.direct_frontend_mutation_of_active_memory,
    sourcemapsPresent: false,
  };
}

async function installFeedbackProbe(context) {
  await context.addInitScript((storageKey) => {
    window.__stage73FeedbackProbe = { vibrate: 0, audio: 0 };
    try {
      window.localStorage.removeItem(storageKey);
    } catch {}
    try {
      Object.defineProperty(navigator, "vibrate", {
        configurable: true,
        value: () => {
          window.__stage73FeedbackProbe.vibrate += 1;
          return true;
        },
      });
    } catch {}
    class Stage73AudioContext {
      constructor() {
        window.__stage73FeedbackProbe.audio += 1;
        this.destination = {};
      }
      createOscillator() {
        return {
          frequency: { value: 0 },
          connect() {},
          start() {},
          stop() {},
        };
      }
      createGain() {
        return {
          gain: { value: 0 },
          connect() {},
        };
      }
      close() {
        return Promise.resolve();
      }
    }
    try {
      Object.defineProperty(window, "AudioContext", { configurable: true, value: Stage73AudioContext });
    } catch {}
  }, FEEDBACK_STORAGE_KEY);
}

async function openTimeline(page) {
  await page.goto(targetUrl, { waitUntil: "domcontentloaded", timeout: 20000 });
  await page.waitForLoadState("networkidle", { timeout: 10000 }).catch(() => undefined);
  await page.locator('[data-nav-view="timeline"]').click({ timeout: 5000 });
  await page.waitForSelector(".memory-river-canvas", { timeout: 15000 });
}

async function readFeedbackContract(page) {
  return page.evaluate(() => {
    const labels = Array.from(document.querySelectorAll("label.feedback-toggle")).map((label) => {
      const input = label.querySelector("input");
      return {
        text: label.textContent?.replace(/\s+/g, " ").trim() || "",
        checked: Boolean(input?.checked),
      };
    });
    const bar = document.querySelector(".memory-river-interaction-bar");
    const canvas = document.querySelector(".memory-river-canvas");
    const playButton = document.querySelector("button[aria-label='播放时间轴'], button[aria-label='暂停时间轴播放']");
    const laneFlow = document.querySelector(".memory-river-lane-flow");
    const markerCircle = document.querySelector(".memory-river-marker circle");
    return {
      prefersReducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      labels,
      bar: {
        reducedMotion: bar?.getAttribute("data-reduced-motion") || "",
        pseudoHaptic: bar?.getAttribute("data-feedback-pseudo-haptic") || "",
        audio: bar?.getAttribute("data-feedback-audio") || "",
        defaults: bar?.getAttribute("data-feedback-defaults") || "",
      },
      canvas: {
        reducedMotion: canvas?.getAttribute("data-feedback-reduced-motion") || "",
        pseudoHaptic: canvas?.getAttribute("data-feedback-pseudo-haptic") || "",
        audio: canvas?.getAttribute("data-feedback-audio") || "",
        evidenceLayers: canvas?.getAttribute("data-evidence-layers") || "",
      },
      playDisabled: Boolean(playButton?.hasAttribute("disabled")),
      laneFlowTransition: laneFlow ? getComputedStyle(laneFlow).transitionDuration : "",
      markerTransition: markerCircle ? getComputedStyle(markerCircle).transitionDuration : "",
      probe: window.__stage73FeedbackProbe || null,
    };
  });
}

function labelChecked(contract, labelText) {
  return contract.labels.find((label) => label.text.includes(labelText))?.checked;
}

async function validateReducedMotion(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 920 }, deviceScaleFactor: 1, reducedMotion: "reduce" });
  await installFeedbackProbe(context);
  const page = await context.newPage();
  try {
    await openTimeline(page);
    const contract = await readFeedbackContract(page);
    assertCondition(contract.prefersReducedMotion === true, "browser reduced-motion media emulation is not active", contract);
    assertCondition(labelChecked(contract, "Reduced Motion") === true, "Reduced Motion setting did not default on from browser preference", contract);
    assertCondition(labelChecked(contract, "伪触感") === false, "pseudo-haptic should default off under reduced motion", contract);
    assertCondition(labelChecked(contract, "音频") === false, "audio feedback should default off under reduced motion", contract);
    assertCondition(contract.bar.reducedMotion === "true" && contract.canvas.reducedMotion === "true", "reduced motion DOM contract is missing", contract);
    assertCondition(contract.playDisabled === true, "timeline playback should be disabled under reduced motion", contract);
    assertCondition(contract.laneFlowTransition === "0s" && contract.markerTransition === "0s", "reduced motion should remove Memory River transitions", contract);
    await page.close();
    await context.close();
    return contract;
  } catch (error) {
    await context.close().catch(() => undefined);
    throw error;
  }
}

async function validateSilentFeedbackDefaults(browser) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 920 }, deviceScaleFactor: 1, reducedMotion: "no-preference" });
  await installFeedbackProbe(context);
  const page = await context.newPage();
  try {
    await openTimeline(page);
    const before = await readFeedbackContract(page);
    assertCondition(before.prefersReducedMotion === false, "no-preference media emulation is not active", before);
    assertCondition(labelChecked(before, "Reduced Motion") === false, "Reduced Motion should not default on without browser preference", before);
    assertCondition(labelChecked(before, "伪触感") === false, "pseudo-haptic should default off", before);
    assertCondition(labelChecked(before, "音频") === false, "audio feedback should default off", before);
    assertCondition(before.bar.pseudoHaptic === "disabled" && before.canvas.pseudoHaptic === "disabled", "pseudo-haptic disabled contract is missing", before);
    assertCondition(before.bar.audio === "disabled" && before.canvas.audio === "disabled", "audio disabled contract is missing", before);
    assertCondition(before.bar.defaults === "silent-by-default", "silent-by-default contract is missing", before);

    await page.locator(".memory-river-marker").first().click({ timeout: 10000, force: true });
    await page.waitForTimeout(180);
    const after = await readFeedbackContract(page);
    assertCondition(after.probe?.vibrate === 0, "default marker click called navigator.vibrate", after);
    assertCondition(after.probe?.audio === 0, "default marker click created AudioContext", after);
    await page.close();
    await context.close();
    return { before, after };
  } catch (error) {
    await context.close().catch(() => undefined);
    throw error;
  }
}

async function runBrowserValidation() {
  const { chromium } = requirePlaywright();
  assertCondition(Boolean(browserExecutable), "No Chromium-compatible browser executable found");
  const browser = await chromium.launch({ executablePath: browserExecutable, headless: true });
  const consoleErrors = [];
  const failedResponses = [];
  try {
    browser.on("disconnected", () => undefined);
    const recordPage = (page) => {
      page.on("console", (message) => {
        if (message.type() === "error") consoleErrors.push(message.text());
      });
      page.on("pageerror", (error) => consoleErrors.push(error.message));
      page.on("response", (response) => {
        if (response.status() >= 400) failedResponses.push({ status: response.status(), url: response.url() });
      });
    };
    const originalNewContext = browser.newContext.bind(browser);
    browser.newContext = async (...args) => {
      const context = await originalNewContext(...args);
      context.on("page", recordPage);
      return context;
    };

    const reducedMotion = await validateReducedMotion(browser);
    const silentDefaults = await validateSilentFeedbackDefaults(browser);
    const actionableFailedResponses = failedResponses.filter((response) => !isIgnoredRuntimeProbe(response));
    const actionableConsoleErrors = consoleErrors.filter((message) => {
      return !(message.startsWith("Failed to load resource:") && actionableFailedResponses.length === 0);
    });
    assertCondition(actionableConsoleErrors.length === 0 && actionableFailedResponses.length === 0, "Browser console/page errors occurred", {
      consoleErrors,
      failedResponses,
      actionableConsoleErrors,
      actionableFailedResponses,
    });
    return { reducedMotion, silentDefaults, consoleErrors, failedResponses, actionableConsoleErrors, actionableFailedResponses };
  } finally {
    await browser.close();
  }
}

(async () => {
  let preview = null;
  try {
    fs.mkdirSync(outputDir, { recursive: true });
    const releaseAudit = runReleasePrivacyAudit();
    const artifact = inspectPublishArtifact();
    preview = startPreviewServer();
    await waitForHttp(targetUrl);
    const browser = await runBrowserValidation();
    await stopPreviewServer(preview.server);
    await assertPortClosed();
    const report = {
      status: "PASS",
      stage: "7.3",
      targetUrl,
      outputDir,
      checks: [
        "publish artifact privacy scan passed",
        "memory_atlas.json is public redacted read-only visualization",
        "production sourcemaps absent by default",
        "browser reduced-motion preference enables Reduced Motion and disables playback",
        "Memory River reduced-motion DOM contract removes transitions",
        "pseudo-haptic and audio feedback default off",
        "default marker interaction does not call vibration or AudioContext",
        "preview server released after validation",
      ],
      results: {
        releaseAudit,
        artifact,
        browser,
      },
    };
    fs.writeFileSync(path.join(outputDir, "stage7-privacy-accessibility-report.json"), `${JSON.stringify(report, null, 2)}\n`);
    console.log(JSON.stringify(report, null, 2));
  } catch (error) {
    if (preview) await stopPreviewServer(preview.server).catch(() => undefined);
    console.error(JSON.stringify({
      status: "FAIL",
      stage: "7.3",
      message: error.message,
      details: error.details || null,
      targetUrl,
      outputDir,
      serverLogs: preview?.logs?.join("").slice(-4000) || "",
    }, null, 2));
    process.exitCode = 1;
  }
})();
