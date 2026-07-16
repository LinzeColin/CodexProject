(function attachPFIV025Stage9DecisionReview(root, factory) {
  const nodeRequire = typeof require === "function" ? require : null;
  const embedded = root?.PFI_V025_STAGE9_PHASE93_DATA
    || (nodeRequire ? nodeRequire("./stage9DecisionReviewData.js") : null);
  const api = factory(root, embedded, nodeRequire);
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.PFI_V025_STAGE9_DECISION_REVIEW = api;
})(typeof window !== "undefined" ? window : globalThis, function buildPFIV025Stage9DecisionReview(root, embedded, nodeRequire) {
  "use strict";

  const STORAGE_KEY = "pfi-v025-stage9-phase93-human-review";
  const REVIEW_DELTA_SCHEMA = "PFIV025Stage9Phase93ReviewDeltaV1";
  const OUTCOMES = Object.freeze(["accepted", "rejected", "deferred", "invalidated"]);
  const TRANSITIONS = Object.freeze({
    awaiting_human_review: Object.freeze([...OUTCOMES]),
    accepted: Object.freeze(["invalidated"]),
    deferred: Object.freeze(["accepted", "rejected", "invalidated"]),
    rejected: Object.freeze([]),
    invalidated: Object.freeze([]),
  });

  function deepFreeze(value) {
    if (!value || typeof value !== "object" || Object.isFrozen(value)) return value;
    Object.values(value).forEach(deepFreeze);
    return Object.freeze(value);
  }

  function clone(value) {
    return JSON.parse(JSON.stringify(value));
  }

  function sortedValue(value) {
    if (Array.isArray(value)) return value.map(sortedValue);
    if (!value || typeof value !== "object") return value;
    return Object.fromEntries(Object.keys(value).sort().map((key) => [key, sortedValue(value[key])]));
  }

  function canonicalJson(value) {
    return JSON.stringify(sortedValue(value));
  }

  function sameKeys(value, expected) {
    if (!value || typeof value !== "object" || Array.isArray(value)) return false;
    return canonicalJson(Object.keys(value).sort()) === canonicalJson([...expected].sort());
  }

  function base64ToBytes(value) {
    const encoded = String(value || "");
    if (typeof Buffer !== "undefined") return Uint8Array.from(Buffer.from(encoded, "base64"));
    const decoded = root.atob(encoded);
    return Uint8Array.from(decoded, (character) => character.charCodeAt(0));
  }

  async function sha256Bytes(bytes) {
    const subtle = root?.crypto?.subtle || globalThis.crypto?.subtle;
    if (subtle) {
      const digest = await subtle.digest("SHA-256", bytes);
      return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
    }
    if (nodeRequire) {
      return nodeRequire("node:crypto").createHash("sha256").update(Buffer.from(bytes)).digest("hex");
    }
    throw new Error("SHA-256 runtime is unavailable");
  }

  async function canonicalHash(value) {
    const bytes = new TextEncoder().encode(canonicalJson(value));
    return `sha256:${await sha256Bytes(bytes)}`;
  }

  function validatePhase93ViewModel(contract = embedded?.uiContract) {
    const errors = [];
    const decisions = Array.isArray(contract?.decision_cards) ? contract.decision_cards : [];
    const exports = Array.isArray(contract?.export_cards) ? contract.export_cards : [];
    if (contract?.schema !== "PFIV025Stage9Phase93UIContractV1") errors.push("schema mismatch");
    if (contract?.phase_id !== "V025-S9-P9.3") errors.push("phase mismatch");
    if (contract?.version !== "v0.2.5") errors.push("version mismatch");
    if (contract?.decision_count !== 2 || decisions.length !== 2) errors.push("two decisions required");
    if (contract?.export_format_count !== 4 || exports.length !== 4) errors.push("four exports required");
    if (contract?.same_snapshot_export !== true) errors.push("same snapshot export required");
    if (contract?.human_review_required !== true) errors.push("human review required");
    if (contract?.automatic_trading_allowed !== false) errors.push("automatic trading forbidden");
    if (contract?.trade_execution_available !== false) errors.push("trade execution forbidden");
    if (contract?.financial_values_emitted !== 0) errors.push("financial values emitted");
    if (contract?.contains_private_values !== false) errors.push("private values emitted");
    if (contract?.stage_9_whole_stage_review_done !== false) errors.push("whole-stage scope leak");
    if (!/^sha256:[0-9a-f]{64}$/.test(String(contract?.export_snapshot_hash || ""))) errors.push("snapshot hash invalid");
    if (!/^sha256:[0-9a-f]{64}$/.test(String(contract?.source_analysis_pack_hash || ""))) errors.push("analysis hash invalid");
    if (!/^sha256:[0-9a-f]{64}$/.test(String(contract?.export_manifest_hash || ""))) errors.push("manifest hash invalid");
    const decisionIds = new Set();
    decisions.forEach((decision) => {
      const id = String(decision?.decision_id || "");
      if (!id || decisionIds.has(id)) errors.push("decision id missing or duplicated");
      decisionIds.add(id);
      for (const key of ["action", "horizon", "status", "thesis", "portfolio_effect", "review_route"]) {
        if (!decision?.[key]) errors.push(`decision field missing: ${id}:${key}`);
      }
      for (const key of ["confidence_dimensions", "catalysts", "evidence", "counter_evidence", "invalidation_conditions", "risks", "model_versions", "source_ids", "review_history"]) {
        if (!Array.isArray(decision?.[key]) || decision[key].length === 0) errors.push(`decision collection missing: ${id}:${key}`);
      }
      if (decision?.human_review_required !== true) errors.push(`human review missing: ${id}`);
      if (decision?.automatic_trading_allowed !== false || decision?.trade_execution_available !== false) errors.push(`unsafe action capability: ${id}`);
      if (!TRANSITIONS[decision?.status]) errors.push(`invalid decision status: ${id}`);
    });
    const formats = new Set(exports.map((item) => item?.format));
    for (const format of ["html", "pdf", "csv", "markdown"]) {
      if (!formats.has(format)) errors.push(`export missing: ${format}`);
    }
    exports.forEach((item) => {
      if (item?.source_snapshot_hash !== contract?.export_snapshot_hash) errors.push(`export snapshot mismatch: ${item?.format}`);
      if (!/^sha256:[0-9a-f]{64}$/.test(String(item?.sha256 || ""))) errors.push(`export hash invalid: ${item?.format}`);
      if (!Number.isInteger(item?.byte_size) || item.byte_size <= 0) errors.push(`export size invalid: ${item?.format}`);
    });
    const serialized = JSON.stringify(contract);
    if (/\bCNY\s+-?[0-9]/.test(serialized)) errors.push("financial amount rendered");
    if (/"(?:value|amount|financial_value)"\s*:/.test(serialized)) errors.push("financial value field rendered");
    if (/"[a-z0-9_]+_cny"\s*:/.test(serialized)) errors.push("financial metric value rendered");
    if (/place[_ -]?order|execute[_ -]?trade|自动交易已启用|直接下单/i.test(serialized)) errors.push("trade action rendered");
    return deepFreeze({
      schema: "PFIV025Stage9Phase93UIViewValidationV1",
      phaseId: "V025-S9-P9.3",
      status: errors.length ? "fail" : "pass",
      errors,
      decisionCount: decisions.length,
      counterEvidenceCount: decisions.reduce((sum, item) => sum + item.counter_evidence.length, 0),
      invalidationConditionCount: decisions.reduce((sum, item) => sum + item.invalidation_conditions.length, 0),
      exportFormatCount: exports.length,
      automaticTradingAllowed: contract?.automatic_trading_allowed === true,
      tradeExecutionAvailable: contract?.trade_execution_available === true,
    });
  }

  function buildPhase93ViewModel(contract = embedded?.uiContract) {
    const normalized = clone(contract);
    const validation = validatePhase93ViewModel(normalized);
    if (validation.status !== "pass") {
      throw new Error(`invalid PFI v0.2.5 Stage 9 Phase 9.3 UI contract: ${validation.errors.join("; ")}`);
    }
    return deepFreeze({
      ...normalized,
      page: "reports",
      kicker_zh: "Stage 9 Phase 9.3 建议、复盘与导出",
      summary_zh: `${validation.decisionCount} 个复核建议、${validation.counterEvidenceCount} 条反方证据、${validation.invalidationConditionCount} 个失效条件与 ${validation.exportFormatCount} 种同源导出已就绪。`,
      warning_zh: "接受只记录人工复核结果，不触发交易；报告仍保持 3 blocked / 2 partial。",
      validation,
    });
  }

  function availableOutcomes(status) {
    return Object.freeze([...(TRANSITIONS[String(status || "")] || [])]);
  }

  async function validateReviewLedger(viewModel) {
    const errors = [];
    for (const decision of viewModel?.decision_cards || []) {
      if (!Array.isArray(decision.review_history) || decision.review_history.length === 0) {
        errors.push(`${decision.decision_id}: review history is required`);
        continue;
      }
      let priorHash = null;
      let priorStatus = null;
      for (const [index, event] of decision.review_history.entries()) {
        const expectedKeys = [
          "event_id", "event_type", "from_status", "to_status", "outcome",
          "actor_role", "actor_ref", "reason_zh", "observed_at",
          "prior_event_hash", "event_hash",
        ];
        if (!sameKeys(event, expectedKeys)) errors.push(`${decision.decision_id}: event shape mismatch ${index + 1}`);
        if (event.event_id !== `${decision.decision_id}-EVT-${String(index + 1).padStart(4, "0")}`) {
          errors.push(`${decision.decision_id}: event id mismatch ${index + 1}`);
        }
        if (event.prior_event_hash !== priorHash) errors.push(`${decision.decision_id}: prior hash mismatch ${index + 1}`);
        if (event.from_status !== priorStatus) errors.push(`${decision.decision_id}: prior status mismatch ${index + 1}`);
        const body = Object.fromEntries(Object.entries(event).filter(([key]) => key !== "event_hash"));
        const expectedHash = await canonicalHash(body);
        if (event.event_hash !== expectedHash) errors.push(`${decision.decision_id}: event hash mismatch ${index + 1}`);
        if (index === 0) {
          if (
            event.event_type !== "created"
            || event.to_status !== "awaiting_human_review"
            || event.outcome !== null
            || event.actor_role !== "system"
          ) errors.push(`${decision.decision_id}: invalid creation event`);
        } else if (!availableOutcomes(priorStatus).includes(event.to_status)) {
          errors.push(`${decision.decision_id}: invalid transition ${priorStatus}->${event.to_status}`);
        } else if (
          event.event_type !== "human_review"
          || event.outcome !== event.to_status
          || event.actor_role !== "owner"
        ) {
          errors.push(`${decision.decision_id}: invalid human review event ${index + 1}`);
        }
        if (!String(event.actor_ref || "").trim()) errors.push(`${decision.decision_id}: actor ref missing ${index + 1}`);
        if (!String(event.reason_zh || "").trim()) errors.push(`${decision.decision_id}: reason missing ${index + 1}`);
        if (!String(event.observed_at || "").trim() || Number.isNaN(Date.parse(event.observed_at))) {
          errors.push(`${decision.decision_id}: observed_at invalid ${index + 1}`);
        }
        priorHash = event.event_hash;
        priorStatus = event.to_status;
      }
      if (priorStatus !== decision.status) errors.push(`${decision.decision_id}: terminal status mismatch`);
    }
    return deepFreeze({
      schema: "PFIV025Stage9Phase93ReviewLedgerValidationV1",
      status: errors.length ? "fail" : "pass",
      errors,
    });
  }

  function immutableViewModelProjection(viewModel) {
    const projected = clone(viewModel);
    projected.decision_cards = (projected.decision_cards || []).map((decision) => {
      const normalized = { ...decision };
      delete normalized.status;
      delete normalized.review_history;
      return normalized;
    });
    return projected;
  }

  function validateEmbeddedBinding(viewModel) {
    const errors = [];
    const baseline = buildPhase93ViewModel();
    if (canonicalJson(immutableViewModelProjection(viewModel)) !== canonicalJson(immutableViewModelProjection(baseline))) {
      errors.push("immutable embedded contract binding mismatch");
    }
    const baselineById = Object.fromEntries(baseline.decision_cards.map((decision) => [decision.decision_id, decision]));
    for (const decision of viewModel?.decision_cards || []) {
      const expected = baselineById[decision.decision_id]?.review_history?.[0];
      const actual = decision.review_history?.[0];
      if (!expected || canonicalJson(actual) !== canonicalJson(expected)) {
        errors.push(`${decision.decision_id}: creation event binding mismatch`);
      }
    }
    return deepFreeze({
      schema: "PFIV025Stage9Phase93EmbeddedBindingValidationV1",
      status: errors.length ? "fail" : "pass",
      errors,
    });
  }

  function reviewDeltaIdentity() {
    const contract = embedded?.uiContract || {};
    return {
      version: "v0.2.5",
      phase_id: "V025-S9-P9.3",
      pack_hash: embedded?.packHash,
      source_analysis_pack_hash: contract.source_analysis_pack_hash,
      export_snapshot_hash: contract.export_snapshot_hash,
      export_manifest_hash: contract.export_manifest_hash,
    };
  }

  function buildReviewDelta(viewModel) {
    return {
      schema: REVIEW_DELTA_SCHEMA,
      ...reviewDeltaIdentity(),
      review_records: viewModel.decision_cards.map((decision) => ({
        decision_id: decision.decision_id,
        status: decision.status,
        review_history: clone(decision.review_history),
      })),
    };
  }

  async function validateReviewDelta(delta) {
    const errors = [];
    const identity = reviewDeltaIdentity();
    const expectedTopKeys = ["schema", ...Object.keys(identity), "review_records"];
    if (!sameKeys(delta, expectedTopKeys)) errors.push("review delta shape mismatch");
    if (delta?.schema !== REVIEW_DELTA_SCHEMA) errors.push("review delta schema mismatch");
    for (const [key, value] of Object.entries(identity)) {
      if (delta?.[key] !== value) errors.push(`review delta identity mismatch: ${key}`);
    }
    const records = Array.isArray(delta?.review_records) ? delta.review_records : [];
    const baseline = buildPhase93ViewModel();
    if (records.length !== baseline.decision_cards.length) errors.push("review delta decision count mismatch");
    const ids = records.map((record) => String(record?.decision_id || ""));
    if (new Set(ids).size !== ids.length) errors.push("review delta decision ids duplicated");
    const expectedIds = baseline.decision_cards.map((decision) => decision.decision_id).sort();
    if (canonicalJson([...ids].sort()) !== canonicalJson(expectedIds)) errors.push("review delta decision ids mismatch");

    const rebuilt = clone(baseline);
    const recordById = Object.fromEntries(records.map((record) => [record?.decision_id, record]));
    for (const decision of rebuilt.decision_cards) {
      const record = recordById[decision.decision_id];
      if (!sameKeys(record, ["decision_id", "status", "review_history"])) {
        errors.push(`${decision.decision_id}: review delta record shape mismatch`);
        continue;
      }
      decision.status = record.status;
      decision.review_history = clone(record.review_history);
    }
    const viewValidation = validatePhase93ViewModel(rebuilt);
    if (viewValidation.status !== "pass") errors.push(...viewValidation.errors.map((error) => `view: ${error}`));
    const binding = validateEmbeddedBinding(rebuilt);
    if (binding.status !== "pass") errors.push(...binding.errors);
    const ledger = await validateReviewLedger(rebuilt);
    if (ledger.status !== "pass") errors.push(...ledger.errors);
    return deepFreeze({
      schema: "PFIV025Stage9Phase93ReviewDeltaValidationV1",
      status: errors.length ? "fail" : "pass",
      errors,
      viewModel: errors.length ? null : deepFreeze(rebuilt),
    });
  }

  async function applyHumanReview(viewModel, decisionId, outcome, options = {}) {
    const validation = validatePhase93ViewModel(viewModel);
    if (validation.status !== "pass") throw new Error("cannot review an invalid Phase 9.3 view model");
    const next = clone(viewModel);
    const decision = next.decision_cards.find((item) => item.decision_id === decisionId);
    if (!decision) throw new Error(`unknown decision: ${decisionId}`);
    const normalizedOutcome = String(outcome || "");
    if (!availableOutcomes(decision.status).includes(normalizedOutcome)) {
      throw new Error(`invalid review transition: ${decision.status}->${normalizedOutcome}`);
    }
    const reviewerRef = String(options.reviewerRef || "local_owner").trim();
    const reasonZh = String(options.reasonZh || `人工复核结果：${normalizedOutcome}`).trim();
    const observedAt = String(options.observedAt || new Date().toISOString()).trim();
    if (!reviewerRef || !reasonZh || !observedAt) throw new Error("review metadata is required");
    const history = decision.review_history;
    const previous = history[history.length - 1];
    const event = {
      event_id: `${decision.decision_id}-EVT-${String(history.length + 1).padStart(4, "0")}`,
      event_type: "human_review",
      from_status: decision.status,
      to_status: normalizedOutcome,
      outcome: normalizedOutcome,
      actor_role: "owner",
      actor_ref: reviewerRef,
      reason_zh: reasonZh,
      observed_at: observedAt,
      prior_event_hash: previous.event_hash,
    };
    event.event_hash = await canonicalHash(event);
    decision.status = normalizedOutcome;
    decision.review_history.push(event);
    const ledger = await validateReviewLedger(next);
    if (ledger.status !== "pass") throw new Error(`review ledger failed: ${ledger.errors.join("; ")}`);
    return deepFreeze(next);
  }

  function exportBytes(format) {
    const normalized = String(format || "").toLowerCase();
    if (!embedded?.assetsBase64?.[normalized]) throw new Error(`unknown export format: ${normalized}`);
    return base64ToBytes(embedded.assetsBase64[normalized]);
  }

  async function verifyExportAsset(format) {
    const normalized = String(format || "").toLowerCase();
    const entry = embedded.uiContract.export_cards.find((item) => item.format === normalized);
    if (!entry) throw new Error(`export manifest missing: ${normalized}`);
    const bytes = exportBytes(normalized);
    const actualHash = `sha256:${await sha256Bytes(bytes)}`;
    return deepFreeze({
      format: normalized,
      status: actualHash === entry.sha256 && bytes.byteLength === entry.byte_size ? "pass" : "fail",
      expectedHash: entry.sha256,
      actualHash,
      expectedSize: entry.byte_size,
      actualSize: bytes.byteLength,
      sourceSnapshotHash: entry.source_snapshot_hash,
    });
  }

  function downloadExport(format, documentRef = root?.document) {
    const normalized = String(format || "").toLowerCase();
    const entry = embedded.uiContract.export_cards.find((item) => item.format === normalized);
    if (!entry) throw new Error(`export manifest missing: ${normalized}`);
    const bytes = exportBytes(normalized);
    if (!documentRef || typeof Blob === "undefined" || !root?.URL?.createObjectURL) {
      return deepFreeze({ format: normalized, filename: entry.filename, bytes });
    }
    const blob = new Blob([bytes], { type: entry.content_type });
    const url = root.URL.createObjectURL(blob);
    const anchor = documentRef.createElement("a");
    anchor.href = url;
    anchor.download = entry.filename;
    anchor.hidden = true;
    documentRef.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
    root.setTimeout(() => root.URL.revokeObjectURL(url), 0);
    return deepFreeze({ format: normalized, filename: entry.filename, byteSize: bytes.byteLength });
  }

  async function loadPersistedViewModel(storage = root?.localStorage) {
    if (!storage) return null;
    try {
      const payload = JSON.parse(storage.getItem(STORAGE_KEY) || "null");
      if (!payload) return null;
      const validation = await validateReviewDelta(payload);
      if (validation.status === "pass") return validation.viewModel;
      storage.removeItem(STORAGE_KEY);
      return null;
    } catch (_error) {
      try { storage.removeItem(STORAGE_KEY); } catch (_removeError) { /* local-only best effort */ }
      return null;
    }
  }

  async function persistViewModel(viewModel, storage = root?.localStorage) {
    if (!storage || validatePhase93ViewModel(viewModel).status !== "pass") return false;
    if (validateEmbeddedBinding(viewModel).status !== "pass") return false;
    if ((await validateReviewLedger(viewModel)).status !== "pass") return false;
    try {
      storage.setItem(STORAGE_KEY, JSON.stringify(buildReviewDelta(viewModel)));
      return true;
    } catch (_error) {
      return false;
    }
  }

  const contract = embedded?.uiContract || null;
  return deepFreeze({
    schema: "PFIV025Stage9Phase93DecisionReviewUIAPIv1",
    version: "v0.2.5",
    phaseId: "V025-S9-P9.3",
    storageKey: STORAGE_KEY,
    embeddedContract: () => contract,
    buildPhase93ViewModel,
    validatePhase93ViewModel,
    validateEmbeddedBinding,
    validateReviewLedger,
    buildReviewDelta,
    validateReviewDelta,
    availableOutcomes,
    applyHumanReview,
    exportBytes,
    verifyExportAsset,
    downloadExport,
    loadPersistedViewModel,
    persistViewModel,
  });
});
