#!/usr/bin/env node

import crypto from "node:crypto";
import {
  chmod,
  lstat,
  readFile,
  readdir,
  realpath,
  rename,
  rm,
  writeFile,
} from "node:fs/promises";
import { createRequire } from "node:module";
import os from "node:os";
import path from "node:path";
import { TextDecoder } from "node:util";
import { fileURLToPath } from "node:url";
import { deflateRawSync, inflateRawSync } from "node:zlib";

const STATE_SCHEMA = "PFIV025Stage1Phase13CandidateStateV1";
const RESULT_SCHEMA = "PFIV025Stage1WholeReviewBrowserValidationV1";
const ACTIVE_SCHEMA = "PFIActiveServiceV1";
const RESERVED_PORTS = new Set([8501, 8502, 8766]);
const TRACE_FILE = "playwright_trace.zip";
const SCREENSHOT_FILE = "browser_official_ui.png";
const IDENTITY_SCREENSHOT_FILE = "browser_release_identity.png";
const RESULT_FILE = "browser_validation.json";
const ACCESSIBILITY_FILE = "accessibility_tree.json";
const FRONTEND_IDENTITY_FILE = "frontend_source_identity.json";
const RUNTIME_API_FILE = "runtime_api_evidence.json";
const PRIVACY_FILE = "privacy_boundary.json";
const STAGING_TRACE_FILE = "stage1_phase13_browser_trace.raw.zip";
const STAGING_SCREENSHOT_FILE = "stage1_phase13_browser_screenshot.raw.png";
const STAGING_IDENTITY_SCREENSHOT_FILE = "stage1_phase13_browser_identity.raw.png";
const CANDIDATE_IDENTITY_FILES = Object.freeze([
  "Contents/MacOS/PFI",
  "Contents/Info.plist",
  "Contents/_CodeSignature/CodeResources",
  "Contents/Resources/PFI_PROJECT_ROOT",
  "Contents/Resources/PFI_STAGE1_ISOLATED_ROOT",
  "Contents/Resources/PFI_STAGE1_STREAMLIT_PORT",
  "Contents/Resources/PFI_STAGE1_HEARTBEAT_PORT",
]);
const FRONTEND_FILES = Object.freeze([
  "PFI/web/index.html",
  "PFI/web/styles/tokens.css",
  "PFI/web/styles.css",
  "PFI/web/app/version.js",
  "PFI/web/app/entry_audit.js",
  "PFI/web/app/navigation.js",
  "PFI/web/app/routes.js",
  "PFI/web/app/data_state.js",
  "PFI/web/app/pages/stage4Subpages.js",
  "PFI/web/app/pages/stage5Subpages.js",
  "PFI/web/app/ux_state.js",
  "PFI/web/app/pages/home.js",
  "PFI/web/app/pages/reports.js",
  "PFI/web/app/shell.js",
]);
const BACKEND_FILES = Object.freeze([
  "PFI/StartPFI.command",
  "PFI/config/jobs/v025_dependency_registry.json",
  "PFI/macos/PFI_launcher.c",
  "PFI/scripts/pfiReleaseIdentity.sh",
  "PFI/scripts/pfiRuntime.sh",
  "PFI/scripts/v025/release_cache_contract.py",
  "PFI/scripts/v025/run_streamlit_with_release_cache.py",
  "PFI/scripts/v025/stage1_phase13_candidate_env.sh",
  "PFI/src/pfi_os/app/streamlit_app.py",
  "PFI/src/pfi_os/application/jobs/__init__.py",
  "PFI/src/pfi_os/application/jobs/lifecycle.py",
  "PFI/src/pfi_os/application/read_model_status.py",
  "PFI/src/pfi_os/application/supervisor/__init__.py",
  "PFI/src/pfi_os/application/supervisor/runtime_jobs.py",
  "PFI/src/pfi_os/application/use_cases/__init__.py",
  "PFI/src/pfi_os/application/use_cases/holding_settings_persistence.py",
  "PFI/src/pfi_os/application/use_cases/import_review_ledger.py",
  "PFI/src/pfi_os/application/use_cases/metric_lineage_drilldown.py",
  "PFI/src/pfi_os/infrastructure/__init__.py",
  "PFI/src/pfi_os/infrastructure/jobs/__init__.py",
  "PFI/src/pfi_os/infrastructure/jobs/sqlite_store.py",
  "PFI/src/pfi_os/infrastructure/operational_holding_settings_store.py",
  "PFI/src/pfi_os/infrastructure/operational_import_store.py",
  "PFI/src/pfi_os/migrations/v025_stage7_holding_idempotency.sql",
  "PFI/src/pfi_os/migrations/v025_stage7_holding_settings.sql",
  "PFI/src/pfi_os/migrations/v025_stage7_import_review_ledger.sql",
  "PFI/src/pfi_os/observability/__init__.py",
  "PFI/src/pfi_os/observability/job_trace.py",
  "PFI/src/pfi_os/system/shutdown_monitor.py",
  "PFI/src/pfi_v02/runtime_diff_v025.py",
  "PFI/src/pfi_v02/stage_v021_runtime_api.py",
  "PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py",
]);
const FRONTEND_GLOBALS = Object.freeze([
  "PFI_RELEASE_IDENTITY",
  "PFI_STAGE2_ENTRY_AUDIT",
  "PFI_V024_STAGE3_NAVIGATION",
  "PFI_V024_STAGE3_ROUTES",
  "PFI_V024_STAGE4_DATA_STATE",
  "PFI_V023_STAGE4_PAGES",
  "PFI_V024_STAGE5_PAGES",
  "PFI_V024_STAGE5_UX_STATE",
  "PFI_V024_STAGE5_HOME",
  "PFI_V024_STAGE7_REPORTS",
  "PFI_STAGE1_SHELL",
]);
const PRIMARY_ROUTES = Object.freeze([
  Object.freeze({ index: 1, workspace: "home", routeAlias: "/home" }),
  Object.freeze({ index: 2, workspace: "accounts", routeAlias: "/accounts" }),
  Object.freeze({ index: 3, workspace: "ledger", routeAlias: "/ledger" }),
  Object.freeze({ index: 4, workspace: "investment", routeAlias: "/investment" }),
  Object.freeze({ index: 5, workspace: "consumption", routeAlias: "/consumption" }),
  Object.freeze({ index: 6, workspace: "sync", routeAlias: "/sources-upload" }),
  Object.freeze({ index: 7, workspace: "recommendations", routeAlias: "/review" }),
  Object.freeze({ index: 8, workspace: "insights", routeAlias: "/reports" }),
  Object.freeze({ index: 9, workspace: "market_research", routeAlias: "/market-research" }),
  Object.freeze({ index: 10, workspace: "settings", routeAlias: "/settings" }),
]);
const REQUIRED_API_HEADERS = Object.freeze([
  "X-PFI-Running-Backend-SHA256",
  "X-PFI-Release-Manifest-SHA256",
  "X-PFI-Streamlit-Cache-Key",
  "X-PFI-Read-Model-SHA256",
  "X-PFI-Data-Boundary",
]);
const MAX_ZIP_ENTRIES = 10_000;
const MAX_ZIP_ENTRY_SIZE = 96 * 1024 * 1024;
const MAX_ZIP_TOTAL_SIZE = 384 * 1024 * 1024;
const UTF8_DECODER = new TextDecoder("utf-8", { fatal: true });
const REDACTED = "${REDACTED}";
const REDACTED_PID = "${REDACTED_PID}";
const EVIDENCE_ROOT_PATTERN = /^pfi-v025-s1p13-evidence-[A-Za-z0-9._-]+$/;
const require = createRequire(import.meta.url);

class BrowserValidationError extends Error {}

function fail(message) {
  throw new BrowserValidationError(message);
}

function parseArgs(argv) {
  const parsed = {};
  for (let index = 0; index < argv.length; index += 1) {
    const token = argv[index];
    if (token !== "--state" && token !== "--output-dir") {
      fail("invalid arguments");
    }
    const value = argv[index + 1];
    if (!value || value.startsWith("--")) fail("invalid arguments");
    const key = token === "--state" ? "statePath" : "outputDir";
    if (parsed[key]) fail("invalid arguments");
    parsed[key] = value;
    index += 1;
  }
  if (!parsed.statePath || !parsed.outputDir) fail("invalid arguments");
  return parsed;
}

function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function isHex(value, length) {
  return typeof value === "string" && new RegExp(`^[0-9a-f]{${length}}$`).test(value);
}

function sha256(buffer) {
  return crypto.createHash("sha256").update(buffer).digest("hex");
}

function hashRecords(records) {
  return sha256(
    Buffer.concat(
      [...records]
        .sort((left, right) => (left.path < right.path ? -1 : left.path > right.path ? 1 : 0))
        .map((record) => Buffer.from(`${record.path}\0${record.sha256}\n`, "utf8")),
    ),
  );
}

async function computeReleaseSourceIdentity(projectRoot) {
  const repoRoot = path.dirname(projectRoot);
  const frontendRecords = [];
  for (const relative of FRONTEND_FILES) {
    const absolute = path.join(repoRoot, relative);
    let bytes = await readFile(absolute);
    if (relative === "PFI/web/index.html") {
      const source = bytes.toString("utf8");
      const pattern = /(<script\s+type="application\/json"\s+id="pfi-release-manifest">)[\s\S]*?(<\/script>)/;
      if (!pattern.test(source)) fail("release index manifest block is unavailable");
      bytes = Buffer.from(source.replace(pattern, "$1{}$2"), "utf8");
    }
    frontendRecords.push({ path: relative, sha256: sha256(bytes), bytes: bytes.length });
  }
  const backendRecords = [];
  for (const relative of BACKEND_FILES) {
    const bytes = await readFile(path.join(repoRoot, relative));
    backendRecords.push({ path: relative, sha256: sha256(bytes), bytes: bytes.length });
  }
  return {
    frontend: {
      files: frontendRecords,
      file_count: frontendRecords.length,
      sha256: hashRecords(frontendRecords),
    },
    backend: {
      definition: "release-critical identity/cache entry closure",
      files: backendRecords,
      file_count: backendRecords.length,
      sha256: hashRecords(backendRecords),
    },
  };
}

function pathWithin(child, parent) {
  const relative = path.relative(parent, child);
  return relative === "" || (!relative.startsWith("..") && !path.isAbsolute(relative));
}

async function readCandidateState(requestedPath) {
  const requestedStatePath = path.resolve(requestedPath);
  let statePath;
  let stateStat;
  let requestedStateStat;
  let rootStat;
  let candidateAppStat;
  let raw;
  try {
    requestedStateStat = await lstat(requestedStatePath);
    statePath = await realpath(requestedStatePath);
    stateStat = await lstat(statePath);
    rootStat = await lstat(path.dirname(statePath));
    candidateAppStat = await lstat(path.join(path.dirname(statePath), "PFI.app"));
    raw = await readFile(statePath, "utf8");
  } catch (_error) {
    fail("candidate state is unavailable");
  }
  const isolatedRoot = path.dirname(statePath);
  const rootName = path.basename(isolatedRoot);
  if (
    path.basename(statePath) !== "state.json" ||
    requestedStatePath !== statePath ||
    path.dirname(isolatedRoot) !== "/private/tmp" ||
    !/^pfi-v025-s1p13-[A-Za-z0-9._-]+$/.test(rootName) ||
    requestedStateStat.isSymbolicLink() ||
    !stateStat.isFile() ||
    stateStat.isSymbolicLink() ||
    !rootStat.isDirectory() ||
    rootStat.isSymbolicLink() ||
    !candidateAppStat.isDirectory() ||
    candidateAppStat.isSymbolicLink() ||
    (typeof process.getuid === "function" && stateStat.uid !== process.getuid()) ||
    (typeof process.getuid === "function" && rootStat.uid !== process.getuid()) ||
    (typeof process.getuid === "function" && candidateAppStat.uid !== process.getuid()) ||
    (stateStat.mode & 0o777) !== 0o600 ||
    (rootStat.mode & 0o777) !== 0o700
  ) {
    fail("candidate state boundary is invalid");
  }
  let state;
  try {
    state = JSON.parse(raw);
  } catch (_error) {
    fail("candidate state is invalid");
  }
  const port = Number(state?.streamlit_port);
  const heartbeatPort = Number(state?.heartbeat_port);
  const projectRoot = path.resolve(String(state?.project_root || ""));
  const checkoutCommit = String(state?.checkout_commit || "");
  const checkoutBindingSha256 = sha256(
    Buffer.from(`${checkoutCommit}\0${projectRoot}`, "utf8"),
  );
  if (
    !isPlainObject(state) ||
    state.schema !== STATE_SCHEMA ||
    path.resolve(String(state.state_path || "")) !== statePath ||
    path.resolve(String(state.isolated_root || "")) !== isolatedRoot ||
    path.resolve(String(state.candidate_app || "")) !== path.join(isolatedRoot, "PFI.app") ||
    path.resolve(String(state.active_marker_path || "")) !==
      path.join(isolatedRoot, "runtime", "pfi_active_service.env") ||
    String(state.project_root || "") !== projectRoot ||
    path.resolve(String(state.git_root || "")) !== path.dirname(projectRoot) ||
    !Number.isInteger(port) ||
    port < 1024 ||
    port > 65535 ||
    RESERVED_PORTS.has(port) ||
    !Number.isInteger(heartbeatPort) ||
    heartbeatPort < 1024 ||
    heartbeatPort > 65535 ||
    heartbeatPort === port ||
    RESERVED_PORTS.has(heartbeatPort) ||
    !isHex(checkoutCommit, 40) ||
    state.checkout_binding_sha256 !== checkoutBindingSha256 ||
    !isHex(state.source_app_tree_sha256, 64) ||
    !isHex(state.copied_app_tree_sha256, 64) ||
    !isHex(state.candidate_app_path_sha256, 64) ||
    !isHex(state.candidate_executable_sha256, 64) ||
    !isHex(state.candidate_bundle_sha256, 64) ||
    state.launchservices_registered !== true ||
    state.launchservices_registration_verified !== true ||
    !Number.isInteger(state.launchservices_registration_record_count) ||
    state.launchservices_registration_record_count < 1 ||
    !isHex(state.launchservices_registration_record_sha256, 64)
  ) {
    fail("candidate state identity is invalid");
  }
  return { state, statePath, isolatedRoot, port, heartbeatPort, projectRoot };
}

function parseMarker(raw) {
  if (
    raw.length === 0 ||
    raw.length > 65_536 ||
    !raw.endsWith("\n") ||
    raw.slice(0, -1).includes("\n\n") ||
    /[^\x20-\x7e\n]/.test(raw)
  ) {
    fail("active marker format is invalid");
  }
  const values = {};
  for (const line of raw.slice(0, -1).split("\n")) {
    const separator = line.indexOf("=");
    if (separator <= 0) fail("active marker format is invalid");
    const key = line.slice(0, separator);
    if (Object.hasOwn(values, key)) fail("active marker format is invalid");
    values[key] = line.slice(separator + 1);
  }
  return values;
}

function isExpectedLoopbackUrl(value, port) {
  try {
    const candidate = new URL(String(value || ""));
    return (
      candidate.protocol === "http:" &&
      (candidate.hostname === "localhost" || candidate.hostname === "127.0.0.1") &&
      Number(candidate.port) === port &&
      candidate.username === "" &&
      candidate.password === "" &&
      candidate.pathname === "/" &&
      candidate.search === "" &&
      candidate.hash === ""
    );
  } catch (_error) {
    return false;
  }
}

async function readAndValidateActiveMarker(candidate) {
  const markerPath = path.join(candidate.isolatedRoot, "runtime", "pfi_active_service.env");
  let markerStat;
  let raw;
  try {
    markerStat = await lstat(markerPath);
    raw = await readFile(markerPath, "utf8");
  } catch (_error) {
    fail("active marker is unavailable");
  }
  if (
    !markerStat.isFile() ||
    markerStat.isSymbolicLink() ||
    (typeof process.getuid === "function" && markerStat.uid !== process.getuid()) ||
    (markerStat.mode & 0o777) !== 0o600
  ) {
    fail("active marker is unavailable");
  }
  const marker = parseMarker(raw);
  const expected = {
    PFI_ACTIVE_SCHEMA: ACTIVE_SCHEMA,
    PFI_ACTIVE_PROJECT_DIR: String(candidate.state.project_root),
    PFI_ACTIVE_PORT: String(candidate.port),
    PFI_ACTIVE_HEARTBEAT_PORT: String(candidate.heartbeatPort),
    PFI_ACTIVE_CANDIDATE_MODE: "1",
    PFI_ACTIVE_CANDIDATE_APP_PATH_SHA256: candidate.state.candidate_app_path_sha256,
    PFI_ACTIVE_CANDIDATE_EXECUTABLE_SHA256: candidate.state.candidate_executable_sha256,
    PFI_ACTIVE_CANDIDATE_BUNDLE_SHA256: candidate.state.candidate_bundle_sha256,
  };
  if (
    Object.entries(expected).some(([key, value]) => marker[key] !== value) ||
    !isExpectedLoopbackUrl(marker.PFI_ACTIVE_URL, candidate.port)
  ) {
    fail("active marker identity mismatch");
  }
  if (
    !/^\d+$/.test(marker.PFI_ACTIVE_PID || "") ||
    Number(marker.PFI_ACTIVE_PID) <= 1 ||
    !/^\d+$/.test(marker.PFI_ACTIVE_MONITOR_PID || "") ||
    Number(marker.PFI_ACTIVE_MONITOR_PID) <= 1 ||
    !/^\d+$/.test(marker.PFI_ACTIVE_LAUNCHER_PID || "") ||
    Number(marker.PFI_ACTIVE_LAUNCHER_PID) <= 1 ||
    !/^\d+$/.test(marker.PFI_ACTIVE_PROCESS_GROUP_ID || "") ||
    marker.PFI_ACTIVE_PROCESS_GROUP_ID !== marker.PFI_ACTIVE_LAUNCHER_PID
  ) {
    fail("active marker identity mismatch");
  }
  const runtimeApiPort = Number(marker.PFI_ACTIVE_RUNTIME_API_PORT);
  if (
    !/^\d+$/.test(marker.PFI_ACTIVE_RUNTIME_API_PORT || "") ||
    !Number.isInteger(runtimeApiPort) ||
    runtimeApiPort < 1024 ||
    runtimeApiPort > 65535 ||
    runtimeApiPort === candidate.port ||
    runtimeApiPort === candidate.heartbeatPort ||
    RESERVED_PORTS.has(runtimeApiPort)
  ) {
    fail("active marker runtime API identity mismatch");
  }
  return {
    values: marker,
    browserBaseUrl: `http://127.0.0.1:${candidate.port}`,
    runtimeApiPort,
    runtimeApiBaseUrl: `http://127.0.0.1:${runtimeApiPort}`,
  };
}

async function readOwnedRegularFile(filePath) {
  let metadata;
  try {
    metadata = await lstat(filePath);
  } catch (_error) {
    fail("candidate bundle identity mismatch");
  }
  if (
    !metadata.isFile() ||
    metadata.isSymbolicLink() ||
    (typeof process.getuid === "function" && metadata.uid !== process.getuid())
  ) {
    fail("candidate bundle identity mismatch");
  }
  return readFile(filePath);
}

async function validateCandidateBundleIdentity(candidate) {
  const candidateApp = path.join(candidate.isolatedRoot, "PFI.app");
  const executablePath = path.join(candidateApp, "Contents", "MacOS", "PFI");
  const executableBytes = await readOwnedRegularFile(executablePath);
  const records = [];
  for (const relative of CANDIDATE_IDENTITY_FILES) {
    const bytes = await readOwnedRegularFile(path.join(candidateApp, relative));
    records.push(Buffer.from(`${relative}=${sha256(bytes)}\n`, "utf8"));
  }
  const expectedMarkers = new Map([
    ["PFI_PROJECT_ROOT", `${candidate.projectRoot}\n`],
    ["PFI_STAGE1_ISOLATED_ROOT", `${candidate.isolatedRoot}\n`],
    ["PFI_STAGE1_STREAMLIT_PORT", `${candidate.port}\n`],
    ["PFI_STAGE1_HEARTBEAT_PORT", `${candidate.heartbeatPort}\n`],
    ["PFI_STAGE1_CHECKOUT_COMMIT", `${candidate.state.checkout_commit}\n`],
    ["PFI_STAGE1_SOURCE_APP_TREE_SHA256", `${candidate.state.source_app_tree_sha256}\n`],
    ["PFI_STAGE1_COPIED_APP_TREE_SHA256", `${candidate.state.copied_app_tree_sha256}\n`],
  ]);
  for (const [name, expected] of expectedMarkers) {
    const bytes = await readOwnedRegularFile(
      path.join(candidateApp, "Contents", "Resources", name),
    );
    if (bytes.toString("ascii") !== expected) fail("candidate bundle identity mismatch");
  }
  if (
    sha256(Buffer.from(candidateApp, "utf8")) !== candidate.state.candidate_app_path_sha256 ||
    sha256(executableBytes) !== candidate.state.candidate_executable_sha256 ||
    sha256(Buffer.concat(records)) !== candidate.state.candidate_bundle_sha256
  ) {
    fail("candidate bundle identity mismatch");
  }
}

function validateLaunchServicesInspection(candidate, active) {
  const marker = active.values;
  const inspection = candidate.state.inspection;
  const observedPid = Number(candidate.state.observed_pid);
  const observedMonitorPid = Number(candidate.state.observed_monitor_pid);
  const observedLauncherPid = Number(candidate.state.observed_launcher_pid);
  const observedProcessGroupId = Number(candidate.state.observed_process_group_id);
  const observedProcessTree = candidate.state.observed_process_tree;
  const observedProcessGroup = candidate.state.observed_process_group;
  const processTreeIdentities = isPlainObject(observedProcessTree)
    ? Object.values(observedProcessTree)
    : [];
  const processTreeIdentitySha256 = sha256(
    Buffer.from(
      processTreeIdentities
        .map(String)
        .sort()
        .map((identity) => `${identity}\n`)
        .join(""),
      "ascii",
    ),
  );
  const processGroupIdentities = isPlainObject(observedProcessGroup)
    ? Object.values(observedProcessGroup)
    : [];
  const processGroupIdentitySha256 = sha256(
    Buffer.from(
      processGroupIdentities
        .map(String)
        .sort()
        .map((identity) => `${identity}\n`)
        .join(""),
      "ascii",
    ),
  );
  if (
    !isPlainObject(inspection) ||
    inspection.schema !== "PFIV025Stage1Phase13CandidateInspectionV1" ||
    inspection.launchservices_started !== true ||
    inspection.candidate_mode !== true ||
    inspection.pid_observed !== true ||
    inspection.monitor_pid_observed !== true ||
    inspection.launcher_pid_observed !== true ||
    inspection.launcher_process_tree_verified !== true ||
    inspection.process_group_verified !== true ||
    inspection.health_ready !== true ||
    inspection.runtime_api_ready !== true ||
    inspection.heartbeat_ready !== true ||
    inspection.streamlit_listener_set_verified !== true ||
    inspection.streamlit_listener_count !== 2 ||
    !isHex(inspection.streamlit_listener_set_sha256, 64) ||
    inspection.monitor_listener_set_verified !== true ||
    inspection.monitor_listener_count !== 1 ||
    !isHex(inspection.monitor_listener_set_sha256, 64) ||
    inspection.listener_owner_port_set_verified !== true ||
    inspection.listener_owner_port_count !== 3 ||
    !isHex(inspection.listener_owner_port_set_sha256, 64) ||
    inspection.listener_endpoint_set_verified !== true ||
    inspection.listener_endpoint_count !== 3 ||
    !isHex(inspection.listener_endpoint_set_sha256, 64) ||
    inspection.launchservices_registration_verified !== true ||
    inspection.streamlit_port !== candidate.port ||
    inspection.runtime_api_port !== active.runtimeApiPort ||
    candidate.state.observed_runtime_api_port !== active.runtimeApiPort ||
    inspection.heartbeat_port !== candidate.heartbeatPort ||
    inspection.candidate_app_path_sha256 !== candidate.state.candidate_app_path_sha256 ||
    inspection.candidate_executable_sha256 !== candidate.state.candidate_executable_sha256 ||
    inspection.candidate_bundle_sha256 !== candidate.state.candidate_bundle_sha256 ||
    !isHex(inspection.process_identity_sha256, 64) ||
    !isHex(inspection.monitor_identity_sha256, 64) ||
    !isHex(inspection.launcher_identity_sha256, 64) ||
    !Number.isInteger(inspection.process_tree_member_count) ||
    inspection.process_tree_member_count < 3 ||
    !isHex(inspection.process_tree_identity_sha256, 64) ||
    inspection.process_group_member_count !== 3 ||
    !isHex(inspection.process_group_identity_sha256, 64) ||
    !Number.isInteger(observedPid) ||
    observedPid <= 1 ||
    String(observedPid) !== marker.PFI_ACTIVE_PID ||
    !Number.isInteger(observedMonitorPid) ||
    observedMonitorPid <= 1 ||
    String(observedMonitorPid) !== marker.PFI_ACTIVE_MONITOR_PID ||
    !Number.isInteger(observedLauncherPid) ||
    observedLauncherPid <= 1 ||
    String(observedLauncherPid) !== marker.PFI_ACTIVE_LAUNCHER_PID ||
    !Number.isInteger(observedProcessGroupId) ||
    observedProcessGroupId !== observedLauncherPid ||
    String(observedProcessGroupId) !== marker.PFI_ACTIVE_PROCESS_GROUP_ID ||
    !isPlainObject(observedProcessTree) ||
    processTreeIdentities.length !== inspection.process_tree_member_count ||
    processTreeIdentities.some((identity) => !isHex(String(identity), 64)) ||
    !Object.hasOwn(observedProcessTree, String(observedPid)) ||
    !Object.hasOwn(observedProcessTree, String(observedMonitorPid)) ||
    !Object.hasOwn(observedProcessTree, String(observedLauncherPid)) ||
    inspection.process_tree_identity_sha256 !== processTreeIdentitySha256 ||
    !isPlainObject(observedProcessGroup) ||
    processGroupIdentities.length !== 3 ||
    processGroupIdentities.some((identity) => !isHex(String(identity), 64)) ||
    !Object.hasOwn(observedProcessGroup, String(observedPid)) ||
    !Object.hasOwn(observedProcessGroup, String(observedMonitorPid)) ||
    !Object.hasOwn(observedProcessGroup, String(observedLauncherPid)) ||
    inspection.process_group_identity_sha256 !== processGroupIdentitySha256
  ) {
    fail("LaunchServices inspection proof is unavailable");
  }
  const expectedListenerSet = [
    [observedPid, candidate.port],
    [observedPid, active.runtimeApiPort],
    [observedMonitorPid, candidate.heartbeatPort],
  ]
    .sort((left, right) => left[0] - right[0] || left[1] - right[1])
    .map(([pid, port]) => `${pid}:${port}\n`)
    .join("");
  const expectedListenerSetSha256 = sha256(Buffer.from(expectedListenerSet, "ascii"));
  if (inspection.listener_owner_port_set_sha256 !== expectedListenerSetSha256) {
    fail("LaunchServices inspection listener proof is invalid");
  }
  const expectedEndpointSet = [
    [observedPid, "127.0.0.1", candidate.port],
    [observedPid, "127.0.0.1", active.runtimeApiPort],
    [observedMonitorPid, "127.0.0.1", candidate.heartbeatPort],
  ]
    .sort((left, right) => left[0] - right[0] || left[2] - right[2])
    .map(([pid, address, port]) => `${pid}:${address}:${port}\n`)
    .join("");
  const expectedEndpointSetSha256 = sha256(Buffer.from(expectedEndpointSet, "ascii"));
  if (inspection.listener_endpoint_set_sha256 !== expectedEndpointSetSha256) {
    fail("LaunchServices inspection endpoint proof is invalid");
  }
  try {
    process.kill(observedPid, 0);
    process.kill(observedMonitorPid, 0);
    process.kill(observedLauncherPid, 0);
  } catch (_error) {
    fail("LaunchServices inspection proof is unavailable");
  }
  return inspection;
}

async function readReleaseContract(candidate, marker) {
  const projectRoot = path.resolve(String(candidate.state.project_root || ""));
  const manifestPath = path.join(projectRoot, "config", "release_manifest.json");
  let manifestBytes;
  let manifest;
  try {
    manifestBytes = await readFile(manifestPath);
    manifest = JSON.parse(manifestBytes.toString("utf8"));
  } catch (_error) {
    fail("release manifest is unavailable");
  }
  const manifestSha256 = sha256(manifestBytes);
  const sourceIdentity = await computeReleaseSourceIdentity(projectRoot);
  const expectedMarker = {
    PFI_ACTIVE_BUILD_ID: manifest.build_id,
    PFI_ACTIVE_GIT_COMMIT: manifest.git_commit,
    PFI_ACTIVE_FRONTEND_HASH: manifest.frontend_bundle_hash,
    PFI_ACTIVE_BACKEND_HASH: manifest.backend_build_hash,
    PFI_RELEASE_MANIFEST_SHA256: manifestSha256,
    PFI_ACTIVE_UI_CONTRACT: "PFI-V025-RELEASE-IDENTITY",
  };
  if (
    manifest.product !== "PFI" ||
    !/^v0\.2\.5(?:[-+].*)?$/.test(manifest.version || "") ||
    manifest.git_commit !== candidate.state.checkout_commit ||
    !isHex(manifest.git_commit, 40) ||
    !isHex(manifest.frontend_bundle_hash, 64) ||
    !isHex(manifest.backend_build_hash, 64) ||
    manifest.frontend_bundle_hash !== sourceIdentity.frontend.sha256 ||
    manifest.backend_build_hash !== sourceIdentity.backend.sha256 ||
    !isHex(marker.PFI_STREAMLIT_CACHE_KEY, 64) ||
    Object.entries(expectedMarker).some(([key, value]) => marker[key] !== value)
  ) {
    fail("active marker release identity mismatch");
  }
  return { manifest, manifestSha256, projectRoot, sourceIdentity };
}

async function readApiJson(url, options = {}) {
  const response = await fetch(url, {
    cache: "no-store",
    signal: AbortSignal.timeout(5_000),
    ...options,
  });
  const raw = Buffer.from(await response.arrayBuffer());
  let body = {};
  try {
    body = raw.length ? JSON.parse(raw.toString("utf8")) : {};
  } catch (_error) {
    fail("runtime API returned invalid JSON");
  }
  return {
    status: response.status,
    headers: Object.fromEntries([...response.headers.entries()].sort()),
    body,
    body_sha256: sha256(raw),
  };
}

async function validateLaunchServicesRuntime(candidate, active, release) {
  const baseUrl = active.browserBaseUrl;
  const marker = active.values;
  let health;
  let heartbeat;
  let apiHealth;
  try {
    health = await fetch(`${baseUrl}/_stcore/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5_000),
    });
    heartbeat = await fetch(`http://127.0.0.1:${candidate.heartbeatPort}/heartbeat`, {
      method: "POST",
      cache: "no-store",
      signal: AbortSignal.timeout(5_000),
    });
    apiHealth = await fetch(`${active.runtimeApiBaseUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(5_000),
    });
  } catch (_error) {
    fail("LaunchServices-started candidate health check failed");
  }
  if (!health.ok || heartbeat.status !== 204 || !apiHealth.ok) {
    fail("LaunchServices-started candidate health check failed");
  }
  const manifest = await readApiJson(`${active.runtimeApiBaseUrl}/api/release-manifest`);
  const policy = await readApiJson(`${active.runtimeApiBaseUrl}/api/release-cache-policy`);
  const status = await readApiJson(`${active.runtimeApiBaseUrl}/api/read-model-status`);
  const post = await readApiJson(`${active.runtimeApiBaseUrl}/api/holdings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ rows: [{ forbidden: true }] }),
  });
  if (
    manifest.status !== 200 ||
    stableJson(manifest.body) !== stableJson(release.manifest) ||
    manifest.body_sha256 !== release.manifestSha256 ||
    manifest.headers["x-pfi-release-manifest-sha256"] !== release.manifestSha256 ||
    manifest.headers["x-pfi-running-backend-sha256"] !== release.sourceIdentity.backend.sha256 ||
    policy.status !== 200 ||
    policy.body.schema !== "PFIV025Stage1ReleaseCachePolicyV1" ||
    policy.body.valid !== true ||
    policy.body.persistent !== false ||
    policy.body.streamlit_cache_key !== marker.PFI_STREAMLIT_CACHE_KEY ||
    policy.body.process_cache_key !== marker.PFI_STREAMLIT_CACHE_KEY ||
    policy.body.running_backend_hash !== release.sourceIdentity.backend.sha256 ||
    policy.headers["x-pfi-running-backend-sha256"] !== release.sourceIdentity.backend.sha256 ||
    policy.headers["x-pfi-streamlit-cache-key"] !== marker.PFI_STREAMLIT_CACHE_KEY ||
    status.status !== 200 ||
    status.body.isolated_candidate !== true ||
    status.body.source?.storage_mode !== "isolated_empty" ||
    !Array.isArray(status.body.core_metric_states) ||
    status.body.core_metric_states.length !== 5 ||
    !status.body.core_metric_states.every(
      (metric) => metric?.status === "not_loaded" && metric?.value === null,
    ) ||
    status.headers["x-pfi-running-backend-sha256"] !== release.sourceIdentity.backend.sha256 ||
    status.headers["x-pfi-read-model-sha256"] !== status.body.read_model_hash ||
    status.headers["x-pfi-data-boundary"] !== "isolated-empty-read-only" ||
    post.status !== 403 ||
    post.body?.error !== "candidate_read_only"
  ) {
    fail("LaunchServices-started runtime API contract failed");
  }
  return {
    baseUrl,
    runtimeApiBaseUrl: active.runtimeApiBaseUrl,
    runtimeApiPort: active.runtimeApiPort,
    heartbeatReady: true,
    heartbeatPortObserved: true,
    api: { manifest, policy, read_model_status: status, blocked_post: post },
  };
}

function stableJson(value) {
  if (Array.isArray(value)) return `[${value.map((item) => stableJson(item)).join(",")}]`;
  if (isPlainObject(value)) {
    return `{${Object.keys(value)
      .sort()
      .map((key) => `${JSON.stringify(key)}:${stableJson(value[key])}`)
      .join(",")}}`;
  }
  return JSON.stringify(value);
}

function releaseQuery(release) {
  return new URLSearchParams({
    pfi_app_version: String(release.manifest.app_short_version),
    pfi_app_build: String(release.manifest.app_build_version),
    pfi_build: String(release.manifest.build_id),
    pfi_commit: String(release.manifest.git_commit),
    pfi_frontend_hash: String(release.manifest.frontend_bundle_hash),
    pfi_backend_hash: String(release.manifest.backend_build_hash),
    pfi_manifest_sha256: release.manifestSha256,
  }).toString();
}

async function resolveShellFrame(page, timeoutMs = 60_000) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    for (const frame of page.frames()) {
      if (frame === page.mainFrame()) continue;
      try {
        const present = await frame.evaluate(
          () => Boolean(document.getElementById("pfi-release-manifest") && window.PFI_RELEASE_IDENTITY_READY),
        );
        if (present) return frame;
      } catch (_error) {
        // The component frame may be replaced while Streamlit reruns.
      }
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
  }
  fail("PFI release shell did not become ready");
}

async function readShellSnapshot(page, release) {
  const frame = await resolveShellFrame(page);
  try {
    await frame.waitForFunction(
      () => document.body?.dataset?.pfiReleaseIdentityState === "ready",
      undefined,
      { timeout: 30_000 },
    );
    await frame.waitForFunction(
      () =>
        Array.isArray(window.__PFI_RUNTIME_API_CALLS__) &&
        window.__PFI_RUNTIME_API_CALLS__.some((item) => item?.path === "/api/read-model-status"),
      undefined,
      { timeout: 30_000 },
    );
    await frame.locator("[data-pfi-release-identity-details]").evaluate((node) => {
      node.open = true;
    });
    const snapshot = await frame.evaluate(async () => {
      const gate = await window.PFI_RELEASE_IDENTITY_READY;
      const manifest = JSON.parse(document.getElementById("pfi-release-manifest")?.textContent || "{}");
      const runtimeConfig = JSON.parse(document.getElementById("pfi-runtime-config")?.textContent || "{}");
      const homeSummary = JSON.parse(document.getElementById("pfi-home-summary")?.textContent || "{}");
      const readModelStatus = JSON.parse(document.getElementById("pfi-read-model-status")?.textContent || "{}");
      const reportPack = JSON.parse(document.getElementById("pfi-stage7-report-schema")?.textContent || "{}");
      const callsBefore = Array.isArray(window.__PFI_RUNTIME_API_CALLS__)
        ? [...window.__PFI_RUNTIME_API_CALLS__]
        : [];
      const apiJson = async (apiPath) => {
        const response = await fetch(`${runtimeConfig.apiBaseUrl}${apiPath}`, { cache: "no-store" });
        const body = await response.json();
        return {
          status: response.status,
          headers: Object.fromEntries([...response.headers.entries()].sort()),
          body,
        };
      };
      const [runtimeManifest, runtimePolicy, runtimeStatus] = await Promise.all([
        apiJson("/api/release-manifest"),
        apiJson("/api/release-cache-policy"),
        apiJson("/api/read-model-status"),
      ]);
      const alipay = homeSummary.alipay_import_summary || {};
      const visibleText = String(document.body?.innerText || "");
      const sourceNodes = [...document.querySelectorAll("[data-pfi-source]")];
      const sourceHashes = [];
      for (const node of sourceNodes) {
        const bytes = new TextEncoder().encode(node.textContent || "");
        const digest = await crypto.subtle.digest("SHA-256", bytes);
        sourceHashes.push({
          path: `PFI/${node.dataset.pfiSource}`,
          sha256: [...new Uint8Array(digest)].map((value) => value.toString(16).padStart(2, "0")).join(""),
          bytes: bytes.byteLength,
        });
      }
      sourceHashes.sort((left, right) => left.path.localeCompare(right.path));
      const primaryEntries = [...document.querySelectorAll('nav[aria-label="一级工作区"] [data-primary-entry="true"]')]
        .filter((node) => !node.hidden)
        .map((node) => String(node.textContent || "").trim());
      const activePrimaryEntry = document.querySelector(
        'nav[aria-label="一级工作区"] [data-primary-entry="true"].is-active',
      );
      const identityDetails = document.querySelector("[data-pfi-release-identity-details]");
      const identitySummary = identityDetails?.querySelector("summary") || null;
      const identityPanel = identityDetails?.querySelector("dl") || null;
      const visible = (node) => {
        if (!node || node.hidden || node.getAttribute?.("aria-hidden") === "true") return false;
        const style = globalThis.getComputedStyle(node);
        return style.display !== "none" && style.visibility !== "hidden" && node.getClientRects().length > 0;
      };
      const identityDetailText = (attribute) =>
        String(document.querySelector(`[${attribute}]`)?.textContent || "").trim();
      const identityFieldNodes = [
        "data-pfi-release-detail-version",
        "data-pfi-release-detail-build",
        "data-pfi-release-detail-commit",
        "data-pfi-release-detail-frontend",
        "data-pfi-release-detail-backend",
      ].map((attribute) => document.querySelector(`[${attribute}]`));
      const fxBadge = document.querySelector("[data-fx-badge]");
      const ids = [...document.querySelectorAll("[id]")].map((node) => node.id);
      const registrations = "serviceWorker" in navigator ? await navigator.serviceWorker.getRegistrations() : [];
      const cacheKeys = "caches" in window ? await caches.keys() : [];
      const metrics = Array.isArray(runtimeStatus.body?.core_metric_states)
        ? runtimeStatus.body.core_metric_states
        : [];
      const isolatedEmptyData =
        runtimeConfig.stage1OfficialCandidate === true &&
        runtimeConfig.runtimeApiEnabled === true &&
        runtimeConfig.readModelStatusApi === true &&
        runtimeConfig.releaseManifestApi === true &&
        runtimeConfig.releaseCachePolicyApi === true &&
        String(runtimeConfig.projectRoot || "") === "" &&
        runtimeConfig.candidateDataMode === "isolated_empty" &&
        Number(alipay.file_count || 0) === 0 &&
        Number(alipay.valid_file_count || 0) === 0 &&
        Number(alipay.transaction_count || 0) === 0 &&
        Number(alipay.review_count || 0) === 0 &&
        String(alipay.date_start || "") === "" &&
        String(alipay.date_end || "") === "" &&
        Object.keys(reportPack).length === 0 &&
        runtimeStatus.body?.isolated_candidate === true &&
        runtimeStatus.body?.source?.status === "not_loaded" &&
        runtimeStatus.body?.source?.storage_mode === "isolated_empty" &&
        metrics.length === 5 &&
        metrics.every(
          (metric) =>
            metric.status === "not_loaded" &&
            metric.value === null &&
            metric.record_count === null &&
            metric.as_of === null &&
            metric.formula_id === null &&
            metric.confidence === null,
        );
      return {
        ready: document.body?.dataset?.pfiReleaseIdentityState === "ready",
        shell_visible: document.querySelector(".app-shell")?.hidden !== true,
        gate_ok: gate?.ok === true,
        mode: String(gate?.mode || ""),
        manifest,
        cache_policy: gate?.cachePolicy || {},
        runtime_manifest: runtimeManifest,
        runtime_cache_policy: runtimePolicy,
        runtime_read_model_status: runtimeStatus,
        embedded_read_model_status: readModelStatus,
        runtime_config: runtimeConfig,
        home_summary: homeSummary,
        report_pack: reportPack,
        api_calls_before_snapshot: callsBefore,
        frontend_source_hashes: sourceHashes,
        frontend_source_hash: "independently-recomputed-below",
        frontend_globals_ready: Object.fromEntries(
          [
            "PFI_RELEASE_IDENTITY",
            "PFI_STAGE2_ENTRY_AUDIT",
            "PFI_V024_STAGE3_NAVIGATION",
            "PFI_V024_STAGE3_ROUTES",
            "PFI_V024_STAGE4_DATA_STATE",
            "PFI_V023_STAGE4_PAGES",
            "PFI_V024_STAGE5_PAGES",
            "PFI_V024_STAGE5_UX_STATE",
            "PFI_V024_STAGE5_HOME",
            "PFI_V024_STAGE7_REPORTS",
            "PFI_STAGE1_SHELL",
          ].map((name) => [name, Boolean(window[name])]),
        ),
        primary_entries: primaryEntries,
        active_primary_route_alias: String(activePrimaryEntry?.dataset?.routeAlias || ""),
        active_primary_workspace: String(activePrimaryEntry?.dataset?.workspace || ""),
        main_active_workspace: String(
          document.querySelector("main#main-workspace")?.dataset?.activeWorkspace || "",
        ),
        shell_schema: document.body?.dataset?.shellSchema || "",
        header_present: Boolean(document.querySelector('header[aria-label="PFI 顶部栏"]')),
        navigation_present: Boolean(document.querySelector('nav[aria-label="一级工作区"]')),
        main_present: Boolean(document.querySelector("main#main-workspace")),
        skip_link_present: Boolean(document.querySelector('a.skip-link[href="#main-workspace"]')),
        h1_text: String(document.querySelector("main#main-workspace h1")?.textContent || "").trim(),
        release_identity_details: {
          chip_visible: visible(identitySummary),
          details_visible: visible(identityDetails),
          details_panel_visible: visible(identityPanel),
          complete: identityDetails?.dataset?.pfiReleaseIdentityComplete === "true",
          visible_field_count: identityFieldNodes.filter(visible).length,
          chip_text: String(identitySummary?.textContent || "").trim(),
          version: identityDetailText("data-pfi-release-detail-version"),
          build_id: identityDetailText("data-pfi-release-detail-build"),
          git_commit: identityDetailText("data-pfi-release-detail-commit"),
          frontend_bundle_hash: identityDetailText("data-pfi-release-detail-frontend"),
          backend_build_hash: identityDetailText("data-pfi-release-detail-backend"),
        },
        fx_badge: {
          text: String(fxBadge?.textContent || "").trim(),
          source_label: String(fxBadge?.dataset?.fxSourceLabel || ""),
          cache_state: String(fxBadge?.dataset?.fxCacheState || ""),
          effective_date: String(fxBadge?.dataset?.fxEffectiveDate || ""),
        },
        duplicate_id_count: ids.length - new Set(ids).size,
        focusable_without_name_count: "independently-collected-below",
        isolated_empty_data: isolatedEmptyData,
        visible_text: visibleText,
        full_html: document.documentElement.outerHTML,
        service_worker_registration_count: registrations.length,
        service_worker_controller_active: Boolean(navigator.serviceWorker?.controller),
        cache_storage_count: cacheKeys.length,
      };
    });
    snapshot.focusable_without_name_count = await frame.evaluate(
      collectFocusableWithoutNameCount,
    );
    snapshot.live_form_control_audit = await frame.evaluate(collectLiveFormControlPrivacyAudit);
    const diskFiles = new Map(release.sourceIdentity.frontend.files.map((item) => [item.path, item]));
    const browserRecords = snapshot.frontend_source_hashes.map((item) => ({ ...item }));
    const indexRecord = diskFiles.get("PFI/web/index.html");
    if (!indexRecord) fail("frontend index source identity is unavailable");
    snapshot.frontend_source_hash = hashRecords([indexRecord, ...browserRecords]);
    snapshot.frontend_source_bytes_match = browserRecords.every(
      (record) => diskFiles.get(record.path)?.sha256 === record.sha256,
    );
    await frame.locator("[data-pfi-release-identity-details]").evaluate((node) => {
      node.open = false;
    });
    return snapshot;
  } catch (_error) {
    fail("PFI release shell identity check failed");
  }
}

async function captureShellScreenshot(page, screenshotPath) {
  const frame = await resolveShellFrame(page);
  const shellElement = await frame.frameElement();
  try {
    await shellElement.screenshot({ path: screenshotPath });
  } finally {
    await shellElement.dispose();
  }
}

async function captureIdentityScreenshot(page, screenshotPath) {
  const frame = await resolveShellFrame(page);
  const details = frame.locator("[data-pfi-release-identity-details]");
  await details.evaluate((node) => {
    node.open = true;
  });
  const panel = details.locator(".pfi-release-identity-panel");
  await panel.locator("[data-pfi-release-detail-backend]").waitFor({ state: "visible" });
  await captureShellScreenshot(page, screenshotPath);
}

function manifestMatchesRelease(snapshot, release) {
  return (
    snapshot.ready === true &&
    snapshot.shell_visible === true &&
    snapshot.gate_ok === true &&
    snapshot.mode === "app_launcher" &&
    stableJson(snapshot.manifest) === stableJson(release.manifest) &&
    snapshot.runtime_manifest.status === 200 &&
    stableJson(snapshot.runtime_manifest.body) === stableJson(release.manifest) &&
    snapshot.runtime_manifest.headers["x-pfi-release-manifest-sha256"] === release.manifestSha256 &&
    snapshot.runtime_manifest.headers["x-pfi-running-backend-sha256"] === release.sourceIdentity.backend.sha256
  );
}

function serviceWorkerAuditReady(snapshot) {
  return (
    snapshot.service_worker_registration_count === 0 &&
    snapshot.service_worker_controller_active === false &&
    snapshot.cache_storage_count === 0
  );
}

function policyMatchesRelease(snapshot, release, marker) {
  const policy = snapshot.runtime_cache_policy.body;
  return (
    isPlainObject(policy) &&
    stableJson(snapshot.cache_policy) === stableJson(policy) &&
    snapshot.runtime_cache_policy.status === 200 &&
    policy.schema === "PFIV025Stage1ReleaseCachePolicyV1" &&
    policy.valid === true &&
    policy.persistent === false &&
    policy.streamlit_cache_key === marker.PFI_STREAMLIT_CACHE_KEY &&
    policy.process_cache_key === marker.PFI_STREAMLIT_CACHE_KEY &&
    policy.build_id === release.manifest.build_id &&
    policy.git_commit === release.manifest.git_commit &&
    policy.frontend_bundle_hash === release.manifest.frontend_bundle_hash &&
    policy.backend_build_hash === release.manifest.backend_build_hash &&
    policy.running_backend_hash === release.sourceIdentity.backend.sha256 &&
    snapshot.runtime_cache_policy.headers["x-pfi-running-backend-sha256"] ===
      release.sourceIdentity.backend.sha256 &&
    snapshot.runtime_cache_policy.headers["x-pfi-streamlit-cache-key"] ===
      marker.PFI_STREAMLIT_CACHE_KEY
  );
}

function sameRuntimeIdentity(snapshot, release, marker) {
  return (
    manifestMatchesRelease(snapshot, release) &&
    policyMatchesRelease(snapshot, release, marker) &&
    snapshot.runtime_read_model_status.status === 200 &&
    snapshot.runtime_read_model_status.body?.isolated_candidate === true &&
    snapshot.runtime_read_model_status.headers["x-pfi-data-boundary"] ===
      "isolated-empty-read-only" &&
    snapshot.frontend_source_hash === release.sourceIdentity.frontend.sha256 &&
    snapshot.frontend_source_bytes_match === true &&
    serviceWorkerAuditReady(snapshot)
  );
}

function officialShellReady(snapshot) {
  const expectedEntries = [
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "市场与研究",
    "设置",
  ];
  return (
    snapshot.shell_schema === "PFIOSWebShellContractV1" &&
    snapshot.header_present === true &&
    snapshot.navigation_present === true &&
    snapshot.main_present === true &&
    snapshot.skip_link_present === true &&
    snapshot.h1_text === "首页总览 · 财务状态" &&
    stableJson(snapshot.primary_entries) === stableJson(expectedEntries) &&
    snapshot.duplicate_id_count === 0 &&
    snapshot.focusable_without_name_count === 0 &&
    FRONTEND_GLOBALS.every((name) => snapshot.frontend_globals_ready?.[name] === true)
  );
}

function completeVisibleIdentityMatchesRelease(snapshot, release) {
  const details = snapshot?.release_identity_details;
  return (
    details?.chip_visible === true &&
    details?.details_visible === true &&
    details?.details_panel_visible === true &&
    details?.complete === true &&
    details?.visible_field_count === 5 &&
    details?.chip_text === "发布身份详情" &&
    details.version === release.manifest.version &&
    details.build_id === release.manifest.build_id &&
    details.git_commit === release.manifest.git_commit &&
    details.frontend_bundle_hash === release.manifest.frontend_bundle_hash &&
    details.backend_build_hash === release.manifest.backend_build_hash
  );
}

function isolatedFxBadgeReady(snapshot) {
  const badge = snapshot?.fx_badge;
  return (
    badge?.text === "AUD/CNY=未加载" &&
    badge?.source_label === "AUD/CNY=未加载" &&
    badge?.cache_state === "not_loaded" &&
    badge?.effective_date === ""
  );
}

function isolatedRuntimePayloadSafe(snapshot) {
  const payload = {
    home_summary: snapshot.home_summary,
    report_pack: snapshot.report_pack,
    embedded_read_model_status: snapshot.embedded_read_model_status,
    runtime_read_model_status: snapshot.runtime_read_model_status?.body,
  };
  const text = stableJson(payload);
  const metrics = snapshot.runtime_read_model_status?.body?.core_metric_states;
  return (
    !/\/Users\//.test(text) &&
    !/MetaDatabase\/PFI/.test(text) &&
    !/pfi\.sqlite/i.test(text) &&
    !/(?:authorization|cookie|credential|password|token|secret)["']?\s*:/i.test(text) &&
    snapshot.home_summary?.alipay_import_summary?.transaction_count === 0 &&
    Object.keys(snapshot.report_pack || {}).length === 0 &&
    Array.isArray(metrics) &&
    metrics.length === 5 &&
    metrics.every((metric) => metric?.value === null && metric?.status === "not_loaded")
  );
}

async function collectLiveFormControlPrivacyAudit(documentObject = document) {
  const financialLabelPattern = /(?:数量|成本|价格|金额|余额|净资产|市值|收益|盈亏|支出|收入|消费|现金流|持仓成本|quantity|averagecost|marketprice|amount|balance|price|cost)/iu;
  const numericValuePattern = /^(?:\(\s*)?(?:(?:CNY|AUD|USD|HKD|¥|￥|A\$|\$)\s*)?[-+]?\d[\d,]*(?:\.\d+)?(?:e[-+]?\d+)?(?:\s*(?:CNY|AUD|USD|HKD|元|万元|亿元|人民币|澳元|美元|港元))?(?:\s*\))?$/iu;
  const structure = [];
  let visibleControlCount = 0;
  let sensitiveControlCount = 0;
  let findingCount = 0;
  for (const element of documentObject.querySelectorAll("input,textarea,select")) {
    const rectangles = typeof element.getClientRects === "function" ? element.getClientRects() : [];
    if (element.hidden || element.getAttribute?.("aria-hidden") === "true" || rectangles.length === 0) continue;
    visibleControlCount += 1;
    const labelText = [
      element.getAttribute?.("aria-label"),
      element.getAttribute?.("name"),
      element.getAttribute?.("data-label"),
      element.getAttribute?.("data-holding-field"),
      element.getAttribute?.("placeholder"),
      ...Array.from(element.labels || [], (label) => label.textContent || ""),
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const tagName = String(element.tagName || "control").toLowerCase();
    const inputType = String(element.type || "").toLowerCase();
    const acceptsFreeformValue =
      tagName === "textarea" ||
      (tagName === "input" &&
        !["hidden", "checkbox", "radio", "file", "button", "submit", "reset"].includes(inputType));
    const currentValue = String(element.value ?? "").trim();
    const numeric = numericValuePattern.test(currentValue);
    const financialLabel = financialLabelPattern.test(labelText);
    const sensitive =
      financialLabel && (acceptsFreeformValue || (tagName === "select" && numeric));
    if (sensitive) sensitiveControlCount += 1;
    if (sensitive && currentValue) findingCount += 1;
    structure.push(
      `${tagName}|${inputType}|${sensitive ? 1 : 0}|${currentValue ? 1 : 0}|${numeric ? 1 : 0}`,
    );
  }
  const digest = await globalThis.crypto.subtle.digest(
    "SHA-256",
    new TextEncoder().encode(structure.sort().join("\n")),
  );
  return {
    schema: "PFIV025Stage1LiveFormControlPrivacyAuditV1",
    visible_control_count: visibleControlCount,
    sensitive_control_count: sensitiveControlCount,
    finding_count: findingCount,
    structure_sha256: [...new Uint8Array(digest)]
      .map((value) => value.toString(16).padStart(2, "0"))
      .join(""),
  };
}

function collectFocusableWithoutNameCount(documentObject = document) {
  return [...documentObject.querySelectorAll(
    'button,input,select,a[href],[tabindex]:not([tabindex="-1"])',
  )].filter((node) => {
    const style = typeof globalThis.getComputedStyle === "function"
      ? globalThis.getComputedStyle(node)
      : { display: "", visibility: "" };
    if (node.hidden || style.display === "none" || style.visibility === "hidden") return false;
    const associatedLabel = Array.from(node.labels || [], (label) => label.textContent || "").join(" ");
    const name = String(
      node.getAttribute?.("aria-label") ||
      node.textContent ||
      node.getAttribute?.("placeholder") ||
      node.getAttribute?.("title") ||
      associatedLabel ||
      "",
    ).trim();
    return !name;
  }).length;
}

function visibleDomPrivacyAudit(snapshot) {
  const visibleText = String(snapshot?.visible_text || "");
  const fullHtml = String(snapshot?.full_html || "");
  const count = (text, pattern) => (text.match(pattern) || []).length;
  const liveFormControlAudit = snapshot?.live_form_control_audit;
  const liveFormControlAuditValid =
    liveFormControlAudit?.schema === "PFIV025Stage1LiveFormControlPrivacyAuditV1" &&
    Number.isInteger(liveFormControlAudit?.visible_control_count) &&
    liveFormControlAudit.visible_control_count >= 0 &&
    Number.isInteger(liveFormControlAudit?.sensitive_control_count) &&
    liveFormControlAudit.sensitive_control_count >= 0 &&
    Number.isInteger(liveFormControlAudit?.finding_count) &&
    liveFormControlAudit.finding_count >= 0 &&
    isHex(liveFormControlAudit?.structure_sha256, 64);
  const findingCounts = {
    visible_private_path: count(visibleText, /(?:\/Users\/|file:\/\/\/Users\/|MetaDatabase\/PFI|pfi\.sqlite)/giu),
    visible_account_identifier: count(
      visibleText,
      /(?<![0-9A-Fa-f])(?:\d[ ]?){12,19}(?![0-9A-Fa-f])/gu,
    ),
    visible_financial_amount: count(
      visibleText,
      /(?:(?:CNY|AUD|USD|HKD)\s*[:=]?\s*[-+]?\d[\d,]*(?:\.\d+)?|(?:¥|￥|A\$|\$)\s*[-+]?\d[\d,]*(?:\.\d+)?)/giu,
    ),
    visible_chinese_financial_amount: count(
      visibleText,
      /(?:(?:余额|净资产|市值|收益|盈亏|支出|收入|消费|现金流)\s*[:：]\s*[-+]?\d[\d,]*(?:\.\d+)?|[-+]?\d[\d,]*(?:\.\d+)?\s*(?:元|万元|亿元|人民币|澳元|美元|港元))/gu,
    ),
    visible_nonzero_sample_count: count(visibleText, /样本量\s*[:：]?\s*[1-9]\d*/gu),
    visible_numeric_financial_label: count(
      visibleText,
      /(?:余额|净资产|市值|收益|盈亏|支出|收入|消费|现金流)[^\n]{0,24}(?:[-+]?\d[\d,]{3,}(?:\.\d+)?)/gu,
    ),
    html_private_path: count(fullHtml, /(?:\/Users\/[A-Za-z0-9._-]+\/|file:\/\/\/Users\/)/giu),
    html_secret_finding_count: count(
      fullHtml,
      /(?:-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\bgh[pousr]_[A-Za-z0-9]{20,}\b|\bsk-[A-Za-z0-9]{20,}\b)/gu,
    ),
    html_financial_input_value: count(
      fullHtml,
      /<(?:input|textarea)\b(?=[^>]*(?:aria-label|name|data-label)=["'][^"']*(?:数量|成本|价格|金额|余额|净资产|市值|收益|盈亏|支出|收入|消费|现金流|持仓成本)[^"']*["'])(?=[^>]*\bvalue=["']\s*[-+]?\d[\d,]*(?:\.\d+)?\s*["'])[^>]*>/giu,
    ),
    live_financial_form_value: liveFormControlAuditValid ? liveFormControlAudit.finding_count : 1,
  };
  const findingCount = Object.values(findingCounts).reduce((total, value) => total + value, 0);
  return {
    schema: "PFIV025Stage1VisibleDomPrivacyAuditV1",
    visible_text_sha256: sha256(Buffer.from(visibleText, "utf8")),
    visible_text_bytes: Buffer.byteLength(visibleText, "utf8"),
    full_html_sha256: sha256(Buffer.from(fullHtml, "utf8")),
    full_html_bytes: Buffer.byteLength(fullHtml, "utf8"),
    live_form_control_audit: liveFormControlAuditValid
      ? { ...liveFormControlAudit, valid: true }
      : { valid: false },
    finding_counts: findingCounts,
    finding_count: findingCount,
    safe: visibleText.length > 0 && fullHtml.length > 0 && findingCount === 0,
  };
}

async function prepareOutputDirectory(requestedOutputDir, isolatedRoot) {
  const outputDir = path.resolve(requestedOutputDir);
  if (
    pathWithin(outputDir, isolatedRoot) ||
    path.dirname(outputDir) !== "/private/tmp" ||
    !EVIDENCE_ROOT_PATTERN.test(path.basename(outputDir))
  ) {
    fail("output directory boundary is invalid");
  }
  let outputStat;
  let resolved;
  try {
    outputStat = await lstat(outputDir);
    resolved = await realpath(outputDir);
  } catch (_error) {
    fail("output directory boundary is invalid");
  }
  if (
    resolved !== outputDir ||
    !outputStat.isDirectory() ||
    outputStat.isSymbolicLink() ||
    (typeof process.getuid === "function" && outputStat.uid !== process.getuid()) ||
    (outputStat.mode & 0o777) !== 0o700
  ) {
    fail("output directory boundary is invalid");
  }
  for (const name of [
    TRACE_FILE,
    SCREENSHOT_FILE,
    IDENTITY_SCREENSHOT_FILE,
    RESULT_FILE,
    ACCESSIBILITY_FILE,
    FRONTEND_IDENTITY_FILE,
    RUNTIME_API_FILE,
    PRIVACY_FILE,
  ]) {
    await rm(path.join(outputDir, name), { force: true });
  }
  return outputDir;
}

async function publishPublicArtifact(sourcePath, outputDir, fileName) {
  const destination = path.join(outputDir, fileName);
  const temporary = path.join(outputDir, `.${fileName}.publish.tmp`);
  try {
    await writeFile(temporary, await readFile(sourcePath), { mode: 0o600 });
    await rename(temporary, destination);
    await chmod(destination, 0o600);
  } finally {
    await rm(temporary, { force: true });
  }
  return destination;
}

async function loadPlaywright() {
  const moduleDir = process.env.PFI_PLAYWRIGHT_MODULE_DIR;
  if (!moduleDir || !path.isAbsolute(moduleDir)) fail("cached Playwright runtime is unavailable");
  try {
    const loaded = require(path.join(moduleDir, "playwright"));
    if (!loaded?.chromium?.launchPersistentContext) fail("cached Playwright runtime is unavailable");
    return loaded;
  } catch (_error) {
    fail("cached Playwright runtime is unavailable");
  }
}

async function validateProfileBoundary(candidate) {
  const expected = path.join(candidate.isolatedRoot, "browser-profile");
  const declared = process.env.PFI_BROWSER_PROFILE_DIR
    ? path.resolve(process.env.PFI_BROWSER_PROFILE_DIR)
    : expected;
  if (declared !== expected) fail("browser profile boundary is invalid");
  let profileStat;
  try {
    profileStat = await lstat(declared);
  } catch (_error) {
    fail("browser profile boundary is invalid");
  }
  if (
    !profileStat.isDirectory() ||
    profileStat.isSymbolicLink() ||
    (typeof process.getuid === "function" && profileStat.uid !== process.getuid()) ||
    (profileStat.mode & 0o777) !== 0o700 ||
    !pathWithin(declared, candidate.isolatedRoot)
  ) {
    fail("browser profile boundary is invalid");
  }
  const initialEntries = await readdir(declared);
  if (initialEntries.length !== 0) fail("browser profile is not new");
  return { profileDir: declared, initiallyEmpty: true };
}

function privateReplacements(privacy) {
  return [
    [privacy.isolatedRoot, "${ISOLATED_ROOT}"],
    [privacy.projectRoot, "${PROJECT_ROOT}"],
    [privacy.home, "${HOME}"],
  ]
    .filter(([value]) => typeof value === "string" && value.length > 1)
    .sort((left, right) => right[0].length - left[0].length);
}

function redactPrivateText(value, privacy) {
  let text = String(value);
  for (const [raw, symbolic] of privateReplacements(privacy)) {
    text = text.split(raw).join(symbolic);
    try {
      text = text.split(encodeURI(raw)).join(symbolic);
      text = text.split(encodeURIComponent(raw)).join(symbolic);
    } catch (_error) {
      // Exact raw replacement still applies if URI encoding is unavailable.
    }
  }
  text = text.replace(
    /((?:proxy-authorization|set-cookie|x-api-key|authorization|cookie|credential|password|token|secret)["']?\s*[:=]\s*["']?)(\$\{REDACTED\}|[^"',\s}\]]+)/gi,
    (match, prefix, secretValue) =>
      secretValue === REDACTED ? match : `${prefix}${REDACTED}`,
  );
  text = text.replace(
    /("name"\s*:\s*"(?:proxy-authorization|set-cookie|x-api-key|authorization|cookie|credential|password|token|secret)"[^\n\r]{0,160}?"value"\s*:\s*")([^"]*)(")/gi,
    (match, prefix, secretValue, suffix) =>
      secretValue === REDACTED ? match : `${prefix}${REDACTED}${suffix}`,
  );
  text = text.replace(
    /("(?:pid|process_id|processId)"\s*:\s*)\d+/g,
    `$1"${REDACTED_PID}"`,
  );
  for (const rawPid of [
    privacy.activePid,
    privacy.activeMonitorPid,
    privacy.activeLauncherPid,
  ]) {
    if (!/^\d+$/.test(rawPid || "")) continue;
    const activePidPattern = new RegExp(`(^|\\D)${rawPid}(?=\\D|$)`, "g");
    text = text.replace(activePidPattern, `$1${REDACTED_PID}`);
  }
  return text;
}

function redactTraceCookieValues(value, insideCookieArray = false) {
  if (Array.isArray(value)) {
    return value.map((item) => redactTraceCookieValues(item, insideCookieArray));
  }
  if (!isPlainObject(value)) return value;
  const sanitized = {};
  for (const [key, item] of Object.entries(value)) {
    if (key.toLowerCase() === "cookies" && Array.isArray(item)) {
      sanitized[key] = item.map((cookie) => redactTraceCookieValues(cookie, true));
    } else {
      sanitized[key] = redactTraceCookieValues(item, false);
    }
  }
  const sensitiveKey = /^(?:proxy-authorization|set-cookie|authorization|cookie|x-api-key|credential|password|token|secret)$/i;
  for (const key of Object.keys(sanitized)) {
    if (sensitiveKey.test(key) && typeof sanitized[key] !== "object") sanitized[key] = REDACTED;
  }
  if (insideCookieArray && Object.hasOwn(sanitized, "value")) sanitized.value = REDACTED;
  if (sensitiveKey.test(String(sanitized.name || "")) && Object.hasOwn(sanitized, "value")) {
    sanitized.value = REDACTED;
  }
  return sanitized;
}

function redactTraceStructure(value, privacy, activePids = null) {
  const pidSet = activePids || new Set(
    [privacy.activePid, privacy.activeMonitorPid, privacy.activeLauncherPid]
      .map((item) => String(item || ""))
      .filter((item) => /^\d+$/.test(item)),
  );
  if (typeof value === "string") return redactPrivateText(value, privacy);
  if (typeof value === "number" && pidSet.has(String(value))) return REDACTED_PID;
  if (Array.isArray(value)) {
    return value.map((item) => redactTraceStructure(item, privacy, pidSet));
  }
  if (!isPlainObject(value)) return value;
  const sanitized = {};
  for (const [key, item] of Object.entries(value)) {
    const sanitizedKey = redactPrivateText(key, privacy);
    sanitized[sanitizedKey] = /^(?:pid|process_id|processId)$/i.test(key)
      ? REDACTED_PID
      : redactTraceStructure(item, privacy, pidSet);
  }
  return sanitized;
}

function sanitizeTraceText(fileName, decoded, privacy) {
  if (fileName.endsWith(".trace") || fileName.endsWith(".network")) {
    const trailingNewline = decoded.endsWith("\n");
    const lines = decoded.split(/\r?\n/).filter(Boolean);
    const sanitized = lines.map((line) => JSON.stringify(
      redactTraceCookieValues(redactTraceStructure(JSON.parse(line), privacy)),
    ));
    return `${sanitized.join("\n")}${trailingNewline ? "\n" : ""}`;
  }
  if (fileName.endsWith(".stacks") && decoded.trim()) {
    return JSON.stringify(
      redactTraceCookieValues(redactTraceStructure(JSON.parse(decoded), privacy)),
    );
  }
  return redactPrivateText(decoded, privacy);
}

function assertNoFinancialEvidence(value, label = "artifact") {
  const text = String(value || "");
  const forbidden = [
    /\/Users\/[A-Za-z0-9._-]+\//u,
    /file:\/\/[^\s"']+/iu,
    /-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/u,
    /(?:authorization|proxy-authorization|set-cookie|x-api-key|credential|password|secret)["']?\s*[:=]\s*["']?(?!\$\{REDACTED\})[^"',\s}\]]+/iu,
  ];
  if (forbidden.some((pattern) => pattern.test(text))) {
    fail(`${label} contains financial or private data`);
  }
}

function containsNoFinancialEvidence(value) {
  try {
    assertNoFinancialEvidence(value, "candidate visible text");
    return true;
  } catch (_error) {
    return false;
  }
}

function assertBufferHasNoPrivateValues(buffer, privacy, label) {
  for (const [raw] of privateReplacements(privacy)) {
    if (buffer.includes(Buffer.from(raw, "utf8"))) fail(`${label} contains private path data`);
    try {
      for (const encoded of [encodeURI(raw), encodeURIComponent(raw)]) {
        if (buffer.includes(Buffer.from(encoded, "utf8"))) fail(`${label} contains private path data`);
      }
    } catch (_error) {
      // The raw value was already checked.
    }
  }
  const latin1 = buffer.toString("latin1");
  for (const rawPid of [
    privacy.activePid,
    privacy.activeMonitorPid,
    privacy.activeLauncherPid,
  ]) {
    if (
      /^\d+$/.test(rawPid || "") &&
      new RegExp(`(^|\\D)${rawPid}(?=\\D|$)`).test(latin1)
    ) {
      fail(`${label} contains raw PID`);
    }
  }
}

function tryDecodeUtf8(buffer) {
  try {
    return UTF8_DECODER.decode(buffer);
  } catch (_error) {
    return null;
  }
}

function assertPrintableBinaryMetadata(buffer, privacy, label) {
  const printable = (buffer.toString("latin1").match(/[\x20-\x7e]{4,}/g) || []).join("\n");
  if (printable && redactPrivateText(printable, privacy) !== printable) {
    fail(`${label} contains sensitive metadata`);
  }
}

function assertTraceTextStructure(fileName, decoded) {
  if (fileName.endsWith(".trace") || fileName.endsWith(".network")) {
    for (const line of decoded.split(/\r?\n/).filter(Boolean)) JSON.parse(line);
  } else if (fileName.endsWith(".stacks") && decoded.trim()) {
    JSON.parse(decoded);
  }
}

function assertTraceRuntimeValues(fileName, decoded) {
  if (!fileName.endsWith(".trace") && !fileName.endsWith(".network")) return;
  const visit = (value, key = "") => {
    if (Array.isArray(value)) {
      value.forEach((item) => visit(item, key));
      return;
    }
    if (!isPlainObject(value)) {
      if (
        /^(?:visibleText|visible_text|metricValue|metric_value)$/i.test(key) &&
        typeof value === "string" &&
        /(?:\b(?:CNY|AUD|USD|HKD)\s+|(?:¥|￥|RMB|人民币)\s*)[-+]?\d[\d,]*(?:\.\d+)?/iu.test(value)
      ) {
        fail("trace runtime payload contains a private financial value");
      }
      return;
    }
    for (const [childKey, childValue] of Object.entries(value)) visit(childValue, childKey);
  };
  for (const line of decoded.split(/\r?\n/).filter(Boolean)) visit(JSON.parse(line));
}

function assertPngMetadata(buffer, privacy) {
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);
  if (buffer.length < signature.length || !buffer.subarray(0, 8).equals(signature)) {
    fail("screenshot artifact is not a PNG");
  }
  let cursor = 8;
  let sawEnd = false;
  while (cursor + 12 <= buffer.length) {
    const length = buffer.readUInt32BE(cursor);
    const type = buffer.subarray(cursor + 4, cursor + 8).toString("ascii");
    const next = cursor + 12 + length;
    if (next > buffer.length) fail("screenshot PNG is invalid");
    const data = buffer.subarray(cursor + 8, cursor + 8 + length);
    const expectedChecksum = buffer.readUInt32BE(cursor + 8 + length);
    if (crc32(buffer.subarray(cursor + 4, cursor + 8 + length)) !== expectedChecksum) {
      fail("screenshot PNG is invalid");
    }
    if (["tEXt", "zTXt", "iTXt", "eXIf"].includes(type)) {
      fail("screenshot PNG contains text or EXIF metadata");
    }
    cursor = next;
    if (type === "IEND") {
      sawEnd = true;
      break;
    }
  }
  if (!sawEnd || cursor !== buffer.length) fail("screenshot PNG is invalid");
}

function crc32(buffer) {
  let crc = 0xffffffff;
  for (const byte of buffer) {
    crc ^= byte;
    for (let bit = 0; bit < 8; bit += 1) {
      crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
    }
  }
  return (crc ^ 0xffffffff) >>> 0;
}

function locateEndOfCentralDirectory(buffer) {
  const minimum = Math.max(0, buffer.length - 65_557);
  for (let offset = buffer.length - 22; offset >= minimum; offset -= 1) {
    if (buffer.readUInt32LE(offset) === 0x06054b50) return offset;
  }
  fail("trace archive is invalid");
}

function parseTraceArchive(buffer) {
  if (buffer.length < 22) fail("trace archive is invalid");
  const endOffset = locateEndOfCentralDirectory(buffer);
  const disk = buffer.readUInt16LE(endOffset + 4);
  const centralDisk = buffer.readUInt16LE(endOffset + 6);
  const diskEntries = buffer.readUInt16LE(endOffset + 8);
  const totalEntries = buffer.readUInt16LE(endOffset + 10);
  const centralSize = buffer.readUInt32LE(endOffset + 12);
  const centralOffset = buffer.readUInt32LE(endOffset + 16);
  const commentLength = buffer.readUInt16LE(endOffset + 20);
  if (
    disk !== 0 ||
    centralDisk !== 0 ||
    diskEntries !== totalEntries ||
    totalEntries > MAX_ZIP_ENTRIES ||
    centralOffset + centralSize !== endOffset ||
    endOffset + 22 + commentLength !== buffer.length
  ) {
    fail("trace archive is invalid");
  }
  const entries = [];
  let cursor = centralOffset;
  let totalSize = 0;
  for (let index = 0; index < totalEntries; index += 1) {
    if (cursor + 46 > buffer.length || buffer.readUInt32LE(cursor) !== 0x02014b50) {
      fail("trace archive is invalid");
    }
    const flags = buffer.readUInt16LE(cursor + 8);
    const method = buffer.readUInt16LE(cursor + 10);
    const modifiedTime = buffer.readUInt16LE(cursor + 12);
    const modifiedDate = buffer.readUInt16LE(cursor + 14);
    const expectedChecksum = buffer.readUInt32LE(cursor + 16);
    const compressedSize = buffer.readUInt32LE(cursor + 20);
    const uncompressedSize = buffer.readUInt32LE(cursor + 24);
    const nameLength = buffer.readUInt16LE(cursor + 28);
    const extraLength = buffer.readUInt16LE(cursor + 30);
    const commentLength = buffer.readUInt16LE(cursor + 32);
    const externalAttributes = buffer.readUInt32LE(cursor + 38);
    const localOffset = buffer.readUInt32LE(cursor + 42);
    const next = cursor + 46 + nameLength + extraLength + commentLength;
    if (
      next > buffer.length ||
      compressedSize === 0xffffffff ||
      uncompressedSize === 0xffffffff ||
      uncompressedSize > MAX_ZIP_ENTRY_SIZE ||
      (flags & 0x1) !== 0 ||
      (method !== 0 && method !== 8) ||
      localOffset + 30 > buffer.length ||
      buffer.readUInt32LE(localOffset) !== 0x04034b50
    ) {
      fail("trace archive is invalid");
    }
    const fileName = buffer.subarray(cursor + 46, cursor + 46 + nameLength).toString("utf8");
    if (!fileName || fileName.includes("\0") || path.isAbsolute(fileName) || fileName.split("/").includes("..")) {
      fail("trace archive is invalid");
    }
    const localNameLength = buffer.readUInt16LE(localOffset + 26);
    const localExtraLength = buffer.readUInt16LE(localOffset + 28);
    const localFlags = buffer.readUInt16LE(localOffset + 6);
    const localMethod = buffer.readUInt16LE(localOffset + 8);
    const dataOffset = localOffset + 30 + localNameLength + localExtraLength;
    const localFileName = buffer
      .subarray(localOffset + 30, localOffset + 30 + localNameLength)
      .toString("utf8");
    if (
      dataOffset + compressedSize > buffer.length ||
      localFlags !== flags ||
      localMethod !== method ||
      localFileName !== fileName
    ) {
      fail("trace archive is invalid");
    }
    const compressed = buffer.subarray(dataOffset, dataOffset + compressedSize);
    let content;
    try {
      content = method === 0
        ? Buffer.from(compressed)
        : inflateRawSync(compressed, { maxOutputLength: MAX_ZIP_ENTRY_SIZE });
    } catch (_error) {
      fail("trace archive is invalid");
    }
    if (content.length !== uncompressedSize || crc32(content) !== expectedChecksum) {
      fail("trace archive is invalid");
    }
    totalSize += content.length;
    if (totalSize > MAX_ZIP_TOTAL_SIZE) fail("trace archive is too large");
    entries.push({
      fileName,
      uncompressedSize,
      content,
      modifiedTime,
      modifiedDate,
      externalAttributes,
    });
    cursor = next;
  }
  if (cursor !== centralOffset + centralSize) fail("trace archive is invalid");
  return entries;
}

function sanitizeTraceEntries(entries, privacy) {
  return entries.map((entry) => {
    let fileName = redactPrivateText(entry.fileName, privacy);
    if (fileName.includes("${")) fileName = `redacted/${sha256(Buffer.from(entry.fileName))}`;
    let content = entry.content;
    const decoded = tryDecodeUtf8(content);
    if (decoded !== null) {
      content = Buffer.from(sanitizeTraceText(entry.fileName, decoded, privacy), "utf8");
    } else {
      assertBufferHasNoPrivateValues(content, privacy, "trace archive member");
    }
    return { ...entry, fileName, content, uncompressedSize: content.length };
  });
}

function buildTraceArchive(entries) {
  const localParts = [];
  const centralParts = [];
  let localOffset = 0;
  for (const entry of entries) {
    const name = Buffer.from(entry.fileName, "utf8");
    const compressed = deflateRawSync(entry.content, { level: 9 });
    const checksum = crc32(entry.content);
    const localHeader = Buffer.alloc(30);
    localHeader.writeUInt32LE(0x04034b50, 0);
    localHeader.writeUInt16LE(20, 4);
    localHeader.writeUInt16LE(0x0800, 6);
    localHeader.writeUInt16LE(8, 8);
    localHeader.writeUInt16LE(entry.modifiedTime, 10);
    localHeader.writeUInt16LE(entry.modifiedDate, 12);
    localHeader.writeUInt32LE(checksum, 14);
    localHeader.writeUInt32LE(compressed.length, 18);
    localHeader.writeUInt32LE(entry.content.length, 22);
    localHeader.writeUInt16LE(name.length, 26);
    localHeader.writeUInt16LE(0, 28);
    localParts.push(localHeader, name, compressed);

    const centralHeader = Buffer.alloc(46);
    centralHeader.writeUInt32LE(0x02014b50, 0);
    centralHeader.writeUInt16LE(20, 4);
    centralHeader.writeUInt16LE(20, 6);
    centralHeader.writeUInt16LE(0x0800, 8);
    centralHeader.writeUInt16LE(8, 10);
    centralHeader.writeUInt16LE(entry.modifiedTime, 12);
    centralHeader.writeUInt16LE(entry.modifiedDate, 14);
    centralHeader.writeUInt32LE(checksum, 16);
    centralHeader.writeUInt32LE(compressed.length, 20);
    centralHeader.writeUInt32LE(entry.content.length, 24);
    centralHeader.writeUInt16LE(name.length, 28);
    centralHeader.writeUInt16LE(0, 30);
    centralHeader.writeUInt16LE(0, 32);
    centralHeader.writeUInt16LE(0, 34);
    centralHeader.writeUInt16LE(0, 36);
    centralHeader.writeUInt32LE(entry.externalAttributes, 38);
    centralHeader.writeUInt32LE(localOffset, 42);
    centralParts.push(centralHeader, name);
    localOffset += localHeader.length + name.length + compressed.length;
  }
  const central = Buffer.concat(centralParts);
  const end = Buffer.alloc(22);
  end.writeUInt32LE(0x06054b50, 0);
  end.writeUInt16LE(0, 4);
  end.writeUInt16LE(0, 6);
  end.writeUInt16LE(entries.length, 8);
  end.writeUInt16LE(entries.length, 10);
  end.writeUInt32LE(central.length, 12);
  end.writeUInt32LE(localOffset, 16);
  end.writeUInt16LE(0, 20);
  return Buffer.concat([...localParts, central, end]);
}

async function scanTraceArchiveEntries(tracePath, privacy, sanitize = false) {
  let archive;
  try {
    archive = await readFile(tracePath);
  } catch (_error) {
    fail("trace archive is unavailable");
  }
  let entries = parseTraceArchive(archive);
  if (sanitize) {
    entries = sanitizeTraceEntries(entries, privacy);
    const temporary = `${tracePath}.sanitized.tmp`;
    try {
      await writeFile(temporary, buildTraceArchive(entries), { mode: 0o600 });
      await rename(temporary, tracePath);
      await chmod(tracePath, 0o600);
    } finally {
      await rm(temporary, { force: true });
    }
    entries = parseTraceArchive(await readFile(tracePath));
  }
  for (const entry of entries) {
    if (!entry.fileName || entry.uncompressedSize !== entry.content.length) {
      fail("trace archive member is invalid");
    }
    assertBufferHasNoPrivateValues(Buffer.from(entry.fileName, "utf8"), privacy, "trace member name");
    assertBufferHasNoPrivateValues(entry.content, privacy, "trace archive member");
    const decoded = tryDecodeUtf8(entry.content);
    if (decoded !== null && redactPrivateText(decoded, privacy) !== decoded) {
      fail("trace archive member contains sensitive data");
    }
    if (decoded !== null && /"(?:pid|process_id|processId)"\s*:\s*\d+/.test(decoded)) {
      fail("trace archive member contains raw PID");
    }
    if (decoded !== null) {
      try {
        assertTraceTextStructure(entry.fileName, decoded);
        assertTraceRuntimeValues(entry.fileName, decoded);
      } catch (_error) {
        fail("trace archive text member is invalid");
      }
      assertNoFinancialEvidence(decoded, "trace archive member");
    }
    if (decoded === null) {
      assertPrintableBinaryMetadata(entry.content, privacy, "trace archive member");
    }
  }
  return entries.map((entry) => ({
    fileName: entry.fileName,
    uncompressedSize: entry.uncompressedSize,
    sha256: sha256(entry.content),
  }));
}

async function assertPublicArtifact(artifactPath, privacy, kind, sanitizeTrace = true) {
  if (kind === "trace") {
    const traceEntries = await scanTraceArchiveEntries(artifactPath, privacy, sanitizeTrace);
    for (const entry of traceEntries) {
      if (!entry.fileName || !Number.isInteger(entry.uncompressedSize)) {
        fail("trace archive member is invalid");
      }
    }
    return { entries: traceEntries.length, sha256: sha256(await readFile(artifactPath)) };
  }
  const buffer = await readFile(artifactPath);
  assertBufferHasNoPrivateValues(buffer, privacy, `${kind} artifact`);
  if (kind === "screenshot") assertPngMetadata(buffer, privacy);
  if (kind === "json") {
    const text = buffer.toString("utf8");
    if (redactPrivateText(text, privacy) !== text) {
      fail("JSON artifact contains sensitive data");
    }
    if (/"(?:pid|process_id|processId)"\s*:\s*\d+/.test(text)) {
      fail("JSON artifact contains raw PID");
    }
    JSON.parse(text);
  }
  return { sha256: sha256(buffer), bytes: buffer.length };
}

async function collectPageShowObservations(page, target) {
  try {
    const observed = await page.evaluate(() =>
      Array.isArray(window.__PFI_PAGESHOW_OBSERVATIONS__)
        ? [...window.__PFI_PAGESHOW_OBSERVATIONS__]
        : [],
    );
    target.push(...observed.filter((value) => value && typeof value === "object"));
  } catch (_error) {
    fail("pageshow observation failed");
  }
}

function frameTreeRecords(frameTree, target = []) {
  if (!frameTree || !isPlainObject(frameTree.frame)) return target;
  target.push(frameTree.frame);
  for (const child of frameTree.childFrames || []) frameTreeRecords(child, target);
  return target;
}

async function collectAccessibilityTree(devtools, snapshot) {
  const expectedPrimaryNames = [
    "首页总览",
    "账户与资产",
    "账本流水",
    "投资管理",
    "消费管理",
    "数据源与上传",
    "建议与复盘",
    "报告与洞察",
    "市场与研究",
    "设置",
  ];
  const interactiveRoles = new Set([
    "button",
    "link",
    "textbox",
    "searchbox",
    "combobox",
    "checkbox",
    "radio",
    "switch",
    "slider",
    "spinbutton",
    "menuitem",
    "tab",
    "listbox",
    "option",
    "treeitem",
  ]);
  const response = await devtools.send("Page.getFrameTree");
  const srcdocFrames = frameTreeRecords(response?.frameTree).filter(
    (frame) => String(frame?.url || "").startsWith("about:srcdoc"),
  );
  let selected = null;
  for (const frame of srcdocFrames) {
    const accessibility = await devtools.send("Accessibility.getFullAXTree", {
      frameId: frame.id,
    });
    const nodes = Array.isArray(accessibility?.nodes) ? accessibility.nodes : [];
    const headingMatchCount = nodes.filter(
      (node) =>
        node?.ignored !== true &&
        String(node?.role?.value || "") === "heading" &&
        String(node?.name?.value || "") === "首页总览 · 财务状态",
    ).length;
    const visibleButtonNames = nodes
      .filter(
        (node) =>
          node?.ignored !== true && String(node?.role?.value || "") === "button",
      )
      .map((node) => String(node?.name?.value || "").trim());
    const primaryNames = new Set(
      expectedPrimaryNames.filter(
        (expectedName) =>
          visibleButtonNames.some((buttonName) => buttonName.includes(expectedName)),
      ),
    );
    const focusableNodes = nodes.filter(
      (node) =>
        node?.ignored !== true &&
        interactiveRoles.has(String(node?.role?.value || "")) &&
        Array.isArray(node?.properties) &&
        node.properties.some(
          (property) => property?.name === "focusable" && property?.value?.value === true,
        ),
    );
    const unnamedFocusableCount = focusableNodes.filter(
      (node) => !String(node?.name?.value || "").trim(),
    ).length;
    const score = headingMatchCount * 100 + primaryNames.size * 10 + focusableNodes.length;
    if (!selected || score > selected.score) {
      selected = {
        frame,
        nodes,
        headingMatchCount,
        primaryNames,
        focusableNodes,
        unnamedFocusableCount,
        score,
      };
    }
  }
  if (
    !selected ||
    selected.headingMatchCount < 1 ||
    selected.primaryNames.size !== expectedPrimaryNames.length ||
    selected.focusableNodes.length < expectedPrimaryNames.length ||
    selected.unnamedFocusableCount !== 0
  ) {
    fail("srcdoc accessibility contract failed");
  }
  const sanitized = selected.nodes.map((node) => ({
    role: String(node?.role?.value || ""),
    name: String(node?.name?.value || ""),
    ignored: node?.ignored === true,
    focusable:
      Array.isArray(node?.properties) &&
      node.properties.some(
        (property) => property?.name === "focusable" && property?.value?.value === true,
      ),
    child_count: Array.isArray(node?.childIds) ? node.childIds.length : 0,
  }));
  return {
    schema: "PFIV025Stage1WholeReviewAccessibilityTreeV1",
    source: "Accessibility.getFullAXTree",
    frame_discovery_source: "Page.getFrameTree",
    frame_url: String(selected.frame.url),
    frame_url_sha256: sha256(Buffer.from(String(selected.frame.url), "utf8")),
    selected_frame_id_sha256: sha256(Buffer.from(String(selected.frame.id), "utf8")),
    srcdoc_frame_candidate_count: srcdocFrames.length,
    node_count: sanitized.length,
    nodes: sanitized,
    ax_contract: {
      h1_exact_match_count: selected.headingMatchCount,
      primary_navigation_named_count: selected.primaryNames.size,
      named_focusable_count:
        selected.focusableNodes.length - selected.unnamedFocusableCount,
      unnamed_focusable_count: selected.unnamedFocusableCount,
    },
    official_dom_contract: {
      shell_schema: snapshot.shell_schema,
      header_present: snapshot.header_present,
      navigation_present: snapshot.navigation_present,
      main_present: snapshot.main_present,
      skip_link_present: snapshot.skip_link_present,
      h1_text: snapshot.h1_text,
      primary_entries: snapshot.primary_entries,
      duplicate_id_count: snapshot.duplicate_id_count,
      focusable_without_name_count: snapshot.focusable_without_name_count,
    },
  };
}

async function selectPrimaryRoute(page, route) {
  const frame = await resolveShellFrame(page);
  await frame
    .locator(
      `nav[aria-label="一级工作区"] [data-primary-entry="true"][data-route-alias="${route.routeAlias}"]`,
    )
    .click();
  await frame.waitForFunction(
    ({ routeAlias, workspace }) => {
      const active = document.querySelector(
        'nav[aria-label="一级工作区"] [data-primary-entry="true"].is-active',
      );
      const main = document.querySelector("main#main-workspace");
      return (
        active?.dataset?.routeAlias === routeAlias &&
        active?.dataset?.workspace === workspace &&
        main?.dataset?.activeWorkspace === workspace
      );
    },
    { routeAlias: route.routeAlias, workspace: route.workspace },
    { timeout: 30_000 },
  );
}

async function collectPrimaryRouteMatrix(page, release, marker) {
  const snapshots = [];
  const audits = [];
  for (const route of PRIMARY_ROUTES) {
    await selectPrimaryRoute(page, route);
    const snapshot = await readShellSnapshot(page, release);
    const privacy = visibleDomPrivacyAudit(snapshot);
    const live = privacy.live_form_control_audit;
    const activeRouteMatches =
      snapshot.active_primary_route_alias === route.routeAlias &&
      snapshot.active_primary_workspace === route.workspace &&
      snapshot.main_active_workspace === route.workspace;
    const identityMatches =
      sameRuntimeIdentity(snapshot, release, marker) &&
      completeVisibleIdentityMatchesRelease(snapshot, release);
    const liveControlsSafe =
      live?.valid === true &&
      live?.finding_count === 0 &&
      isHex(live?.structure_sha256, 64);
    const fxBadgeSafe = isolatedFxBadgeReady(snapshot);
    const routeShellReady =
      snapshot.shell_schema === "PFIOSWebShellContractV1" &&
      snapshot.header_present === true &&
      snapshot.navigation_present === true &&
      snapshot.main_present === true &&
      snapshot.skip_link_present === true &&
      snapshot.h1_text.length > 0 &&
      snapshot.primary_entries.length === PRIMARY_ROUTES.length &&
      snapshot.duplicate_id_count === 0 &&
      snapshot.focusable_without_name_count === 0;
    const failedChecks = [
      activeRouteMatches,
      identityMatches,
      privacy.safe === true,
      liveControlsSafe,
      fxBadgeSafe,
      routeShellReady,
    ].filter((value) => value !== true).length;
    snapshots.push(snapshot);
    audits.push({
      route_visit_count: 1,
      route_alias_sha256: sha256(Buffer.from(route.routeAlias, "utf8")),
      workspace_sha256: sha256(Buffer.from(route.workspace, "utf8")),
      active_route_match_count: activeRouteMatches ? 1 : 0,
      identity_match_count: identityMatches ? 1 : 0,
      identity_field_visible_count: Number(snapshot.release_identity_details?.visible_field_count || 0),
      visible_dom_safe_count: privacy.safe === true ? 1 : 0,
      live_control_safe_count: liveControlsSafe ? 1 : 0,
      isolated_fx_badge_safe_count: fxBadgeSafe ? 1 : 0,
      official_shell_safe_count: routeShellReady ? 1 : 0,
      failed_check_count: failedChecks,
      visible_text_sha256: privacy.visible_text_sha256,
      full_html_sha256: privacy.full_html_sha256,
      visible_dom_finding_count: privacy.finding_count,
      visible_control_count: Number(live?.visible_control_count || 0),
      sensitive_control_count: Number(live?.sensitive_control_count || 0),
      live_control_finding_count: Number(live?.finding_count || 0),
      live_control_structure_sha256: String(live?.structure_sha256 || ""),
      release_identity_sha256: sha256(
        Buffer.from(stableJson(snapshot.release_identity_details), "utf8"),
      ),
      fx_badge_sha256: sha256(Buffer.from(stableJson(snapshot.fx_badge), "utf8")),
    });
  }
  await selectPrimaryRoute(page, PRIMARY_ROUTES[0]);
  const restoredHome = await readShellSnapshot(page, release);
  return { snapshots, audits, restoredHome };
}

async function runBrowserValidation(candidate, marker, release, runtime) {
  const { chromium } = await loadPlaywright();
  const profile = await validateProfileBoundary(candidate);
  const stagingDir = path.join(candidate.isolatedRoot, "tmp");
  const stagingStat = await lstat(stagingDir);
  if (
    !stagingStat.isDirectory() ||
    stagingStat.isSymbolicLink() ||
    (typeof process.getuid === "function" && stagingStat.uid !== process.getuid()) ||
    (stagingStat.mode & 0o777) !== 0o700
  ) {
    fail("browser staging boundary is invalid");
  }
  const tracePath = path.join(stagingDir, STAGING_TRACE_FILE);
  const screenshotPath = path.join(stagingDir, STAGING_SCREENSHOT_FILE);
  const identityScreenshotPath = path.join(stagingDir, STAGING_IDENTITY_SCREENSHOT_FILE);
  await rm(tracePath, { force: true });
  await rm(screenshotPath, { force: true });
  await rm(identityScreenshotPath, { force: true });
  const pageShowObservations = [];
  const consoleErrors = [];
  const pageErrors = [];
  const requestFailures = [];
  const httpErrors = [];
  const unexpectedHosts = [];
  const webSocketErrors = [];
  const observedRequestPorts = new Set();
  const apiResponseCounts = new Map();
  let webSocketCount = 0;
  let closingContext = false;
  let navigationTransition = false;
  let context;
  let tracingStarted = false;
  let browserFailure = null;
  let heartbeatFailure = false;
  let snapshots;
  const sendHeartbeat = async () => {
    try {
      const response = await fetch(
        `http://127.0.0.1:${candidate.heartbeatPort}/heartbeat`,
        {
          method: "POST",
          cache: "no-store",
          signal: AbortSignal.timeout(5_000),
        },
      );
      if (response.status !== 204) heartbeatFailure = true;
    } catch (_error) {
      heartbeatFailure = true;
    }
  };
  await sendHeartbeat();
  const heartbeatTimer = setInterval(() => {
    void sendHeartbeat();
  }, 20_000);
  try {
    context = await chromium.launchPersistentContext(profile.profileDir, {
      headless: true,
      viewport: { width: 1440, height: 1000 },
      serviceWorkers: "allow",
      env: {
        PATH: process.env.PATH || "/usr/bin:/bin:/usr/sbin:/sbin",
        LANG: process.env.LANG || "en_US.UTF-8",
        LC_ALL: process.env.LC_ALL || process.env.LANG || "en_US.UTF-8",
        HOME: path.join(candidate.isolatedRoot, "home"),
        TMPDIR: path.join(candidate.isolatedRoot, "tmp"),
        XDG_CACHE_HOME: path.join(candidate.isolatedRoot, "cache"),
      },
    });
    await context.addInitScript(() => {
      window.__PFI_PAGESHOW_OBSERVATIONS__ = [];
      window.__PFI_RUNTIME_API_CALLS__ = [];
      const originalFetch = window.fetch.bind(window);
      window.fetch = (...args) => {
        const value = typeof args[0] === "string" ? args[0] : args[0]?.url || "";
        try {
          const parsed = new URL(String(value), window.location.href);
          if (parsed.pathname.startsWith("/api/")) {
            window.__PFI_RUNTIME_API_CALLS__.push({
              path: parsed.pathname,
              sequence: window.__PFI_RUNTIME_API_CALLS__.length + 1,
            });
          }
        } catch (_error) {
          // Invalid URLs are handled by the native fetch implementation.
        }
        return originalFetch(...args);
      };
      window.addEventListener("pageshow", (event) => {
        const navigation = performance.getEntriesByType("navigation")[0];
        window.__PFI_PAGESHOW_OBSERVATIONS__.push({
          persisted: Boolean(event.persisted),
          navigation_type: String(navigation?.type || "unknown"),
          url: window.location.href,
          sequence: window.__PFI_PAGESHOW_OBSERVATIONS__.length + 1,
        });
      });
    });
    context.on("request", (request) => {
      try {
        const requestUrl = new URL(request.url());
        const port = Number(requestUrl.port || (requestUrl.protocol === "https:" ? 443 : 80));
        if (Number.isInteger(port)) observedRequestPorts.add(port);
        if (
          ["http:", "https:", "ws:", "wss:"].includes(requestUrl.protocol) &&
          !["localhost", "127.0.0.1"].includes(requestUrl.hostname)
        ) {
          unexpectedHosts.push("unexpected_host");
        }
      } catch (_error) {
        // Non-network requests do not affect the live-port assertion.
      }
    });
    context.on("requestfailed", (request) => {
      if (closingContext) return;
      const reason = String(request.failure()?.errorText || "");
      const expectedAbort =
        navigationTransition &&
        (reason.includes("ERR_ABORTED") || reason.includes("NS_BINDING_ABORTED"));
      if (!expectedAbort) {
        requestFailures.push("request_failed");
      }
    });
    context.on("response", (response) => {
      if (response.status() >= 400) httpErrors.push("http_error");
      try {
        const parsed = new URL(response.url());
        if (parsed.pathname.startsWith("/api/")) {
          apiResponseCounts.set(parsed.pathname, (apiResponseCounts.get(parsed.pathname) || 0) + 1);
        }
      } catch (_error) {
        // Non-URL responses do not affect API evidence counts.
      }
    });
    await context.tracing.start({ screenshots: true, snapshots: true, sources: false });
    tracingStarted = true;
    const page = context.pages()[0] || (await context.newPage());
    page.on("console", (message) => {
      if (message.type() === "error") consoleErrors.push("console_error");
    });
    page.on("pageerror", () => pageErrors.push("page_error"));
    page.on("websocket", (socket) => {
      webSocketCount += 1;
      socket.on("socketerror", () => {
        if (!closingContext) webSocketErrors.push("websocket_error");
      });
    });
    const navigate = async (operation) => {
      navigationTransition = true;
      try {
        return await operation();
      } finally {
        navigationTransition = false;
      }
    };

    const appUrl = `${runtime.baseUrl}/?${releaseQuery(release)}`;
    await navigate(() => page.goto(appUrl, { waitUntil: "domcontentloaded", timeout: 60_000 }));
    const initial = await readShellSnapshot(page, release);
    const initialUrl = page.url();
    await collectPageShowObservations(page, pageShowObservations);

    await navigate(() => page.reload({ waitUntil: "domcontentloaded", timeout: 60_000 }));
    const ordinaryReload = await readShellSnapshot(page, release);
    await collectPageShowObservations(page, pageShowObservations);

    const devtools = await context.newCDPSession(page);
    await devtools.send("Network.enable");
    await devtools.send("Network.clearBrowserCache");
    await navigate(() => page.reload({ waitUntil: "domcontentloaded", timeout: 60_000 }));
    const cacheClearedReload = await readShellSnapshot(page, release);
    await collectPageShowObservations(page, pageShowObservations);

    const legacyUrl = new URL(appUrl);
    legacyUrl.searchParams.set("pfi_legacy", "1");
    await navigate(() =>
      page.goto(legacyUrl.toString(), { waitUntil: "domcontentloaded", timeout: 60_000 }),
    );
    const legacyQuery = await readShellSnapshot(page, release);
    const legacyObservedUrl = page.url();
    await collectPageShowObservations(page, pageShowObservations);
    await navigate(() => page.goto(appUrl, { waitUntil: "domcontentloaded", timeout: 60_000 }));
    const legacyReturn = await readShellSnapshot(page, release);
    await collectPageShowObservations(page, pageShowObservations);

    const probeUrl = new URL(appUrl);
    probeUrl.searchParams.set("pfi_probe", "stage1-phase13");
    await navigate(() =>
      page.goto(probeUrl.toString(), { waitUntil: "domcontentloaded", timeout: 60_000 }),
    );
    const probe = await readShellSnapshot(page, release);
    const probeObservedUrl = page.url();
    await collectPageShowObservations(page, pageShowObservations);
    await navigate(() => page.goBack({ waitUntil: "domcontentloaded", timeout: 60_000 }));
    const back = await readShellSnapshot(page, release);
    const backObservedUrl = page.url();
    await collectPageShowObservations(page, pageShowObservations);
    await navigate(() => page.goForward({ waitUntil: "domcontentloaded", timeout: 60_000 }));
    const forward = await readShellSnapshot(page, release);
    const forwardObservedUrl = page.url();
    await collectPageShowObservations(page, pageShowObservations);
    const frame = await resolveShellFrame(page);
    const callsBeforeSynthetic = await frame.evaluate(() =>
      Array.isArray(window.__PFI_RUNTIME_API_CALLS__) ? window.__PFI_RUNTIME_API_CALLS__.length : 0,
    );
    await frame.evaluate(() => {
      window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true }));
    });
    await frame.waitForFunction(
      () => document.body?.dataset?.pfiReleaseIdentityState === "ready",
      undefined,
      { timeout: 30_000 },
    );
    const callsAfterSynthetic = await frame.evaluate(() =>
      Array.isArray(window.__PFI_RUNTIME_API_CALLS__) ? window.__PFI_RUNTIME_API_CALLS__.length : 0,
    );
    const primaryRouteMatrix = await collectPrimaryRouteMatrix(page, release, marker);
    const screenshotBefore = await readShellSnapshot(page, release);
    await devtools.send("Accessibility.enable");
    const accessibilityTree = await collectAccessibilityTree(devtools, screenshotBefore);
    await captureShellScreenshot(page, screenshotPath);
    await captureIdentityScreenshot(page, identityScreenshotPath);
    const screenshotAfter = await readShellSnapshot(page, release);
    snapshots = {
      initial,
      ordinaryReload,
      cacheClearedReload,
      legacyQuery,
      legacyReturn,
      probe,
      back,
      forward,
      screenshotBefore,
      screenshotAfter,
      accessibilityTree,
      primaryRouteSnapshots: primaryRouteMatrix.snapshots,
      primaryRouteAudits: primaryRouteMatrix.audits,
      primaryRouteRestoredHome: primaryRouteMatrix.restoredHome,
      legacyQueryAudit: {
        visit_count: 1,
        url_sha256: sha256(Buffer.from(legacyObservedUrl, "utf8")),
        query_value_sha256: sha256(
          Buffer.from(String(new URL(legacyObservedUrl).searchParams.get("pfi_legacy") || ""), "utf8"),
        ),
        query_value_match_count:
          new URL(legacyObservedUrl).searchParams.get("pfi_legacy") === "1" ? 1 : 0,
      },
      syntheticPageshow: {
        synthetic: true,
        persisted: true,
        api_calls_before: callsBeforeSynthetic,
        api_calls_after: callsAfterSynthetic,
      },
      history: {
        expectedInitial: appUrl,
        expectedProbe: probeUrl.toString(),
        initial: initialUrl,
        probe: probeObservedUrl,
        back: backObservedUrl,
        forward: forwardObservedUrl,
      },
    };
  } catch (error) {
    browserFailure = error;
  } finally {
    clearInterval(heartbeatTimer);
    closingContext = true;
    if (context && tracingStarted) {
      try {
        await context.tracing.stop({ path: tracePath });
      } catch (error) {
        browserFailure ||= error;
      }
    }
    if (context) {
      try {
        await context.close();
      } catch (error) {
        browserFailure ||= error;
      }
    }
  }
  if (browserFailure || heartbeatFailure || !snapshots) {
    await rm(tracePath, { force: true });
    await rm(screenshotPath, { force: true });
    await rm(identityScreenshotPath, { force: true });
    fail("browser runtime validation failed");
  }

  const afterEntries = await readdir(profile.profileDir);
  const identity = (snapshot) => sameRuntimeIdentity(snapshot, release, marker);
  const shellSnapshots = [
    snapshots.initial,
    snapshots.ordinaryReload,
    snapshots.cacheClearedReload,
    snapshots.legacyQuery,
    snapshots.legacyReturn,
    snapshots.probe,
    snapshots.back,
    snapshots.forward,
    snapshots.primaryRouteRestoredHome,
    snapshots.screenshotBefore,
    snapshots.screenshotAfter,
  ];
  const allRouteAuditsPass =
    snapshots.primaryRouteAudits.length === PRIMARY_ROUTES.length &&
    snapshots.primaryRouteAudits.every(
      (audit, index) =>
        audit.route_visit_count === 1 &&
        audit.route_alias_sha256 ===
          sha256(Buffer.from(PRIMARY_ROUTES[index].routeAlias, "utf8")) &&
        audit.workspace_sha256 === sha256(Buffer.from(PRIMARY_ROUTES[index].workspace, "utf8")) &&
        audit.active_route_match_count === 1 &&
        audit.identity_match_count === 1 &&
        audit.identity_field_visible_count === 5 &&
        audit.visible_dom_safe_count === 1 &&
        audit.live_control_safe_count === 1 &&
        audit.isolated_fx_badge_safe_count === 1 &&
        audit.official_shell_safe_count === 1 &&
        audit.failed_check_count === 0 &&
        audit.visible_dom_finding_count === 0 &&
        audit.live_control_finding_count === 0 &&
        isHex(audit.visible_text_sha256, 64) &&
        isHex(audit.full_html_sha256, 64) &&
        isHex(audit.live_control_structure_sha256, 64) &&
        isHex(audit.release_identity_sha256, 64) &&
        isHex(audit.fx_badge_sha256, 64),
    );
  const privacySnapshots = [...shellSnapshots, ...snapshots.primaryRouteSnapshots];
  const frontendPaths = new Set(snapshots.initial.frontend_source_hashes.map((item) => item.path));
  const expectedInlinePaths = new Set(FRONTEND_FILES.filter((item) => item !== "PFI/web/index.html"));
  const apiCount = (apiPath) => apiResponseCounts.get(apiPath) || 0;
  const accessibility = snapshots.accessibilityTree;
  const checks = {
    official_shell_contract_verified: shellSnapshots.every(officialShellReady),
    frontend_source_set_exact_14:
      frontendPaths.size === 13 &&
      frontendPaths.size === expectedInlinePaths.size &&
      [...frontendPaths].every((item) => expectedInlinePaths.has(item)) &&
      release.sourceIdentity.frontend.file_count === 15,
    frontend_source_bytes_match:
      shellSnapshots.every((snapshot) => snapshot.frontend_source_bytes_match === true),
    frontend_bundle_hash_recomputed:
      release.sourceIdentity.frontend.sha256 === release.manifest.frontend_bundle_hash,
    frontend_bundle_hash_cross_surface_match:
      shellSnapshots.every(
        (snapshot) =>
          snapshot.frontend_source_hash === release.manifest.frontend_bundle_hash &&
          snapshot.manifest.frontend_bundle_hash === release.manifest.frontend_bundle_hash &&
          snapshot.runtime_manifest.body.frontend_bundle_hash === release.manifest.frontend_bundle_hash,
      ),
    frontend_modules_executed: shellSnapshots.every((snapshot) =>
      FRONTEND_GLOBALS.every((name) => snapshot.frontend_globals_ready?.[name] === true),
    ),
    three_loopback_endpoints_owned:
      candidate.state.inspection?.process_group_verified === true &&
      candidate.state.inspection?.process_group_member_count === 3 &&
      isHex(candidate.state.inspection?.process_group_identity_sha256, 64) &&
      candidate.state.inspection?.listener_endpoint_set_verified === true &&
      candidate.state.inspection?.listener_endpoint_count === 3 &&
      candidate.state.inspection?.streamlit_listener_count === 2 &&
      candidate.state.inspection?.runtime_api_port === runtime.runtimeApiPort &&
      runtime.heartbeatReady === true,
    fresh_profile_initially_empty: profile.initiallyEmpty && afterEntries.length > 0,
    manifest_api_real:
      shellSnapshots.every((snapshot) => manifestMatchesRelease(snapshot, release)) &&
      apiCount("/api/release-manifest") >= shellSnapshots.length,
    cache_policy_api_real:
      shellSnapshots.every((snapshot) => policyMatchesRelease(snapshot, release, marker)) &&
      apiCount("/api/release-cache-policy") >= shellSnapshots.length,
    read_model_status_api_real:
      shellSnapshots.every(
        (snapshot) =>
          snapshot.runtime_read_model_status.status === 200 &&
          snapshot.runtime_read_model_status.headers["x-pfi-read-model-sha256"] ===
            snapshot.runtime_read_model_status.body.read_model_hash,
      ) && apiCount("/api/read-model-status") >= shellSnapshots.length,
    read_model_status_drives_ui: shellSnapshots.every((snapshot) =>
      snapshot.api_calls_before_snapshot.some((item) => item?.path === "/api/read-model-status"),
    ),
    running_backend_header_verified:
      runtime.api.manifest.headers["x-pfi-running-backend-sha256"] ===
        release.sourceIdentity.backend.sha256 &&
      runtime.api.policy.headers["x-pfi-running-backend-sha256"] ===
        release.sourceIdentity.backend.sha256 &&
      runtime.api.read_model_status.headers["x-pfi-running-backend-sha256"] ===
        release.sourceIdentity.backend.sha256,
    ordinary_reload_revalidated: identity(snapshots.ordinaryReload),
    cache_cleared_reload_revalidated: identity(snapshots.cacheClearedReload),
    back_forward_revalidated:
      identity(snapshots.probe) &&
      identity(snapshots.back) &&
      identity(snapshots.forward) &&
      snapshots.history.initial === snapshots.history.expectedInitial &&
      snapshots.history.probe === snapshots.history.expectedProbe &&
      snapshots.history.back === snapshots.history.expectedInitial &&
      snapshots.history.forward === snapshots.history.expectedProbe,
    pageshow_real_observed: pageShowObservations.length > 0,
    pageshow_persisted_guard_verified:
      snapshots.syntheticPageshow.synthetic === true &&
      snapshots.syntheticPageshow.persisted === true &&
      snapshots.syntheticPageshow.api_calls_after >= snapshots.syntheticPageshow.api_calls_before + 2,
    service_worker_and_cache_storage_empty:
      privacySnapshots.every(serviceWorkerAuditReady),
    legacy_query_official_isolated_verified:
      snapshots.legacyQueryAudit.visit_count === 1 &&
      snapshots.legacyQueryAudit.query_value_match_count === 1 &&
      isHex(snapshots.legacyQueryAudit.url_sha256, 64) &&
      isHex(snapshots.legacyQueryAudit.query_value_sha256, 64) &&
      identity(snapshots.legacyQuery) &&
      officialShellReady(snapshots.legacyQuery) &&
      snapshots.legacyQuery.isolated_empty_data === true &&
      isolatedRuntimePayloadSafe(snapshots.legacyQuery) &&
      visibleDomPrivacyAudit(snapshots.legacyQuery).safe === true,
    primary_route_matrix_verified: allRouteAuditsPass,
    primary_route_identity_verified:
      snapshots.primaryRouteSnapshots.length === PRIMARY_ROUTES.length &&
      snapshots.primaryRouteSnapshots.every(
        (snapshot) =>
          sameRuntimeIdentity(snapshot, release, marker) &&
          completeVisibleIdentityMatchesRelease(snapshot, release),
      ),
    primary_route_visible_dom_privacy_verified:
      snapshots.primaryRouteSnapshots.length === PRIMARY_ROUTES.length &&
      snapshots.primaryRouteSnapshots.every(
        (snapshot) => visibleDomPrivacyAudit(snapshot).safe === true,
      ),
    primary_route_live_controls_verified:
      snapshots.primaryRouteSnapshots.length === PRIMARY_ROUTES.length &&
      snapshots.primaryRouteSnapshots.every((snapshot) => {
        const audit = visibleDomPrivacyAudit(snapshot).live_form_control_audit;
        return audit?.valid === true && audit?.finding_count === 0;
      }),
    isolated_fx_badge_not_loaded_verified:
      privacySnapshots.every(isolatedFxBadgeReady),
    visible_release_identity_chip_verified:
      privacySnapshots.every(
        (snapshot) => snapshot.release_identity_details?.chip_visible === true,
      ),
    complete_release_identity_details_verified:
      privacySnapshots.every((snapshot) => completeVisibleIdentityMatchesRelease(snapshot, release)),
    accessibility_tree_captured:
      accessibility.source === "Accessibility.getFullAXTree" &&
      accessibility.frame_discovery_source === "Page.getFrameTree" &&
      accessibility.frame_url.startsWith("about:srcdoc") &&
      accessibility.srcdoc_frame_candidate_count > 0 &&
      accessibility.node_count > 0,
    accessibility_contract_verified:
      accessibility.ax_contract.h1_exact_match_count > 0 &&
      accessibility.ax_contract.primary_navigation_named_count === 10 &&
      accessibility.ax_contract.named_focusable_count >= 10 &&
      accessibility.ax_contract.unnamed_focusable_count === 0 &&
      accessibility.official_dom_contract.shell_schema === "PFIOSWebShellContractV1" &&
      accessibility.official_dom_contract.header_present === true &&
      accessibility.official_dom_contract.navigation_present === true &&
      accessibility.official_dom_contract.main_present === true &&
      accessibility.official_dom_contract.skip_link_present === true &&
      accessibility.official_dom_contract.h1_text === "首页总览 · 财务状态" &&
      accessibility.official_dom_contract.primary_entries.length === 10 &&
      accessibility.official_dom_contract.duplicate_id_count === 0 &&
      accessibility.official_dom_contract.focusable_without_name_count === 0,
    network_allowlist_exact:
      observedRequestPorts.size === 2 &&
      observedRequestPorts.has(candidate.port) &&
      observedRequestPorts.has(runtime.runtimeApiPort) &&
      ![8501, 8502, 8766].some((port) => observedRequestPorts.has(port)) &&
      unexpectedHosts.length === 0,
    no_console_page_request_http_ws_errors:
      consoleErrors.length === 0 &&
      pageErrors.length === 0 &&
      requestFailures.length === 0 &&
      httpErrors.length === 0 &&
      webSocketErrors.length === 0,
    isolated_empty_runtime_verified:
      shellSnapshots.every(
        (snapshot) => snapshot.isolated_empty_data === true && isolatedRuntimePayloadSafe(snapshot),
      ) && runtime.api.blocked_post.status === 403,
    isolated_candidate_availability_truthful:
      shellSnapshots.every(
        (snapshot) =>
          snapshot.visible_text.includes("隔离候选未加载真实数据") &&
          !snapshot.visible_text.includes("本机数据可用"),
      ),
    visible_dom_privacy_verified:
      privacySnapshots.every((snapshot) => visibleDomPrivacyAudit(snapshot).safe === true),
    no_private_runtime_leakage:
      privacySnapshots.every(
        (snapshot) =>
          isolatedRuntimePayloadSafe(snapshot) && visibleDomPrivacyAudit(snapshot).safe === true,
      ) &&
      pathWithin(profile.profileDir, candidate.isolatedRoot),
    screenshot_bracketed_by_identical_state:
      identity(snapshots.screenshotBefore) &&
      identity(snapshots.screenshotAfter) &&
      snapshots.screenshotBefore.frontend_source_hash === snapshots.screenshotAfter.frontend_source_hash &&
      snapshots.screenshotBefore.runtime_read_model_status.body.read_model_hash ===
        snapshots.screenshotAfter.runtime_read_model_status.body.read_model_hash,
  };
  return {
    checks,
    real_persisted_observed: pageShowObservations.some((item) => item.persisted === true),
    pageshow_observations: pageShowObservations,
    pageshow_observation_count: pageShowObservations.length,
    console_error_count: consoleErrors.length,
    page_error_count: pageErrors.length,
    request_failure_count: requestFailures.length,
    http_error_count: httpErrors.length,
    unexpected_host_count: unexpectedHosts.length,
    websocket_count: webSocketCount,
    websocket_error_count: webSocketErrors.length,
    requested_port_count: observedRequestPorts.size,
    requested_ports: [...observedRequestPorts].sort((left, right) => left - right),
    api_response_counts: Object.fromEntries([...apiResponseCounts.entries()].sort()),
    legacyQueryAudit: snapshots.legacyQueryAudit,
    primaryRouteAudits: snapshots.primaryRouteAudits,
    primaryRouteAuditCount: snapshots.primaryRouteAudits.length,
    accessibilityTree: snapshots.accessibilityTree,
    frontendIdentity: {
      schema: "PFIV025Stage1WholeReviewFrontendSourceIdentityV1",
      disk: release.sourceIdentity.frontend,
      browser: {
        files: snapshots.initial.frontend_source_hashes,
        file_count_with_index: snapshots.initial.frontend_source_hashes.length + 1,
        sha256: snapshots.initial.frontend_source_hash,
      },
    },
    runtimeApiEvidence: {
      schema: "PFIV025Stage1WholeReviewRuntimeAPIEvidenceV1",
      runtime_api_port: runtime.runtimeApiPort,
      required_headers: REQUIRED_API_HEADERS,
      initial_node_probe: runtime.api,
      browser_response_counts: Object.fromEntries([...apiResponseCounts.entries()].sort()),
      browser_initial: {
        manifest: snapshots.initial.runtime_manifest,
        cache_policy: snapshots.initial.runtime_cache_policy,
        read_model_status: snapshots.initial.runtime_read_model_status,
      },
    },
    privacyBoundary: {
      schema: "PFIV025Stage1WholeReviewPrivacyBoundaryV1",
      candidate_data_mode: "isolated_empty",
      write_api_status: runtime.api.blocked_post.status,
      browser_ports: [...observedRequestPorts].sort((left, right) => left - right),
      home_summary: snapshots.initial.home_summary,
      report_pack: snapshots.initial.report_pack,
      read_model_status: snapshots.initial.runtime_read_model_status.body,
      visible_dom: visibleDomPrivacyAudit(snapshots.initial),
      primary_route_audit_count: snapshots.primaryRouteAudits.length,
      primary_route_audits: snapshots.primaryRouteAudits,
      checks: {
        runtime_payloads_safe: privacySnapshots.every(isolatedRuntimePayloadSafe),
        visible_dom_safe: privacySnapshots.every(
          (snapshot) => visibleDomPrivacyAudit(snapshot).safe === true,
        ),
        external_host_count: unexpectedHosts.length,
      },
    },
    tracePath,
    screenshotPath,
    identityScreenshotPath,
  };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const candidate = await readCandidateState(args.statePath);
  const active = await readAndValidateActiveMarker(candidate);
  await validateCandidateBundleIdentity(candidate);
  const inspection = validateLaunchServicesInspection(candidate, active);
  const marker = active.values;
  const release = await readReleaseContract(candidate, marker);
  const runtime = await validateLaunchServicesRuntime(candidate, active, release);
  const outputDir = await prepareOutputDirectory(args.outputDir, candidate.isolatedRoot);
  const stagingTracePath = path.join(candidate.isolatedRoot, "tmp", STAGING_TRACE_FILE);
  const stagingScreenshotPath = path.join(candidate.isolatedRoot, "tmp", STAGING_SCREENSHOT_FILE);
  const stagingIdentityScreenshotPath = path.join(
    candidate.isolatedRoot,
    "tmp",
    STAGING_IDENTITY_SCREENSHOT_FILE,
  );
  try {
    const privacy = {
      home: os.homedir(),
      projectRoot: release.projectRoot,
      isolatedRoot: candidate.isolatedRoot,
      activePid: marker.PFI_ACTIVE_PID,
      activeMonitorPid: marker.PFI_ACTIVE_MONITOR_PID,
      activeLauncherPid: marker.PFI_ACTIVE_LAUNCHER_PID,
    };
    const browser = await runBrowserValidation(candidate, marker, release, runtime);
    await assertPublicArtifact(browser.tracePath, privacy, "trace", true);
    await assertPublicArtifact(browser.screenshotPath, privacy, "screenshot");
    await assertPublicArtifact(browser.identityScreenshotPath, privacy, "screenshot");
    const publishedTrace = await publishPublicArtifact(browser.tracePath, outputDir, TRACE_FILE);
    const publishedScreenshot = await publishPublicArtifact(
      browser.screenshotPath,
      outputDir,
      SCREENSHOT_FILE,
    );
    const publishedIdentityScreenshot = await publishPublicArtifact(
      browser.identityScreenshotPath,
      outputDir,
      IDENTITY_SCREENSHOT_FILE,
    );
    const trace = await assertPublicArtifact(publishedTrace, privacy, "trace", false);
    const screenshot = await assertPublicArtifact(publishedScreenshot, privacy, "screenshot");
    const identityScreenshot = await assertPublicArtifact(
      publishedIdentityScreenshot,
      privacy,
      "screenshot",
    );
    const jsonArtifacts = [
      [ACCESSIBILITY_FILE, browser.accessibilityTree],
      [FRONTEND_IDENTITY_FILE, browser.frontendIdentity],
      [RUNTIME_API_FILE, browser.runtimeApiEvidence],
      [PRIVACY_FILE, browser.privacyBoundary],
    ];
    const artifactMetadata = {};
    for (const [fileName, payload] of jsonArtifacts) {
      const artifactPath = path.join(outputDir, fileName);
      await writeFile(artifactPath, `${JSON.stringify(payload, null, 2)}\n`, { mode: 0o600 });
      await chmod(artifactPath, 0o600);
      artifactMetadata[fileName] = await assertPublicArtifact(artifactPath, privacy, "json");
    }
    const resultPath = path.join(outputDir, RESULT_FILE);
    const result = {
      schema: RESULT_SCHEMA,
      acceptance_id: "ACC-PFI-V025-STAGE1-WHOLE-REVIEW",
      candidate_mode: true,
      launchservices_started_runtime: true,
      canonical_app_install: false,
      pid_observed: true,
      monitor_pid_observed: true,
      launcher_pid_observed: true,
      app_port: candidate.port,
      runtime_api_port: runtime.runtimeApiPort,
      heartbeat_port: candidate.heartbeatPort,
      checkout_commit: candidate.state.checkout_commit,
      checkout_binding_sha256: candidate.state.checkout_binding_sha256,
      process_identity_sha256: inspection.process_identity_sha256,
      monitor_identity_sha256: inspection.monitor_identity_sha256,
      launcher_identity_sha256: inspection.launcher_identity_sha256,
      launcher_process_tree_verified: inspection.launcher_process_tree_verified,
      process_tree_member_count: inspection.process_tree_member_count,
      process_tree_identity_sha256: inspection.process_tree_identity_sha256,
      process_group_verified: inspection.process_group_verified,
      process_group_member_count: inspection.process_group_member_count,
      process_group_identity_sha256: inspection.process_group_identity_sha256,
      listener_endpoint_set_verified: inspection.listener_endpoint_set_verified,
      listener_endpoint_count: inspection.listener_endpoint_count,
      listener_endpoint_set_sha256: inspection.listener_endpoint_set_sha256,
      candidate_app_path_sha256: candidate.state.candidate_app_path_sha256,
      candidate_executable_sha256: candidate.state.candidate_executable_sha256,
      candidate_bundle_sha256: candidate.state.candidate_bundle_sha256,
      manifest_sha256: release.manifestSha256,
      git_commit: release.manifest.git_commit,
      frontend_bundle_hash: release.manifest.frontend_bundle_hash,
      backend_build_hash: release.manifest.backend_build_hash,
      streamlit_cache_key_sha256: sha256(Buffer.from(marker.PFI_STREAMLIT_CACHE_KEY, "utf8")),
      checks: browser.checks,
      real_persisted_observed: browser.real_persisted_observed,
      pageshow_observation_count: browser.pageshow_observation_count,
      pageshow_observations: browser.pageshow_observations,
      console_error_count: browser.console_error_count,
      page_error_count: browser.page_error_count,
      request_failure_count: browser.request_failure_count,
      http_error_count: browser.http_error_count,
      unexpected_host_count: browser.unexpected_host_count,
      websocket_count: browser.websocket_count,
      websocket_error_count: browser.websocket_error_count,
      requested_port_count: browser.requested_port_count,
      requested_ports: browser.requested_ports,
      api_response_counts: browser.api_response_counts,
      legacy_query_audit: browser.legacyQueryAudit,
      primary_route_audit_count: browser.primaryRouteAuditCount,
      primary_route_audits: browser.primaryRouteAudits,
      artifacts: {
        official_ui_screenshot: { file: SCREENSHOT_FILE, ...screenshot },
        release_identity_screenshot: {
          file: IDENTITY_SCREENSHOT_FILE,
          ...identityScreenshot,
        },
        trace: { file: TRACE_FILE, ...trace },
        accessibility_tree: { file: ACCESSIBILITY_FILE, ...artifactMetadata[ACCESSIBILITY_FILE] },
        frontend_source_identity: {
          file: FRONTEND_IDENTITY_FILE,
          ...artifactMetadata[FRONTEND_IDENTITY_FILE],
        },
        runtime_api_evidence: { file: RUNTIME_API_FILE, ...artifactMetadata[RUNTIME_API_FILE] },
        privacy_boundary: { file: PRIVACY_FILE, ...artifactMetadata[PRIVACY_FILE] },
      },
    };
    await writeFile(resultPath, `${JSON.stringify(result, null, 2)}\n`, { mode: 0o600 });
    await chmod(resultPath, 0o600);
    await assertPublicArtifact(resultPath, privacy, "json");
    if (!Object.values(result.checks).every((value) => value === true)) {
      fail("browser validation checks failed");
    }
    process.stdout.write(`${JSON.stringify(result)}\n`);
  } catch (error) {
    await Promise.all(
      [
        TRACE_FILE,
        `${TRACE_FILE}.sanitized.tmp`,
        SCREENSHOT_FILE,
        IDENTITY_SCREENSHOT_FILE,
        RESULT_FILE,
        ACCESSIBILITY_FILE,
        FRONTEND_IDENTITY_FILE,
        RUNTIME_API_FILE,
        PRIVACY_FILE,
      ].map((name) =>
        rm(path.join(outputDir, name), { force: true }),
      ),
    );
    throw error;
  } finally {
    await Promise.all(
      [
        stagingTracePath,
        `${stagingTracePath}.sanitized.tmp`,
        stagingScreenshotPath,
        stagingIdentityScreenshotPath,
      ].map((artifactPath) => rm(artifactPath, { force: true })),
    );
  }
}

export const __test = Object.freeze({
  buildTraceArchive,
  parseTraceArchive,
  redactPrivateText,
  redactTraceStructure,
  redactTraceCookieValues,
  assertNoFinancialEvidence,
  collectFocusableWithoutNameCount,
  collectLiveFormControlPrivacyAudit,
  computeReleaseSourceIdentity,
  visibleDomPrivacyAudit,
  scanTraceArchiveEntries,
  isExpectedLoopbackUrl,
  assertPngMetadata,
});

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  main().catch((error) => {
    const message =
      error instanceof BrowserValidationError ? error.message : "browser validation failed";
    process.stderr.write(`PFI_STAGE1_BROWSER_ERROR: ${message}\n`);
    process.exitCode = 1;
  });
}
