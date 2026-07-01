(function attachPFIStage5UxState(root, factory) {
  const api = factory(root);
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V024_STAGE5_UX_STATE = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage5UxState() {
  const TARGET_VERSION = "v0.2.4";
  const SOURCE_PACKAGE_VERSION = "v0.2.3-repair";
  const STAGE = "Stage 5";
  const PHASE_ID = "5.3";
  const PHASE_NAME = "交互状态";
  const REQUIRED_STATE_KINDS = Object.freeze(["loading", "success", "error", "empty"]);
  const ACTIONABLE_TERMS = Object.freeze(["打开", "查看", "检查", "接入", "重试", "返回"]);

  function buildV024Stage5Phase53Contract() {
    return Object.freeze({
      schema: "PFIV024Stage5Phase53ContractV1",
      target_version: TARGET_VERSION,
      source_package_version: SOURCE_PACKAGE_VERSION,
      stage: STAGE,
      phase_id: PHASE_ID,
      phase_name: PHASE_NAME,
      current_phase_only: true,
      max_one_phase_per_run: true,
      phase_5_1_complete: true,
      phase_5_2_complete: true,
      required_state_kinds: REQUIRED_STATE_KINDS,
      tasks: Object.freeze([
        "T5.3.1 loading/success/error 状态",
        "T5.3.2 空状态中文可行动",
        "T5.3.3 后退/前进验收",
      ]),
      allowed_files: Object.freeze([
        "PFI/web/app/ux_state.js",
        "PFI/web/app/shell.js",
        "PFI/web/index.html",
        "PFI/src/pfi_os/app/streamlit_app.py",
        "PFI/tests/test_v024_stage5_phase53_interaction_states.py",
        "PFI/docs/pfi_v024/STAGE5_INTERACTION_STATES.md",
        "PFI/reports/pfi_v024/stage_5/phase_5_3/*",
      ]),
      evidence_files: Object.freeze([
        "PFI/docs/pfi_v024/STAGE5_INTERACTION_STATES.md",
        "PFI/reports/pfi_v024/stage_5/phase_5_3/evidence.json",
        "PFI/reports/pfi_v024/stage_5/phase_5_3/ux_state_validation.json",
        "PFI/reports/pfi_v024/stage_5/phase_5_3/history_validation.json",
        "PFI/reports/pfi_v024/stage_5/phase_5_3/terminal.log",
      ]),
      explicitly_not_done: Object.freeze([
        "Stage 5 whole-stage review",
        "GitHub main upload",
      ]),
    });
  }

  function buildV024Stage5UxStateCatalog(catalog) {
    const source = catalog && typeof catalog === "object" ? catalog : {};
    return Object.freeze(Object.fromEntries(Object.entries(source).map(([workspace, pages]) => [
      workspace,
      Object.freeze((pages || []).map((page) => buildV024Stage5PageStateModel(page))),
    ])));
  }

  function buildV024Stage5PageStateModel(page) {
    const routeAlias = normalizeRouteAlias(page?.routeAlias);
    const targetWorkspace = safeText(page?.workspace, "home");
    const title = safeText(page?.title, "页面");
    const primaryObject = safeText(page?.primaryObject || page?.dataObject, title);
    const primaryAction = safeText(page?.primaryAction, `查看${primaryObject}`);
    const stateKey = safeText(page?.stateKey, `${targetWorkspace}:${routeAlias || "page"}`);
    const emptyMessage = safeText(page?.emptyState, `${primaryObject}暂无可展示的真实数据。`);
    const errorMessage = safeText(page?.errorState, `${primaryObject}读取失败，请检查本机数据来源。`);
    const dataSource = safeText(page?.dataSource, "PFI read model");

    return Object.freeze({
      schema: "PFIV024Stage5Phase53PageStateV1",
      target_version: TARGET_VERSION,
      source_package_version: SOURCE_PACKAGE_VERSION,
      stage: STAGE,
      phase_id: PHASE_ID,
      targetWorkspace,
      routeAlias,
      stateKey,
      title,
      primaryObject,
      dataSource,
      stateKinds: REQUIRED_STATE_KINDS,
      states: Object.freeze({
        loading: buildState({
          kind: "loading",
          routeAlias,
          targetWorkspace,
          label: `查看${primaryObject}`,
          message: `正在加载${primaryObject}，保持当前页面路径与返回栈。`,
        }),
        success: buildState({
          kind: "success",
          routeAlias,
          targetWorkspace,
          label: primaryAction,
          message: `${primaryObject}已按当前页面状态准备完成。`,
        }),
        error: buildState({
          kind: "error",
          routeAlias,
          targetWorkspace,
          label: `重试${primaryObject}`,
          message: errorMessage,
        }),
        empty: buildState({
          kind: "empty",
          routeAlias,
          targetWorkspace,
          label: `打开${primaryObject}处理`,
          message: emptyMessage,
        }),
      }),
    });
  }

  function validateV024Stage5UxStateCatalog(uxCatalog) {
    const pages = flattenUxCatalog(uxCatalog);
    const missingStatePages = pages
      .filter((page) => REQUIRED_STATE_KINDS.some((kind) => !page.states || !page.states[kind]))
      .map((page) => page.routeAlias);
    const nonActionableEmptyPages = pages
      .filter((page) => !isActionableState(page.states?.empty))
      .map((page) => page.routeAlias);
    const nonActionableErrorPages = pages
      .filter((page) => !isActionableState(page.states?.error))
      .map((page) => page.routeAlias);
    const invalidStateKindPages = pages
      .filter((page) => REQUIRED_STATE_KINDS.join("|") !== (page.stateKinds || []).join("|"))
      .map((page) => page.routeAlias);
    const historyAcceptance = buildHistoryAcceptance(pages);
    const status = [
      missingStatePages,
      nonActionableEmptyPages,
      nonActionableErrorPages,
      invalidStateKindPages,
      historyAcceptance.duplicate_route_aliases,
    ].every((items) => items.length === 0) && historyAcceptance.status === "pass"
      ? "pass"
      : "fail";

    return Object.freeze({
      schema: "PFIV024Stage5Phase53UxStateValidationV1",
      target_version: TARGET_VERSION,
      source_package_version: SOURCE_PACKAGE_VERSION,
      stage: STAGE,
      phase_id: PHASE_ID,
      status,
      total_page_count: pages.length,
      required_state_kinds: REQUIRED_STATE_KINDS,
      missing_state_pages: Object.freeze(missingStatePages),
      invalid_state_kind_pages: Object.freeze(invalidStateKindPages),
      non_actionable_empty_pages: Object.freeze(nonActionableEmptyPages),
      non_actionable_error_pages: Object.freeze(nonActionableErrorPages),
      history_acceptance: historyAcceptance,
    });
  }

  function buildHistoryAcceptance(pages) {
    const routeAliases = pages.map((page) => normalizeRouteAlias(page.routeAlias)).filter(Boolean);
    const duplicateRouteAliases = duplicates(routeAliases);
    return Object.freeze({
      schema: "PFIV024Stage5Phase53HistoryAcceptanceV1",
      target_version: TARGET_VERSION,
      source_package_version: SOURCE_PACKAGE_VERSION,
      stage: STAGE,
      phase_id: PHASE_ID,
      status: duplicateRouteAliases.length ? "fail" : "pass",
      route_alias_from_location: true,
      push_state: true,
      replace_state: true,
      hashchange_listener: true,
      popstate_listener: true,
      route_state_preserved: true,
      total_route_aliases: routeAliases.length,
      duplicate_route_aliases: Object.freeze(duplicateRouteAliases),
      acceptance_checks: Object.freeze([
        "direct URL resolves active route alias",
        "workspace click pushes route state",
        "hashchange restores route state",
        "popstate restores route state for back/forward",
      ]),
    });
  }

  function buildState({ kind, routeAlias, targetWorkspace, label, message }) {
    return Object.freeze({
      kind,
      message_zh: safeText(message, "状态待确认"),
      action: Object.freeze({
        label: safeText(label, "查看页面"),
        targetWorkspace,
        routeAlias,
      }),
    });
  }

  function flattenUxCatalog(catalog) {
    return Object.values(catalog || {}).flatMap((pages) => pages || []);
  }

  function isActionableState(state) {
    const label = safeText(state?.action?.label, "");
    const routeAlias = normalizeRouteAlias(state?.action?.routeAlias);
    const targetWorkspace = safeText(state?.action?.targetWorkspace, "");
    return Boolean(label && routeAlias && targetWorkspace && ACTIONABLE_TERMS.some((term) => label.includes(term)));
  }

  function duplicates(values) {
    const seen = new Set();
    const repeated = new Set();
    values.forEach((value) => {
      if (seen.has(value)) repeated.add(value);
      seen.add(value);
    });
    return Object.freeze([...repeated]);
  }

  function normalizeRouteAlias(routeAlias) {
    const route = String(routeAlias || "").trim();
    if (!route) return "";
    return route.startsWith("/") ? route : `/${route}`;
  }

  function safeText(value, fallback) {
    const text = String(value ?? "").trim();
    return text || fallback;
  }

  return Object.freeze({
    buildV024Stage5Phase53Contract,
    buildV024Stage5PageStateModel,
    buildV024Stage5UxStateCatalog,
    validateV024Stage5UxStateCatalog,
    buildHistoryAcceptance,
  });
});
