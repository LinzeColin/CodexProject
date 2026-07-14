#!/usr/bin/env node

const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const path = require("path");

const PFI_ROOT = path.resolve(__dirname, "..");
const PLAYWRIGHT_CORE_PATH = process.env.PLAYWRIGHT_CORE_PATH || "playwright-core";
const CHROME_EXECUTABLE_PATH =
  process.env.CHROME_EXECUTABLE_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const VERSION_QUERY =
  "pfi_app_version=0.2.3&pfi_build=pfi-v024-stage2-phase22&pfi_ui_contract=PFI-V024-STAGE2-ENTRY-CONSISTENCY";
const BUNDLE_FILES = [
  "web/index.html",
  "web/styles/tokens.css",
  "web/app/version.js",
  "web/app/entry_audit.js",
  "web/app/routes.js",
  "web/app/shell.js",
];

function fileSha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function diskBundleHash() {
  const digest = crypto.createHash("sha256");
  for (const relative of BUNDLE_FILES) {
    digest.update(relative, "utf8");
    digest.update(Buffer.from([0]));
    digest.update(fileSha256(path.join(PFI_ROOT, relative)), "ascii");
    digest.update(Buffer.from([0]));
  }
  return digest.digest("hex");
}

function healthOk(baseUrl) {
  return new Promise((resolve) => {
    const request = http.get(`${baseUrl}/_stcore/health`, { timeout: 1500 }, (response) => {
      const chunks = [];
      response.on("data", (chunk) => chunks.push(chunk));
      response.on("end", () => {
        const body = Buffer.concat(chunks).toString("utf8").trim().toLowerCase();
        resolve(response.statusCode === 200 && body === "ok");
      });
    });
    request.on("timeout", () => {
      request.destroy();
      resolve(false);
    });
    request.on("error", () => resolve(false));
  });
}

async function resolveBaseUrl() {
  const explicit = process.env.PFI_FINAL_DELIVERY_BASE_URL;
  if (explicit) {
    if (!(await healthOk(explicit))) throw new Error(`PFI health failed: ${explicit}`);
    return explicit;
  }
  for (let port = 8501; port <= 8510; port += 1) {
    const candidate = `http://127.0.0.1:${port}`;
    if (await healthOk(candidate)) return candidate;
  }
  throw new Error("No healthy PFI service on ports 8501-8510");
}

function sleep(milliseconds) {
  return new Promise((resolve) => setTimeout(resolve, milliseconds));
}

async function waitForPfiFrame(page) {
  for (let attempt = 0; attempt < 160; attempt += 1) {
    for (const frame of page.frames()) {
      const ready = await frame
        .evaluate(
          () =>
            Boolean(document.querySelector("[data-pfi-entry-version-strip]")) &&
            typeof window.PFI_READ_STAGE2_ENTRY_AUDIT === "function"
        )
        .catch(() => false);
      if (ready) return frame;
    }
    await sleep(125);
  }
  throw new Error("Timed out waiting for PFI Web Shell iframe");
}

function ignoredError(value) {
  return String(value).includes("favicon") || String(value).includes("/_stcore/health");
}

async function probeEntry(browser, name, url, expectedSources) {
  const context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  const page = await context.newPage();
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
  page.on("console", (message) => {
    if (message.type() === "error" && !ignoredError(message.text())) consoleErrors.push(message.text());
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400 && !ignoredError(response.url())) {
      httpErrors.push({ status: response.status(), url: response.url() });
    }
  });
  try {
    await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
    const frame = await waitForPfiFrame(page);
    const framePayload = await frame.evaluate(async (sourceNames) => {
      const hashText = async (value) => {
        const bytes = new TextEncoder().encode(value);
        const digest = await crypto.subtle.digest("SHA-256", bytes);
        return [...new Uint8Array(digest)].map((part) => part.toString(16).padStart(2, "0")).join("");
      };
      const inlineAssetHashes = {};
      for (const relative of sourceNames) {
        const selector = `[data-pfi-source="${CSS.escape(relative)}"]`;
        const element = document.querySelector(selector);
        inlineAssetHashes[relative] = element ? await hashText(element.textContent || "") : "";
      }
      return {
        audit: window.PFI_READ_STAGE2_ENTRY_AUDIT(),
        inlineAssetHashes,
      };
    }, Object.keys(expectedSources));
    return {
      name,
      url,
      topLevelUrl: page.url(),
      audit: framePayload.audit,
      inlineAssetHashes: framePayload.inlineAssetHashes,
      consoleErrors,
      pageErrors,
      httpErrors,
    };
  } finally {
    await context.close();
  }
}

function unique(values) {
  return [...new Set(values.filter(Boolean))].sort();
}

async function main() {
  const { chromium } = require(PLAYWRIGHT_CORE_PATH);
  const baseUrl = await resolveBaseUrl();
  const expectedSources = Object.fromEntries(
    BUNDLE_FILES.filter((relative) => relative !== "web/index.html").map((relative) => [
      relative,
      fs.readFileSync(path.join(PFI_ROOT, relative), "utf8"),
    ])
  );
  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME_EXECUTABLE_PATH,
    args: ["--no-first-run", "--no-default-browser-check"],
  });
  let probes;
  try {
    probes = await Promise.all([
      probeEntry(browser, "localhost", `${baseUrl}/?${VERSION_QUERY}&pfi_entry=localhost`, expectedSources),
      probeEntry(
        browser,
        "app",
        `${baseUrl}/?${VERSION_QUERY}&pfi_entry=app&pfi_app_path=${encodeURIComponent("/Applications/PFI.app")}`,
        expectedSources
      ),
    ]);
  } finally {
    await browser.close();
  }

  const byName = Object.fromEntries(probes.map((probe) => [probe.name, probe]));
  const diskHash = diskBundleHash();
  const runtimeHashes = {
    app: byName.app.audit.webBundleHash || "",
    localhost: byName.localhost.audit.webBundleHash || "",
  };
  const consoleErrors = probes.flatMap((probe) => probe.consoleErrors);
  const pageErrors = probes.flatMap((probe) => probe.pageErrors);
  const httpErrors = probes.flatMap((probe) => probe.httpErrors);
  const projectRoots = unique(probes.map((probe) => probe.audit.projectRoot));
  const expectedLoadedAssets = Object.fromEntries(
    BUNDLE_FILES.filter((relative) => relative !== "web/index.html").map((relative) => [
      relative,
      fileSha256(path.join(PFI_ROOT, relative)),
    ])
  );
  const loadedAssetHashesByEntry = Object.fromEntries(
    probes.map((probe) => [probe.name, probe.inlineAssetHashes])
  );
  const loadedAssetsMatchDisk = probes.every((probe) =>
    Object.entries(expectedLoadedAssets).every(
      ([relative, expectedHash]) => probe.inlineAssetHashes[relative] === expectedHash
    )
  );
  const appPaths = unique(
    probes
      .filter((probe) => probe.name === "app")
      .map((probe) => new URL(probe.topLevelUrl).searchParams.get("pfi_app_path"))
  );
  const appLocalhostSameBundleHash =
    Boolean(runtimeHashes.app) && runtimeHashes.app === runtimeHashes.localhost;
  const runtimeDiskBundleHashMatch =
    appLocalhostSameBundleHash && runtimeHashes.app === diskHash;
  const checks = [
    projectRoots.length === 1 && projectRoots[0] === PFI_ROOT,
    appPaths.length === 1 && appPaths[0] === "/Applications/PFI.app",
    appLocalhostSameBundleHash,
    runtimeDiskBundleHashMatch,
    loadedAssetsMatchDisk,
    consoleErrors.length === 0,
    pageErrors.length === 0,
    httpErrors.length === 0,
  ];
  const fail = checks.filter((value) => !value).length;
  const payload = {
    schema: "PFIV024ReadOnlyRuntimeSnapshotV1",
    status: fail === 0 ? "Pass" : "Blocked",
    mode: "read_only_no_pfi_data_or_reports_write",
    healthy_urls: [`${baseUrl}/_stcore/health`],
    disk_web_bundle_hash: diskHash,
    runtime_web_bundle_hashes: runtimeHashes,
    app_localhost_same_bundle_hash: appLocalhostSameBundleHash,
    runtime_disk_bundle_hash_match: runtimeDiskBundleHashMatch,
    loaded_asset_sha256: expectedLoadedAssets,
    loaded_asset_sha256_by_entry: loadedAssetHashesByEntry,
    loaded_assets_match_disk: loadedAssetsMatchDisk,
    project_roots: projectRoots,
    app_paths: appPaths,
    build_ids: unique(probes.map((probe) => probe.audit.buildId)),
    ui_contract_versions: unique(probes.map((probe) => probe.audit.uiContractVersion)),
    repair_labels: unique(probes.map((probe) => probe.audit.repairLabel)),
    console_errors: consoleErrors,
    page_errors: pageErrors,
    http_errors: httpErrors,
    summary: { pass: checks.length - fail, fail, total: checks.length },
  };
  process.stdout.write(`${JSON.stringify(payload)}\n`);
  process.exitCode = fail === 0 ? 0 : 1;
}

main().catch((error) => {
  process.stdout.write(
    `${JSON.stringify({
      schema: "PFIV024ReadOnlyRuntimeSnapshotV1",
      status: "Blocked",
      mode: "read_only_no_pfi_data_or_reports_write",
      error: String(error && error.stack ? error.stack : error),
      summary: { pass: 0, fail: 1, total: 1 },
    })}\n`
  );
  process.exitCode = 1;
});
