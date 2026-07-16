(() => {
  const MANIFEST_FIELDS = Object.freeze([
    "product",
    "version",
    "build_id",
    "git_commit",
    "frontend_bundle_hash",
    "backend_build_hash",
    "app_short_version",
    "app_build_version",
    "data_schema_version",
    "formula_version",
    "parameter_version",
    "generated_at",
  ]);
  const LAUNCHER_QUERY_MAP = Object.freeze({
    pfi_app_version: "app_short_version",
    pfi_app_build: "app_build_version",
    pfi_build: "build_id",
    pfi_commit: "git_commit",
    pfi_frontend_hash: "frontend_bundle_hash",
    pfi_backend_hash: "backend_build_hash",
    pfi_manifest_sha256: "manifest_sha256",
  });
  const HEX_PATTERNS = Object.freeze({
    git_commit: /^[0-9a-f]{40}$/,
    frontend_bundle_hash: /^[0-9a-f]{64}$/,
    backend_build_hash: /^[0-9a-f]{64}$/,
    manifest_sha256: /^[0-9a-f]{64}$/,
  });
  const CACHE_DIMENSION_FIELDS = Object.freeze([
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
  ]);
  const DEPENDENCY_DOMAINS = Object.freeze([
    "raw",
    "source",
    "ledger",
    "interconnection",
    "parameter",
    "formula",
    "fx",
    "read_model",
    "report",
  ]);
  let releaseGateEpoch = 0;

  function readJsonNode(documentRef, id) {
    try {
      const raw = documentRef?.getElementById?.(id)?.textContent || "{}";
      const payload = JSON.parse(raw);
      return payload && typeof payload === "object" && !Array.isArray(payload) ? payload : {};
    } catch (_error) {
      return {};
    }
  }

  function parseLauncherIdentity(search = "") {
    const query = new URLSearchParams(search || "");
    const keys = Object.keys(LAUNCHER_QUERY_MAP);
    const presentKeys = keys.filter((key) => query.has(key));
    const duplicateKeys = keys.filter((key) => query.getAll(key).length > 1);
    const values = {};
    for (const [queryKey, manifestField] of Object.entries(LAUNCHER_QUERY_MAP)) {
      values[manifestField] = query.get(queryKey) || "";
    }
    return Object.freeze({
      present: presentKeys.length > 0,
      complete:
        presentKeys.length === keys.length &&
        duplicateKeys.length === 0 &&
        keys.every((key) => Boolean(query.get(key))),
      presentKeys: Object.freeze(presentKeys),
      duplicateKeys: Object.freeze(duplicateKeys),
      values: Object.freeze(values),
    });
  }

  function hasLauncherQuery(search = "") {
    const query = new URLSearchParams(search || "");
    return Object.keys(LAUNCHER_QUERY_MAP).some((key) => query.has(key));
  }

  function launcherSearchSignature(search = "") {
    const query = new URLSearchParams(search || "");
    return Object.keys(LAUNCHER_QUERY_MAP)
      .map((key) => `${key}\u0000${query.getAll(key).join("\u0000")}`)
      .join("\n");
  }

  function resolveLauncherSearch(options = {}) {
    if (options.search !== undefined) {
      return Object.freeze({
        search: String(options.search || ""),
        source: "explicit_override",
        issues: Object.freeze([]),
      });
    }

    const windowRef = options.windowRef || window;
    const documentRef = options.documentRef || windowRef.document;
    const candidates = [];
    const addCandidate = (source, search) => {
      const normalized = String(search || "");
      candidates.push({ source, search: normalized });
    };

    addCandidate("local", windowRef.location?.search || "");
    try {
      if (windowRef.parent && windowRef.parent !== windowRef) {
        addCandidate("parent", windowRef.parent.location?.search || "");
      }
    } catch (_error) {
      // Streamlit component iframes can deny parent access. In that case the
      // top-level App URL remains available through document.referrer.
    }

    const referrer = String(documentRef?.referrer || "").trim();
    if (referrer) {
      try {
        const base = windowRef.location?.href || "http://127.0.0.1/";
        addCandidate("referrer", new URL(referrer, base).search);
      } catch (_error) {
        // An invalid referrer is ignored; any launcher-bearing local/parent
        // source is still enforced, and an absent launcher remains direct-localhost.
      }
    }

    const launcherCandidates = candidates.filter((candidate) => hasLauncherQuery(candidate.search));
    if (launcherCandidates.length === 0) {
      return Object.freeze({
        search: candidates[0]?.search || "",
        source: "local",
        issues: Object.freeze([]),
      });
    }

    const primary = launcherCandidates[0];
    const signatures = new Set(
      launcherCandidates.map((candidate) => launcherSearchSignature(candidate.search)),
    );
    const issues = signatures.size > 1 ? ["launcher:search_sources:mismatch"] : [];
    return Object.freeze({
      search: primary.search,
      source: primary.source,
      issues: Object.freeze(issues),
    });
  }

  function validateManifest(label, manifest, issues) {
    if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) {
      issues.push(`${label}:not_object`);
      return;
    }
    for (const field of MANIFEST_FIELDS) {
      if (typeof manifest[field] !== "string" || !manifest[field]) {
        issues.push(`${label}:${field}:missing`);
      }
    }
    if (manifest.product && manifest.product !== "PFI") issues.push(`${label}:product:mismatch`);
    if (manifest.version && !/^v0\.2\.5(?:[-+].*)?$/.test(manifest.version)) {
      issues.push(`${label}:version:unsupported`);
    }
    for (const [field, pattern] of Object.entries(HEX_PATTERNS)) {
      if (field === "manifest_sha256") continue;
      if (manifest[field] && !pattern.test(manifest[field])) issues.push(`${label}:${field}:invalid`);
    }
  }

  function evaluateIdentity({ embedded, backend, launcher = null, backendManifestSha256 = "" }) {
    const issues = [];
    validateManifest("embedded", embedded, issues);
    validateManifest("backend", backend, issues);

    if (issues.length === 0) {
      for (const field of MANIFEST_FIELDS) {
        if (embedded[field] !== backend[field]) issues.push(`backend:${field}:mismatch`);
      }
    }

    if (launcher?.present) {
      if (!launcher.complete) {
        issues.push("launcher:incomplete");
      } else {
        for (const manifestField of Object.values(LAUNCHER_QUERY_MAP)) {
          const value = launcher.values[manifestField];
          if (manifestField === "manifest_sha256") {
            if (!HEX_PATTERNS.manifest_sha256.test(value)) {
              issues.push("launcher:manifest_sha256:invalid");
            } else if (!HEX_PATTERNS.manifest_sha256.test(backendManifestSha256)) {
              issues.push("backend:manifest_sha256:missing_or_invalid");
            } else if (value !== backendManifestSha256) {
              issues.push("launcher:manifest_sha256:mismatch");
            }
            continue;
          }
          if (value !== embedded[manifestField]) issues.push(`launcher:${manifestField}:mismatch`);
        }
      }
    }

    return Object.freeze({ ok: issues.length === 0, issues: Object.freeze(issues) });
  }

  function normalizeRuntimeConfig(documentRef, manifest) {
    const issues = [];
    validateManifest("embedded", manifest, issues);
    const node = documentRef?.getElementById?.("pfi-runtime-config");
    const current = readJsonNode(documentRef, "pfi-runtime-config");
    if (!node || issues.length > 0) return current;
    const normalized = {
      ...current,
      targetVersion: manifest.version,
      sourcePackageVersion: manifest.version,
      pfiVersion: manifest.version,
      appVersion: manifest.app_short_version,
      repairLabel: `PFI ${manifest.version}`,
      buildId: manifest.build_id,
      bundleVersion: manifest.app_build_version,
      uiContractVersion: "PFI-V025-RELEASE-IDENTITY",
      entryConsistencyContract: "PFI-V025-RELEASE-IDENTITY",
      stage: "Stage 1",
      phase: "1.2",
      webBundleHash: manifest.frontend_bundle_hash,
      backendBuildHash: manifest.backend_build_hash,
      gitCommit: manifest.git_commit,
    };
    node.textContent = JSON.stringify(normalized);
    return normalized;
  }

  function applyReadyState(documentRef, result = {}) {
    const body = documentRef?.body;
    const shell = documentRef?.querySelector?.(".app-shell");
    const conflict = documentRef?.getElementById?.("pfi-release-conflict");
    if (body?.dataset) body.dataset.pfiReleaseIdentityState = "ready";
    if (shell) {
      shell.hidden = false;
      shell.removeAttribute?.("hidden");
    }
    if (conflict) conflict.hidden = true;
    return Object.freeze({ ok: true, ...result });
  }

  function applyPendingState(documentRef, reason = "正在重新核对发布与缓存身份") {
    const body = documentRef?.body;
    const shell = documentRef?.querySelector?.(".app-shell");
    const conflict = documentRef?.getElementById?.("pfi-release-conflict");
    const title = conflict?.querySelector?.("[data-pfi-release-conflict-title]");
    const detail = conflict?.querySelector?.("[data-pfi-release-conflict-detail]");
    if (body?.dataset) body.dataset.pfiReleaseIdentityState = "pending";
    if (shell) {
      shell.hidden = true;
      shell.setAttribute?.("hidden", "");
    }
    if (conflict) conflict.hidden = false;
    if (title) title.textContent = "正在核对 PFI 发布与缓存身份";
    if (detail) detail.textContent = String(reason || "正在重新核对发布与缓存身份");
    return Object.freeze({ ok: false, pending: true, reason: String(reason || "") });
  }

  function applyBlockedState(documentRef, issues = ["unknown_identity_error"]) {
    const body = documentRef?.body;
    const shell = documentRef?.querySelector?.(".app-shell");
    const conflict = documentRef?.getElementById?.("pfi-release-conflict");
    const title = conflict?.querySelector?.("[data-pfi-release-conflict-title]");
    const detail = conflict?.querySelector?.("[data-pfi-release-conflict-detail]");
    if (body?.dataset) body.dataset.pfiReleaseIdentityState = "blocked";
    if (shell) {
      shell.hidden = true;
      shell.setAttribute?.("hidden", "");
    }
    if (conflict) conflict.hidden = false;
    if (title) title.textContent = "版本冲突";
    if (detail) {
      detail.textContent = `版本冲突：${issues.join("；")}。请重新启动 PFI；仍不一致时重新安装 PFI.app，并清除缓存后重试。`;
    }
    return Object.freeze({ ok: false, issues: Object.freeze([...issues]) });
  }

  async function disableLegacyServiceWorkers(options = {}) {
    const windowRef = options.windowRef || window;
    const serviceWorker = options.serviceWorker ?? windowRef.navigator?.serviceWorker ?? null;
    const cachesRef = options.cachesRef ?? windowRef.caches ?? null;
    const issues = [];
    let registrations = [];
    const deletedCaches = [];

    if (serviceWorker) {
      if (typeof serviceWorker.getRegistrations !== "function") {
        issues.push("service_worker:getRegistrations:unavailable");
      } else {
        try {
          registrations = await serviceWorker.getRegistrations();
          if (!Array.isArray(registrations)) registrations = [];
          for (const registration of registrations) {
            if (!registration || typeof registration.unregister !== "function") {
              issues.push("service_worker:registration:invalid");
              continue;
            }
            if ((await registration.unregister()) !== true) {
              issues.push("service_worker:unregister:failed");
            }
          }
        } catch (error) {
          issues.push(`service_worker:cleanup:${error instanceof Error ? error.message : String(error)}`);
        }
      }
    }

    if (cachesRef) {
      if (typeof cachesRef.keys !== "function" || typeof cachesRef.delete !== "function") {
        issues.push("cache_storage:unavailable");
      } else {
        try {
          const cacheNames = await cachesRef.keys();
          for (const cacheName of Array.isArray(cacheNames) ? cacheNames : []) {
            if ((await cachesRef.delete(cacheName)) !== true) {
              issues.push(`cache_storage:delete_failed:${cacheName}`);
            } else {
              deletedCaches.push(String(cacheName));
            }
          }
        } catch (error) {
          issues.push(`cache_storage:cleanup:${error instanceof Error ? error.message : String(error)}`);
        }
      }
    }

    if (serviceWorker?.controller) issues.push("service_worker:controller:still_active");
    return Object.freeze({
      ok: issues.length === 0,
      issues: Object.freeze(issues),
      registrationsFound: registrations.length,
      registrationsUnregistered: Math.max(0, registrations.length - issues.filter((issue) => issue.includes("unregister")).length),
      cacheNamesDeleted: Object.freeze(deletedCaches),
      controllerActive: Boolean(serviceWorker?.controller),
    });
  }

  function validateReleaseCachePolicy(policy, manifest) {
    const issues = [];
    if (!policy || typeof policy !== "object" || Array.isArray(policy)) {
      return Object.freeze({ ok: false, issues: Object.freeze(["cache_policy:not_object"]) });
    }
    if (policy.schema !== "PFIV025Stage1ReleaseCachePolicyV1") issues.push("cache_policy:schema:mismatch");
    for (const field of CACHE_DIMENSION_FIELDS) {
      if (typeof policy[field] !== "string" || !policy[field]) issues.push(`cache_policy:${field}:missing`);
    }
    for (const field of [
      "frontend_bundle_hash",
      "backend_build_hash",
      "data_hash",
      "parameter_hash",
      "formula_hash",
      "fx_snapshot_hash",
      "read_model_hash",
      "requirements_lock_hash",
      "streamlit_cache_key",
      "process_cache_key",
      "running_backend_hash",
      "dependency_registry_sha256",
      "dependency_snapshot_hash",
      "frontend_cache_key",
    ]) {
      if (policy[field] && !/^[0-9a-f]{64}$/.test(policy[field])) issues.push(`cache_policy:${field}:invalid`);
    }
    if (policy.ttl_seconds !== 30) issues.push("cache_policy:ttl_seconds:mismatch");
    if (policy.cache_mode !== "streamlit_cache_data_composite_key_v1") issues.push("cache_policy:cache_mode:mismatch");
    if (policy.persistent !== false) issues.push("cache_policy:persistent:must_be_false");
    if (!Array.isArray(policy.invalidation)) {
      issues.push("cache_policy:invalidation:missing");
    } else {
      for (const field of CACHE_DIMENSION_FIELDS) {
        if (!policy.invalidation.includes(field)) issues.push(`cache_policy:invalidation:${field}:missing`);
      }
    }
    if (!policy.dependency_hashes || typeof policy.dependency_hashes !== "object" || Array.isArray(policy.dependency_hashes)) {
      issues.push("cache_policy:dependency_hashes:missing");
    } else {
      const keys = Object.keys(policy.dependency_hashes).sort();
      if (keys.join("\u0000") !== [...DEPENDENCY_DOMAINS].sort().join("\u0000")) {
        issues.push("cache_policy:dependency_hashes:domains_mismatch");
      }
      for (const domain of DEPENDENCY_DOMAINS) {
        if (!/^[0-9a-f]{64}$/.test(policy.dependency_hashes[domain] || "")) {
          issues.push(`cache_policy:dependency_hashes:${domain}:invalid`);
        }
      }
    }
    if (!policy.dependency_statuses || typeof policy.dependency_statuses !== "object" || Array.isArray(policy.dependency_statuses)) {
      issues.push("cache_policy:dependency_statuses:missing");
    } else {
      for (const domain of DEPENDENCY_DOMAINS) {
        if (typeof policy.dependency_statuses[domain] !== "string" || !policy.dependency_statuses[domain]) {
          issues.push(`cache_policy:dependency_statuses:${domain}:missing`);
        }
      }
    }
    if (policy.data_hash !== policy.dependency_snapshot_hash) issues.push("cache_policy:dependency_snapshot:data_hash_mismatch");
    if (policy.dependency_hashes?.parameter !== policy.parameter_hash) issues.push("cache_policy:dependency_hashes:parameter_mismatch");
    if (policy.dependency_hashes?.formula !== policy.formula_hash) issues.push("cache_policy:dependency_hashes:formula_mismatch");
    if (policy.dependency_hashes?.fx !== policy.fx_snapshot_hash) issues.push("cache_policy:dependency_hashes:fx_mismatch");
    if (policy.dependency_hashes?.read_model !== policy.read_model_hash) issues.push("cache_policy:dependency_hashes:read_model_mismatch");
    if (policy.frontend_cache_key !== policy.streamlit_cache_key) issues.push("cache_policy:frontend_key:mismatch");
    if (policy.ordinary_run_network_allowed !== false) issues.push("cache_policy:ordinary_run_network:must_be_false");
    if (policy.no_diff_network_allowed !== false) issues.push("cache_policy:no_diff_network:must_be_false");
    if (policy.no_diff_recompute_scope !== "none") issues.push("cache_policy:no_diff_recompute_scope:mismatch");
    if (policy.no_diff_codex_allowed !== false) issues.push("cache_policy:no_diff_codex:must_be_false");
    if (policy.no_diff_llm_allowed !== false) issues.push("cache_policy:no_diff_llm:must_be_false");
    if (policy.dependency_snapshot_valid !== true) issues.push("cache_policy:dependency_snapshot:invalid");
    if (policy.streamlit_cache_key !== policy.process_cache_key) issues.push("cache_policy:process_key:mismatch");
    if (policy.valid !== true) issues.push("cache_policy:valid:false");
    if (policy.asset_identity_valid !== true) issues.push("cache_policy:asset_identity:invalid");
    if (manifest && typeof manifest === "object") {
      for (const field of ["build_id", "git_commit", "frontend_bundle_hash", "backend_build_hash"]) {
        if (policy[field] !== manifest[field]) issues.push(`cache_policy:${field}:manifest_mismatch`);
      }
      if (policy.running_backend_hash !== manifest.backend_build_hash) {
        issues.push("cache_policy:running_backend_hash:mismatch");
      }
    }
    return Object.freeze({ ok: issues.length === 0, issues: Object.freeze(issues) });
  }

  function validateIsolatedCandidateCachePolicy(policy, manifest, manifestSha256) {
    const issues = [];
    if (!policy || typeof policy !== "object" || Array.isArray(policy)) {
      return Object.freeze({ ok: false, issues: Object.freeze(["candidate_cache_policy:not_object"]) });
    }
    if (policy.schema !== "PFIV025Stage1IsolatedCandidateCachePolicyV1") {
      issues.push("candidate_cache_policy:schema:mismatch");
    }
    if (policy.namespace !== "isolated_candidate_empty_data_v1") {
      issues.push("candidate_cache_policy:namespace:mismatch");
    }
    for (const field of [
      "git_commit",
      "frontend_bundle_hash",
      "backend_build_hash",
      "release_manifest_sha256",
      "streamlit_cache_key",
      "process_cache_key",
    ]) {
      const length = field === "git_commit" ? 40 : 64;
      if (typeof policy[field] !== "string" || !new RegExp(`^[0-9a-f]{${length}}$`).test(policy[field])) {
        issues.push(`candidate_cache_policy:${field}:invalid`);
      }
    }
    if (typeof policy.build_id !== "string" || !policy.build_id) {
      issues.push("candidate_cache_policy:build_id:missing");
    }
    if (policy.streamlit_cache_key !== policy.process_cache_key) {
      issues.push("candidate_cache_policy:process_key:mismatch");
    }
    if (policy.release_manifest_sha256 !== manifestSha256) {
      issues.push("candidate_cache_policy:manifest_sha256:mismatch");
    }
    if (policy.persistent !== false) issues.push("candidate_cache_policy:persistent:must_be_false");
    if (policy.data_access !== "disabled") issues.push("candidate_cache_policy:data_access:not_disabled");
    if (policy.runtime_api !== "disabled") issues.push("candidate_cache_policy:runtime_api:not_disabled");
    if (policy.valid !== true) issues.push("candidate_cache_policy:valid:false");
    if (manifest && typeof manifest === "object") {
      for (const field of ["build_id", "git_commit", "frontend_bundle_hash", "backend_build_hash"]) {
        if (policy[field] !== manifest[field]) issues.push(`candidate_cache_policy:${field}:manifest_mismatch`);
      }
    }
    return Object.freeze({ ok: issues.length === 0, issues: Object.freeze(issues) });
  }

  async function fetchReleaseJson(fetchImpl, url, authToken = "") {
    const headers = { Accept: "application/json" };
    if (authToken) headers["X-PFI-Runtime-Token"] = String(authToken);
    const response = await fetchImpl(url, {
      method: "GET",
      cache: "no-store",
      headers,
    });
    if (!response || response.ok !== true) {
      throw new Error(`http:${response?.status || "unavailable"}`);
    }
    return Object.freeze({ response, payload: await response.json() });
  }

  async function runReleaseIdentityCheck(options = {}) {
    const epoch = ++releaseGateEpoch;
    const windowRef = options.window || window;
    const documentRef = options.document || windowRef.document;
    applyPendingState(documentRef, options.reason || "正在核对发布身份、旧缓存与运行时缓存键");
    const applyIfCurrent = (result, ready = false) => {
      if (epoch !== releaseGateEpoch) {
        return Object.freeze({ ok: false, stale: true, issues: Object.freeze(["runtime:stale_gate_epoch"]) });
      }
      return ready
        ? applyReadyState(documentRef, result)
        : applyBlockedState(documentRef, result.issues || ["unknown_identity_error"]);
    };

    const runtimeConfig = readJsonNode(documentRef, "pfi-runtime-config");
    const embedded = readJsonNode(documentRef, "pfi-release-manifest");
    const launcherSearch = resolveLauncherSearch({
      windowRef,
      documentRef,
      search: options.search,
    });
    if (launcherSearch.issues.length > 0) return applyIfCurrent({ issues: launcherSearch.issues });
    const launcher = parseLauncherIdentity(launcherSearch.search);

    const swAudit = await disableLegacyServiceWorkers({
      windowRef,
      serviceWorker: options.serviceWorker,
      cachesRef: options.cachesRef,
    });
    if (!swAudit.ok) return applyIfCurrent({ issues: swAudit.issues });

    if (runtimeConfig.isolatedCandidate === true) {
      const isolatedIssues = [];
      if (runtimeConfig.runtimeApiEnabled !== false) isolatedIssues.push("candidate:runtime_api:not_disabled");
      if (runtimeConfig.readModelStatusApi !== false) isolatedIssues.push("candidate:read_model_api:not_disabled");
      if (runtimeConfig.releaseManifestApi !== false || runtimeConfig.releaseCachePolicyApi !== false) {
        isolatedIssues.push("candidate:release_api:not_disabled");
      }
      if (!launcher.present || !launcher.complete) isolatedIssues.push("candidate:launcher:missing_or_incomplete");
      const manifestSha256 = String(runtimeConfig.releaseManifestSha256 || "");
      const identity = evaluateIdentity({
        embedded,
        backend: embedded,
        launcher,
        backendManifestSha256: manifestSha256,
      });
      isolatedIssues.push(...identity.issues);
      const cachePolicyValidation = validateIsolatedCandidateCachePolicy(
        runtimeConfig.candidateCachePolicy,
        embedded,
        manifestSha256,
      );
      isolatedIssues.push(...cachePolicyValidation.issues);
      if (isolatedIssues.length > 0) return applyIfCurrent({ issues: isolatedIssues });
      return applyIfCurrent(
        {
          mode: "isolated_candidate_app_launcher",
          identity: embedded,
          cachePolicy: runtimeConfig.candidateCachePolicy,
          swAudit,
        },
        true,
      );
    }

    const manifestOptOut = runtimeConfig.releaseManifestApi === false;
    const cachePolicyOptOut = runtimeConfig.releaseCachePolicyApi === false;
    if (manifestOptOut || cachePolicyOptOut) {
      if (!(manifestOptOut && cachePolicyOptOut)) {
        return applyIfCurrent({ issues: ["static_source:release_api_opt_out_incomplete"] });
      }
      const staticIssues = [];
      validateManifest("embedded", embedded, staticIssues);
      if (staticIssues.length > 0) return applyIfCurrent({ issues: staticIssues });
      if (launcher.present) {
        return applyIfCurrent({
          issues: [launcher.complete ? "static_source:launcher_identity_unverifiable" : "launcher:incomplete"],
        });
      }
      return applyIfCurrent({ mode: "static_source_explicit_opt_out", swAudit }, true);
    }

    const apiBaseUrl = String(runtimeConfig.apiBaseUrl || "").replace(/\/$/, "");
    if (!apiBaseUrl) return applyIfCurrent({ issues: ["runtime:apiBaseUrl:missing"] });
    const runtimeAuthToken = String(runtimeConfig.apiAuthToken || "");
    const fetchImpl = options.fetchImpl || (typeof fetch === "function" ? fetch : null);
    if (!fetchImpl) return applyIfCurrent({ issues: ["runtime:fetch:unavailable"] });

    try {
      const manifestResult = await fetchReleaseJson(fetchImpl, `${apiBaseUrl}/api/release-manifest`, runtimeAuthToken);
      const backend = manifestResult.payload;
      const backendManifestSha256 = manifestResult.response.headers?.get?.("X-PFI-Release-Manifest-SHA256") || "";
      const runningBackendSha256 = manifestResult.response.headers?.get?.("X-PFI-Running-Backend-SHA256") || "";
      const identity = evaluateIdentity({ embedded, backend, launcher, backendManifestSha256 });
      const identityIssues = [...identity.issues];
      if (!HEX_PATTERNS.backend_build_hash.test(runningBackendSha256)) {
        identityIssues.push("backend:running_backend_hash:missing_or_invalid");
      } else if (runningBackendSha256 !== embedded.backend_build_hash) {
        identityIssues.push("backend:running_backend_hash:mismatch");
      }
      if (identityIssues.length > 0) return applyIfCurrent({ issues: identityIssues });

      const policyResult = await fetchReleaseJson(fetchImpl, `${apiBaseUrl}/api/release-cache-policy`, runtimeAuthToken);
      const policyValidation = validateReleaseCachePolicy(policyResult.payload, backend);
      if (!policyValidation.ok) return applyIfCurrent({ issues: policyValidation.issues });
      return applyIfCurrent(
        {
          mode: launcher.present ? "app_launcher" : "direct_localhost",
          identity: embedded,
          cachePolicy: policyResult.payload,
          swAudit,
        },
        true,
      );
    } catch (error) {
      const reason = error instanceof Error ? error.message : String(error || "unavailable");
      return applyIfCurrent({ issues: [`backend:unavailable:${reason}`] });
    }
  }

  async function bootReleaseIdentityGate(options = {}) {
    return runReleaseIdentityCheck(options);
  }

  function installBfcacheRevalidation(windowRef = window) {
    if (!windowRef || typeof windowRef.addEventListener !== "function") return false;
    if (windowRef.__PFI_RELEASE_BFCACHE_GUARD_INSTALLED__ === true) return true;
    windowRef.__PFI_RELEASE_BFCACHE_GUARD_INSTALLED__ = true;
    windowRef.addEventListener("pageshow", (event) => {
      if (event?.persisted !== true) return;
      applyPendingState(windowRef.document, "检测到浏览器恢复旧页面，正在重新核对版本与缓存");
      windowRef.PFI_RELEASE_IDENTITY_READY = runReleaseIdentityCheck({
        window: windowRef,
        document: windowRef.document,
        reason: "检测到浏览器恢复旧页面，正在重新核对版本与缓存",
      });
    });
    return true;
  }

  const embeddedManifest = readJsonNode(window.document, "pfi-release-manifest");
  normalizeRuntimeConfig(window.document, embeddedManifest);
  const VERSION_INFO = Object.freeze({
    schema: "PFIV025Stage1ReleaseIdentityVersionInfoV1",
    compatibilitySchemas: ["PFIV024Stage2EntryVersionInfoV1", "PFIV024Stage1VersionInfoV1"],
    targetVersion: embeddedManifest.version || "v0.2.5",
    sourcePackageVersion: embeddedManifest.version || "v0.2.5",
    repairLabel: "PFI v0.2.5",
    buildId: embeddedManifest.build_id || "pfi-v025-s1p1-20260712.1",
    bundleVersion: embeddedManifest.app_build_version || "20260712.1",
    webBundleHash: embeddedManifest.frontend_bundle_hash || "manifest-pending",
    backendBuildHash: embeddedManifest.backend_build_hash || "manifest-pending",
    gitCommit: embeddedManifest.git_commit || "manifest-pending",
    uiContractVersion: "PFI-V025-RELEASE-IDENTITY",
    shellIntegrityContract: "PFI-V024-STAGE1-SHELL-INTEGRITY",
    entryConsistencyContract: "PFI-V025-RELEASE-IDENTITY",
    stage: "Stage 1",
    phase: "1.2",
    visibleFields: ["repairLabel", "buildId", "webBundleHash", "uiContractVersion"],
  });

  function readPFIStage1Version() {
    return VERSION_INFO;
  }

  const API = Object.freeze({
    manifestFields: MANIFEST_FIELDS,
    launcherQueryMap: LAUNCHER_QUERY_MAP,
    readJsonNode,
    parseLauncherIdentity,
    resolveLauncherSearch,
    evaluateIdentity,
    normalizeRuntimeConfig,
    applyPendingState,
    applyReadyState,
    applyBlockedState,
    disableLegacyServiceWorkers,
    validateReleaseCachePolicy,
    validateIsolatedCandidateCachePolicy,
    fetchReleaseJson,
    runReleaseIdentityCheck,
    installBfcacheRevalidation,
    bootReleaseIdentityGate,
  });

  window.PFI_STAGE1_VERSION = VERSION_INFO;
  window.PFI_READ_STAGE1_VERSION = readPFIStage1Version;
  window.PFI_STAGE2_ENTRY_VERSION = VERSION_INFO;
  window.PFI_READ_STAGE2_ENTRY_VERSION = readPFIStage1Version;
  window.PFI_RELEASE_IDENTITY = API;
  installBfcacheRevalidation(window);
  window.PFI_RELEASE_IDENTITY_READY = bootReleaseIdentityGate();
})();
