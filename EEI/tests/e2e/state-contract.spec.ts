import { expect, test, type Locator, type Page } from "@playwright/test";

const expectedContext = {
  modelVersion: "business-empire-model-v2",
  profileVersion: "balanced-v2@2",
  dataSnapshot: "fixture-v1",
  scoreSnapshot: "score-fixture-v1"
};

const expectedPreviewContext = {
  modelVersion: "business-empire-model-v2",
  profileVersion: "supply-chain-preview@draft",
  dataSnapshot: "fixture-v1",
  scoreSnapshot: "score-preview-session-v1"
};

const savedViewApiBaseStorageKey = "eei.apiBaseUrl.v1";
const modelApiBaseStorageKey = "eei.modelApiBaseUrl.v1";
const savedViewWorkspaceKey = "mvp";
const savedViewLayout =
  "upstream-left focus-center downstream-right capital-top policy-bottom";

async function expectActiveContext(target: Locator) {
  await expect(target).toHaveAttribute("data-active-model-version", expectedContext.modelVersion);
  await expect(target).toHaveAttribute("data-active-profile-version", expectedContext.profileVersion);
  await expect(target).toHaveAttribute("data-active-data-snapshot", expectedContext.dataSnapshot);
  await expect(target).toHaveAttribute("data-active-score-snapshot", expectedContext.scoreSnapshot);
}

async function expectPreviewContext(target: Locator) {
  await expect(target).toHaveAttribute(
    "data-active-model-version",
    expectedPreviewContext.modelVersion
  );
  await expect(target).toHaveAttribute(
    "data-active-profile-version",
    expectedPreviewContext.profileVersion
  );
  await expect(target).toHaveAttribute(
    "data-active-data-snapshot",
    expectedPreviewContext.dataSnapshot
  );
  await expect(target).toHaveAttribute(
    "data-active-score-snapshot",
    expectedPreviewContext.scoreSnapshot
  );
}

async function expectCloudState(page: Page) {
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Cloud Customer");
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic AI Data Center Campus");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-active-lens", "supply_chain");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L2");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-active-time", "2026-06-12");
}

async function expectWorkspacePath(page: Page, focusKey: string, path: string) {
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-focus-key", focusKey);
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-path", path);
  await expect(page).toHaveURL(new RegExp(`path=${path.replaceAll(".", "\\.")}`));
}

test("stores subject selected node lens time filters and zoom in URL session and reload state", async ({
  page
}) => {
  await page.goto(
    "/?subject=cloud&selected=datacenter&lens=supply_chain&zoom=L2&asOf=2026-06-12&path=nvidia.cloud"
  );

  await expectCloudState(page);
  await expect(page).toHaveURL(/subject=cloud/);
  await expect(page).toHaveURL(/selected=datacenter/);
  await expect(page).toHaveURL(/filters=supply_chain/);
  await expect(page).toHaveURL(/path=nvidia\.cloud/);
  await expect(page.getByTestId("timeline-controls")).toHaveAttribute(
    "data-active-as-of",
    "2026-06-12"
  );

  const sessionState = await page.evaluate(() =>
    JSON.parse(window.sessionStorage.getItem("eei.workspaceState.v1") ?? "{}")
  );
  expect(sessionState).toMatchObject({
    focusKey: "cloud",
    selectedKey: "datacenter",
    activeLens: "supply_chain",
    semanticZoom: "L2",
    asOf: "2026-06-12"
  });

  await page.reload();
  await expectCloudState(page);
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-path-length", "2");
});

test("restores identical subject state through browser back app back and breadcrumb", async ({
  page
}) => {
  await page.goto("/");

  await page.getByRole("button", { name: "以 Synthetic Advanced Foundry 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
  await expectWorkspacePath(page, "foundry", "nvidia.foundry");
  await page.getByRole("button", { name: "以 Synthetic Lithography Equipment Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
  await expectWorkspacePath(page, "equipment", "nvidia.foundry.equipment");

  await page.goBack();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
  await expectWorkspacePath(page, "foundry", "nvidia.foundry");

  await page.goForward();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
  await expectWorkspacePath(page, "equipment", "nvidia.foundry.equipment");

  await page.getByTestId("app-back").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
  await expectWorkspacePath(page, "foundry", "nvidia.foundry");

  await page.getByRole("button", { name: "以 Synthetic Lithography Equipment Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
  await page.getByRole("button", { name: "以 Synthetic Specialty Materials Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Specialty Materials Co."
  );
  await expectWorkspacePath(page, "materials", "nvidia.foundry.equipment.materials");
  await expect(page.getByTestId("breadcrumb-subject-nvidia-0")).toBeVisible();
  await expect(page.getByTestId("breadcrumb-subject-foundry-1")).toBeVisible();
  await expect(page.getByTestId("breadcrumb-subject-equipment-2")).toBeVisible();
  await expect(page.getByTestId("breadcrumb-subject-materials-3")).toBeVisible();

  await page.getByTestId("breadcrumb-subject-foundry-1").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-path-length", "2");
  await expectWorkspacePath(page, "foundry", "nvidia.foundry");
});

test("A048 completes three consecutive semiconductor reroots without fallback", async ({
  page
}) => {
  await page.goto("/");

  await page.getByRole("button", { name: "以 Synthetic Advanced Foundry 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
  await expectWorkspacePath(page, "foundry", "nvidia.foundry");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-reroot-state", "ready");

  await page.getByRole("button", { name: "以 Synthetic Lithography Equipment Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
  await expectWorkspacePath(page, "equipment", "nvidia.foundry.equipment");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-reroot-state", "ready");

  await page.getByRole("button", { name: "以 Synthetic Specialty Materials Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Specialty Materials Co."
  );
  await expectWorkspacePath(page, "materials", "nvidia.foundry.equipment.materials");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-path-length", "4");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-reroot-state", "ready");
  await expect(page.getByTestId("breadcrumb-subject-nvidia-0")).toBeVisible();
  await expect(page.getByTestId("breadcrumb-subject-foundry-1")).toBeVisible();
  await expect(page.getByTestId("breadcrumb-subject-equipment-2")).toBeVisible();
  await expect(page.getByTestId("breadcrumb-subject-materials-3")).toBeVisible();
  await expect(page.getByTestId("graph-node-materials")).toBeVisible();
  await expect(page.getByTestId("transition-fallback")).not.toBeVisible();
});

test("A034 visibly marks cross-industry reroot path from chips to energy", async ({
  page
}) => {
  await page.goto("/");

  await expect(page.getByTestId("cross-industry-reroot-notice")).toHaveAttribute(
    "data-cross-industry",
    "false"
  );
  await expect(page.getByTestId("cross-industry-reroot-notice")).toContainText("Semiconductors");

  await page.getByRole("button", { name: "以 Synthetic Cloud Customer 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Cloud Customer");
  await expectWorkspacePath(page, "cloud", "nvidia.cloud");
  await expect(page.getByTestId("cross-industry-reroot-notice")).toHaveAttribute(
    "data-cross-industry",
    "true"
  );
  await expect(page.getByTestId("cross-industry-reroot-notice")).toHaveAttribute(
    "data-industry-path",
    "semiconductors>ai-cloud"
  );
  await expect(page.getByTestId("cross-industry-reroot-notice")).toContainText(
    "Semiconductors -> AI cloud infrastructure"
  );

  await page.getByRole("button", { name: "以 Synthetic AI Data Center Campus 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic AI Data Center Campus"
  );
  await expectWorkspacePath(page, "datacenter", "nvidia.cloud.datacenter");

  await page.getByRole("button", { name: "以 Synthetic Grid Utility 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Grid Utility");
  await expectWorkspacePath(page, "energy", "nvidia.cloud.datacenter.energy");
  await expect(page.getByTestId("cross-industry-reroot-notice")).toHaveAttribute(
    "data-industry-path",
    "semiconductors>ai-cloud>energy"
  );
  await expect(page.getByTestId("cross-industry-reroot-notice")).toContainText(
    "Semiconductors -> AI cloud infrastructure -> Power and data-center energy"
  );
  await expect(page.getByTestId("cross-industry-reroot-notice")).toContainText(
    "已从 Semiconductors 进入 Power and data-center energy"
  );
  await expect(page.getByTestId("breadcrumb-subject-nvidia-0")).toBeVisible();
  await expect(page.getByTestId("breadcrumb-subject-cloud-1")).toBeVisible();
  await expect(page.getByTestId("breadcrumb-subject-datacenter-2")).toBeVisible();
  await expect(page.getByTestId("breadcrumb-subject-energy-3")).toBeVisible();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-reroot-state", "ready");
});

test("previews model edits across loaded visual modules before global refresh", async ({
  page
}) => {
  await page.goto("/");
  await expectActiveContext(page.getByTestId("workspace-shell"));
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute(
    "data-preview-state",
    "active"
  );
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute(
    "data-preview-scope",
    "workspace,graph-table,saved-view,industry-landscape"
  );

  await page.getByTestId("preview-model-edit").click();
  await expectPreviewContext(page.getByTestId("workspace-shell"));
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute(
    "data-preview-state",
    "preview"
  );
  await expect(page.getByTestId("model-preview-status")).toContainText("Supply chain preview");
  await expect(page.getByTestId("model-contract-state")).toContainText(
    "supply-chain-preview@draft"
  );
  await expect(page.getByTestId("active-context-state")).toContainText("score-preview-session-v1");

  await page.getByTestId("save-current-view").click();
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-profile-version",
    expectedPreviewContext.profileVersion
  );
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-score-snapshot",
    expectedPreviewContext.scoreSnapshot
  );

  await page.goto("/industries");
  await expectPreviewContext(page.getByTestId("industry-landscape-page"));

  await page.goto("/");
  await expectPreviewContext(page.getByTestId("workspace-shell"));
  await page.getByTestId("clear-model-preview").click();
  await expectActiveContext(page.getByTestId("workspace-shell"));
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute(
    "data-preview-state",
    "active"
  );
});

test("A204 and A205 hydrate activate refresh and rollback model context through the server API", async ({
  page
}) => {
  const activeProfile = {
    id: "profile-balanced-v2",
    profile_key: "balanced-v2",
    name: "Balanced v2",
    version: 2,
    model_key: expectedContext.modelVersion,
    active: true,
    reason: "Current active profile"
  };
  const targetProfile = {
    id: "profile-supply-v3",
    profile_key: "supply-chain-v3",
    name: "Supply Chain v3",
    version: 3,
    model_key: "business-empire-model-v3",
    active: false,
    reason: "A204/A205 frontend activation candidate"
  };
  const activeContext = {
    schema_version: "active-analysis-context-v1",
    context_key: "global",
    active_scoring_profile_version_id: activeProfile.id,
    active_data_snapshot_id: null,
    active_data_snapshot_key: expectedContext.dataSnapshot,
    active_scoring_run_id: expectedContext.scoreSnapshot,
    refresh_token: "refresh-token-1",
    refresh_generation: 1,
    status: "active",
    activated_at: "2026-06-20T00:00:00Z",
    activated_by: "system",
    affected_modules: ["business_empire", "supply_chain", "model_center"],
    model_version: expectedContext.modelVersion,
    profile_version: expectedContext.profileVersion,
    client_state: "current",
    stale_client_semantics: "clients compare refresh_token and refresh_generation",
    metadata: { source: "test" }
  };
  const activatedContext = {
    ...activeContext,
    active_scoring_profile_version_id: targetProfile.id,
    active_data_snapshot_key: "fixture-v2",
    active_scoring_run_id: "score-live-v2",
    refresh_token: "refresh-token-2",
    refresh_generation: 2,
    model_version: "business-empire-model-v3",
    profile_version: "supply-chain-v3@3",
    client_state: "stale"
  };
  const rollbackContext = {
    ...activeContext,
    refresh_token: "refresh-token-3",
    refresh_generation: 3,
    client_state: "stale"
  };
  let currentContext = activeContext;
  let activatePayload: Record<string, unknown> | undefined;
  let rollbackPayload: Record<string, unknown> | undefined;

  await page.route("https://model.eei.test/v1/scoring/active-context**", async (route) => {
    const requestUrl = new URL(route.request().url());
    const clientToken = requestUrl.searchParams.get("client_refresh_token");
    await route.fulfill({
      contentType: "application/json",
      status: 200,
      body: JSON.stringify({
        ...currentContext,
        client_state:
          clientToken && clientToken !== currentContext.refresh_token ? "stale" : "current"
      })
    });
  });
  await page.route("https://model.eei.test/v1/scoring/profiles", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      status: 200,
      body: JSON.stringify([activeProfile, targetProfile])
    });
  });
  await page.route("https://model.eei.test/v1/scoring/profiles/*/activate", async (route) => {
    const requestUrl = new URL(route.request().url());
    const profileId = requestUrl.pathname.split("/").at(-2);
    if (profileId === targetProfile.id) {
      activatePayload = route.request().postDataJSON() as Record<string, unknown>;
      currentContext = activatedContext;
      await route.fulfill({
        contentType: "application/json",
        status: 200,
        body: JSON.stringify({
          schema_version: "model-activation-v1",
          status: "activated",
          previous_profile: activeProfile,
          activated_profile: { ...targetProfile, active: true },
          active_context: activatedContext,
          cache_invalidation: {
            previous_refresh_token: "refresh-token-1",
            refresh_token: "refresh-token-2",
            refresh_generation: 2,
            stale_client_semantics: "clients refetch"
          }
        })
      });
      return;
    }
    rollbackPayload = route.request().postDataJSON() as Record<string, unknown>;
    currentContext = rollbackContext;
    await route.fulfill({
      contentType: "application/json",
      status: 200,
      body: JSON.stringify({
        schema_version: "model-activation-v1",
        status: "activated",
        previous_profile: { ...targetProfile, active: true },
        activated_profile: activeProfile,
        active_context: rollbackContext,
        cache_invalidation: {
          previous_refresh_token: "refresh-token-2",
          refresh_token: "refresh-token-3",
          refresh_generation: 3,
          stale_client_semantics: "clients refetch"
        }
      })
    });
  });
  await page.addInitScript(
    ({ storageKey, apiBase }: { storageKey: string; apiBase: string }) =>
      window.localStorage.setItem(storageKey, apiBase),
    { storageKey: modelApiBaseStorageKey, apiBase: "https://model.eei.test" }
  );

  await page.goto("/");
  await expect(page.getByTestId("model-activation-status")).toHaveText("server-current");
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute(
    "data-model-sync-mode",
    "server"
  );
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute(
    "data-active-profile-id",
    activeProfile.id
  );
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute(
    "data-target-profile-id",
    targetProfile.id
  );

  await page.getByTestId("activate-model-profile").click();
  await expect(page.getByTestId("model-activation-status")).toHaveText("server-activated");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-model-version",
    "business-empire-model-v3"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-profile-version",
    "supply-chain-v3@3"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-score-snapshot",
    "score-live-v2"
  );
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute(
    "data-model-refresh-generation",
    "2"
  );
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute(
    "data-rollback-profile-id",
    activeProfile.id
  );
  expect(activatePayload).toMatchObject({
    expected_active_profile_version_id: activeProfile.id,
    client_refresh_token: "refresh-token-1"
  });

  await page.getByTestId("check-model-refresh").click();
  await expect(page.getByTestId("model-activation-status")).toHaveText("server-refreshed");
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute("data-client-state", "stale");
  await expect(page.getByTestId("model-preview-panel")).toHaveAttribute(
    "data-model-sync-reason",
    "stale_client_refetched"
  );

  await page.getByTestId("rollback-model-activation").click();
  await expect(page.getByTestId("model-activation-status")).toHaveText("server-activated");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-profile-version",
    expectedContext.profileVersion
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-score-snapshot",
    expectedContext.scoreSnapshot
  );
  expect(rollbackPayload).toMatchObject({
    expected_active_profile_version_id: targetProfile.id,
    client_refresh_token: "refresh-token-2"
  });
});

test("saves versioned views restores deterministically and shows as-of change overlays", async ({
  page
}) => {
  await page.goto(
    "/?subject=cloud&selected=datacenter&lens=supply_chain&zoom=L2&asOf=2026-06-12&path=nvidia.cloud"
  );

  await expectCloudState(page);
  await expect(page.getByTestId("change-overlay")).toHaveAttribute(
    "data-timeline-mode",
    "as-of-snapshot"
  );
  await expect(page.getByTestId("change-overlay")).toContainText("As of 2026-06-12");
  await expect(page.getByTestId("change-overlay")).toContainText("not real-time");

  await page.getByTestId("save-current-view").click();
  await expect(page.getByTestId("saved-view-status")).toHaveText("local-saved");
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-saved-view-version",
    "saved-view-v1"
  );
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-api-base-storage-key",
    savedViewApiBaseStorageKey
  );
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-workspace-key",
    savedViewWorkspaceKey
  );
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-sync-mode",
    "local_fallback"
  );
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-sync-reason",
    "api_base_missing"
  );
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-saved-view-id",
    "sv-cloud-supply_chain-L2-2026-06-12"
  );

  await page.getByTestId("timeline-2026-06-01").click();
  await page.getByTestId("lens-policy_risk").click();
  await page.getByRole("button", { name: "回到 NVIDIA" }).click();
  await page.reload();

  await page.getByTestId("restore-saved-view").click();
  await expectCloudState(page);
  await expect(page.getByTestId("saved-view-status")).toHaveText("local-restored");
  await expect(page.getByTestId("saved-view-contract")).toContainText("Synthetic Cloud Customer");
  await expect(page.getByTestId("saved-view-contract")).toContainText("supply_chain / 2026-06-12");
  await expect(page.getByTestId("saved-view-contract")).toContainText(
    savedViewLayout
  );
  await expect(page.getByTestId("saved-view-contract")).toContainText(
    "Synthetic Cloud Customer / supply_chain / 2026-06-12"
  );
});

test("A207 saves and restores saved views through the configured server API", async ({
  page
}) => {
  const serverRecord = {
    id: "server-sv-cloud",
    name: "Synthetic Cloud Customer / supply_chain / 2026-06-12",
    workspace_key: savedViewWorkspaceKey,
    state: {
      local_id: "sv-cloud-supply_chain-L2-2026-06-12",
      focus_key: "cloud",
      selected_key: "datacenter",
      path: ["nvidia", "cloud"],
      visual_lens: "supply_chain",
      semantic_zoom: "L2",
      as_of: "2026-06-12",
      filters: "supply_chain",
      layout: savedViewLayout,
      model_version: expectedContext.modelVersion,
      profile_version: expectedContext.profileVersion,
      data_snapshot: expectedContext.dataSnapshot,
      score_snapshot: expectedContext.scoreSnapshot,
      notes: "Synthetic Cloud Customer / supply_chain / 2026-06-12"
    },
    schema_version: "saved-view-v1",
    current_version: 1,
    version_count: 1,
    updated_at: "2026-06-20T00:00:00Z",
    metadata: {
      source: "eei-web",
      workspace_key: savedViewWorkspaceKey
    }
  };

  let savePayload: Record<string, unknown> | undefined;
  await page.route("https://eei.test/v1/saved-views", async (route) => {
    expect(route.request().method()).toBe("POST");
    savePayload = route.request().postDataJSON() as Record<string, unknown>;
    await route.fulfill({
      contentType: "application/json",
      status: 201,
      body: JSON.stringify(serverRecord)
    });
  });
  await page.route("https://eei.test/v1/saved-views/server-sv-cloud", async (route) => {
    expect(route.request().method()).toBe("GET");
    await route.fulfill({
      contentType: "application/json",
      status: 200,
      body: JSON.stringify(serverRecord)
    });
  });
  await page.addInitScript(
    ({ storageKey, apiBase }: { storageKey: string; apiBase: string }) =>
      window.localStorage.setItem(storageKey, apiBase),
    { storageKey: savedViewApiBaseStorageKey, apiBase: "https://eei.test" }
  );

  await page.goto(
    "/?subject=cloud&selected=datacenter&lens=supply_chain&zoom=L2&asOf=2026-06-12&path=nvidia.cloud"
  );
  await expectCloudState(page);

  await page.getByTestId("save-current-view").click();
  await expect(page.getByTestId("saved-view-status")).toHaveText("server-saved");
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute("data-sync-mode", "server");
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute("data-sync-reason", "ok");
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-server-id",
    "server-sv-cloud"
  );
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute("data-server-version", "1");
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-server-endpoint",
    "https://eei.test/v1/saved-views"
  );

  expect(savePayload).toMatchObject({
    workspace_key: savedViewWorkspaceKey,
    schema_version: "saved-view-v1"
  });
  expect(savePayload?.state).toMatchObject({
    focus_key: "cloud",
    selected_key: "datacenter",
    visual_lens: "supply_chain",
    semantic_zoom: "L2",
    as_of: "2026-06-12",
    model_version: expectedContext.modelVersion,
    profile_version: expectedContext.profileVersion
  });

  await page.getByTestId("timeline-2026-06-01").click();
  await page.getByTestId("lens-policy_risk").click();
  await page.getByRole("button", { name: "回到 NVIDIA" }).click();
  await page.getByTestId("restore-saved-view").click();

  await expectCloudState(page);
  await expect(page.getByTestId("saved-view-status")).toHaveText("server-restored");
  await expect(page.getByTestId("saved-view-panel")).toHaveAttribute("data-sync-mode", "server");
  await expect(page.getByTestId("saved-view-contract")).toContainText(
    "Synthetic Cloud Customer / supply_chain / 2026-06-12"
  );
});

test("reports one active model profile data and score snapshot across visible modules", async ({
  page
}) => {
  await page.goto("/");
  await expectActiveContext(page.getByTestId("workspace-shell"));
  await expect(page.getByTestId("model-contract-state")).toContainText(
    "formula-registry-v4.2"
  );
  await expect(page.getByTestId("model-contract-state")).toContainText(
    "parameter-catalog-v4.2"
  );
  await expect(page.getByTestId("model-contract-state")).toContainText(
    "threshold-registry-v4.2"
  );

  await page.goto("/industries");
  await expectActiveContext(page.getByTestId("industry-landscape-page"));

  await page.goto("/objects-scope");
  await expectActiveContext(page.getByTestId("objects-scope-screen"));

  await page.goto("/development-status");
  await expectActiveContext(page.getByTestId("development-status-screen"));
});
