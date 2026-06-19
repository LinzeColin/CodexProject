import { expect, test } from "@playwright/test";

test("shows development status navigation with separated state classes", async ({ page }) => {
  await page.goto("/");
  await page.getByTestId("development-status-nav-link").click();

  await expect(page).toHaveURL(/\/development-status$/);
  await expect(page.getByTestId("development-status-screen")).toBeVisible();
  await expect(page.getByTestId("development-status-nav-active")).toHaveAttribute(
    "aria-current",
    "page"
  );
  await expect(page.getByTestId("development-status-screen")).toHaveAttribute(
    "data-active-model-version",
    "business-empire-model-v2"
  );

  for (const lane of [
    "resolved",
    "prototyped",
    "specified",
    "not-started",
    "blocked",
    "out-of-scope"
  ]) {
    await expect(page.getByTestId(`status-lane-${lane}`)).toBeVisible();
  }

  await expect(page.getByTestId("status-current-gate")).toContainText("G4 / IN PROGRESS");
  await expect(page.getByTestId("status-task-count")).toHaveText("120");
  await expect(page.getByTestId("status-acceptance-done")).not.toHaveText("0");
  await expect(page.getByTestId("status-open-risks")).not.toHaveText("0");
});

test("links tasks risks controls and acceptance evidence from the status screen", async ({
  page
}) => {
  await page.goto("/development-status");

  await expect(page.getByTestId("status-linked-evidence")).toContainText("tasks");
  await expect(page.getByTestId("status-linked-evidence")).toContainText("risks");
  await expect(page.getByTestId("status-linked-evidence")).toContainText("controls");
  await expect(page.getByTestId("status-linked-evidence")).toContainText("acceptance evidence");
  await expect(page.getByTestId("status-link-tasks")).toHaveAttribute("href", /task_backlog\.csv/);
  await expect(page.getByTestId("status-link-risks")).toHaveAttribute("href", /risk_register\.csv/);
  await expect(page.getByTestId("status-link-controls")).toHaveAttribute(
    "href",
    /risk_control_traceability\.csv/
  );
  await expect(page.getByTestId("status-link-acceptance")).toHaveAttribute(
    "href",
    /acceptance_traceability\.csv/
  );

  await expect(page.getByTestId("status-ledger-panel")).toContainText("FUN-EXP-01");
  await expect(page.getByTestId("status-ledger-panel")).toContainText("LOCAL_E2E_VALIDATED");
  await expect(page.getByTestId("status-task-panel")).toContainText("T1206");
  await expect(page.getByTestId("status-acceptance-panel")).toContainText("DONE");
  await expect(page.getByTestId("status-risk-control-panel")).toContainText("R001");
  await expect(page.getByTestId("status-risk-control-panel")).toContainText("critical");
});
