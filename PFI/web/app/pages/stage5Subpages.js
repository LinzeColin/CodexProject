(function attachPFIStage5Subpages(root, factory) {
  const api = factory(root);
  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  }
  if (root) {
    root.PFI_V024_STAGE5_PAGES = api;
  }
})(typeof window !== "undefined" ? window : globalThis, function buildPFIStage5Subpages(root) {
  const TARGET_VERSION = "v0.2.4";
  const SOURCE_PACKAGE_VERSION = "v0.2.3-repair";
  const STAGE = "Stage 5";
  const PHASE_ID = "5.2";
  const PHASE_NAME = "二级页面差异化";
  const PRIMARY_WORKSPACES = Object.freeze([
    "home",
    "accounts",
    "ledger",
    "investment",
    "consumption",
    "sync",
    "recommendations",
    "insights",
    "market_research",
    "settings",
  ]);
  const DIFFERENTIATION_FIELDS = Object.freeze([
    "routeAlias",
    "stateKey",
    "title",
    "layoutKind",
    "primaryAction",
    "dataObject",
  ]);

  function buildV024Stage5Phase52Contract() {
    return Object.freeze({
      schema: "PFIV024Stage5Phase52ContractV1",
      target_version: TARGET_VERSION,
      source_package_version: SOURCE_PACKAGE_VERSION,
      stage: STAGE,
      phase_id: PHASE_ID,
      phase_name: PHASE_NAME,
      current_phase_only: true,
      max_one_phase_per_run: true,
      phase_5_1_complete: true,
      phase_5_3_started: false,
      primary_entry_count: PRIMARY_WORKSPACES.length,
      min_subpages_per_primary: 3,
      differentiation_fields: DIFFERENTIATION_FIELDS,
      tasks: Object.freeze([
        "T5.2.1 账户二级页面差异化",
        "T5.2.2 投资二级页面差异化",
        "T5.2.3 消费二级页面差异化",
        "T5.2.4 数据源/报告/市场差异化",
      ]),
      allowed_files: Object.freeze([
        "PFI/web/index.html",
        "PFI/web/app/pages/stage5Subpages.js",
        "PFI/web/app/shell.js",
        "PFI/src/pfi_os/app/streamlit_app.py",
        "PFI/tests/test_v024_stage5_phase52_subpage_differentiation.py",
        "PFI/docs/pfi_v024/STAGE5_SUBPAGE_DIFFERENTIATION.md",
        "PFI/reports/pfi_v024/stage_5/phase_5_2/*",
      ]),
      evidence_files: Object.freeze([
        "PFI/docs/pfi_v024/STAGE5_SUBPAGE_DIFFERENTIATION.md",
        "PFI/reports/pfi_v024/stage_5/phase_5_2/evidence.json",
        "PFI/reports/pfi_v024/stage_5/phase_5_2/route_validation.json",
        "PFI/reports/pfi_v024/stage_5/phase_5_2/ux_diff_report.md",
        "PFI/reports/pfi_v024/stage_5/phase_5_2/terminal.log",
      ]),
      explicitly_not_done: Object.freeze([
        "Phase 5.3 交互状态",
        "Stage 5 whole-stage review",
        "GitHub main upload",
      ]),
    });
  }

  function buildV024Stage5Phase52Catalog() {
    const baseCatalog = stage4Catalog();
    return Object.freeze(Object.fromEntries(
      PRIMARY_WORKSPACES.map((workspace) => [
        workspace,
        Object.freeze((baseCatalog[workspace] || []).map((page, index) => normalizeStage5Page(page, workspace, index))),
      ]),
    ));
  }

  function flattenV024Stage5Phase52Pages(catalog = buildV024Stage5Phase52Catalog()) {
    return Object.freeze(PRIMARY_WORKSPACES.flatMap((workspace) => catalog[workspace] || []));
  }

  function validateV024Stage5Phase52Catalog(catalog = buildV024Stage5Phase52Catalog(), stage3SecondaryRoutes = []) {
    const flatPages = flattenV024Stage5Phase52Pages(catalog);
    const stage5Routes = flatPages.map((page) => page.routeAlias);
    const stage5StateKeys = flatPages.map((page) => page.stateKey);
    const stage3Routes = stage3SecondaryRoutes.map((route) => normalizeRouteAlias(route.routeAlias));
    const missingWorkspaces = PRIMARY_WORKSPACES.filter((workspace) => !Array.isArray(catalog[workspace]));
    const workspacesBelowMinimum = PRIMARY_WORKSPACES.filter((workspace) => (catalog[workspace] || []).length < 3);
    const missingStage3SecondaryRoutes = stage3Routes.filter((routeAlias) => !stage5Routes.includes(routeAlias));
    const orphanStage5Routes = stage5Routes.filter((routeAlias) => !stage3Routes.includes(routeAlias));
    const titleOnlyCloneGroups = detectTitleOnlyCloneGroups(catalog);
    const duplicateRouteAliases = duplicates(stage5Routes);
    const duplicateStateKeys = duplicates(stage5StateKeys);
    const workspaceSummaries = Object.freeze(Object.fromEntries(PRIMARY_WORKSPACES.map((workspace) => {
      const pages = catalog[workspace] || [];
      return [workspace, Object.freeze({
        subpage_count: pages.length,
        route_count: uniqueCount(pages.map((page) => page.routeAlias)),
        state_count: uniqueCount(pages.map((page) => page.stateKey)),
        title_count: uniqueCount(pages.map((page) => page.title)),
        layout_count: uniqueCount(pages.map((page) => page.layoutKind)),
        action_count: uniqueCount(pages.map((page) => page.primaryAction)),
        data_object_count: uniqueCount(pages.map((page) => page.dataObject)),
      })];
    })));
    const pass = [
      missingWorkspaces,
      workspacesBelowMinimum,
      missingStage3SecondaryRoutes,
      orphanStage5Routes,
      titleOnlyCloneGroups,
      duplicateRouteAliases,
      duplicateStateKeys,
    ].every((items) => items.length === 0);

    return Object.freeze({
      schema: "PFIV024Stage5Phase52RouteValidationV1",
      target_version: TARGET_VERSION,
      source_package_version: SOURCE_PACKAGE_VERSION,
      stage: STAGE,
      phase_id: PHASE_ID,
      status: pass ? "pass" : "fail",
      primary_entry_count: PRIMARY_WORKSPACES.length,
      workspace_count: Object.keys(catalog).length,
      total_subpage_count: flatPages.length,
      min_subpages_per_primary: Math.min(...PRIMARY_WORKSPACES.map((workspace) => (catalog[workspace] || []).length)),
      differentiation_fields: DIFFERENTIATION_FIELDS,
      workspace_summaries: workspaceSummaries,
      missing_workspaces: missingWorkspaces,
      workspaces_below_minimum: workspacesBelowMinimum,
      duplicate_route_aliases: duplicateRouteAliases,
      duplicate_state_keys: duplicateStateKeys,
      missing_stage3_secondary_routes: missingStage3SecondaryRoutes,
      orphan_stage5_routes: orphanStage5Routes,
      title_only_clone_groups: titleOnlyCloneGroups,
    });
  }

  function normalizeStage5Page(page, workspace, index) {
    const routeAlias = normalizeRouteAlias(page.routeAlias);
    const stateKey = `${workspace}:${routeAlias.replace(/^\//, "").replace(/[^a-zA-Z0-9]+/g, "_").replace(/^_+|_+$/g, "") || index}`;
    const primaryObject = safeText(page.primaryObject, "页面对象");
    const dataObject = safeText(page.dataObject || page.primaryObject, primaryObject);
    return Object.freeze({
      workspace,
      routeAlias,
      stateKey,
      title: safeText(page.title, "二级页面"),
      breadcrumb: Object.freeze([...(page.breadcrumb || [])]),
      layoutKind: safeText(page.layoutKind, `${workspace}-layout-${index + 1}`),
      primaryObject,
      primaryAction: safeText(page.primaryAction, "打开页面"),
      dataObject,
      emptyState: safeText(page.emptyState, "等待真实数据。"),
      errorState: safeText(page.errorState, "无法读取该页面。"),
      dataSource: safeText(page.dataSource, "本机 read-model"),
      sections: Object.freeze((page.sections || []).map((section) => Object.freeze({
        kind: safeText(section.kind, "section"),
        title: safeText(section.title, "页面区域"),
        detail: safeText(section.detail, "等待真实数据。"),
      }))),
      legacyAliases: Object.freeze([...(page.legacyAliases || [])]),
      alternateRoutes: Object.freeze([...(page.alternateRoutes || [])]),
      phase52Differentiated: true,
    });
  }

  function stage4Catalog() {
    const api = stage4Api();
    return {
      ...(api?.stage4ReviewSubpages || {}),
      ...(api?.phase41Subpages || {}),
      ...(api?.phase42Subpages || {}),
      ...(api?.phase43Subpages || {}),
    };
  }

  function stage4Api() {
    if (root && root.PFI_V023_STAGE4_PAGES) return root.PFI_V023_STAGE4_PAGES;
    if (typeof require === "function") {
      try {
        return require("./stage4Subpages.js");
      } catch (_error) {
        return null;
      }
    }
    return null;
  }

  function detectTitleOnlyCloneGroups(catalog) {
    return PRIMARY_WORKSPACES.flatMap((workspace) => {
      const pages = catalog[workspace] || [];
      const groups = new Map();
      pages.forEach((page) => {
        const sectionKinds = (page.sections || []).map((section) => section.kind).join("|");
        const signature = [
          page.layoutKind,
          page.primaryAction,
          page.dataObject,
          page.dataSource,
          sectionKinds,
        ].join("::");
        const items = groups.get(signature) || [];
        items.push(page.routeAlias);
        groups.set(signature, items);
      });
      return [...groups.entries()]
        .filter(([_signature, routes]) => routes.length > 1)
        .map(([signature, routes]) => Object.freeze({ workspace, signature, routes: Object.freeze(routes) }));
    });
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

  function uniqueCount(values) {
    return new Set(values).size;
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
    buildV024Stage5Phase52Contract,
    buildV024Stage5Phase52Catalog,
    flattenV024Stage5Phase52Pages,
    validateV024Stage5Phase52Catalog,
  });
});
