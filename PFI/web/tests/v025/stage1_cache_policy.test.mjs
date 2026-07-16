import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import { fileURLToPath } from "node:url";


const HERE = path.dirname(fileURLToPath(import.meta.url));
const PFI_ROOT = path.resolve(HERE, "../../..");
const VERSION_SOURCE = fs.readFileSync(path.join(PFI_ROOT, "web/app/version.js"), "utf8");

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

const CACHE_KEY = "d".repeat(64);
const BASE_POLICY = Object.freeze({
  schema: "PFIV025Stage1ReleaseCachePolicyV1",
  build_id: BASE_MANIFEST.build_id,
  git_commit: BASE_MANIFEST.git_commit,
  frontend_bundle_hash: BASE_MANIFEST.frontend_bundle_hash,
  backend_build_hash: BASE_MANIFEST.backend_build_hash,
  data_hash: "e".repeat(64),
  parameter_hash: "f".repeat(64),
  formula_hash: "0".repeat(64),
  fx_snapshot_id: "fx_AUD_CNY_20260628",
  fx_snapshot_hash: "1".repeat(64),
  read_model_hash: "2".repeat(64),
  streamlit_version: "1.35.0",
  requirements_lock_hash: "3".repeat(64),
  streamlit_cache_key: CACHE_KEY,
  process_cache_key: CACHE_KEY,
  ttl_seconds: 30,
  cache_mode: "streamlit_cache_data_composite_key_v1",
  persistent: false,
  invalidation: [
    "build_id",
    "git_commit",
    "frontend_bundle_hash",
    "backend_build_hash",
    "data_hash",
    "parameter_hash",
    "formula_hash",
    "fx_snapshot_id",
    "fx_snapshot_hash",
    "read_model_hash",
    "streamlit_version",
    "requirements_lock_hash",
  ],
  running_backend_hash: BASE_MANIFEST.backend_build_hash,
  asset_identity_valid: true,
  dependency_registry_sha256: "4".repeat(64),
  dependency_snapshot_hash: "e".repeat(64),
  dependency_hashes: {
    raw: "5".repeat(64),
    source: "6".repeat(64),
    ledger: "7".repeat(64),
    interconnection: "8".repeat(64),
    parameter: "f".repeat(64),
    formula: "0".repeat(64),
    fx: "1".repeat(64),
    read_model: "2".repeat(64),
    report: "9".repeat(64),
  },
  dependency_statuses: {
    raw: "ready",
    source: "ready",
    ledger: "ready",
    interconnection: "ready",
    parameter: "ready",
    formula: "ready",
    fx: "ready",
    read_model: "ready",
    report: "ready",
  },
  frontend_cache_key: CACHE_KEY,
  ordinary_run_network_allowed: false,
  no_diff_network_allowed: false,
  no_diff_recompute_scope: "none",
  no_diff_codex_allowed: false,
  no_diff_llm_allowed: false,
  dependency_snapshot_valid: true,
  valid: true,
});

function makeDocument({
  embedded = BASE_MANIFEST,
  runtimeConfig = { apiBaseUrl: "http://127.0.0.1:8766", apiAuthToken: "stage1-cache-policy-token" },
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
  const shell = {
    hidden: true,
    removeAttribute(name) { if (name === "hidden") this.hidden = false; },
    setAttribute(name) { if (name === "hidden") this.hidden = true; },
  };
  const body = { dataset: {}, classList: { add() {}, remove() {} } };
  const elements = new Map([
    ["pfi-release-manifest", { textContent: JSON.stringify(embedded) }],
    ["pfi-runtime-config", { textContent: JSON.stringify(runtimeConfig) }],
    ["pfi-release-conflict", conflict],
  ]);
  return {
    body,
    referrer: "",
    title,
    detail,
    conflict,
    shell,
    getElementById(id) { return elements.get(id) ?? null; },
    querySelector(selector) { return selector === ".app-shell" ? shell : null; },
  };
}

function response(body, headers = {}) {
  const normalized = new Map(Object.entries(headers).map(([key, value]) => [key.toLowerCase(), value]));
  return {
    ok: true,
    status: 200,
    headers: { get(name) { return normalized.get(String(name).toLowerCase()) ?? null; } },
    async json() { return structuredClone(body); },
  };
}

function routedFetch({ manifest = BASE_MANIFEST, policy = BASE_POLICY, calls = [] } = {}) {
  return async (url, options = {}) => {
    calls.push({ url: String(url), options });
    if (String(url).endsWith("/api/release-manifest")) {
      return response(manifest, {
        "X-PFI-Release-Manifest-SHA256": "4".repeat(64),
        "X-PFI-Running-Backend-SHA256": manifest.backend_build_hash,
      });
    }
    if (String(url).endsWith("/api/release-cache-policy")) return response(policy);
    return { ok: false, status: 404, headers: { get() { return null; } }, async json() { return {}; } };
  };
}

function makeServiceWorker({ registrations = [], controller = null } = {}) {
  return {
    controller,
    async getRegistrations() { return registrations; },
    addEventListener() {},
  };
}

function makeCaches(names = []) {
  const active = new Set(names);
  return {
    active,
    async keys() { return [...active]; },
    async delete(name) { return active.delete(name); },
  };
}

function loadGate({
  document = makeDocument(),
  fetchImpl = routedFetch(),
  serviceWorker = makeServiceWorker(),
  cachesRef = makeCaches(),
} = {}) {
  const listeners = new Map();
  const window = {
    document,
    location: { search: "", href: "http://127.0.0.1:8503/", origin: "http://127.0.0.1:8503" },
    navigator: { serviceWorker },
    caches: cachesRef,
    addEventListener(type, listener) {
      const values = listeners.get(type) ?? [];
      values.push(listener);
      listeners.set(type, values);
    },
    removeEventListener(type, listener) {
      listeners.set(type, (listeners.get(type) ?? []).filter((item) => item !== listener));
    },
    dispatch(type, event) {
      for (const listener of listeners.get(type) ?? []) listener(event);
    },
  };
  window.parent = window;
  const context = vm.createContext({
    window,
    document,
    navigator: window.navigator,
    caches: cachesRef,
    fetch: fetchImpl,
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
    structuredClone,
  });
  vm.runInContext(VERSION_SOURCE, context, { filename: "version.js" });
  return { api: window.PFI_RELEASE_IDENTITY, document, window, listeners, serviceWorker, cachesRef };
}

test("cache governance API exposes the Phase 1.2 primitives", () => {
  const { api } = loadGate();
  for (const name of [
    "applyPendingState",
    "disableLegacyServiceWorkers",
    "validateReleaseCachePolicy",
    "runReleaseIdentityCheck",
    "installBfcacheRevalidation",
  ]) {
    assert.equal(typeof api?.[name], "function", name);
  }
});

test("legacy Service Workers and dedicated-origin caches are removed", async () => {
  const unregistered = [];
  const registrations = ["one", "two"].map((name) => ({
    scope: `http://127.0.0.1:8503/${name}`,
    async unregister() { unregistered.push(name); return true; },
  }));
  const serviceWorker = makeServiceWorker({ registrations });
  const cachesRef = makeCaches(["pfi-v024-shell", "streamlit-old"]);
  const { api } = loadGate();
  assert.equal(typeof api.disableLegacyServiceWorkers, "function");
  const result = await api.disableLegacyServiceWorkers({ serviceWorker, cachesRef });
  assert.equal(result.ok, true, JSON.stringify(result));
  assert.deepEqual(unregistered.sort(), ["one", "two"]);
  assert.deepEqual([...cachesRef.active], []);
});

test("cleanup failure or a surviving controller fails closed before fetch", async () => {
  for (const serviceWorker of [
    makeServiceWorker({ registrations: [{ scope: "http://127.0.0.1:8503/", async unregister() { return false; } }] }),
    makeServiceWorker({ controller: { scriptURL: "http://127.0.0.1:8503/legacy-sw.js" } }),
  ]) {
    let fetchCount = 0;
    const document = makeDocument();
    const { api } = loadGate({ document, serviceWorker });
    const result = await api.runReleaseIdentityCheck({
      document,
      serviceWorker,
      cachesRef: makeCaches(),
      fetchImpl: async () => { fetchCount += 1; return routedFetch()(); },
      search: "",
    });
    assert.equal(result.ok, false, JSON.stringify(result));
    assert.equal(fetchCount, 0);
    assert.equal(document.shell.hidden, true);
    assert.equal(document.conflict.hidden, false);
    assert.match(document.detail.textContent, /重新启动/);
    assert.match(document.detail.textContent, /清除缓存/);
  }
});

test("cache policy requires every dimension, matching process key, build, and running backend", () => {
  const { api } = loadGate();
  assert.equal(typeof api.validateReleaseCachePolicy, "function");
  assert.equal(api.validateReleaseCachePolicy(BASE_POLICY, BASE_MANIFEST).ok, true);
  for (const field of [
    "build_id",
    "data_hash",
    "parameter_hash",
    "formula_hash",
    "fx_snapshot_id",
    "fx_snapshot_hash",
    "read_model_hash",
    "streamlit_cache_key",
    "process_cache_key",
    "ttl_seconds",
    "invalidation",
  ]) {
    const invalid = { ...BASE_POLICY };
    delete invalid[field];
    assert.equal(api.validateReleaseCachePolicy(invalid, BASE_MANIFEST).ok, false, field);
  }
  assert.equal(api.validateReleaseCachePolicy({ ...BASE_POLICY, valid: false }, BASE_MANIFEST).ok, false);
  assert.equal(
    api.validateReleaseCachePolicy({ ...BASE_POLICY, process_cache_key: "9".repeat(64) }, BASE_MANIFEST).ok,
    false,
  );
  assert.equal(
    api.validateReleaseCachePolicy({ ...BASE_POLICY, running_backend_hash: "8".repeat(64) }, BASE_MANIFEST).ok,
    false,
  );
});

test("dynamic boot uses no-store for manifest and cache policy before revealing shell", async () => {
  const calls = [];
  const document = makeDocument();
  const fetchImpl = routedFetch({ calls });
  const { api } = loadGate({ document, fetchImpl });
  const result = await api.runReleaseIdentityCheck({
    document,
    fetchImpl,
    serviceWorker: makeServiceWorker(),
    cachesRef: makeCaches(),
    search: "",
  });
  assert.equal(result.ok, true, JSON.stringify(result));
  const relevant = calls.filter((item) => item.url.includes("/api/release-"));
  assert.ok(relevant.some((item) => item.url.endsWith("/api/release-manifest")));
  assert.ok(relevant.some((item) => item.url.endsWith("/api/release-cache-policy")));
  assert.ok(relevant.every((item) => item.options.cache === "no-store"));
  assert.ok(relevant.every((item) => item.options.headers["X-PFI-Runtime-Token"] === "stage1-cache-policy-token"));
  assert.equal(document.shell.hidden, false);
  assert.equal(document.body.dataset.pfiReleaseIdentityState, "ready");
});

test("static source must opt out of manifest and cache policy together", async () => {
  for (const runtimeConfig of [
    { releaseManifestApi: false, releaseCachePolicyApi: false },
    { releaseManifestApi: false },
    { releaseCachePolicyApi: false },
  ]) {
    let fetchCount = 0;
    const document = makeDocument({ runtimeConfig });
    const { api } = loadGate({ document, fetchImpl: async () => { fetchCount += 1; throw new Error("no fetch"); } });
    const result = await api.runReleaseIdentityCheck({
      document,
      fetchImpl: async () => { fetchCount += 1; throw new Error("no fetch"); },
      serviceWorker: makeServiceWorker(),
      cachesRef: makeCaches(),
      search: "",
    });
    const paired = runtimeConfig.releaseManifestApi === false && runtimeConfig.releaseCachePolicyApi === false;
    assert.equal(result.ok, paired, JSON.stringify({ runtimeConfig, result }));
    assert.equal(fetchCount, 0);
  }
});

test("pageshow persisted immediately hides and revalidates; non-persisted is a no-op", async () => {
  const calls = [];
  let policy = BASE_POLICY;
  const fetchImpl = async (url, options) => routedFetch({ policy, calls })(url, options);
  const document = makeDocument();
  const { window } = loadGate({ document, fetchImpl });
  await window.PFI_RELEASE_IDENTITY_READY;
  const baselineCalls = calls.length;
  window.dispatch("pageshow", { persisted: false });
  await Promise.resolve();
  assert.equal(calls.length, baselineCalls);

  policy = { ...BASE_POLICY, valid: false, process_cache_key: "9".repeat(64) };
  window.dispatch("pageshow", { persisted: true });
  assert.equal(document.shell.hidden, true, "persisted restore must synchronously hide the shell");
  assert.equal(document.body.dataset.pfiReleaseIdentityState, "pending");
  const result = await window.PFI_RELEASE_IDENTITY_READY;
  assert.equal(result.ok, false, JSON.stringify(result));
  assert.equal(document.shell.hidden, true);
  assert.equal(document.conflict.hidden, false);
  assert.match(document.detail.textContent, /版本冲突/);
});

test("an older slow success cannot override a newer mismatch", async () => {
  let releaseFirst;
  const firstManifest = new Promise((resolve) => { releaseFirst = resolve; });
  let manifestRequests = 0;
  const fetchImpl = async (url) => {
    if (String(url).endsWith("/api/release-manifest")) {
      manifestRequests += 1;
      if (manifestRequests === 2) return firstManifest;
      return response(BASE_MANIFEST, {
        "X-PFI-Release-Manifest-SHA256": "4".repeat(64),
        "X-PFI-Running-Backend-SHA256": BASE_MANIFEST.backend_build_hash,
      });
    }
    return response(manifestRequests >= 3 ? { ...BASE_POLICY, valid: false } : BASE_POLICY);
  };
  const document = makeDocument();
  const { api } = loadGate({ document, fetchImpl });
  await Promise.resolve();
  const slow = api.runReleaseIdentityCheck({
    document,
    fetchImpl,
    serviceWorker: makeServiceWorker(),
    cachesRef: makeCaches(),
    search: "",
  });
  await Promise.resolve();
  const newer = api.runReleaseIdentityCheck({
    document,
    fetchImpl,
    serviceWorker: makeServiceWorker(),
    cachesRef: makeCaches(),
    search: "",
  });
  const newerResult = await newer;
  assert.equal(newerResult.ok, false, JSON.stringify(newerResult));
  releaseFirst(response(BASE_MANIFEST, {
    "X-PFI-Release-Manifest-SHA256": "4".repeat(64),
    "X-PFI-Running-Backend-SHA256": BASE_MANIFEST.backend_build_hash,
  }));
  await slow;
  assert.equal(document.shell.hidden, true);
  assert.equal(document.conflict.hidden, false);
});
