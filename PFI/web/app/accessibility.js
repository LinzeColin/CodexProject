(() => {
  "use strict";

  const contract = Object.freeze({
    schema: "PFIV025Stage8Phase83AccessibilityContractV1",
    targetVersion: "v0.2.5",
    stage: "Stage 8",
    phase: "8.3",
    standard: "WCAG 2.2 AA",
    primaryPageCount: 10,
    focusAppearancePx: 3,
    targetSizePx: 44,
    routeAnnouncement: "polite_atomic",
    keyboardRouteFocus: "heading_without_scroll",
    errorPrevention: "financial_data_error_prevention",
  });

  let lastInputModality = "pointer";
  let lastRouteSignature = "";
  let routeAnnouncer = null;

  function setAttributeIfChanged(node, name, value) {
    if (node && node.getAttribute(name) !== value) node.setAttribute(name, value);
  }

  function ensureRouteAnnouncer() {
    routeAnnouncer = document.querySelector("[data-stage8-route-announcer]");
    if (routeAnnouncer) return routeAnnouncer;
    routeAnnouncer = document.createElement("p");
    routeAnnouncer.className = "sr-only";
    routeAnnouncer.dataset.stage8RouteAnnouncer = "phase_8_3";
    routeAnnouncer.id = "pfi-stage8-route-announcer";
    routeAnnouncer.setAttribute("role", "status");
    routeAnnouncer.setAttribute("aria-live", "polite");
    routeAnnouncer.setAttribute("aria-atomic", "true");
    document.body.appendChild(routeAnnouncer);
    return routeAnnouncer;
  }

  function activeHeading() {
    const invalid = document.querySelector("[data-stage6-invalid-route]:not([hidden]) [data-stage6-invalid-route-title]");
    const secondary = document.querySelector("[data-stage6-page-heading]");
    return invalid || secondary || document.querySelector("#workspace-title");
  }

  function focusMainForKeyboardRoute() {
    const heading = activeHeading();
    if (!heading) return false;
    heading.tabIndex = -1;
    if (lastInputModality !== "keyboard") return false;
    heading.focus({ preventScroll: true });
    return document.activeElement === heading;
  }

  function syncCurrentNavigation() {
    document.querySelectorAll("[aria-current]").forEach((node) => {
      if (node.getAttribute("aria-current") === "false") node.removeAttribute("aria-current");
    });
  }

  function syncStatusRegions() {
    const polite = [
      document.querySelector("[data-action-feedback]"),
      document.querySelector("[data-toast]"),
      document.querySelector("[data-source-availability]"),
      document.querySelector("[data-settings-operation-state]"),
      document.querySelector("[data-stage8-job-list]"),
    ].filter(Boolean);
    polite.forEach((node) => {
      setAttributeIfChanged(node, "role", "status");
      setAttributeIfChanged(node, "aria-live", "polite");
      setAttributeIfChanged(node, "aria-atomic", "true");
    });
    [document.querySelector("[data-error-banner]"), document.querySelector("[data-upload-error]")]
      .filter(Boolean)
      .forEach((node) => {
        setAttributeIfChanged(node, "role", "alert");
        setAttributeIfChanged(node, "aria-live", "assertive");
        setAttributeIfChanged(node, "aria-atomic", "true");
      });
    return { polite: polite.length, assertive: 2 };
  }

  function describeControl(control, descriptor, marker) {
    if (!control || !descriptor) return false;
    if (!descriptor.id) descriptor.id = `pfi-stage8-${marker}-description`;
    const existing = new Set(String(control.getAttribute("aria-describedby") || "").split(/\s+/).filter(Boolean));
    existing.add(descriptor.id);
    setAttributeIfChanged(control, "aria-describedby", [...existing].join(" "));
    control.dataset.stage8ErrorPrevention = marker;
    return true;
  }

  function syncFinancialDataErrorPrevention() {
    const importConfirm = document.querySelector("[data-import-confirm]");
    const importStatus = document.querySelector("[data-import-confirm-status]");
    if (importConfirm && importStatus) {
      const previewReady = importStatus.textContent?.trim().startsWith("预览通过") === true;
      importConfirm.disabled = !previewReady;
      setAttributeIfChanged(importConfirm, "aria-disabled", String(!previewReady));
    }
    const bindings = [
      [importConfirm, document.querySelector("[data-upload-preview]"), "import-preview-before-commit"],
      [document.querySelector("[data-holdings-save]"), document.querySelector("[data-holdings-persistence-status]"), "holding-review-before-save"],
      [document.querySelector("[data-holdings-reset]"), document.querySelector("[data-holdings-draft-label]"), "holding-reset-state"],
      [document.querySelector("[data-settings-save]"), document.querySelector("[data-settings-save-status]"), "settings-review-before-save"],
      [document.querySelector("[data-settings-reset]"), document.querySelector("[data-settings-operation-state]"), "settings-reset-state"],
    ];
    return bindings.filter(([control, descriptor, marker]) => describeControl(control, descriptor, marker)).length;
  }

  function syncRouteSemantics({ announce = true } = {}) {
    const main = document.querySelector("#main-workspace");
    const heading = activeHeading();
    if (!main || !heading) return null;
    heading.tabIndex = -1;
    if (!heading.id) heading.id = "pfi-stage8-active-heading";
    setAttributeIfChanged(main, "aria-labelledby", heading.id);
    const route = String(main.dataset.routeAlias || window.location.pathname || "/overview");
    const signature = `${route}|${heading.textContent?.trim() || "PFI"}`;
    if (announce && signature !== lastRouteSignature) {
      lastRouteSignature = signature;
      const announcer = ensureRouteAnnouncer();
      announcer.textContent = `已打开${heading.textContent?.trim() || "PFI 页面"}`;
      window.queueMicrotask(focusMainForKeyboardRoute);
    }
    document.body.dataset.v025Stage8AccessibleRoute = route;
    return { route, heading: heading.textContent?.trim() || "", labelledBy: heading.id };
  }

  function sync() {
    syncCurrentNavigation();
    const statusRegions = syncStatusRegions();
    const errorPreventionBindingCount = syncFinancialDataErrorPrevention();
    const route = syncRouteSemantics();
    const primaryEntryCount = document.querySelectorAll('[data-primary-entry="true"]').length;
    document.body.dataset.v025Stage8Accessibility = "phase_8_3";
    document.body.dataset.v025Stage8PrimaryEntryCount = String(primaryEntryCount);
    document.body.dataset.v025Stage8ErrorPreventionCount = String(errorPreventionBindingCount);
    return { route, statusRegions, errorPreventionBindingCount, primaryEntryCount };
  }

  function auditSnapshot() {
    const main = document.querySelector("#main-workspace");
    const heading = activeHeading();
    return Object.freeze({
      schema: contract.schema,
      standard: contract.standard,
      primaryEntryCount: document.querySelectorAll('[data-primary-entry="true"]').length,
      mainLabelledBy: main?.getAttribute("aria-labelledby") || "",
      activeHeading: heading?.textContent?.trim() || "",
      activeElement: document.activeElement?.id || document.activeElement?.getAttribute?.("data-route-alias") || document.activeElement?.tagName || "",
      lastInputModality,
      statusRegionCount: document.querySelectorAll('[role="status"][aria-live]').length,
      alertRegionCount: document.querySelectorAll('[role="alert"][aria-live]').length,
      errorPreventionBindingCount: document.querySelectorAll("[data-stage8-error-prevention]").length,
    });
  }

  function observe() {
    const main = document.querySelector("#main-workspace");
    if (!main) return null;
    let scheduled = false;
    const observer = new MutationObserver(() => {
      if (scheduled) return;
      scheduled = true;
      window.queueMicrotask(() => {
        scheduled = false;
        sync();
      });
    });
    observer.observe(main, {
      attributes: true,
      attributeFilter: ["data-active-workspace", "data-route-alias", "data-stage6-route-state"],
      childList: true,
      subtree: true,
    });
    return observer;
  }

  function initialize() {
    ensureRouteAnnouncer();
    document.addEventListener("keydown", (event) => {
      if (["Tab", "Enter", " ", "ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(event.key)) {
        lastInputModality = "keyboard";
        document.body.dataset.v025InputModality = "keyboard";
      }
    }, true);
    document.addEventListener("pointerdown", () => {
      lastInputModality = "pointer";
      document.body.dataset.v025InputModality = "pointer";
    }, true);
    sync();
    observe();
  }

  window.PFI_V025_STAGE8_ACCESSIBILITY = Object.freeze({
    contract,
    auditSnapshot,
    focusMainForKeyboardRoute,
    sync,
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
