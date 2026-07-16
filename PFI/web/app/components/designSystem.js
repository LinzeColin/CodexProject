(function installPFIV025Stage8DesignSystem(global) {
  "use strict";

  const ARCHETYPES = Object.freeze({
    home: "status_board",
    accounts: "balance_sheet",
    ledger: "review_table",
    investment: "portfolio_analytics",
    consumption: "spending_flow",
    sync: "data_pipeline",
    recommendations: "decision_inbox",
    insights: "report_library",
    market_research: "research_workspace",
    settings: "control_center",
  });

  const CHART_STATE_LABELS = Object.freeze({
    empty: "暂无真实趋势数据，不绘制曲线",
    error: "趋势数据读取失败，请先处理错误",
    stale: "趋势数据已过期，请核对更新时间",
    ready: "真实趋势数据已加载",
  });

  function currentChartState(panel, empty) {
    const explicit = String(panel?.dataset.stage8RequestedChartState || "").trim();
    if (Object.prototype.hasOwnProperty.call(CHART_STATE_LABELS, explicit)) return explicit;
    const source = String(panel?.dataset.trendSource || "").toLowerCase();
    const errorVisible = document.querySelector("[data-error-banner]:not([hidden])");
    if (errorVisible || /error|失败|不可用/.test(source)) return "error";
    if (!empty?.hidden) return "empty";
    if (/stale|expired|过期|陈旧/.test(source)) return "stale";
    return "ready";
  }

  function syncChartState() {
    const panel = document.querySelector("[data-trend-panel]");
    const canvas = panel?.querySelector("[data-trend-canvas]");
    const empty = panel?.querySelector("[data-trend-empty]");
    const legend = panel?.querySelector("[data-trend-legend]");
    if (!panel || !canvas || !empty || !legend) return null;

    empty.id = empty.id || "pfi-stage8-trend-empty";
    legend.id = legend.id || "pfi-stage8-trend-legend";
    let status = panel.querySelector("[data-stage8-chart-status]");
    if (!status) {
      status = document.createElement("p");
      status.className = "stage8-chart-status";
      status.dataset.stage8ChartStatus = "true";
      status.id = "pfi-stage8-trend-state";
      status.setAttribute("aria-live", "polite");
      panel.appendChild(status);
    }

    const state = currentChartState(panel, empty);
    if (panel.dataset.stage8ChartState !== state) panel.dataset.stage8ChartState = state;
    if (status.textContent !== CHART_STATE_LABELS[state]) status.textContent = CHART_STATE_LABELS[state];
    if (status.dataset.state !== state) status.dataset.state = state;
    const canvasShouldBeHidden = state === "empty" || state === "error";
    if (canvas.hidden !== canvasShouldBeHidden) canvas.hidden = canvasShouldBeHidden;
    canvas.setAttribute("role", "img");
    canvas.setAttribute("aria-describedby", `${legend.id} ${empty.id} ${status.id}`);
    const title = panel.querySelector("[data-trend-title]")?.textContent?.trim() || "趋势图";
    const scope = panel.querySelector("[data-trend-scope]")?.textContent?.trim() || "当前工作区";
    const detail = state === "ready" ? "数值同时通过图例和端点标签表达。" : CHART_STATE_LABELS[state];
    canvas.setAttribute("aria-label", `${scope}，${title}。${detail}`);
    panel.setAttribute("aria-label", `${scope}，${CHART_STATE_LABELS[state]}`);
    return state;
  }

  function syncWorkspaceArchetype() {
    const main = document.querySelector("#main-workspace");
    if (!main) return null;
    const workspace = String(main.dataset.activeWorkspace || "home");
    const archetype = ARCHETYPES[workspace] || ARCHETYPES.home;
    if (main.dataset.stage8Archetype !== archetype) main.dataset.stage8Archetype = archetype;
    document.body.dataset.stage8ActiveWorkspace = workspace;
    return { workspace, archetype };
  }

  function ensureMobileNavigation() {
    const shell = document.querySelector(".app-shell");
    if (!shell) return null;
    let navigation = shell.querySelector("[data-stage8-mobile-primary]");
    if (!navigation) {
      const primaryEntries = [...document.querySelectorAll('[data-primary-entry="true"]')];
      navigation = document.createElement("nav");
      navigation.className = "mobile-bottom-nav";
      navigation.dataset.stage8MobilePrimary = String(primaryEntries.length);
      navigation.setAttribute("aria-label", "移动端一级工作区");
      primaryEntries.forEach((entry) => {
        const button = document.createElement("button");
        const icon = document.createElement("span");
        const label = document.createElement("span");
        button.type = "button";
        button.className = "mobile-tab";
        button.dataset.stage8MobileWorkspace = entry.dataset.workspace || "";
        button.dataset.routeAlias = entry.dataset.routeAlias || "";
        icon.textContent = entry.dataset.navIcon || "•";
        icon.setAttribute("aria-hidden", "true");
        label.textContent = entry.textContent?.trim() || entry.dataset.workspace || "工作区";
        button.append(icon, label);
        button.addEventListener("click", () => entry.click());
        navigation.appendChild(button);
      });
      shell.appendChild(navigation);
    }
    const activeWorkspace = document.querySelector("#main-workspace")?.dataset.activeWorkspace || "home";
    navigation.querySelectorAll("[data-stage8-mobile-workspace]").forEach((button) => {
      const active = button.dataset.stage8MobileWorkspace === activeWorkspace;
      button.classList.toggle("is-active", active);
      button.setAttribute("aria-current", active ? "page" : "false");
    });
    return navigation;
  }

  function sync() {
    return {
      workspace: syncWorkspaceArchetype(),
      chartState: syncChartState(),
      mobileNavigation: ensureMobileNavigation(),
    };
  }

  function observe() {
    const main = document.querySelector("#main-workspace");
    const panel = document.querySelector("[data-trend-panel]");
    let syncScheduled = false;
    const observer = new MutationObserver(() => {
      if (syncScheduled) return;
      syncScheduled = true;
      queueMicrotask(() => {
        syncScheduled = false;
        sync();
      });
    });
    if (main) observer.observe(main, { attributes: true, attributeFilter: ["data-active-workspace"] });
    if (panel) {
      observer.observe(panel, {
        attributes: true,
        attributeFilter: ["data-trend-source", "data-stage8-requested-chart-state"],
        childList: true,
        subtree: true,
      });
    }
    return observer;
  }

  const api = Object.freeze({
    schema: "PFIV025Stage8Phase81DesignSystemV1",
    phase: "8.1",
    archetypes: ARCHETYPES,
    chartStates: Object.freeze(Object.keys(CHART_STATE_LABELS)),
    sync,
  });
  global.PFI_V025_STAGE8_DESIGN_SYSTEM = api;

  const initialize = () => {
    sync();
    observe();
  };
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initialize, { once: true });
  } else {
    initialize();
  }
})(window);
