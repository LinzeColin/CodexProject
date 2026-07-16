#!/usr/bin/env node
import crypto from "node:crypto";
import fs from "node:fs";
import http from "node:http";
import os from "node:os";
import path from "node:path";
import process from "node:process";
import { spawn, execFileSync } from "node:child_process";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";


const HERE = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_PFI_ROOT = path.resolve(HERE, "../..");

function parseArgs(argv) {
  const result = { pfiRoot: DEFAULT_PFI_ROOT, outputDir: null };
  for (let index = 0; index < argv.length; index += 1) {
    if (argv[index] === "--pfi-root") result.pfiRoot = path.resolve(argv[++index]);
    else if (argv[index] === "--output-dir") result.outputDir = path.resolve(argv[++index]);
    else throw new Error(`unknown argument: ${argv[index]}`);
  }
  if (!result.outputDir) throw new Error("--output-dir is required");
  return result;
}

function loadPlaywright() {
  const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
  if (!moduleDir) throw new Error("PFI_PLAYWRIGHT_MODULE_DIR is required; installation is forbidden in this run");
  const require = createRequire(path.join(path.resolve(moduleDir), "package.json"));
  return require("playwright");
}

async function reserveEphemeralPort() {
  for (;;) {
    const server = http.createServer();
    await new Promise((resolve, reject) => {
      server.once("error", reject);
      server.listen(0, "127.0.0.1", resolve);
    });
    const address = server.address();
    const port = typeof address === "object" && address ? address.port : 0;
    await new Promise((resolve) => server.close(resolve));
    if (port && port !== 8501 && port !== 8502) return port;
  }
}

async function waitForHttp(url, child, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) throw new Error(`isolated Streamlit exited early: ${child.exitCode}`);
    try {
      const response = await fetch(url);
      if (response.ok) return;
    } catch (_error) {
      // The isolated server is still starting.
    }
    await new Promise((resolve) => setTimeout(resolve, 100));
  }
  throw new Error(`isolated Streamlit did not become ready: ${url}`);
}

function stopProcessGroup(child) {
  if (!child || child.exitCode !== null) return;
  try {
    process.kill(-child.pid, "SIGTERM");
  } catch (_error) {
    child.kill("SIGTERM");
  }
}

function sanitizeTraceArchive(tracePath, pythonBin) {
  const script = String.raw`
import os
import pathlib
import sys
import zipfile

source = pathlib.Path(sys.argv[1])
temporary = source.with_name(source.name + ".sanitized")
home_marker = str(pathlib.Path.home()).encode("utf-8")
with zipfile.ZipFile(source, "r") as archive, zipfile.ZipFile(temporary, "w") as sanitized:
    if archive.testzip() is not None:
        raise SystemExit("input Playwright trace archive is corrupt")
    for info in archive.infolist():
        payload = archive.read(info.filename).replace(home_marker, b"$HOME")
        clone = zipfile.ZipInfo(info.filename, date_time=info.date_time)
        clone.comment = info.comment
        clone.extra = info.extra
        clone.create_system = info.create_system
        clone.external_attr = info.external_attr
        clone.internal_attr = info.internal_attr
        clone.flag_bits = info.flag_bits
        sanitized.writestr(clone, payload, compress_type=zipfile.ZIP_DEFLATED)
os.replace(temporary, source)
`;
  execFileSync(pythonBin, ["-c", script, tracePath], { stdio: "pipe" });
}

async function captureStreamlitHeaders({ pfiRoot, pythonBin, cacheKey, tempRoot }) {
  const port = await reserveEphemeralPort();
  const appPath = path.join(tempRoot, "minimal_streamlit.py");
  fs.writeFileSync(appPath, "import streamlit as st\nst.title('PFI cache header evidence')\n", "utf8");
  const wrapperPath = path.join(pfiRoot, "scripts/v025/run_streamlit_with_release_cache.py");
  const child = spawn(
    pythonBin,
    [
      wrapperPath,
      "run",
      appPath,
      "--server.port",
      String(port),
      "--server.address",
      "127.0.0.1",
      "--server.headless",
      "true",
      "--server.fileWatcherType",
      "none",
      "--browser.gatherUsageStats",
      "false",
    ],
    {
      cwd: pfiRoot,
      detached: true,
      stdio: ["ignore", "pipe", "pipe"],
      env: {
        ...process.env,
        HOME: path.join(tempRoot, "home"),
        PYTHONPATH: path.join(pfiRoot, "src"),
        PFI_STREAMLIT_CACHE_KEY: cacheKey,
        PFI_V021_RUNTIME_API_PORT: "0",
        PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION: "python",
      },
    },
  );
  let childOutput = "";
  child.stdout.on("data", (chunk) => { childOutput += String(chunk); });
  child.stderr.on("data", (chunk) => { childOutput += String(chunk); });
  const baseUrl = `http://127.0.0.1:${port}`;
  try {
    await waitForHttp(`${baseUrl}/_stcore/health`, child);
    const rootResponse = await fetch(`${baseUrl}/`);
    const html = await rootResponse.text();
    const etag = rootResponse.headers.get("etag");
    const lastModified = rootResponse.headers.get("last-modified");
    const cacheControl = rootResponse.headers.get("cache-control");
    const assetMatch = html.match(/(?:src|href)="(?:\.\/|\/)?(static\/(?:js|css)\/[^"?]+\.[0-9a-f]{8,}\.(?:js|css))/);
    if (!assetMatch) throw new Error("content-hashed Streamlit asset URL was not found");
    const assetResponse = await fetch(`${baseUrl}/${assetMatch[1]}`);
    await assetResponse.arrayBuffer();
    const faviconResponse = await fetch(`${baseUrl}/favicon.png`);
    await faviconResponse.arrayBuffer();
    const conditional = await fetch(`${baseUrl}/`, { headers: { "If-None-Match": etag || "" } });
    const result = {
      schema: "PFIV025Stage1CacheHeadersEvidenceV1",
      runtime: "isolated_minimal_streamlit_same_process_wrapper",
      live_ports_8501_8502_accessed: false,
      html: {
        status: rootResponse.status,
        cache_control: cacheControl,
        etag_present: Boolean(etag),
        last_modified_present: Boolean(lastModified),
        conditional_if_none_match_status: conditional.status,
      },
      hashed_asset: {
        path_pattern: "static/(js|css)/<name>.<content-hash>.(js|css)",
        status: assetResponse.status,
        cache_control: assetResponse.headers.get("cache-control"),
      },
      unhashed_asset: {
        path: "favicon.png",
        status: faviconResponse.status,
        cache_control: faviconResponse.headers.get("cache-control"),
      },
      checks: {
        html_private_revalidation: cacheControl === "no-cache, private" && Boolean(etag) && Boolean(lastModified),
        conditional_304: conditional.status === 304,
        hashed_immutable: assetResponse.headers.get("cache-control") === "public, max-age=31536000, immutable",
        unhashed_private_revalidation: faviconResponse.headers.get("cache-control") === "no-cache, private",
      },
    };
    if (!Object.values(result.checks).every(Boolean)) throw new Error(`header checks failed: ${JSON.stringify(result.checks)}`);
    return result;
  } catch (error) {
    const summary = childOutput.split("\n").filter(Boolean).slice(-8).join(" | ");
    throw new Error(`${error.message}; isolated Streamlit summary: ${summary}`);
  } finally {
    stopProcessGroup(child);
    await new Promise((resolve) => setTimeout(resolve, 250));
  }
}

function htmlPage({ manifest, versionSource, apiBaseUrl }) {
  const safeVersionSource = versionSource.replace(/<\/script/gi, "<\\/script");
  return `<!doctype html>
<html><body>
<section id="pfi-release-conflict" role="alert">
  <h1 data-pfi-release-conflict-title>正在核对 PFI 发布身份</h1>
  <p data-pfi-release-conflict-detail></p>
</section>
<div class="app-shell" hidden>PFI v0.2.5 cache-governed shell</div>
<script type="application/json" id="pfi-runtime-config">${JSON.stringify({ apiBaseUrl })}</script>
<script type="application/json" id="pfi-release-manifest">${JSON.stringify(manifest)}</script>
<script>${safeVersionSource}</script>
</body></html>`;
}

async function createGateServer({ manifest, policy, versionSource }) {
  let policyValid = true;
  const requests = { manifest: 0, policy: 0 };
  const server = http.createServer((request, response) => {
    const origin = `http://127.0.0.1:${server.address().port}`;
    if (request.url === "/legacy-sw.js") {
      response.writeHead(200, { "Content-Type": "application/javascript", "Service-Worker-Allowed": "/" });
      response.end("self.addEventListener('install',e=>e.waitUntil(self.skipWaiting()));self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));");
      return;
    }
    if (request.url === "/seed.html") {
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
      response.end(`<!doctype html><body>seed<script>
        window.seedLegacy = async () => {
          const registration = await navigator.serviceWorker.register('/legacy-sw.js', { scope: '/' });
          await navigator.serviceWorker.ready;
          const cache = await caches.open('pfi-v024-shell');
          await cache.put('/legacy-cache-probe', new Response('old'));
          return { scope: registration.scope, cacheNames: await caches.keys() };
        };
      </script></body>`);
      return;
    }
    if (request.url === "/gate.html") {
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
      response.end(htmlPage({ manifest, versionSource, apiBaseUrl: origin }));
      return;
    }
    if (request.url === "/other.html") {
      response.writeHead(200, { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" });
      response.end("<!doctype html><body>other</body>");
      return;
    }
    if (request.url === "/api/release-manifest") {
      requests.manifest += 1;
      const body = JSON.stringify(manifest);
      response.writeHead(200, {
        "Content-Type": "application/json",
        "Cache-Control": "no-store, private",
        "X-PFI-Release-Manifest-SHA256": crypto.createHash("sha256").update(`${JSON.stringify(manifest, null, 2)}\n`).digest("hex"),
        "X-PFI-Running-Backend-SHA256": manifest.backend_build_hash,
      });
      response.end(body);
      return;
    }
    if (request.url === "/api/release-cache-policy") {
      requests.policy += 1;
      const body = policyValid
        ? policy
        : { ...policy, valid: false, process_cache_key: "9".repeat(64) };
      response.writeHead(200, { "Content-Type": "application/json", "Cache-Control": "no-store, private" });
      response.end(JSON.stringify(body));
      return;
    }
    response.writeHead(404, { "Content-Type": "text/plain" });
    response.end("not found");
  });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  if ([8501, 8502].includes(server.address().port)) {
    await new Promise((resolve) => server.close(resolve));
    return createGateServer({ manifest, policy, versionSource });
  }
  return {
    server,
    origin: `http://127.0.0.1:${server.address().port}`,
    requests,
    setPolicyValid(value) { policyValid = Boolean(value); },
  };
}

async function captureBrowserEvidence({ chromium, manifest, policy, versionSource, outputDir, pythonBin }) {
  const gateServer = await createGateServer({ manifest, policy, versionSource });
  const browser = await chromium.launch({ headless: true });
  const context = await browser.newContext();
  await context.addInitScript(() => {
    window.__pfiPageshowEvents = [];
    window.addEventListener("pageshow", (event) => {
      window.__pfiPageshowEvents.push({ persisted: event.persisted, navigationType: performance.getEntriesByType("navigation")[0]?.type || "unknown" });
    });
  });
  await context.tracing.start({ screenshots: true, snapshots: true, sources: true });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  page.on("console", (message) => { if (message.type() === "error") consoleErrors.push(message.text()); });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  try {
    await page.goto(`${gateServer.origin}/seed.html`, { waitUntil: "networkidle" });
    const seeded = await page.evaluate(() => window.seedLegacy());
    await page.reload({ waitUntil: "networkidle" });
    await page.waitForFunction(() => Boolean(navigator.serviceWorker.controller));
    const controllerBeforeGate = await page.evaluate(() => Boolean(navigator.serviceWorker.controller));

    const requestsBeforeControlledGate = { ...gateServer.requests };
    await page.goto(`${gateServer.origin}/gate.html`, { waitUntil: "networkidle" });
    await page.waitForFunction(() => document.body.dataset.pfiReleaseIdentityState === "blocked");
    const controlledGate = await page.evaluate(async () => ({
      state: document.body.dataset.pfiReleaseIdentityState,
      shellHidden: document.querySelector(".app-shell").hidden,
      conflictHidden: document.querySelector("#pfi-release-conflict").hidden,
      detail: document.querySelector("[data-pfi-release-conflict-detail]").textContent,
      controllerActive: Boolean(navigator.serviceWorker.controller),
      registrations: (await navigator.serviceWorker.getRegistrations()).length,
      caches: await caches.keys(),
    }));
    const noBackendFetchWhileControlled =
      gateServer.requests.manifest === requestsBeforeControlledGate.manifest &&
      gateServer.requests.policy === requestsBeforeControlledGate.policy;

    await page.reload({ waitUntil: "networkidle" });
    await page.waitForFunction(() => document.body.dataset.pfiReleaseIdentityState === "ready");
    await page.evaluate(() => window.PFI_RELEASE_IDENTITY_READY);
    const cleanReload = await page.evaluate(async () => ({
      state: document.body.dataset.pfiReleaseIdentityState,
      shellHidden: document.querySelector(".app-shell").hidden,
      controllerActive: Boolean(navigator.serviceWorker.controller),
      registrations: (await navigator.serviceWorker.getRegistrations()).length,
      caches: await caches.keys(),
    }));

    await page.goto(`${gateServer.origin}/other.html`, { waitUntil: "networkidle" });
    await page.goBack({ waitUntil: "networkidle" });
    await page.waitForFunction(() => Boolean(window.PFI_RELEASE_IDENTITY_READY));
    await page.evaluate(() => window.PFI_RELEASE_IDENTITY_READY);
    const realNavigation = await page.evaluate(() => ({
      pageshowEvents: window.__pfiPageshowEvents,
      state: document.body.dataset.pfiReleaseIdentityState,
      navigationType: performance.getEntriesByType("navigation")[0]?.type || "unknown",
    }));

    gateServer.setPolicyValid(false);
    const immediatePending = await page.evaluate(() => {
      let event;
      try {
        event = new PageTransitionEvent("pageshow", { persisted: true });
      } catch (_error) {
        event = new Event("pageshow");
        Object.defineProperty(event, "persisted", { value: true });
      }
      window.dispatchEvent(event);
      return {
        state: document.body.dataset.pfiReleaseIdentityState,
        shellHidden: document.querySelector(".app-shell").hidden,
      };
    });
    await page.evaluate(() => window.PFI_RELEASE_IDENTITY_READY);
    await page.waitForFunction(() => document.body.dataset.pfiReleaseIdentityState === "blocked");
    const syntheticMismatch = await page.evaluate(() => ({
      state: document.body.dataset.pfiReleaseIdentityState,
      shellHidden: document.querySelector(".app-shell").hidden,
      title: document.querySelector("[data-pfi-release-conflict-title]").textContent,
      detail: document.querySelector("[data-pfi-release-conflict-detail]").textContent,
    }));
    const screenshotPath = path.join(outputDir, "bfcache_mismatch.png");
    await page.screenshot({ path: screenshotPath, fullPage: true });

    const checks = {
      legacy_worker_seeded: Boolean(seeded.scope) && controllerBeforeGate,
      controlled_page_failed_closed: controlledGate.state === "blocked" && controlledGate.shellHidden,
      cleanup_removed_registration_and_cache: controlledGate.registrations === 0 && controlledGate.caches.length === 0,
      controlled_page_skipped_backend_fetch: noBackendFetchWhileControlled,
      reload_has_no_old_controller: cleanReload.controllerActive === false,
      reload_ready_after_manifest_and_policy: cleanReload.state === "ready" && cleanReload.shellHidden === false,
      pageshow_telemetry_recorded: realNavigation.pageshowEvents.length > 0,
      synthetic_persisted_immediately_hides: immediatePending.state === "pending" && immediatePending.shellHidden,
      mismatch_fails_visible_in_chinese:
        syntheticMismatch.state === "blocked" &&
        syntheticMismatch.shellHidden &&
        syntheticMismatch.title === "版本冲突" &&
        /重新启动/.test(syntheticMismatch.detail) &&
        /清除缓存/.test(syntheticMismatch.detail),
      no_console_or_page_errors: consoleErrors.length === 0 && pageErrors.length === 0,
    };
    if (!Object.values(checks).every(Boolean)) {
      throw new Error(`browser checks failed: ${JSON.stringify({ checks, syntheticMismatch, immediatePending })}`);
    }
    return {
      schema: "PFIV025Stage1Phase12BrowserValidationV1",
      browser: "Playwright Chromium headless",
      origin: "ephemeral_loopback_dedicated_to_pfi_validation",
      live_ports_8501_8502_accessed: false,
      service_worker: { seeded, controlled_gate: controlledGate, clean_reload: cleanReload },
      bfcache: {
        real_navigation: realNavigation,
        real_persisted_observed: realNavigation.pageshowEvents.some((event) => event.persisted === true),
        synthetic_event_used_only_for_deterministic_mismatch_path: true,
        immediate_pending: immediatePending,
        mismatch: syntheticMismatch,
      },
      backend_request_counts: gateServer.requests,
      console_errors: consoleErrors,
      page_errors: pageErrors,
      evidence_files: ["bfcache_mismatch.png", "playwright_trace.zip"],
      checks,
    };
  } finally {
    const tracePath = path.join(outputDir, "playwright_trace.zip");
    await context.tracing.stop({ path: tracePath });
    sanitizeTraceArchive(tracePath, pythonBin);
    await context.close();
    await browser.close();
    await new Promise((resolve) => gateServer.server.close(resolve));
  }
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  fs.mkdirSync(args.outputDir, { recursive: true });
  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), "pfi-v025-s1p12-"));
  const pythonBin = path.resolve(process.env.PFI_PYTHON || path.join(args.pfiRoot, ".venv/bin/python"));
  const contractCli = path.join(args.pfiRoot, "scripts/v025/release_cache_contract.py");
  const env = { ...process.env, PYTHONPATH: path.join(args.pfiRoot, "src") };
  try {
    const cacheKey = execFileSync(
      pythonBin,
      [contractCli, "--project-root", args.pfiRoot, "--key-only"],
      { cwd: args.pfiRoot, env, encoding: "utf8" },
    ).trim();
    const policy = JSON.parse(execFileSync(
      pythonBin,
      [contractCli, "--project-root", args.pfiRoot, "--policy-json"],
      { cwd: args.pfiRoot, env, encoding: "utf8" },
    ));
    const manifest = JSON.parse(fs.readFileSync(path.join(args.pfiRoot, "config/release_manifest.json"), "utf8"));
    const versionSource = fs.readFileSync(path.join(args.pfiRoot, "web/app/version.js"), "utf8");
    const cacheHeaders = await captureStreamlitHeaders({
      pfiRoot: args.pfiRoot,
      pythonBin,
      cacheKey,
      tempRoot,
    });
    const { chromium } = loadPlaywright();
    const browserValidation = await captureBrowserEvidence({
      chromium,
      manifest,
      policy,
      versionSource,
      outputDir: args.outputDir,
      pythonBin,
    });
    fs.writeFileSync(path.join(args.outputDir, "cache_headers.json"), `${JSON.stringify(cacheHeaders, null, 2)}\n`, "utf8");
    fs.writeFileSync(path.join(args.outputDir, "browser_validation.json"), `${JSON.stringify(browserValidation, null, 2)}\n`, "utf8");
    process.stdout.write(`${JSON.stringify({ cache_headers: cacheHeaders.checks, browser: browserValidation.checks })}\n`);
  } finally {
    fs.rmSync(tempRoot, { recursive: true, force: true });
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack : String(error));
  process.exitCode = 1;
});
