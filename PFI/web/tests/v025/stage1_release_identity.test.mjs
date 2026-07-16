import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";


const HERE = path.dirname(fileURLToPath(import.meta.url));
const PFI_ROOT = path.resolve(HERE, "../../..");
const VERSION_SOURCE = fs.readFileSync(path.join(PFI_ROOT, "web/app/version.js"), "utf8");
const INDEX_SOURCE = fs.readFileSync(path.join(PFI_ROOT, "web/index.html"), "utf8");
const SHELL_SOURCE = fs.readFileSync(path.join(PFI_ROOT, "web/app/shell.js"), "utf8");

function sourceBetween(source, start, end) {
  const startIndex = source.indexOf(start);
  assert.notEqual(startIndex, -1, `missing source marker: ${start}`);
  const endIndex = source.indexOf(end, startIndex + start.length);
  assert.notEqual(endIndex, -1, `missing source marker: ${end}`);
  return source.slice(startIndex, endIndex);
}

const BASE_MANIFEST = Object.freeze({
  product: "PFI",
  version: "v0.2.5",
  build_id: "pfi-v025-s1p1-20260712.1",
  git_commit: "a".repeat(40),
  frontend_bundle_hash: "b".repeat(64),
  backend_build_hash: "c".repeat(64),
  app_short_version: "0.2.5",
  app_build_version: "20260712.1",
  data_schema_version: "PFIV021HoldingsPersistenceV1",
  formula_version: "v0.2.3",
  parameter_version: "v0.2.2",
  generated_at: "2026-07-11T21:26:06Z",
});

const QUERY_KEYS = Object.freeze({
  pfi_app_version: "0.2.5",
  pfi_app_build: "20260712.1",
  pfi_build: BASE_MANIFEST.build_id,
  pfi_commit: BASE_MANIFEST.git_commit,
  pfi_frontend_hash: BASE_MANIFEST.frontend_bundle_hash,
  pfi_backend_hash: BASE_MANIFEST.backend_build_hash,
  pfi_manifest_sha256: "d".repeat(64),
});
const CACHE_KEY = "e".repeat(64);
const CACHE_DIMENSIONS = Object.freeze({
  build_id: BASE_MANIFEST.build_id,
  git_commit: BASE_MANIFEST.git_commit,
  frontend_bundle_hash: BASE_MANIFEST.frontend_bundle_hash,
  backend_build_hash: BASE_MANIFEST.backend_build_hash,
  data_hash: "f".repeat(64),
  parameter_hash: "0".repeat(64),
  formula_hash: "1".repeat(64),
  fx_snapshot_id: "fx_AUD_CNY_20260628",
  fx_snapshot_hash: "2".repeat(64),
  read_model_hash: "3".repeat(64),
  streamlit_version: "1.35.0",
  requirements_lock_hash: "4".repeat(64),
});
const BASE_CACHE_POLICY = Object.freeze({
  schema: "PFIV025Stage1ReleaseCachePolicyV1",
  ...CACHE_DIMENSIONS,
  streamlit_cache_key: CACHE_KEY,
  process_cache_key: CACHE_KEY,
  ttl_seconds: 30,
  cache_mode: "streamlit_cache_data_composite_key_v1",
  persistent: false,
  invalidation: Object.keys(CACHE_DIMENSIONS),
  running_backend_hash: BASE_MANIFEST.backend_build_hash,
  asset_identity_valid: true,
  valid: true,
});

function makeRuntimeFetch({ manifest = BASE_MANIFEST, policy = BASE_CACHE_POLICY } = {}) {
  return async (url) => {
    if (String(url).endsWith("/api/release-cache-policy")) {
      return { ok: true, status: 200, headers: { get() { return null; } }, async json() { return { ...policy }; } };
    }
    return {
      ok: true,
      status: 200,
      headers: {
        get(name) {
          if (name === "X-PFI-Release-Manifest-SHA256") return QUERY_KEYS.pfi_manifest_sha256;
          if (name === "X-PFI-Running-Backend-SHA256") return manifest.backend_build_hash;
          return null;
        },
      },
      async json() { return { ...manifest }; },
    };
  };
}

function makeDocument({
  embedded = BASE_MANIFEST,
  runtimeConfig = { apiBaseUrl: "http://127.0.0.1:8766" },
  referrer = "",
} = {}) {
  const title = { textContent: "正在核对 PFI 发布身份" };
  const detail = { textContent: "" };
  const conflict = {
    hidden: true,
    querySelector(selector) {
      if (selector === "[data-pfi-release-conflict-title]") return title;
      return selector === "[data-pfi-release-conflict-detail]" ? detail : null;
    },
  };
  const shell = { hidden: true, removeAttribute(name) { if (name === "hidden") this.hidden = false; } };
  const body = { dataset: {}, classList: { add() {}, remove() {} } };
  const elements = new Map([
    ["pfi-release-manifest", { textContent: JSON.stringify(embedded) }],
    ["pfi-runtime-config", { textContent: JSON.stringify(runtimeConfig) }],
    ["pfi-release-conflict", conflict],
  ]);
  return {
    body,
    referrer,
    title,
    detail,
    conflict,
    shell,
    getElementById(id) { return elements.get(id) ?? null; },
    querySelector(selector) { return selector === ".app-shell" ? shell : null; },
  };
}

function queryString(values = QUERY_KEYS) {
  return `?${new URLSearchParams(values).toString()}`;
}

function loadGate({
  search = "",
  parentSearch,
  parentAccessThrows = false,
  referrer = "",
  document = makeDocument({ referrer }),
  fetchImpl,
} = {}) {
  const fetchValue = fetchImpl ?? makeRuntimeFetch();
  const window = {
    document,
    location: { search, href: `http://127.0.0.1:8501/${search}`, origin: "http://127.0.0.1:8501" },
  };
  if (parentAccessThrows) {
    Object.defineProperty(window, "parent", {
      get() { throw new Error("cross-origin parent"); },
    });
  } else if (parentSearch !== undefined) {
    window.parent = {
      location: {
        search: parentSearch,
        href: `http://127.0.0.1:8501/${parentSearch}`,
        origin: "http://127.0.0.1:8501",
      },
    };
  } else {
    window.parent = window;
  }
  const context = vm.createContext({
    window,
    document,
    fetch: fetchValue,
    URLSearchParams,
    URL,
    Promise,
    Object,
    Array,
    JSON,
    Error,
    TypeError,
    console,
    setTimeout,
    clearTimeout,
  });
  vm.runInContext(VERSION_SOURCE, context, { filename: "version.js" });
  return { api: window.PFI_RELEASE_IDENTITY, document, window };
}

function launcherIdentity(api, search = queryString()) {
  return api.parseLauncherIdentity(search);
}

test("matching embedded, backend, and complete launcher identity passes", () => {
  const { api } = loadGate({ search: queryString() });
  assert.ok(api, "version.js must publish PFI_RELEASE_IDENTITY");
  const result = api.evaluateIdentity({
    embedded: { ...BASE_MANIFEST },
    backend: { ...BASE_MANIFEST },
    launcher: launcherIdentity(api),
    backendManifestSha256: QUERY_KEYS.pfi_manifest_sha256,
  });
  assert.equal(result.ok, true, JSON.stringify(result));
  assert.equal(result.issues.length, 0);
});

test("every release identity field mismatch blocks", () => {
  const { api } = loadGate();
  assert.ok(api, "version.js must publish PFI_RELEASE_IDENTITY");
  for (const field of ["version", "build_id", "git_commit", "frontend_bundle_hash", "backend_build_hash"]) {
    const backend = { ...BASE_MANIFEST, [field]: `${BASE_MANIFEST[field]}-mismatch` };
    const result = api.evaluateIdentity({ embedded: BASE_MANIFEST, backend, launcher: null });
    assert.equal(result.ok, false, field);
    assert.ok(result.issues.some((issue) => issue.includes(field)), `${field}: ${result.issues}`);
  }
});

test("presence of any launcher key requires all seven launcher keys", () => {
  const { api } = loadGate({ search: "?pfi_build=partial" });
  assert.ok(api, "version.js must publish PFI_RELEASE_IDENTITY");
  const launcher = api.parseLauncherIdentity("?pfi_build=partial");
  assert.equal(launcher.present, true);
  assert.equal(launcher.complete, false);
  const result = api.evaluateIdentity({ embedded: BASE_MANIFEST, backend: BASE_MANIFEST, launcher });
  assert.equal(result.ok, false);
  assert.ok(result.issues.some((issue) => issue.includes("launcher")));
});

test("launcher manifest hash must equal the runtime response header", () => {
  const { api } = loadGate({ search: queryString() });
  const result = api.evaluateIdentity({
    embedded: BASE_MANIFEST,
    backend: BASE_MANIFEST,
    launcher: launcherIdentity(api),
    backendManifestSha256: "e".repeat(64),
  });
  assert.equal(result.ok, false);
  assert.ok(result.issues.some((issue) => issue === "launcher:manifest_sha256:mismatch"));
});

test("embedded v0.2.5 identity synchronously replaces stale runtime metadata", () => {
  const document = makeDocument({
    runtimeConfig: {
      apiBaseUrl: "http://127.0.0.1:8766",
      targetVersion: "v0.2.4",
      buildId: "pfi-v024-stage2-phase22",
      webBundleHash: "stale",
    },
  });
  const { api } = loadGate({ document });
  assert.ok(api);
  const runtime = JSON.parse(document.getElementById("pfi-runtime-config").textContent);
  assert.equal(runtime.targetVersion, BASE_MANIFEST.version);
  assert.equal(runtime.appVersion, BASE_MANIFEST.app_short_version);
  assert.equal(runtime.buildId, BASE_MANIFEST.build_id);
  assert.equal(runtime.bundleVersion, BASE_MANIFEST.app_build_version);
  assert.equal(runtime.webBundleHash, BASE_MANIFEST.frontend_bundle_hash);
  assert.equal(runtime.backendBuildHash, BASE_MANIFEST.backend_build_hash);
  assert.equal(runtime.gitCommit, BASE_MANIFEST.git_commit);
  assert.equal(runtime.uiContractVersion, "PFI-V025-RELEASE-IDENTITY");
});

test("direct localhost may omit every launcher key but still compares backend", () => {
  const { api } = loadGate();
  assert.ok(api, "version.js must publish PFI_RELEASE_IDENTITY");
  const launcher = api.parseLauncherIdentity("");
  assert.equal(launcher.present, false);
  assert.equal(api.evaluateIdentity({ embedded: BASE_MANIFEST, backend: BASE_MANIFEST, launcher }).ok, true);
  const mismatch = { ...BASE_MANIFEST, backend_build_hash: "f".repeat(64) };
  assert.equal(api.evaluateIdentity({ embedded: BASE_MANIFEST, backend: mismatch, launcher }).ok, false);
});

test("unreachable or invalid backend stays blocked with Chinese recovery UI", async () => {
  for (const fetchImpl of [
    async () => { throw new Error("offline"); },
    async () => ({ ok: true, status: 200, async json() { throw new SyntaxError("invalid json"); } }),
  ]) {
    const document = makeDocument();
    const { api } = loadGate({ document, fetchImpl });
    assert.ok(api, "version.js must publish PFI_RELEASE_IDENTITY");
    const result = await api.bootReleaseIdentityGate({ document, fetchImpl, search: "" });
    assert.equal(result.ok, false);
    assert.equal(document.shell.hidden, true);
    assert.equal(document.conflict.hidden, false);
    assert.equal(document.title.textContent, "版本冲突");
    assert.match(document.detail.textContent, /版本冲突/);
    assert.match(document.detail.textContent, /重新启动/);
    assert.match(document.detail.textContent, /重新安装/);
    assert.match(document.detail.textContent, /清除缓存/);
  }
});

test("static source opt-out is explicit and reveals shell without a network fallback", async () => {
  let fetchCount = 0;
  const fetchImpl = async () => { fetchCount += 1; throw new Error("must not fetch"); };
  const document = makeDocument({
    runtimeConfig: {
      apiBaseUrl: "http://127.0.0.1:8766",
      releaseManifestApi: false,
      releaseCachePolicyApi: false,
    },
  });
  const { api } = loadGate({ document, fetchImpl });
  assert.ok(api, "version.js must publish PFI_RELEASE_IDENTITY");
  const result = await api.bootReleaseIdentityGate({ document, fetchImpl, search: "" });
  assert.equal(result.ok, true);
  assert.equal(result.mode, "static_source_explicit_opt_out");
  assert.equal(fetchCount, 0);
  assert.equal(document.shell.hidden, false);
  assert.equal(document.conflict.hidden, true);

  const partialDocument = makeDocument({
    runtimeConfig: {
      apiBaseUrl: "http://127.0.0.1:8766",
      releaseManifestApi: false,
      releaseCachePolicyApi: false,
    },
  });
  const partial = loadGate({ document: partialDocument, search: "?pfi_build=partial", fetchImpl });
  const partialResult = await partial.api.bootReleaseIdentityGate({
    document: partialDocument,
    fetchImpl,
    search: "?pfi_build=partial",
  });
  assert.equal(partialResult.ok, false);
  assert.equal(partialDocument.shell.hidden, true);
  assert.equal(partialDocument.conflict.hidden, false);
});

test("isolated candidate verifies a complete launcher and release-only cache policy without an API port", async () => {
  let fetchCount = 0;
  const fetchImpl = async () => { fetchCount += 1; throw new Error("candidate must not fetch an auxiliary API"); };
  const candidateCachePolicy = {
    schema: "PFIV025Stage1IsolatedCandidateCachePolicyV1",
    namespace: "isolated_candidate_empty_data_v1",
    build_id: BASE_MANIFEST.build_id,
    git_commit: BASE_MANIFEST.git_commit,
    frontend_bundle_hash: BASE_MANIFEST.frontend_bundle_hash,
    backend_build_hash: BASE_MANIFEST.backend_build_hash,
    release_manifest_sha256: QUERY_KEYS.pfi_manifest_sha256,
    streamlit_cache_key: CACHE_KEY,
    process_cache_key: CACHE_KEY,
    persistent: false,
    data_access: "disabled",
    runtime_api: "disabled",
    valid: true,
  };
  const document = makeDocument({
    runtimeConfig: {
      isolatedCandidate: true,
      runtimeApiEnabled: false,
      releaseManifestApi: false,
      releaseCachePolicyApi: false,
      readModelStatusApi: false,
      releaseManifestSha256: QUERY_KEYS.pfi_manifest_sha256,
      candidateCachePolicy,
    },
  });
  const { api } = loadGate({ document, fetchImpl, parentSearch: queryString() });
  const result = await api.bootReleaseIdentityGate({ document, fetchImpl });
  assert.equal(result.ok, true, JSON.stringify(result));
  assert.equal(result.mode, "isolated_candidate_app_launcher");
  assert.deepEqual(result.cachePolicy, candidateCachePolicy);
  assert.equal(fetchCount, 0);
  assert.equal(document.shell.hidden, false);

  for (const runtimeConfig of [
    { ...JSON.parse(document.getElementById("pfi-runtime-config").textContent), candidateCachePolicy: { ...candidateCachePolicy, process_cache_key: "9".repeat(64) } },
    { ...JSON.parse(document.getElementById("pfi-runtime-config").textContent), releaseManifestSha256: "9".repeat(64) },
  ]) {
    const rejectedDocument = makeDocument({ runtimeConfig });
    const rejected = loadGate({ document: rejectedDocument, fetchImpl, parentSearch: queryString() });
    const rejectedResult = await rejected.api.bootReleaseIdentityGate({ document: rejectedDocument, fetchImpl });
    assert.equal(rejectedResult.ok, false, JSON.stringify(rejectedResult));
    assert.equal(rejectedDocument.shell.hidden, true);
  }
  assert.equal(fetchCount, 0);
});

test("static source opt-out still blocks a missing or invalid embedded manifest", async () => {
  let fetchCount = 0;
  const fetchImpl = async () => { fetchCount += 1; throw new Error("must not fetch"); };
  for (const embedded of [{}, { ...BASE_MANIFEST, git_commit: "invalid" }]) {
    const document = makeDocument({
      embedded,
      runtimeConfig: {
        apiBaseUrl: "http://127.0.0.1:8766",
        releaseManifestApi: false,
        releaseCachePolicyApi: false,
      },
    });
    const { api } = loadGate({ document, fetchImpl });
    const result = await api.bootReleaseIdentityGate({ document, fetchImpl, search: "" });
    assert.equal(result.ok, false, JSON.stringify(result));
    assert.equal(document.shell.hidden, true);
    assert.equal(document.conflict.hidden, false);
  }
  assert.equal(fetchCount, 0);
});

test("Streamlit srcdoc iframe consumes a complete parent launcher query", async () => {
  const document = makeDocument();
  const fetchImpl = makeRuntimeFetch();
  const { api } = loadGate({ document, search: "", parentSearch: queryString(), fetchImpl });
  const result = await api.bootReleaseIdentityGate({ document, fetchImpl });
  assert.equal(result.ok, true, JSON.stringify(result));
  assert.equal(result.mode, "app_launcher");
  assert.equal(document.shell.hidden, false);
});

test("Streamlit srcdoc iframe blocks partial or tampered parent launcher identity", async () => {
  const fetchImpl = makeRuntimeFetch();
  for (const parentSearch of [
    "?pfi_build=partial",
    queryString({ ...QUERY_KEYS, pfi_commit: "f".repeat(40) }),
  ]) {
    const document = makeDocument();
    const { api } = loadGate({ document, search: "", parentSearch, fetchImpl });
    const result = await api.bootReleaseIdentityGate({ document, fetchImpl });
    assert.equal(result.ok, false, JSON.stringify(result));
    assert.equal(document.shell.hidden, true);
    assert.equal(document.conflict.hidden, false);
  }
});

test("Streamlit srcdoc iframe uses referrer when parent access is unavailable", async () => {
  const document = makeDocument({ referrer: `http://127.0.0.1:8501/${queryString()}` });
  const fetchImpl = makeRuntimeFetch();
  const { api } = loadGate({
    document,
    search: "",
    parentAccessThrows: true,
    fetchImpl,
  });
  const result = await api.bootReleaseIdentityGate({ document, fetchImpl });
  assert.equal(result.ok, true, JSON.stringify(result));
  assert.equal(result.mode, "app_launcher");
});

test("conflicting iframe and parent launcher sources fail closed", async () => {
  const document = makeDocument();
  const fetchImpl = makeRuntimeFetch();
  const parentSearch = queryString({ ...QUERY_KEYS, pfi_commit: "f".repeat(40) });
  const { api } = loadGate({ document, search: queryString(), parentSearch, fetchImpl });
  const result = await api.bootReleaseIdentityGate({ document, fetchImpl });
  assert.equal(result.ok, false, JSON.stringify(result));
  assert.ok(result.issues.includes("launcher:search_sources:mismatch"));
  assert.equal(document.shell.hidden, true);
});

test("matching runtime fetch reveals shell and publishes a readiness promise", async () => {
  const document = makeDocument();
  const { api, window } = loadGate({ document });
  assert.ok(api, "version.js must publish PFI_RELEASE_IDENTITY");
  assert.equal(typeof window.PFI_RELEASE_IDENTITY_READY?.then, "function");
  const result = await api.bootReleaseIdentityGate({ document, search: "" });
  assert.equal(result.ok, true, JSON.stringify(result));
  assert.equal(document.shell.hidden, false);
  assert.equal(document.conflict.hidden, true);
  assert.equal(document.body.dataset.pfiReleaseIdentityState, "ready");
});

test("complete launcher query passes only with the matching backend manifest header", async () => {
  const document = makeDocument();
  const fetchImpl = makeRuntimeFetch();
  const { api } = loadGate({ document, search: queryString(), fetchImpl });
  const result = await api.bootReleaseIdentityGate({ document, search: queryString(), fetchImpl });
  assert.equal(result.ok, true, JSON.stringify(result));
  assert.equal(result.mode, "app_launcher");
  assert.equal(document.shell.hidden, false);
});

test("visible release identity details expose the complete manifest values without ellipsis-only text", () => {
  const hooks = {
    version: "manifest.version",
    build: "manifest.build_id",
    commit: "manifest.git_commit",
    frontend: "manifest.frontend_bundle_hash",
    backend: "manifest.backend_build_hash",
  };
  assert.match(INDEX_SOURCE, /<details[^>]+data-pfi-release-identity-details/);
  assert.match(INDEX_SOURCE, /<summary[^>]+data-pfi-release-identity-summary>发布身份详情<\/summary>/);
  for (const [hook, manifestExpression] of Object.entries(hooks)) {
    const valueMatch = INDEX_SOURCE.match(new RegExp(`<dd[^>]+data-pfi-release-detail-${hook}[^>]*>([^<]+)<\\/dd>`));
    assert.ok(valueMatch, hook);
    assert.equal(valueMatch[1], "正在核对", hook);
    assert.match(SHELL_SOURCE, new RegExp(`${hook}: ${manifestExpression.replace(".", "\\.")} \\|\\|`), hook);
    assert.match(SHELL_SOURCE, new RegExp(`write\\(\"\\[data-pfi-release-detail-${hook}\\]`), hook);
  }
  assert.match(INDEX_SOURCE, /overflow-wrap:\s*anywhere/);
  assert.match(INDEX_SOURCE, /user-select:\s*text/);
});

test("official isolated-empty candidate keeps AUD/CNY explicitly not loaded while normal mode retains compatibility", () => {
  const refreshBlock = sourceBetween(SHELL_SOURCE, "function refreshFxBadgeDisplay()", "function readRuntimeConfig()");
  assert.match(INDEX_SOURCE, /data-fx-cache-state="not_loaded"/);
  assert.match(INDEX_SOURCE, /data-fx-source-label="AUD\/CNY=未加载"/);
  assert.match(refreshBlock, /RUNTIME_CONFIG\.stage1OfficialCandidate === true/);
  assert.match(refreshBlock, /RUNTIME_CONFIG\.candidateDataMode === "isolated_empty"/);
  assert.match(refreshBlock, /candidatePolicy\.data_access === "disabled"/);
  assert.match(refreshBlock, /candidateNotLoaded \? "not_loaded" : FX_SNAPSHOT\.cacheState/);
  assert.match(SHELL_SOURCE, /const CURRENT_FX_BADGE_DISPLAY = "AUD\/CNY=4\.69（2026\/06\/28 06:00）"/);
});

test("not-ready Stage 7 reports remain blocked without historical fallback facts or inferred confidence", () => {
  const builderBlock = sourceBetween(
    SHELL_SOURCE,
    "function buildV024Stage7ReportPackFromStatus(statusPayload)",
    "function applyV024Stage7Phase72FallbackReportCenter()",
  );
  const fallbackBlock = sourceBetween(
    SHELL_SOURCE,
    "function applyV024Stage7Phase72FallbackReportCenter()",
    "function recommendationTypeLabel(value)",
  );
  assert.match(SHELL_SOURCE, /if \(reportPack\.source\?\.status !== "ready"\) return null/);
  assert.match(builderBlock, /metricIsReady\(consumptionMetric\) \? \{/);
  assert.match(builderBlock, /metricIsReady\(qualityMetric\) \? \{/);
  assert.doesNotMatch(builderBlock, /source_id \|\| "MetaDatabase/);
  assert.doesNotMatch(builderBlock, /confidence \|\| 0\./);
  for (const report of ["净资产报告", "现金报告", "投资报告", "消费报告", "现金流报告", "数据质量报告"]) {
    assert.match(fallbackBlock, new RegExp(`\\[\"${report}\", \"已阻断\"`), report);
  }
  assert.match(fallbackBlock, /样本量：未加载/);
  assert.match(fallbackBlock, /数据范围：未加载/);
  assert.match(fallbackBlock, /置信度：未加载/);
  assert.doesNotMatch(fallbackBlock, /8815|2022-06-06|2026-06-03|98%|MetaDatabase/);
});

test("isolated-empty primary routes never render not-loaded counters as confirmed zero", () => {
  const skeletonBlock = sourceBetween(
    SHELL_SOURCE,
    "function installStage2PageSkeletons()",
    "function feature(title, status, evidence, description, target = null)",
  );
  for (const label of ["账户列表", "分类复核", "异常消费", "待复核"]) {
    assert.doesNotMatch(skeletonBlock, new RegExp(`\\["${label}", "0"`), label);
  }

  const sourceDetailBlock = sourceBetween(
    SHELL_SOURCE,
    "function sourceStatusDetail(statusPayload)",
    "function shortReadModelHash(hash)",
  ).trim();
  const sourceStatusDetail = vm.runInNewContext(`(${sourceDetailBlock})`);
  assert.equal(
    sourceStatusDetail({
      source: {
        status: "not_loaded",
        record_count: 0,
        raw_file_count: 0,
        blocking_reason_zh: "隔离验收未读取财务数据",
      },
    }),
    "隔离验收未读取财务数据",
  );
  assert.equal(
    sourceStatusDetail({ source: { status: "ready", record_count: 0, raw_file_count: 0 } }),
    "0 条记录 · 0 个原始文件",
  );
  assert.equal(
    sourceStatusDetail({ source: { status: "ready", record_count: null, raw_file_count: null } }),
    "等待 read model 状态",
  );

  const applySummaryBlock = sourceBetween(
    SHELL_SOURCE,
    "function applyAlipayImportSummary(summary)",
    "function applyHomeSummary(summary)",
  );
  const renderSummary = (sourceStatus) => {
    const context = {
      summary: {
        file_count: 0,
        transaction_count: 0,
        review_count: 0,
        date_start: "",
        date_end: "",
        status: "隔离验收未读取",
      },
      runtimeReadModelStatusState: { source: { status: sourceStatus } },
      readEmbeddedReadModelStatus: () => null,
      normalizeAlipayImportSummary: (value) => ({
        fileCount: Number(value.file_count),
        transactionCount: Number(value.transaction_count),
        reviewCount: Number(value.review_count),
        dateStart: value.date_start,
        dateEnd: value.date_end,
        status: value.status,
      }),
      alipayImportState: null,
      WORKSPACES: { sync: {} },
      row: (...values) => values,
      task: (...values) => values,
      result: null,
    };
    vm.runInNewContext(
      `${applySummaryBlock}\napplyAlipayImportSummary(summary); result = WORKSPACES.sync;`,
      context,
    );
    return context.result;
  };
  const notLoaded = JSON.stringify(renderSummary("not_loaded"));
  assert.doesNotMatch(notLoaded, /0 (?:条|个文件|个原始文件)/);
  assert.match(notLoaded, /待导入/);
  assert.match(notLoaded, /文件数未加载/);

  const readyZero = JSON.stringify(renderSummary("ready"));
  assert.match(readyZero, /0 条/);
  assert.match(readyZero, /0 个文件/);
  assert.match(readyZero, /0 个原始文件/);
});
