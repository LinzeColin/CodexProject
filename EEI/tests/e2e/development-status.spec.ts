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
  await expect(page.getByTestId("status-task-count")).toHaveText("130");
  await expect(page.getByTestId("status-acceptance-done")).not.toHaveText("0");
  await expect(page.getByTestId("status-open-risks")).not.toHaveText("0");
  await expect(page.getByTestId("status-operator-input-count")).toContainText("0/6");
  await expect(page.getByTestId("status-validator-count")).toContainText("0/6");
});

test("links tasks risks controls and acceptance evidence from the status screen", async ({
  page
}) => {
  await page.goto("/development-status");

  await expect(page.getByTestId("status-linked-evidence")).toContainText("tasks");
  await expect(page.getByTestId("status-linked-evidence")).toContainText("risks");
  await expect(page.getByTestId("status-linked-evidence")).toContainText("controls");
  await expect(page.getByTestId("status-linked-evidence")).toContainText("acceptance evidence");
  await expect(page.getByTestId("status-linked-evidence")).toContainText("operator gates");
  await expect(page.getByTestId("status-linked-evidence")).toContainText("operator receipts");
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
  await expect(page.getByTestId("status-link-operator-inputs")).toHaveAttribute(
    "href",
    /operator_input_status\.json/
  );
  await expect(page.getByTestId("status-link-operator-receipts")).toHaveAttribute(
    "href",
    /operator_input_submission_receipts\.json/
  );

  await expect(page.getByTestId("status-operator-gates-panel")).toContainText("A202");
  await expect(page.getByTestId("status-operator-gates-panel")).toContainText("A210");
  await expect(page.getByTestId("status-operator-gates-panel")).toContainText("A026");
  await expect(page.getByTestId("status-operator-gates-panel")).toContainText("A027");
  await expect(page.getByTestId("status-operator-gates-panel")).toContainText("A209");
  await expect(page.getByTestId("status-operator-gates-panel")).toContainText("MISSING");
  await expect(page.getByTestId("status-operator-gates-panel")).toContainText(
    "VAL-A202-SIGNED-INTAKE-PREFLIGHT"
  );
  await expect(page.getByTestId("status-operator-gates-panel")).toContainText(
    "NOT_RUN_INPUT_MISSING"
  );
  await expect(page.getByTestId("status-operator-gates-panel")).toContainText(
    "operator input target is missing"
  );
  await expect(page.getByTestId("status-receipt-ledger-panel")).toContainText(
    "eei-operator-input-submission-receipt-ledger-v1"
  );
  await expect(page.getByTestId("status-receipt-ledger-panel")).toContainText("local artifact");
  await expect(page.getByTestId("status-receipt-ledger-counts")).toContainText("0 accepted");
  await expect(page.getByTestId("status-receipt-ledger-conflict-policy")).toContainText(
    "idempotent retry"
  );
  await expect(page.getByTestId("status-receipt-ledger-release-policy")).toContainText(
    "release-manager refresh blocked"
  );
  await expect(page.getByTestId("status-ledger-panel")).toContainText("FUN-EXP-01");
  await expect(page.getByTestId("status-ledger-panel")).toContainText("LOCAL_E2E_VALIDATED");
  await expect(page.getByTestId("status-task-T1302")).toContainText(
    "Complete production API"
  );
  await expect(page.getByTestId("status-task-T1302")).toContainText("DONE");
  await expect(page.getByTestId("status-acceptance-panel")).toContainText("DONE");
  await expect(page.getByTestId("status-risk-control-panel")).toContainText("R001");
  await expect(page.getByTestId("status-risk-control-panel")).toContainText("critical");
});

test("hydrates operator receipt ledger from the production API when configured", async ({
  page
}) => {
  await page.addInitScript(() => {
    window.localStorage.setItem("eei.apiBaseUrl.v1", "https://eei.test");
  });
  await page.route("https://eei.test/v1/release/operator-input-submission-receipts", async (route) => {
    await route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        schema_version: "eei-operator-input-submission-receipt-ledger-v1",
        artifact_id: "t1303-operator-input-submission-receipt-ledger",
        task_id: "T1303",
        acceptance_ids: ["A202", "A204", "A205"],
        receipt_count: 2,
        accepted_receipt_count: 1,
        rejected_receipt_count: 1,
        latest_receipt_id: "receipt-live-002",
        receipt_ids: ["receipt-live-001", "receipt-live-002"],
        release_gate_closed_by_receipt_ledger: false,
        release_manager_preflight_refresh_allowed: false,
        mvp_release_gate_refresh_allowed: false,
        conflict_policy: {
          expected_previous_receipt_id_required_when_supplied: true,
          identical_receipt_is_idempotent: true,
          ledger_never_modifies_operator_input_files: true,
          receipt_id_must_be_unique: true
        },
        non_claims: ["mock API receipt ledger for frontend hydration test"],
        receipts: []
      })
    });
  });

  await page.goto("/development-status");

  await expect(page.getByTestId("status-receipt-ledger-schema")).toContainText("API hydrated");
  await expect(page.getByTestId("status-receipt-ledger-counts")).toContainText(
    "1 accepted / 1 rejected"
  );
  await expect(page.getByTestId("status-receipt-ledger-counts")).toContainText("receipt-live-002");
  await expect(page.getByTestId("status-receipt-ledger-release-policy")).toContainText(
    "release open"
  );
});
