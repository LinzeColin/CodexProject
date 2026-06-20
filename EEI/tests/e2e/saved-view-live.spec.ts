import { expect, test, type BrowserContext, type Page } from "@playwright/test";

const savedViewApiBaseStorageKey = "eei.apiBaseUrl.v1";
const productionDataApiBaseStorageKey = "eei.productionDataApiBaseUrl.v1";
const savedViewStorageKey = "eei.savedView.current.v1";
const liveApiBaseUrl = process.env.EEI_LIVE_API_BASE_URL ?? "http://127.0.0.1:8000";

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
