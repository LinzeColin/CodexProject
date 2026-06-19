const CONTEXT_STORAGE_KEY = "pfi-context-v1";
const FEEDBACK_SLA_MS = {
  instant: 100,
  skeleton: 300,
  stepped: 1000,
  background: 10000,
};

const WORKSPACES = {
  home: {
    label: "首页",
    kicker: "Cached daily brief",
    conclusion: "今日可用缓存已加载；先处理数据新鲜度和证据阻塞，再进入研究或策略实验室。",
  },
  market: {
    label: "市场",
    kicker: "Market context",
    conclusion: "市场视图聚合宽度、主题、催化和自选监控；所有卡片显示来源、更新时间和状态。",
  },
  research: {
    label: "研究",
    kicker: "Evidence workspace",
    conclusion: "研究视图聚合公司、基金、行业、政策和证据对象；结论必须连接来源与反证条件。",
  },
  portfolio: {
    label: "持仓",
    kicker: "Portfolio review",
    conclusion: "持仓视图聚合暴露、归因、风险、纪律和决策队列；所有行动需要人工复核。",
  },
  strategy: {
    label: "策略实验室",
    kicker: "Backtest and training",
    conclusion: "策略实验室保留回测、参数扫描、模拟和盘感训练；训练模式不会输出实盘信号。",
  },
  data: {
    label: "数据与系统",
    kicker: "Freshness and lineage",
    conclusion: "数据与系统视图聚合来源、任务、质量、血缘、隐私、备份和诊断状态。",
  },
};

function readContext() {
  try {
    return JSON.parse(localStorage.getItem(CONTEXT_STORAGE_KEY) || "{}");
  } catch (_error) {
    return {};
  }
}

function writeContext(nextContext) {
  localStorage.setItem(CONTEXT_STORAGE_KEY, JSON.stringify(nextContext));
}

function currentContext() {
  const values = readContext();
  document.querySelectorAll("[data-context-field]").forEach((field) => {
    values[field.dataset.contextField] = field.value || field.textContent || "";
  });
  return values;
}

function restoreContext() {
  const values = readContext();
  document.querySelectorAll("[data-context-field]").forEach((field) => {
    const key = field.dataset.contextField;
    if (!Object.prototype.hasOwnProperty.call(values, key)) return;
    if ("value" in field) {
      field.value = values[key];
    } else {
      field.textContent = values[key];
    }
  });
}

function showToast(message) {
  const toast = document.querySelector("[data-toast]");
  if (!toast) return;
  toast.textContent = message;
  toast.hidden = false;
  window.setTimeout(() => {
    toast.hidden = true;
  }, 2600);
}

function readHomeSummary() {
  const node = document.querySelector("#pfi-home-summary");
  if (!node) return null;
  try {
    const payload = JSON.parse(node.textContent || "{}");
    return payload.schema === "PFIOSHomeSummaryV1" ? payload : null;
  } catch (_error) {
    return null;
  }
}

function applyHomeSummary(summary) {
  if (!summary) return;
  const cardByKey = {};
  (summary.metric_cards || []).forEach((card) => {
    cardByKey[card.key] = card;
  });
  document.querySelectorAll("[data-home-card]").forEach((tile) => {
    const card = cardByKey[tile.dataset.homeCard];
    if (!card) return;
    const value = tile.querySelector("[data-card-value]");
    const detail = tile.querySelector("[data-card-detail]");
    const label = tile.querySelector("span");
    if (label && card.label) label.textContent = card.label;
    if (value) value.textContent = card.value;
    if (detail) detail.textContent = card.detail;
  });

  const freshness = document.querySelector("#freshness-label");
  if (freshness && summary.as_of) {
    freshness.textContent = `Updated ${summary.as_of}`;
  }

  applyDecisionRows(summary.decision_rows || []);
  applyEvidenceDrawer(summary.evidence_drawer || {});
  applyWorkflowRuntime(summary.workflow_runtime || {});
}

function applyDecisionRows(rows) {
  const body = document.querySelector("[data-home-decision-rows]");
  if (!body || rows.length === 0) return;
  body.replaceChildren();
  rows.forEach((row) => {
    const tr = document.createElement("tr");
    [row.priority, row.object, row.evidence, row.action].forEach((value) => {
      const td = document.createElement("td");
      td.textContent = value || "";
      tr.appendChild(td);
    });
    const statusCell = document.createElement("td");
    const status = document.createElement("span");
    status.className = `status-pill ${statusClass(row.status)}`;
    status.textContent = row.status || "Review";
    statusCell.appendChild(status);
    tr.appendChild(statusCell);
    body.appendChild(tr);
  });
}

function statusClass(status) {
  const normalized = String(status || "").toLowerCase();
  if (["ready", "completed", "pass"].includes(normalized)) return "status-ready";
  if (["watch", "running", "queued"].includes(normalized)) return "status-watch";
  return "status-review";
}

function applyEvidenceDrawer(drawer) {
  const title = document.querySelector("[data-evidence-title]");
  if (title && drawer.title) title.textContent = drawer.title;
  document.querySelectorAll("[data-evidence-field]").forEach((node) => {
    const key = node.dataset.evidenceField;
    if (!Object.prototype.hasOwnProperty.call(drawer, key)) return;
    node.textContent = drawer[key] || "";
  });
}

function applyWorkflowRuntime(runtime) {
  if (!runtime || runtime.schema !== "PFIOSPhaseCWorkflowRuntimeReadModelV1") return;
  const rows = runtime.task_center_rows || [];
  const list = document.querySelector(".task-list");
  if (list && rows.length > 0) {
    list.replaceChildren();
    rows.slice(0, 6).forEach((row) => {
      const item = document.createElement("li");
      item.dataset.taskState = String(row.status || "review").toLowerCase();
      const title = document.createElement("strong");
      title.textContent = `${row.priority || "P1"} · ${row.object || row.workspace || "Workflow"}`;
      const detail = document.createElement("span");
      detail.textContent = `${row.status || "Review"} · ${row.action || ""}`;
      item.appendChild(title);
      item.appendChild(detail);
      list.appendChild(item);
    });
  }
  const jobLabel = document.querySelector("#background-job-label");
  if (jobLabel && runtime.fast_path) {
    jobLabel.textContent = `Fast Path ${runtime.fast_path.status || "Review"} · target ${runtime.fast_path.target_seconds || 60}s · estimated ${runtime.fast_path.estimated_seconds || 0}s`;
  }
}

function setPressedFeedback(element) {
  const startedAt = performance.now();
  element.dataset.feedback = "pressed";
  element.setAttribute("aria-busy", "true");
  requestAnimationFrame(() => {
    element.classList.add("is-pressed");
    if (performance.now() - startedAt <= FEEDBACK_SLA_MS.instant) {
      element.dataset.feedbackSla = "instant";
    }
  });
  window.setTimeout(() => {
    element.classList.remove("is-pressed");
    element.removeAttribute("aria-busy");
  }, 120);
}

function setActiveWorkspace(workspaceId) {
  const workspace = WORKSPACES[workspaceId] || WORKSPACES.home;
  const shell = document.querySelector(".app-shell");
  const main = document.querySelector("#main-workspace");
  const title = document.querySelector("#workspace-title");
  const kicker = document.querySelector("#workspace-kicker");
  const conclusion = document.querySelector("#workspace-conclusion");

  document.querySelectorAll("[data-workspace]").forEach((button) => {
    const active = button.dataset.workspace === workspaceId;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-current", active ? "page" : "false");
  });

  title.textContent = workspace.label;
  kicker.textContent = workspace.kicker;
  conclusion.textContent = workspace.conclusion;
  main.dataset.activeWorkspace = workspaceId;
  shell.dataset.state = "ready";
  writeContext({ ...currentContext(), workspace: workspaceId });
  showToast(`${workspace.label} ready from cached shell`);
  main.focus({ preventScroll: true });
}

function openCommandPalette() {
  const dialog = document.querySelector("[data-command-palette]");
  const input = document.querySelector("[data-command-input]");
  if (!dialog) return;
  if (typeof dialog.showModal === "function") {
    dialog.showModal();
  } else {
    dialog.setAttribute("open", "");
  }
  if (input) input.focus();
}

function closeCommandPalette() {
  const dialog = document.querySelector("[data-command-palette]");
  if (!dialog) return;
  if (typeof dialog.close === "function") {
    dialog.close();
  } else {
    dialog.removeAttribute("open");
  }
}

function setEvidenceDrawer(open) {
  const drawer = document.querySelector("[data-evidence-drawer]");
  if (!drawer) return;
  drawer.classList.toggle("is-open", open);
  drawer.setAttribute("aria-expanded", open ? "true" : "false");
}

function toggleTaskCenter() {
  const taskCenter = document.querySelector("[data-task-center]");
  if (!taskCenter) return;
  taskCenter.toggleAttribute("hidden");
}

function runCachedRefresh() {
  const skeleton = document.querySelector("[data-skeleton]");
  const errorBanner = document.querySelector("[data-error-banner]");
  const taskPhase = document.querySelector("#task-phase");
  const jobLabel = document.querySelector("#background-job-label");
  if (errorBanner) errorBanner.hidden = true;

  window.setTimeout(() => {
    if (skeleton) skeleton.hidden = false;
  }, FEEDBACK_SLA_MS.skeleton);

  window.setTimeout(() => {
    if (taskPhase) taskPhase.textContent = "Step 2 of 3 · loading cached evidence";
  }, FEEDBACK_SLA_MS.stepped);

  window.setTimeout(() => {
    if (jobLabel) jobLabel.textContent = `Background job PFI-${Date.now()} · safe to leave this page`;
  }, FEEDBACK_SLA_MS.background);

  window.setTimeout(() => {
    if (skeleton) skeleton.hidden = true;
    if (taskPhase) taskPhase.textContent = "Step 3 of 3 · cached slice ready";
    showToast("Cached slice updated");
  }, 1350);
}

function showRecoverableError() {
  const errorBanner = document.querySelector("[data-error-banner]");
  if (!errorBanner) return;
  errorBanner.hidden = false;
  showToast("Cached fallback is active");
}

function drawSparkline() {
  const canvas = document.querySelector("#market-sparkline");
  if (!canvas || !canvas.getContext) return;
  const ctx = canvas.getContext("2d");
  const points = [22, 28, 24, 36, 34, 43, 39, 48, 45, 58, 52, 63, 59, 67];
  const width = canvas.width;
  const height = canvas.height;
  const step = width / (points.length - 1);
  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--pfi-surface-muted").trim() || "#eef2f4";
  ctx.fillRect(0, 0, width, height);
  ctx.strokeStyle = getComputedStyle(document.documentElement).getPropertyValue("--pfi-blue").trim() || "#215f9a";
  ctx.lineWidth = 3;
  ctx.beginPath();
  points.forEach((point, index) => {
    const x = index * step;
    const y = height - 18 - point;
    if (index === 0) {
      ctx.moveTo(x, y);
    } else {
      ctx.lineTo(x, y);
    }
  });
  ctx.stroke();
  ctx.fillStyle = getComputedStyle(document.documentElement).getPropertyValue("--pfi-teal").trim() || "#0f766e";
  points.forEach((point, index) => {
    ctx.beginPath();
    ctx.arc(index * step, height - 18 - point, 4, 0, Math.PI * 2);
    ctx.fill();
  });
}

function filterRows(value) {
  const query = value.trim().toLowerCase();
  document.querySelectorAll("#decision-rows tr").forEach((row) => {
    row.hidden = query.length > 0 && !row.textContent.toLowerCase().includes(query);
  });
}

function sortRows() {
  const body = document.querySelector("#decision-rows");
  if (!body) return;
  [...body.querySelectorAll("tr")]
    .sort((a, b) => a.cells[0].textContent.localeCompare(b.cells[0].textContent))
    .forEach((row) => body.appendChild(row));
  showToast("Table sorted");
}

function exportRows() {
  const rows = [...document.querySelectorAll("#decision-rows tr")].map((row) => [...row.cells].map((cell) => cell.textContent.trim()));
  const blob = new Blob([JSON.stringify(rows, null, 2)], { type: "application/json" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = "pfi-decision-queue.json";
  link.click();
  URL.revokeObjectURL(link.href);
  showToast("Export prepared");
}

function bindEvents() {
  document.querySelectorAll("[data-workspace]").forEach((button) => {
    button.addEventListener("click", () => {
      setPressedFeedback(button);
      setActiveWorkspace(button.dataset.workspace);
    });
  });

  document.querySelectorAll("[data-context-field]").forEach((field) => {
    field.addEventListener("change", () => writeContext(currentContext()));
    field.addEventListener("input", () => writeContext(currentContext()));
  });

  document.querySelectorAll("[data-command-open]").forEach((button) => {
    button.addEventListener("click", openCommandPalette);
  });

  document.querySelectorAll("[data-command-workspace]").forEach((button) => {
    button.addEventListener("click", () => {
      setActiveWorkspace(button.dataset.commandWorkspace);
      closeCommandPalette();
    });
  });

  document.querySelectorAll("[data-evidence-toggle]").forEach((button) => {
    button.addEventListener("click", () => {
      const drawer = document.querySelector("[data-evidence-drawer]");
      setEvidenceDrawer(!drawer.classList.contains("is-open"));
    });
  });

  document.querySelectorAll("[data-task-toggle]").forEach((button) => {
    button.addEventListener("click", toggleTaskCenter);
  });

  document.querySelector("[data-run-refresh]")?.addEventListener("click", runCachedRefresh);
  document.querySelector("[data-retry]")?.addEventListener("click", runCachedRefresh);
  document.querySelector("[data-cache-fallback]")?.addEventListener("click", showRecoverableError);
  document.querySelector("[data-raw-document]")?.addEventListener("click", () => showToast("Sanitized source record opened"));
  document.querySelector("[data-table-filter]")?.addEventListener("input", (event) => filterRows(event.target.value));
  document.querySelector("[data-table-sort]")?.addEventListener("click", sortRows);
  document.querySelector("[data-table-export]")?.addEventListener("click", exportRows);

  document.addEventListener("keydown", (event) => {
    if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === "k") {
      event.preventDefault();
      openCommandPalette();
    }
    if (event.key === "Escape") {
      closeCommandPalette();
      setEvidenceDrawer(false);
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  restoreContext();
  bindEvents();
  applyHomeSummary(readHomeSummary());
  drawSparkline();
  writeContext({ ...currentContext(), workspace: document.querySelector("#main-workspace").dataset.activeWorkspace });
});
