import { expect, test, type BrowserContext, type Page } from "@playwright/test";

const savedViewApiBaseStorageKey = "eei.apiBaseUrl.v1";
const productionDataApiBaseStorageKey = "eei.productionDataApiBaseUrl.v1";
const modelApiBaseStorageKey = "eei.modelApiBaseUrl.v1";
const savedViewStorageKey = "eei.savedView.current.v1";
const liveApiBaseUrl = process.env.EEI_LIVE_API_BASE_URL ?? "http://127.0.0.1:8000";

test.describe.configure({ mode: "serial" });

async function configureApiBase(context: BrowserContext) {
  await context.addInitScript(
    ({ storageKey, apiBaseUrl }: { storageKey: string; apiBaseUrl: string }) =>
      window.localStorage.setItem(storageKey, apiBaseUrl),
    { storageKey: savedViewApiBaseStorageKey, apiBaseUrl: liveApiBaseUrl }
  );
  await context.addInitScript(
    ({ storageKey, apiBaseUrl }: { storageKey: string; apiBaseUrl: string }) =>
      window.localStorage.setItem(storageKey, apiBaseUrl),
    { storageKey: productionDataApiBaseStorageKey, apiBaseUrl: liveApiBaseUrl }
  );
  await context.addInitScript(
    ({ storageKey, apiBaseUrl }: { storageKey: string; apiBaseUrl: string }) =>
      window.localStorage.setItem(storageKey, apiBaseUrl),
    { storageKey: modelApiBaseStorageKey, apiBaseUrl: liveApiBaseUrl }
  );
}

async function seedSavedView(context: BrowserContext, savedViewPayload: string) {
  await context.addInitScript(
    ({ storageKey, payload }: { storageKey: string; payload: string }) =>
      window.localStorage.setItem(storageKey, payload),
    { storageKey: savedViewStorageKey, payload: savedViewPayload }
  );
}

async function expectCloudState(page: Page) {
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Cloud Customer");
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic AI Data Center Campus");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L2");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-active-time", "2026-06-12");
}

test("A207 live multi-session saved-view conflict resolves from FastAPI PostgreSQL", async ({
  browser
}) => {
  const firstContext = await browser.newContext();
  await configureApiBase(firstContext);
  const firstPage = await firstContext.newPage();

  await firstPage.goto(
    "/?subject=cloud&selected=datacenter&lens=supply_chain&zoom=L2&asOf=2026-06-12&path=nvidia.cloud"
  );
  await expectCloudState(firstPage);
  await firstPage.getByTestId("save-current-view").click();
  await expect(firstPage.getByTestId("saved-view-status")).toHaveText("server-saved");
  await expect(firstPage.getByTestId("saved-view-panel")).toHaveAttribute("data-sync-mode", "server");
  await expect(firstPage.getByTestId("saved-view-panel")).toHaveAttribute("data-server-version", "1");
  const serverId = await firstPage.getByTestId("saved-view-panel").getAttribute("data-server-id");
  expect(serverId).toMatch(/^[0-9a-f-]{36}$/);

  const savedViewPayload = await firstPage.evaluate((storageKey) => {
    const payload = window.localStorage.getItem(storageKey);
    if (!payload) throw new Error("missing saved view payload");
    return payload;
  }, savedViewStorageKey);

  const secondContext = await browser.newContext();
  await configureApiBase(secondContext);
  await seedSavedView(secondContext, savedViewPayload);
  const secondPage = await secondContext.newPage();
  await secondPage.goto(
    "/?subject=cloud&selected=datacenter&lens=supply_chain&zoom=L2&asOf=2026-06-12&path=nvidia.cloud"
  );
  await expectCloudState(secondPage);
  await secondPage.getByTestId("lens-policy_risk").click();
  await secondPage.getByTestId("save-current-view").click();
  await expect(secondPage.getByTestId("saved-view-status")).toHaveText("server-saved");
  await expect(secondPage.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-server-version",
    "2"
  );

  await firstPage.getByTestId("lens-business_segments").click();
  await firstPage.getByTestId("save-current-view").click();
  await expect(firstPage.getByTestId("saved-view-status")).toHaveText("server-conflict");
  await expect(firstPage.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-sync-reason",
    "stale_saved_view_version"
  );
  await expect(firstPage.getByTestId("resolve-saved-view-conflict")).toBeVisible();

  await firstPage.getByTestId("resolve-saved-view-conflict").click();
  await expect(firstPage.getByTestId("saved-view-status")).toHaveText(
    "server-conflict-resolved"
  );
  await expect(firstPage.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-server-version",
    "2"
  );
  await expect(firstPage.getByTestId("saved-view-panel")).toHaveAttribute(
    "data-sync-reason",
    "resolved_latest"
  );
  await expect(firstPage.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "policy_risk"
  );

  await firstContext.close();
  await secondContext.close();
});

test("A204 and A205 live model activation refreshes and rolls back through FastAPI PostgreSQL", async ({
  browser
}) => {
  const context = await browser.newContext();
  await configureApiBase(context);
  const page = await context.newPage();
  const uuidPattern = /^[0-9a-f-]{36}$/;

  await page.goto("/");
  const panel = page.getByTestId("model-preview-panel");
  const status = page.getByTestId("model-activation-status");
  const workspace = page.getByTestId("workspace-shell");

  await expect(status).toHaveText("server-current");
  await expect(panel).toHaveAttribute("data-model-sync-mode", "server");
  await expect(panel).toHaveAttribute("data-active-profile-id", uuidPattern);
  await expect(panel).toHaveAttribute("data-target-profile-id", uuidPattern);
  await expect(workspace).toHaveAttribute("data-active-profile-version", "balanced-v2@2");

  const initialActiveProfileId = await panel.getAttribute("data-active-profile-id");
  const targetProfileId = await panel.getAttribute("data-target-profile-id");
  const initialRefreshGeneration = Number(
    await panel.getAttribute("data-model-refresh-generation")
  );
  if (!initialActiveProfileId || !targetProfileId) {
    throw new Error("missing model activation profile ids");
  }
  expect(initialActiveProfileId).toMatch(uuidPattern);
  expect(targetProfileId).toMatch(uuidPattern);
  expect(targetProfileId).not.toBe(initialActiveProfileId);

  await page.getByTestId("activate-model-profile").click();
  await expect(status).toHaveText("server-activated");
  await expect(panel).toHaveAttribute("data-active-profile-id", targetProfileId);
  await expect(panel).toHaveAttribute("data-rollback-profile-id", initialActiveProfileId);
  await expect(panel).toHaveAttribute(
    "data-model-refresh-generation",
    String(initialRefreshGeneration + 1)
  );
  await expect(workspace).toHaveAttribute(
    "data-active-model-version",
    "business-empire-model-v3@3"
  );
  await expect(workspace).toHaveAttribute("data-active-profile-version", "supply-chain-v3@3");
  await expect(workspace).toHaveAttribute("data-active-score-snapshot", uuidPattern);
  const activatedScoreSnapshot = await workspace.getAttribute("data-active-score-snapshot");

  await page.getByTestId("check-model-refresh").click();
  await expect(status).toHaveText("server-refreshed");
  await expect(panel).toHaveAttribute("data-client-state", "stale");
  await expect(panel).toHaveAttribute("data-model-sync-reason", "stale_client_refetched");
  await expect(panel).toHaveAttribute("data-active-profile-id", targetProfileId);

  await page.getByTestId("rollback-model-activation").click();
  await expect(status).toHaveText("server-activated");
  await expect(panel).toHaveAttribute("data-active-profile-id", initialActiveProfileId);
  await expect(panel).toHaveAttribute("data-rollback-profile-id", targetProfileId);
  await expect(panel).toHaveAttribute(
    "data-model-refresh-generation",
    String(initialRefreshGeneration + 2)
  );
  await expect(workspace).toHaveAttribute("data-active-profile-version", "balanced-v2@2");
  await expect(workspace).toHaveAttribute("data-active-score-snapshot", uuidPattern);
  const rollbackScoreSnapshot = await workspace.getAttribute("data-active-score-snapshot");
  expect(rollbackScoreSnapshot).not.toBe(activatedScoreSnapshot);

  await context.close();
});
