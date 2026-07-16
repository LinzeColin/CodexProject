(() => {
  "use strict";

  const TERMINAL_STATES = new Set(["succeeded", "failed", "cancelled", "dead_letter"]);
  const STATE_MAP = Object.freeze({
    queued: "queued",
    running: "running",
    retrying: "retrying",
    succeeded: "succeeded",
    failed: "failed",
    cancelled: "cancelled",
    dead_letter: "dead_letter",
  });
  const contract = Object.freeze({
    schema: "PFIV025Stage10RuntimeJobsClientV1",
    phaseId: "V025-S10-P10.3",
    acceptanceId: "ACC-PFI-V025-STAGE10-WHOLE-REVIEW",
    source: "durable_job_api",
    progressTruth: "completed_units_over_total_units_only",
    timerBasedProgress: false,
    pollPurpose: "read_persisted_state_only",
    externalNetworkCalls: 0,
  });

  function safeText(value, fallback = "", limit = 160) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    return (text || fallback).slice(0, limit);
  }

  function normalize(job) {
    if (!job || typeof job !== "object" || !job.job_id || !STATE_MAP[job.status]) {
      throw new Error("后台任务响应不符合 durable job contract");
    }
    const completedUnits = Number(job.progress?.completed_units);
    const totalUnits = Number(job.progress?.total_units);
    const revision = Number(job.revision);
    const retryCount = Number(job.observability?.retry_count || 0);
    const traceId = safeText(job.trace?.trace_id, "", 32);
    const startedAt = Date.parse(job.created_at);
    const updatedAt = Date.parse(job.updated_at);
    if (!Number.isFinite(startedAt)) throw new Error("后台任务缺少持久化创建时间");
    if (!Number.isFinite(updatedAt)) throw new Error("后台任务缺少持久化更新时间");
    const state = STATE_MAP[job.status];
    const errorMessage = safeText(job.error?.message, "", 240);
    const stage = safeText(job.progress?.step || job.trace?.stage, state, 160);
    return Object.freeze({
      id: safeText(job.job_id, "", 80),
      label: "缓存切片刷新",
      state,
      backendState: safeText(job.status, "", 24),
      stageLabel: errorMessage && TERMINAL_STATES.has(job.status)
        ? `${stage} · ${errorMessage}`
        : stage,
      startedAt,
      updatedAt,
      completedUnits: Number.isFinite(completedUnits) ? completedUnits : null,
      totalUnits: Number.isFinite(totalUnits) && totalUnits > 0 ? totalUnits : null,
      source: contract.source,
      timerBased: false,
      revision: Number.isInteger(revision) ? revision : 0,
      traceId,
      retryCount: Number.isInteger(retryCount) ? retryCount : 0,
      cacheFallbackUsed: job.observability?.cache_fallback_used === true,
      errorCode: safeText(job.error?.code, "", 64),
      errorMessage,
      resultUri: safeText(job.result?.artifact_uri, "", 240),
    });
  }

  function ingest(job) {
    const normalized = normalize(job);
    const timeline = window.PFI_V025_STAGE8_JOB_TIMELINE;
    if (!timeline?.snapshot?.(normalized.id)) timeline?.start?.(normalized);
    else timeline?.update?.(normalized.id, normalized);
    const currentUpdatedAt = Number(document.body?.dataset.pfiStage10JobUpdatedAt || -1);
    if (document.body && normalized.updatedAt >= currentUpdatedAt) {
      document.body.dataset.pfiStage10JobId = normalized.id;
      document.body.dataset.pfiStage10JobStatus = normalized.backendState;
      document.body.dataset.pfiStage10JobRevision = String(normalized.revision);
      document.body.dataset.pfiStage10JobTraceId = normalized.traceId;
      document.body.dataset.pfiStage10JobProgressSource = contract.source;
      document.body.dataset.pfiStage10JobTimerBased = "false";
      document.body.dataset.pfiStage10JobExternalNetworkCalls = "0";
      document.body.dataset.pfiStage10JobUpdatedAt = String(normalized.updatedAt);
    }
    return normalized;
  }

  window.PFI_V025_STAGE10_RUNTIME_JOBS = Object.freeze({
    contract,
    normalize,
    ingest,
    isTerminal: (status) => TERMINAL_STATES.has(String(status || "")),
  });
})();
