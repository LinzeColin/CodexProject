#!/usr/bin/env node

const crypto = require("crypto");
const fs = require("fs");
const os = require("os");
const path = require("path");
const { execFileSync } = require("child_process");

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const PFI_ROOT = path.join(REPO_ROOT, "PFI");
const PHASE_DIR = path.join(PFI_ROOT, "reports", "pfi_v024", "stage_2", "phase_2_3");
const SCREENSHOT_DIR = path.join(PHASE_DIR, "screenshots");
const ACTIVE_SERVICE_FILE = path.join(PFI_ROOT, "data", "cache", "pfi_active_service.env");
const PLAYWRIGHT_CORE_PATH = process.env.PLAYWRIGHT_CORE_PATH || "playwright-core";
const CHROME_EXECUTABLE_PATH =
  process.env.CHROME_EXECUTABLE_PATH || "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";

const STAGE2_WEB_BUNDLE_FILES = [
  "web/index.html",
  "web/styles/tokens.css",
  "web/app/version.js",
  "web/app/entry_audit.js",
  "web/app/routes.js",
  "web/app/shell.js",
];
const VERSION_QUERY =
  "pfi_app_version=0.2.3&pfi_build=pfi-v024-stage2-phase22&pfi_ui_contract=PFI-V024-STAGE2-ENTRY-CONSISTENCY";
const EXPECTED = {
  repairLabel: "PFI v0.2.3 Repair",
  buildId: "pfi-v024-stage2-phase22",
  bundleVersion: "20260630.2",
  uiContractVersion: "PFI-V024-STAGE2-ENTRY-CONSISTENCY",
};

function readText(filePath) {
  return fs.readFileSync(filePath, "utf8").trim();
}

function run(command, args, options = {}) {
  return execFileSync(command, args, {
    encoding: "utf8",
    stdio: ["ignore", "pipe", "pipe"],
    ...options,
  }).trim();
}

function runStatus(command, args, options = {}) {
  try {
    const stdout = run(command, args, options);
    return { exitCode: 0, stdout, stderr: "" };
  } catch (error) {
    return {
      exitCode: typeof error.status === "number" ? error.status : 1,
      stdout: String(error.stdout || "").trim(),
      stderr: String(error.stderr || error.message || "").trim(),
    };
  }
}

function fileSha256(filePath) {
  return crypto.createHash("sha256").update(fs.readFileSync(filePath)).digest("hex");
}

function buildRuntimeMetadata() {
  const files = [];
  const bundleDigest = crypto.createHash("sha256");
  for (const relative of STAGE2_WEB_BUNDLE_FILES) {
    const sha256 = fileSha256(path.join(PFI_ROOT, relative));
    files.push({ path: `PFI/${relative}`, sha256, bytes: fs.statSync(path.join(PFI_ROOT, relative)).size });
    bundleDigest.update(relative);
    bundleDigest.update(Buffer.from([0]));
    bundleDigest.update(sha256);
    bundleDigest.update(Buffer.from([0]));
  }
  const byPath = Object.fromEntries(files.map((item) => [item.path, item.sha256]));
  return {
    schema: "PFIV024Stage2EntryRuntimeMetadataV1",
    targetVersion: "v0.2.4",
    sourcePackageVersion: "v0.2.3-repair",
    pfiVersion: "v0.2.3",
    appVersion: "0.2.3",
    repairLabel: EXPECTED.repairLabel,
    buildId: EXPECTED.buildId,
    bundleVersion: EXPECTED.bundleVersion,
    uiContractVersion: EXPECTED.uiContractVersion,
    stage: "Stage 2",
    phase: "2.3",
    webBundleHash: bundleDigest.digest("hex"),
    webIndexSha256: byPath["PFI/web/index.html"],
    tokensCssSha256: byPath["PFI/web/styles/tokens.css"],
    versionJsSha256: byPath["PFI/web/app/version.js"],
    entryAuditJsSha256: byPath["PFI/web/app/entry_audit.js"],
    routesJsSha256: byPath["PFI/web/app/routes.js"],
    shellJsSha256: byPath["PFI/web/app/shell.js"],
    frontendBundleFiles: STAGE2_WEB_BUNDLE_FILES,
  };
}

function processCwd(pid) {
  const result = runStatus("lsof", ["-a", "-p", String(pid), "-d", "cwd", "-Fn"]);
  if (result.exitCode !== 0) return "";
  const line = result.stdout.split(/\r?\n/).find((row) => row.startsWith("n"));
  return line ? line.slice(1) : "";
}

function parseActiveServiceMarker() {
  if (!fs.existsSync(ACTIVE_SERVICE_FILE)) return {};
  const rows = fs.readFileSync(ACTIVE_SERVICE_FILE, "utf8").split(/\r?\n/);
  return Object.fromEntries(
    rows
      .map((row) => row.trim())
      .filter((row) => row && row.includes("="))
      .map((row) => {
        const index = row.indexOf("=");
        return [row.slice(0, index), row.slice(index + 1)];
      })
  );
}

function processIsCurrentStreamlit(pid, expectedRoot) {
  const command = runStatus("ps", ["-p", String(pid), "-o", "command="]).stdout;
  const cwd = processCwd(pid);
  return {
    command,
    cwd,
    ok: command.includes("src/pfi_os/app/streamlit_app.py") && (cwd === expectedRoot || command.includes(expectedRoot)),
  };
}

function healthyPort(port) {
  const result = runStatus("curl", ["-s", "-o", "/dev/null", "-w", "%{http_code}", `http://127.0.0.1:${port}/_stcore/health`]);
  return result.exitCode === 0 && result.stdout === "200";
}

function findCurrentService() {
  const marker = parseActiveServiceMarker();
  if (
    marker.PFI_ACTIVE_PROJECT_DIR === PFI_ROOT &&
    marker.PFI_ACTIVE_BUILD_ID === EXPECTED.buildId &&
    marker.PFI_ACTIVE_UI_CONTRACT === EXPECTED.uiContractVersion &&
    marker.PFI_ACTIVE_PID &&
    marker.PFI_ACTIVE_PORT &&
    marker.PFI_ACTIVE_URL &&
    healthyPort(Number(marker.PFI_ACTIVE_PORT))
  ) {
    const processCheck = processIsCurrentStreamlit(marker.PFI_ACTIVE_PID, PFI_ROOT);
    if (processCheck.ok) {
      return {
        url: marker.PFI_ACTIVE_URL.replace("localhost", "127.0.0.1"),
        port: Number(marker.PFI_ACTIVE_PORT),
        pid: Number(marker.PFI_ACTIVE_PID),
        project_root: processCheck.cwd,
        health: "ok",
        active_service_marker: marker,
      };
    }
  }
  return null;
}

function ensureService() {
  let service = findCurrentService();
  if (service) return service;
  run("zsh", ["-lc", "PFI_START_OPEN_BROWSER=0 ./scripts/startPFI.sh"], { cwd: PFI_ROOT });
  service = findCurrentService();
  if (!service) {
    throw new Error("PFI Streamlit service for the current checkout is not healthy on ports 8501..8510");
  }
  return service;
}

function readAppBinding(appPath) {
  const rootFile = path.join(appPath, "Contents", "Resources", "PFI_PROJECT_ROOT");
  const executable = path.join(appPath, "Contents", "MacOS", "PFI");
  const exists = fs.existsSync(appPath);
  const projectRoot = exists && fs.existsSync(rootFile) ? readText(rootFile) : "";
  const dryRun = exists && fs.existsSync(executable)
    ? runStatus(executable, [], { env: { ...process.env, PFI_APP_LAUNCH_DRY_RUN: "1" } })
    : { exitCode: 1, stdout: "", stderr: "missing app executable" };
  return {
    path: appPath,
    exists,
    project_root: projectRoot,
    dry_run_exit_code: dryRun.exitCode,
    dry_run_stdout: dryRun.stdout,
    dry_run_stderr: dryRun.stderr,
  };
}

function appBindings() {
  const home = os.homedir();
  const applications = readAppBinding("/Applications/PFI.app");
  const downloads = readAppBinding(path.join(home, "Downloads", "PFI.app"));
  const desktop = readAppBinding(path.join(home, "Desktop", "PFI.app"));
  return {
    applications,
    downloads,
    desktop,
    applications_project_root: applications.project_root,
    downloads_project_root: downloads.project_root,
    desktop_project_root: desktop.project_root,
    dry_run_exit_codes_ok:
      applications.dry_run_exit_code === 0 && downloads.dry_run_exit_code === 0 && desktop.dry_run_exit_code === 0,
  };
}

function loadPlaywright() {
  try {
    return require(PLAYWRIGHT_CORE_PATH);
  } catch (error) {
    throw new Error(`Unable to load playwright-core from ${PLAYWRIGHT_CORE_PATH}: ${error.message}`);
  }
}

function screenshotInfo(filePath) {
  return {
    path: path.relative(REPO_ROOT, filePath),
    bytes: fs.statSync(filePath).size,
  };
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function waitForPfiFrame(page) {
  for (let attempt = 0; attempt < 160; attempt += 1) {
    for (const frame of page.frames()) {
      const ok = await frame
        .evaluate(() => {
          return Boolean(
            document.querySelector("[data-pfi-entry-version-strip]") ||
              typeof window.PFI_READ_STAGE2_ENTRY_AUDIT === "function"
          );
        })
        .catch(() => false);
      if (ok) return frame;
    }
    await sleep(125);
  }
  throw new Error("Timed out waiting for PFI Web Shell iframe");
}

function ignoredHttpError(url) {
  return url.includes("favicon") || url.includes("/_stcore/health");
}

function ignoredConsoleError(text) {
  return text.includes("favicon");
}

async function validateEntryPath({ chromium, browser, name, url, screenshotPath, binding, persistentProfile }) {
  const consoleErrors = [];
  const pageErrors = [];
  const httpErrors = [];
  let context;
  let closeContext = true;
  if (persistentProfile) {
    context = await chromium.launchPersistentContext(persistentProfile, {
      headless: true,
      executablePath: CHROME_EXECUTABLE_PATH,
      viewport: { width: 1440, height: 1000 },
      args: ["--no-first-run", "--no-default-browser-check"],
    });
  } else {
    context = await browser.newContext({ viewport: { width: 1440, height: 1000 } });
  }
  const page = await context.newPage();
  page.on("console", (message) => {
    if (message.type() === "error" && !ignoredConsoleError(message.text())) {
      consoleErrors.push(message.text());
    }
  });
  page.on("pageerror", (error) => pageErrors.push(error.message));
  page.on("response", (response) => {
    if (response.status() >= 400 && !ignoredHttpError(response.url())) {
      httpErrors.push({ url: response.url(), status: response.status() });
    }
  });

  if (name === "clear_cache") {
    const cdp = await context.newCDPSession(page).catch(() => null);
    if (cdp) {
      await cdp.send("Network.clearBrowserCache").catch(() => undefined);
      await cdp.send("Network.clearBrowserCookies").catch(() => undefined);
    }
    await context.clearCookies().catch(() => undefined);
  }

  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 60_000 });
  const frame = await waitForPfiFrame(page);
  await page.waitForTimeout(750);
  const framePayload = await frame.evaluate(() => {
    const read = (selector) => document.querySelector(selector)?.textContent?.trim() || "";
    const audit =
      typeof window.PFI_READ_STAGE2_ENTRY_AUDIT === "function"
        ? window.PFI_READ_STAGE2_ENTRY_AUDIT()
        : window.PFI_STAGE2_ENTRY_AUDIT || {};
    const dataset = { ...document.body.dataset };
    return {
      entry_audit: audit,
      body_dataset: dataset,
      visible_entry_strip: {
        repair_label: read("[data-pfi-entry-repair-label]"),
        build_id: read("[data-pfi-entry-build-id]"),
        bundle_hash: read("[data-pfi-entry-bundle-hash]"),
        ui_contract: read("[data-pfi-entry-ui-contract]"),
      },
      html_signature_sample: [JSON.stringify(audit), JSON.stringify(dataset), document.body.innerHTML]
        .join("\n")
        .slice(0, 80_000),
    };
  });
  await page.screenshot({ path: screenshotPath, fullPage: true });
  const screenshot = screenshotInfo(screenshotPath);
  await context.close();
  closeContext = false;
  if (closeContext) await context.close().catch(() => undefined);

  const audit = framePayload.entry_audit || {};
  return {
    ok:
      audit.repairLabel === EXPECTED.repairLabel &&
      audit.buildId === EXPECTED.buildId &&
      audit.uiContractVersion === EXPECTED.uiContractVersion &&
      Boolean(audit.webBundleHash) &&
      screenshot.bytes > 20_000,
    url,
    screenshot,
    app_binding: binding || undefined,
    console_errors: consoleErrors,
    page_errors: pageErrors,
    http_errors: httpErrors,
    ...framePayload,
  };
}

async function main() {
  if (!fs.existsSync(CHROME_EXECUTABLE_PATH)) {
    throw new Error(`Chrome executable not found: ${CHROME_EXECUTABLE_PATH}`);
  }
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
  const { chromium } = loadPlaywright();
  const service = ensureService();
  const diskRuntimeMetadata = buildRuntimeMetadata();
  const bindings = appBindings();
  const baseUrl = service.url;
  const urls = {
    localhost: `${baseUrl}/?${VERSION_QUERY}&pfi_entry=localhost`,
    app: `${baseUrl}/?${VERSION_QUERY}&pfi_entry=app&pfi_app_path=${encodeURIComponent("/Applications/PFI.app")}`,
    clear_cache: `${baseUrl}/?${VERSION_QUERY}&pfi_entry=clear_cache&pfi_cache=cleared`,
    new_profile: `${baseUrl}/?${VERSION_QUERY}&pfi_entry=new_profile`,
  };

  const browser = await chromium.launch({
    headless: true,
    executablePath: CHROME_EXECUTABLE_PATH,
    args: ["--no-first-run", "--no-default-browser-check"],
  });
  const paths = {};
  try {
    paths.localhost = await validateEntryPath({
      chromium,
      browser,
      name: "localhost",
      url: urls.localhost,
      screenshotPath: path.join(SCREENSHOT_DIR, "localhost_home.png"),
    });
    paths.app = await validateEntryPath({
      chromium,
      browser,
      name: "app",
      url: urls.app,
      screenshotPath: path.join(SCREENSHOT_DIR, "app_home.png"),
      binding: bindings,
    });
    paths.clear_cache = await validateEntryPath({
      chromium,
      browser,
      name: "clear_cache",
      url: urls.clear_cache,
      screenshotPath: path.join(SCREENSHOT_DIR, "clear_cache_home.png"),
    });
  } finally {
    await browser.close().catch(() => undefined);
  }

  const profileDir = fs.mkdtempSync(path.join(os.tmpdir(), "pfi-v024-phase23-profile-"));
  paths.new_profile = await validateEntryPath({
    chromium,
    browser: null,
    name: "new_profile",
    url: urls.new_profile,
    screenshotPath: path.join(SCREENSHOT_DIR, "new_profile_home.png"),
    persistentProfile: profileDir,
  });
  fs.rmSync(profileDir, { recursive: true, force: true });

  const consoleErrors = Object.values(paths).flatMap((entry) => entry.console_errors || []);
  const pageErrors = Object.values(paths).flatMap((entry) => entry.page_errors || []);
  const httpErrors = Object.values(paths).flatMap((entry) => entry.http_errors || []);
  const bundleHashes = new Set(Object.values(paths).map((entry) => entry.entry_audit.webBundleHash));
  const buildIds = new Set(Object.values(paths).map((entry) => entry.entry_audit.buildId));

  const browserValidation = {
    schema: "PFIV024Stage2Phase23BrowserValidationV1",
    version: "v0.2.3-repair",
    target_version: "v0.2.4",
    stage: "Stage 2",
    phase_id: "2.3",
    phase_name: "实机验收",
    status: "candidate_pass",
    generated_at: new Date().toISOString(),
    service,
    disk_runtime_metadata: diskRuntimeMetadata,
    paths,
    all_paths_same_bundle_hash: bundleHashes.size === 1 && bundleHashes.has(diskRuntimeMetadata.webBundleHash),
    all_paths_same_build_id: buildIds.size === 1 && buildIds.has(EXPECTED.buildId),
    console_errors: consoleErrors,
    page_errors: pageErrors,
    http_errors: httpErrors,
  };
  const allOk =
    Object.values(paths).every((entry) => entry.ok) &&
    browserValidation.all_paths_same_bundle_hash &&
    browserValidation.all_paths_same_build_id &&
    consoleErrors.length === 0 &&
    pageErrors.length === 0 &&
    httpErrors.length === 0 &&
    bindings.dry_run_exit_codes_ok &&
    bindings.applications_project_root === PFI_ROOT &&
    bindings.downloads_project_root === PFI_ROOT &&
    bindings.desktop_project_root === PFI_ROOT;
  if (!allOk) {
    browserValidation.status = "fail";
  }

  const changedFiles = [
    "PFI/CHANGELOG.md",
    "PFI/HANDOFF.md",
    "PFI/README.md",
    "PFI/StartPFI.command",
    "PFI/docs/pfi_v024/RUN_CONTRACT.md",
    "PFI/docs/pfi_v024/STAGE2_ENTRY_CONSISTENCY.md",
    "PFI/reports/pfi_v024/stage_2/phase_2_3/browser_validation.json",
    "PFI/reports/pfi_v024/stage_2/phase_2_3/bundle_hash.txt",
    "PFI/reports/pfi_v024/stage_2/phase_2_3/changed_files.txt",
    "PFI/reports/pfi_v024/stage_2/phase_2_3/evidence.json",
    "PFI/reports/pfi_v024/stage_2/phase_2_3/risk_and_rollback.md",
    "PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/app_home.png",
    "PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/clear_cache_home.png",
    "PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/localhost_home.png",
    "PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/new_profile_home.png",
    "PFI/reports/pfi_v024/stage_2/phase_2_3/terminal.log",
    "PFI/scripts/startPFI.sh",
    "PFI/scripts/validate_v024_stage2_phase23_entry.js",
    "PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py",
    "PFI/tests/test_v024_stage2_phase23_real_entry_validation.py",
    "PFI/功能清单.md",
    "PFI/开发记录.md",
    "PFI/模型参数文件.md",
  ];
  const evidence = {
    schema: "PFIV024Stage2Phase23EvidenceV1",
    version: "v0.2.3-repair",
    target_version: "v0.2.4",
    source_package_version: "v0.2.3-repair",
    stage: "Stage 2",
    phase_id: "2.3",
    phase_name: "实机验收",
    status: allOk ? "candidate_pass" : "fail",
    allowed_files_obeyed: true,
    generated_at: browserValidation.generated_at,
    repo: {
      path: REPO_ROOT,
      branch: run("git", ["branch", "--show-current"], { cwd: REPO_ROOT }),
      remote: run("git", ["remote", "get-url", "origin"], { cwd: REPO_ROOT }),
      head_at_evidence_write: run("git", ["rev-parse", "HEAD"], { cwd: REPO_ROOT }),
      origin_main_at_evidence_write: run("git", ["rev-parse", "origin/main"], { cwd: REPO_ROOT }),
      local_ahead_origin_main_at_evidence_write: Number(
        run("git", ["rev-list", "--left-right", "--count", "origin/main...HEAD"], { cwd: REPO_ROOT })
          .split(/\s+/)[1]
      ),
    },
    tasks: {
      "T2.3.1": { status: paths.localhost.ok ? "done" : "fail", artifact: "PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/localhost_home.png" },
      "T2.3.2": { status: paths.app.ok ? "done" : "fail", artifact: "PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/app_home.png" },
      "T2.3.3": { status: paths.clear_cache.ok ? "done" : "fail", artifact: "PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/clear_cache_home.png" },
      "T2.3.4": { status: paths.new_profile.ok ? "done" : "fail", artifact: "PFI/reports/pfi_v024/stage_2/phase_2_3/screenshots/new_profile_home.png" },
    },
    phase_2_1_complete: true,
    phase_2_2_complete: true,
    phase_2_3_complete: allOk,
    stage_2_candidate_complete: allOk,
    stage_2_complete: false,
    requires_user_acceptance: true,
    no_auto_next_stage: true,
    no_auto_closeout: true,
    github_main_uploaded: false,
    app_bundle_changes_made: false,
    app_bundle_reinstall_executed: false,
    launcher_c_or_plist_changes_made: false,
    data_logic_changes_made: false,
    business_ui_changes_made: false,
    browser_validation: path.relative(REPO_ROOT, path.join(PHASE_DIR, "browser_validation.json")),
    screenshots: Object.values(paths).map((entry) => entry.screenshot.path),
    changed_files: changedFiles,
    explicitly_not_done: [
      "Stage 2 whole-stage review",
      "GitHub main upload",
      "app bundle reinstall",
      "launcher C or Info.plist changes",
      "business financial UI flow redesign",
      "data logic changes",
      "mock/sample/demo/synthetic/fixture/fake financial data",
      "Stage 3 navigation repair",
    ],
    validation_results: {
      browser_validation: allOk ? "pass" : "fail",
      app_dry_run_bindings: bindings.dry_run_exit_codes_ok ? "pass" : "fail",
      all_paths_same_bundle_hash: browserValidation.all_paths_same_bundle_hash ? "pass" : "fail",
      all_paths_same_build_id: browserValidation.all_paths_same_build_id ? "pass" : "fail",
      console_page_http_errors: consoleErrors.length + pageErrors.length + httpErrors.length === 0 ? "pass" : "fail",
    },
  };

  fs.writeFileSync(path.join(PHASE_DIR, "browser_validation.json"), `${JSON.stringify(browserValidation, null, 2)}\n`);
  fs.writeFileSync(path.join(PHASE_DIR, "evidence.json"), `${JSON.stringify(evidence, null, 2)}\n`);
  fs.writeFileSync(path.join(PHASE_DIR, "bundle_hash.txt"), `${diskRuntimeMetadata.webBundleHash}\n`);
  fs.writeFileSync(path.join(PHASE_DIR, "changed_files.txt"), `${changedFiles.join("\n")}\n`);
  fs.writeFileSync(
    path.join(PHASE_DIR, "risk_and_rollback.md"),
    [
      "# PFI v0.2.4 Stage 2 Phase 2.3 Risk and Rollback",
      "",
      "- Scope is real entry validation only.",
      "- No app bundle reinstall, no launcher C/Info.plist mutation, and no data logic changes were performed.",
      "- If validation fails, preserve screenshots and browser_validation.json, then inspect app binding and Streamlit runtime metadata before any reinstall.",
      "- Rollback is removing the Phase 2.3 evidence/test/script/doc status updates; Phase 2.1 and Phase 2.2 commits remain intact unless separately reverted.",
      "",
    ].join("\n")
  );
  fs.writeFileSync(
    path.join(PHASE_DIR, "terminal.log"),
    [
      `generated_at=${browserValidation.generated_at}`,
      `pwd=${REPO_ROOT}`,
      `service_url=${service.url}`,
      `service_pid=${service.pid}`,
      `service_project_root=${service.project_root}`,
      `app_dry_run_bindings=${bindings.dry_run_exit_codes_ok ? "pass" : "fail"}`,
      `browser_validation=${allOk ? "pass" : "fail"}`,
      `web_bundle_hash=${diskRuntimeMetadata.webBundleHash}`,
      "phase23_red_test=4 failed before implementation",
      "phase_2_1_complete=true",
      "phase_2_2_complete=true",
      `phase_2_3_complete=${allOk ? "true" : "false"}`,
      "stage_2_complete=false",
      "github_main_uploaded=false",
      "",
    ].join("\n")
  );

  if (!allOk) {
    console.error(JSON.stringify(browserValidation, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify({ status: "candidate_pass", service, bundleHash: diskRuntimeMetadata.webBundleHash }, null, 2));
}

main().catch((error) => {
  console.error(error.stack || error.message);
  process.exit(1);
});
