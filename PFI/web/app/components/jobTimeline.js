(() => {
  "use strict";

  const STATES = Object.freeze([
    "queued", "running", "retrying", "blocked", "succeeded", "failed", "cancelled", "dead_letter",
  ]);
  const TERMINAL_STATES = new Set(["succeeded", "failed", "cancelled", "dead_letter"]);
  const STORAGE_KEY = "pfi-v025-stage8-job-timeline";
  const contract = Object.freeze({
    schema: "PFIV025Stage8Phase82JobTimelineContractV1",
    targetVersion: "v0.2.5",
    stage: "Stage 8",
    phase: "8.2",
    stageMs: 1000,
    durableMs: 10000,
    persistence: "sessionStorage",
    storageFields: Object.freeze(["id", "state", "startedAt", "updatedAt", "completedUnits", "totalUnits"]),
    routeBehavior: "leave_page_safe",
    progressTruth: "completedUnits_over_totalUnits_only",
    states: STATES,
  });
  const jobs = new Map();
  const timers = new Map();

  function numericUnit(value) {
    if (value === null || value === undefined || value === "") return null;
    const numeric = Number(value);
    return Number.isFinite(numeric) ? numeric : null;
  }

  function safeText(value, fallback, limit = 96) {
    const text = String(value || "").replace(/\s+/g, " ").trim();
    return (text || fallback).slice(0, limit);
  }

  function actualProgress(job) {
    const completed = numericUnit(job.completedUnits);
    const total = numericUnit(job.totalUnits);
    if (completed === null || total === null || total <= 0 || completed < 0) return null;
    return Math.min(completed, total) / total;
  }

  function elapsedMs(job) {
    return Math.max(0, Date.now() - Number(job.startedAt || Date.now()));
  }

  function snapshot(id) {
    const job = jobs.get(String(id));
    if (!job) return null;
    const elapsed = elapsedMs(job);
    const backendDurable = job.source === "durable_job_api";
    return Object.freeze({
      ...job,
      elapsedMs: elapsed,
      durable: !TERMINAL_STATES.has(job.state) && (backendDurable || elapsed >= contract.durableMs),
      actualProgress: actualProgress(job),
    });
  }

  function persist() {
    try {
      const payload = [...jobs.values()].slice(-20).map((job) => ({
        id: job.id,
        state: job.state,
        startedAt: job.startedAt,
        updatedAt: job.updatedAt,
        completedUnits: numericUnit(job.completedUnits),
        totalUnits: numericUnit(job.totalUnits),
      }));
      window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(payload));
    } catch (_error) {
      // The in-memory timeline remains available when session storage is denied.
    }
  }

  function ensureMount() {
    let mount = document.querySelector("[data-stage8-job-timeline]");
    if (mount) return mount;
    const taskCenter = document.querySelector("[data-task-center]");
    if (!taskCenter) return null;
    mount = document.createElement("section");
    mount.className = "stage8-job-timeline";
    mount.dataset.stage8JobTimeline = "phase_8_2";
    mount.setAttribute("aria-labelledby", "stage8-job-timeline-title");
    const heading = document.createElement("div");
    heading.className = "stage8-job-timeline-head";
    const title = document.createElement("strong");
    title.id = "stage8-job-timeline-title";
    title.textContent = "后台任务时间线";
    const hint = document.createElement("span");
    hint.textContent = "离开当前页面后仍可查看";
    heading.append(title, hint);
    const list = document.createElement("ol");
    list.dataset.stage8JobList = "true";
    list.setAttribute("aria-live", "polite");
    const empty = document.createElement("p");
    empty.dataset.stage8JobEmpty = "true";
    empty.textContent = "当前没有后台任务。";
    mount.append(heading, list, empty);
    taskCenter.appendChild(mount);
    return mount;
  }

  function stateLabel(state) {
    return ({
      queued: "排队中",
      running: "进行中",
      retrying: "等待重试",
      blocked: "等待处理",
      succeeded: "已完成",
      failed: "失败",
      cancelled: "已取消",
      dead_letter: "死信",
    })[state] || "进行中";
  }

  function renderJob(job, list) {
    const state = snapshot(job.id);
    const item = document.createElement("li");
    item.dataset.stage8JobId = job.id;
    item.dataset.stage8JobState = job.state;
    item.dataset.stage8JobDurable = state.durable ? "true" : "false";
    const header = document.createElement("div");
    const label = document.createElement("strong");
    label.textContent = job.label;
    const badge = document.createElement("span");
    badge.textContent = state.durable && job.state === "running" ? "后台运行" : stateLabel(job.state);
    header.append(label, badge);
    const stage = document.createElement("p");
    stage.textContent = job.stageLabel || (state.durable ? "任务仍在后台运行，可离开本页。" : stateLabel(job.state));
    const progress = document.createElement("progress");
    progress.setAttribute("aria-label", `${job.label}真实工作量`);
    if (state.actualProgress === null) {
      progress.removeAttribute("value");
      progress.hidden = true;
      progress.setAttribute("aria-valuetext", "未提供真实工作量，不显示百分比");
    } else {
      progress.max = Number(job.totalUnits);
      progress.value = Math.min(Number(job.completedUnits), Number(job.totalUnits));
      progress.setAttribute("aria-valuetext", `${progress.value}/${progress.max} 个真实单元`);
    }
    const meta = document.createElement("small");
    meta.textContent = job.source === "durable_job_api"
      ? `SQLite revision ${job.revision} · trace ${job.traceId || "待生成"} · 重试 ${job.retryCount || 0} 次`
      : state.durable
        ? `已运行 ${Math.floor(state.elapsedMs / 1000)} 秒 · 可离开页面`
        : `${stateLabel(job.state)} · ${Math.floor(state.elapsedMs / 1000)} 秒`;
    item.append(header, stage, progress, meta);
    if (job.errorCode || job.errorMessage) {
      const error = document.createElement("p");
      error.dataset.stage10JobError = "true";
      error.textContent = `错误 ${job.errorCode || "UNKNOWN"} · ${job.errorMessage || "未提供详情"}`;
      item.appendChild(error);
    }
    if (job.resultUri) {
      const result = document.createElement("small");
      result.dataset.stage10JobResult = "true";
      result.textContent = `结果入口 ${job.resultUri}`;
      item.appendChild(result);
    }
    if (job.cacheFallbackUsed) item.dataset.stage10CacheFallback = "true";
    if (job.source === "durable_job_api") {
      item.dataset.stage10JobSource = "durable_job_api";
      item.dataset.stage10BackendState = job.backendState;
    }
    list.appendChild(item);
  }

  function render() {
    const mount = ensureMount();
    if (!mount) return;
    const list = mount.querySelector("[data-stage8-job-list]");
    const empty = mount.querySelector("[data-stage8-job-empty]");
    if (!list || !empty) return;
    list.replaceChildren();
    [...jobs.values()].sort((first, second) => second.updatedAt - first.updatedAt).forEach((job) => renderJob(job, list));
    empty.hidden = jobs.size > 0;
    document.body.dataset.v025Stage8JobCount = String(jobs.size);
  }

  function scheduleBoundaries(job) {
    window.clearTimeout(timers.get(job.id));
    timers.delete(job.id);
    if (TERMINAL_STATES.has(job.state)) return;
    if (job.source === "durable_job_api") return;
    const elapsed = elapsedMs(job);
    const nextBoundary = elapsed < contract.stageMs
      ? contract.stageMs
      : elapsed < contract.durableMs ? contract.durableMs : null;
    if (nextBoundary === null) return;
    const timer = window.setTimeout(() => {
      render();
      scheduleBoundaries(job);
    }, Math.max(0, nextBoundary - elapsed) + 8);
    timers.set(job.id, timer);
  }

  function normalize(input, existing = {}) {
    const state = STATES.includes(input.state) ? input.state : existing.state || "running";
    return {
      ...existing,
      id: safeText(input.id || existing.id, `job-${Date.now()}`, 128),
      label: safeText(input.label || existing.label, "后台任务"),
      stageLabel: safeText(input.stageLabel ?? existing.stageLabel, "正在处理真实任务"),
      state,
      startedAt: Number(input.startedAt || existing.startedAt || Date.now()),
      updatedAt: Number(input.updatedAt || existing.updatedAt || Date.now()),
      completedUnits: input.completedUnits ?? existing.completedUnits ?? null,
      totalUnits: input.totalUnits ?? existing.totalUnits ?? null,
      source: safeText(input.source || existing.source, "session_timeline", 40),
      timerBased: input.timerBased === true,
      backendState: safeText(input.backendState || existing.backendState, state, 24),
      revision: Number(input.revision ?? existing.revision ?? 0),
      traceId: safeText(input.traceId || existing.traceId, "", 32),
      retryCount: Number(input.retryCount ?? existing.retryCount ?? 0),
      cacheFallbackUsed: input.cacheFallbackUsed === true,
      errorCode: safeText(input.errorCode ?? existing.errorCode, "", 64),
      errorMessage: safeText(input.errorMessage ?? existing.errorMessage, "", 240),
      resultUri: safeText(input.resultUri ?? existing.resultUri, "", 240),
    };
  }

  function start(input = {}) {
    const job = normalize({ ...input, state: input.state || "running" });
    jobs.set(job.id, job);
    persist();
    render();
    scheduleBoundaries(job);
    return snapshot(job.id);
  }

  function update(id, patch = {}) {
    const key = String(id);
    const existing = jobs.get(key);
    if (!existing) return null;
    const job = normalize({ ...patch, id: key }, existing);
    jobs.set(key, job);
    persist();
    render();
    scheduleBoundaries(job);
    return snapshot(key);
  }

  function settle(id, state, patch = {}) {
    if (!TERMINAL_STATES.has(state) && state !== "blocked") return null;
    return update(id, { ...patch, state });
  }

  function remove(id) {
    const key = String(id);
    window.clearTimeout(timers.get(key));
    timers.delete(key);
    const removed = jobs.delete(key);
    persist();
    render();
    return removed;
  }

  function restore() {
    try {
      const stored = JSON.parse(window.sessionStorage.getItem(STORAGE_KEY) || "[]");
      if (Array.isArray(stored)) stored.forEach((item) => {
        if (!item?.id || !STATES.includes(item.state)) return;
        const job = normalize(item);
        jobs.set(job.id, job);
        scheduleBoundaries(job);
      });
    } catch (_error) {
      jobs.clear();
    }
  }

  function initialize() {
    restore();
    render();
    const observer = new MutationObserver(() => {
      if (!document.querySelector("[data-stage8-job-timeline]")) render();
    });
    observer.observe(document.body, { childList: true, subtree: true });
    document.addEventListener("pfi:job", (event) => {
      const detail = event.detail || {};
      if (detail.action === "start") start(detail.job || {});
      else if (detail.action === "remove") remove(detail.id);
      else if (detail.action === "succeed") settle(detail.id, "succeeded", detail.patch || {});
      else if (detail.action === "fail") settle(detail.id, "failed", detail.patch || {});
      else update(detail.id, detail.patch || {});
    });
  }

  window.PFI_V025_STAGE8_JOB_TIMELINE = Object.freeze({
    contract,
    start,
    update,
    succeed: (id, patch = {}) => settle(id, "succeeded", patch),
    fail: (id, patch = {}) => settle(id, "failed", patch),
    cancel: (id, patch = {}) => settle(id, "cancelled", patch),
    remove,
    snapshot,
    actualProgress,
  });
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
