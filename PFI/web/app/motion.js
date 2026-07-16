(() => {
  "use strict";

  const feedbackBudgetMs = Object.freeze({
    instant: 100,
    cached: 300,
    staged: 1000,
    durable: 10000,
  });
  const contract = Object.freeze({
    schema: "PFIV025Stage8Phase82MotionContractV1",
    targetVersion: "v0.2.5",
    stage: "Stage 8",
    phase: "8.2",
    feedbackBudgetMs,
    stateMotionMs: 180,
    maxMotionMs: 220,
    animatedProperties: Object.freeze(["transform", "opacity"]),
    viewTransitionMode: "progressive_enhancement",
    reducedMotionMode: "zero_duration_state_preserving",
  });
  const media = typeof window.matchMedia === "function"
    ? window.matchMedia("(prefers-reduced-motion: reduce)")
    : { matches: false, addEventListener: () => {} };
  let motionEnabled = true;
  let lastRouteSignature = "";

  function reducedMotionActive() {
    return !motionEnabled || media.matches || document.body?.classList.contains("reduce-motion") === true;
  }

  function classifyElapsed(value) {
    const elapsed = Math.max(0, Number(value) || 0);
    if (elapsed <= feedbackBudgetMs.instant) return "instant";
    if (elapsed <= feedbackBudgetMs.cached) return "cached";
    if (elapsed < feedbackBudgetMs.staged) return "skeleton";
    if (elapsed < feedbackBudgetMs.durable) return "staged";
    return "durable";
  }

  function stateFrames(state) {
    if (state === "pressed") return [{ transform: "scale(0.985)", opacity: 0.94 }, { transform: "scale(1)", opacity: 1 }];
    if (state === "failure" || state === "error" || state === "blocked") {
      return [{ transform: "translate3d(0, -2px, 0)", opacity: 0.72 }, { transform: "translate3d(0, 0, 0)", opacity: 1 }];
    }
    return [{ transform: "translate3d(0, 4px, 0)", opacity: 0.72 }, { transform: "translate3d(0, 0, 0)", opacity: 1 }];
  }

  function animateState(element, state = "enter") {
    const duration = reducedMotionActive() ? 0 : Math.min(contract.stateMotionMs, contract.maxMotionMs);
    if (!element) return { status: "skipped", state, duration };
    element.dataset.v025MotionState = state;
    element.dataset.v025MotionDuration = String(duration);
    if (!duration || typeof element.animate !== "function") {
      delete element.dataset.v025MotionActive;
      return { status: duration ? "css_fallback" : "reduced", state, duration };
    }
    element.dataset.v025MotionActive = "true";
    const animation = element.animate(stateFrames(state), {
      duration,
      easing: "cubic-bezier(0.2, 0, 0, 1)",
      fill: "none",
    });
    animation.finished
      .catch(() => undefined)
      .finally(() => { delete element.dataset.v025MotionActive; });
    return { status: "animated", state, duration };
  }

  function transitionRoute(update, target = document.querySelector("#main-workspace")) {
    if (typeof update !== "function") return { status: "skipped" };
    if (!reducedMotionActive() && typeof document.startViewTransition === "function") {
      document.body.dataset.v025ViewTransition = "view_transition";
      return document.startViewTransition(() => update());
    }
    update();
    document.body.dataset.v025ViewTransition = "css_fallback";
    return animateState(target, "route_enter");
  }

  function setEnabled(value) {
    motionEnabled = value !== false;
    if (document.body) {
      document.body.dataset.v025MotionPreference = motionEnabled ? "enabled" : "disabled";
      document.body.dataset.v025ReducedMotion = reducedMotionActive() ? "true" : "false";
    }
    return !reducedMotionActive();
  }

  function observeStateChanges() {
    const main = document.querySelector("#main-workspace");
    const feedback = document.querySelector("[data-action-feedback]");
    const targets = [main, feedback].filter(Boolean);
    if (!targets.length) return null;
    const observer = new MutationObserver((records) => {
      records.forEach((record) => {
        if (record.target === main) {
          const signature = `${main.dataset.activeWorkspace || ""}|${main.dataset.routeAlias || ""}`;
          if (signature && signature !== lastRouteSignature) {
            lastRouteSignature = signature;
            animateState(main, "route_enter");
          }
          return;
        }
        const state = feedback?.dataset.feedbackState || "success";
        animateState(feedback, state);
      });
    });
    if (main) observer.observe(main, { attributes: true, attributeFilter: ["data-active-workspace", "data-route-alias"] });
    if (feedback) observer.observe(feedback, { attributes: true, attributeFilter: ["data-feedback-state", "hidden"] });
    return observer;
  }

  function initialize() {
    document.body.dataset.v025Stage8Motion = "phase_8_2";
    document.body.dataset.v025MotionContract = contract.schema;
    const toggle = document.querySelector('[data-feedback-toggle="motion"]');
    setEnabled(toggle ? Boolean(toggle.checked) : true);
    toggle?.addEventListener("change", () => setEnabled(Boolean(toggle.checked)));
    media.addEventListener?.("change", () => setEnabled(motionEnabled));
    observeStateChanges();
  }

  window.PFI_V025_STAGE8_MOTION = Object.freeze({
    contract,
    animateState,
    classifyElapsed,
    reducedMotionActive,
    setEnabled,
    transitionRoute,
  });

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", initialize, { once: true });
  else initialize();
})();
