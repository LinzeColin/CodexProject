import { expect, test, type Locator } from "@playwright/test";

async function boxFor(locator: Locator) {
  const box = await locator.boundingBox();
  expect(box).not.toBeNull();
  return box!;
}

function centerX(box: { x: number; width: number }) {
  return box.x + box.width / 2;
}

function centerY(box: { y: number; height: number }) {
  return box.y + box.height / 2;
}

test("renders the watchlist-first EEI workspace", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("main")).toBeVisible();
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");
  await expect(page.getByTestId("app-brand-icon")).toBeVisible();
  await expect(page.locator('link[rel="icon"]')).toHaveAttribute(
    "href",
    "/eei-app-icon.png"
  );
  await expect(page.locator('link[rel="apple-touch-icon"]')).toHaveAttribute(
    "href",
    "/eei-app-icon.png"
  );
  await expect(page.locator('link[rel="manifest"]')).toHaveAttribute(
    "href",
    "/manifest.webmanifest"
  );
  const iconResponse = await page.request.get("/eei-app-icon.png");
  expect(iconResponse.ok()).toBeTruthy();
  expect(iconResponse.headers()["content-type"]).toContain("image/png");
  const manifestResponse = await page.request.get("/manifest.webmanifest");
  expect(manifestResponse.ok()).toBeTruthy();
  expect(manifestResponse.headers()["content-type"]).toContain("application/manifest+json");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-workspace-model",
    "recursive-enterprise-map"
  );
  await expect(page.getByRole("navigation", { name: "主导航" })).toContainText("商业版图");
  await expect(page.getByLabel("系统模块")).toContainText("对象与范围");
  await expect(page.getByRole("img", { name: /NVIDIA synthetic recursive supply-chain graph/ })).toBeVisible();
  await expect(page.getByTestId("fixture-disclosure")).toContainText("Fixture-only data");
  await expect(page.getByText("Live facts: disabled")).toBeVisible();
});

test("shows user-oriented home contract entry points and model freshness", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("home-global-search")).toHaveAttribute(
    "data-endpoint",
    "/v1/entities"
  );
  await expect(page.getByTestId("home-global-search")).toHaveAttribute(
    "data-supported-types",
    "legal_entity,industry,theme,facility"
  );
  await expect(page.getByTestId("global-search-input")).toBeVisible();
  await expect(page.getByTestId("global-search-results")).toContainText("NVIDIA Corporation");
  await expect(page.getByTestId("home-industries")).toContainText("Semiconductors");
  await expect(page.getByTestId("home-industries")).toContainText("AI cloud infrastructure");
  await expect(page.getByTestId("home-watchlist")).toContainText("NVIDIA");
  await expect(page.getByTestId("home-watchlist")).toContainText("unread");
  await expect(page.getByTestId("home-recent-explorations")).toContainText(
    "NVIDIA -> Foundry"
  );
  await expect(page.getByTestId("home-changes")).toContainText("Capital/control signal refreshed");
  await expect(page.getByTestId("home-freshness")).toContainText("synthetic_fixture");
  await expect(page.getByTestId("home-freshness")).toContainText("3 sources");
  await expect(page.getByTestId("home-model-status")).toContainText("Balanced v2");
  await expect(page.getByTestId("home-model-status")).toContainText("scheduled / 14d");
  await expect(page.getByTestId("home-model-status")).toContainText("2026-07-03");
});

test("A211 exposes WorkspaceContext routes controls disabled entries and persisted query wiring", async ({
  page
}) => {
  await page.goto("/");

  const context = page.getByTestId("workspace-context-contract");
  await expect(context).toHaveAttribute("data-context-version", "workspace-context-v1");
  await expect(context).toHaveAttribute("data-module-count", "16");
  await expect(context).toHaveAttribute(
    "data-query-keys",
    "subject,selected,lens,zoom,asOf,path"
  );
  await expect(context).toHaveAttribute("data-state-persistence", "url,sessionStorage,localStorage");
  await expect(context).toHaveAttribute("data-workspace-state-storage-key", "eei.workspaceState.v1");
  await expect(context).toHaveAttribute("data-saved-view-storage-key", "eei.savedView.current.v1");
  await expect(context).toHaveAttribute(
    "data-disabled-unfinished",
    "ma_transactions,control_relationships"
  );
  const serverEndpoints = await context.getAttribute("data-server-endpoints");
  expect(serverEndpoints).toContain("/v1/saved-views");
  expect(serverEndpoints).toContain("/v1/scoring/active-context");
  expect(serverEndpoints).toContain("/v1/scoring/recompute");

  await expect(page.getByTestId("main-nav-business_map")).toHaveAttribute("href", "/");
  await expect(page.getByTestId("main-nav-business_map")).toHaveAttribute(
    "data-control-kind",
    "route"
  );
  await page.getByTestId("main-nav-supply_chain").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "supply_chain"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-last-nav-action",
    "lens:supply_chain:supply_chain"
  );
  await expect(page).toHaveURL(/lens=supply_chain/);

  await page.getByTestId("main-nav-time_evolution").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-last-nav-action",
    "section:time_evolution:timeline-controls"
  );
  await page.getByTestId("main-nav-evidence_center").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-last-nav-action",
    "section:evidence_center:evidence-center"
  );

  await expect(page.getByTestId("main-nav-ma_transactions")).toBeDisabled();
  await expect(page.getByTestId("main-nav-ma_transactions")).toHaveAttribute(
    "data-route-state",
    "planned"
  );
  await expect(page.getByTestId("main-nav-ma_transactions")).toHaveAttribute(
    "data-disabled-reason",
    /Requires reviewed M&A transaction facts/
  );
  await expect(page.getByTestId("main-nav-control_relationships")).toBeDisabled();
  await page.getByTestId("main-nav-strategic_signals").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-last-nav-action",
    "section:strategic_signals:strategic-signal-panel"
  );

  await page.getByTestId("main-nav-system_status").click();
  await expect(page).toHaveURL(/\/development-status$/);
});

test("shows strategic signal support contradiction alternatives decay and rule version", async ({
  page
}) => {
  await page.goto("/");

  await page.getByTestId("main-nav-strategic_signals").click();
  const panel = page.getByTestId("strategic-signal-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toHaveAttribute("data-support-count", "1");
  await expect(panel).toHaveAttribute("data-contradiction-count", "1");
  await expect(panel).toHaveAttribute("data-alternative-count", "1");
  await expect(panel).toHaveAttribute("data-rule-version", "F-SS-001@balanced-v2");
  await expect(panel).toHaveAttribute("data-decay-policy", /half_life_days/);

  await expect(page.getByTestId("strategic-signal-contract")).toContainText("Support");
  await expect(page.getByTestId("strategic-signal-contract")).toContainText("Contradiction");
  await expect(page.getByTestId("strategic-signal-contract")).toContainText("Alternatives");
  await expect(page.getByTestId("strategic-signal-contract")).toContainText("Time decay");
  await expect(page.getByTestId("strategic-signal-contract")).toContainText(
    "F-SS-001@balanced-v2"
  );

  await expect(page.getByTestId("strategic-signal-ai-capacity")).toHaveAttribute(
    "data-signal-stance",
    "support"
  );
  await expect(page.getByTestId("strategic-signal-export-control")).toHaveAttribute(
    "data-signal-stance",
    "contradiction"
  );
  await expect(page.getByTestId("strategic-signal-edge-inference")).toHaveAttribute(
    "data-signal-stance",
    "alternative"
  );
  await expect(page.getByTestId("strategic-signal-ai-capacity")).toHaveAttribute(
    "data-half-life",
    "365d"
  );
});

test("shows supply-chain ordered stages upstream downstream metadata and unknowns", async ({
  page
}) => {
  const apiBaseUrl = "http://127.0.0.1:45321";
  const stageIds = Array.from({ length: 16 }, (_, index) => {
    const stageNumber = String(index + 1).padStart(2, "0");
    return `SC-${stageNumber}`;
  });
  await page.route(`${apiBaseUrl}/v1/catalogs`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        as_of: "2026-06-19T00:00:00Z",
        catalog_version: "taxonomy-v4.2",
        catalog_count: 10,
        source_of_truth_count: 10,
        total_declared_rows: 363,
        catalogs: []
      }
    });
  });
  await page.route(`${apiBaseUrl}/v1/entities/**/supply-chain**`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        schema_version: "entity-supply-chain-v1",
        as_of: "2026-06-19T00:00:00Z",
        focus: {
          id: "00000000-0000-4000-8000-000000000006",
          canonical_name: "NVIDIA Corporation",
          entity_type: "legal_entity"
        },
        directional_summary: {
          upstream_edge_count: 2,
          downstream_edge_count: 3,
          supports_upstream_downstream: true
        },
        chain_stages: stageIds.map((stageId, index) => ({
          stage_id: stageId,
          stage_order: (index + 1) * 10,
          slug: `stage-${stageId.toLowerCase()}`,
          name_zh: stageId,
          name_en: stageId === "SC-12" ? "Customer" : `Stage ${stageId}`,
          default_direction: index < 7 ? "upstream" : "downstream",
          relationship_count: stageId === "SC-02" || stageId === "SC-12" ? 1 : 0,
          upstream_edge_count: stageId === "SC-02" ? 1 : 0,
          downstream_edge_count: stageId === "SC-12" ? 1 : 0,
          unknown_count: stageId === "SC-02" ? 1 : 0
        })),
        edges: [
          {
            id: "rel-supply-metadata-1",
            subject: {
              id: "00000000-0000-4000-8000-000000000023",
              canonical_name: "Synthetic Specialty Materials Co.",
              entity_type: "legal_entity"
            },
            object: {
              id: "00000000-0000-4000-8000-000000000006",
              canonical_name: "NVIDIA Corporation",
              entity_type: "legal_entity"
            },
            relationship_type: "material_provider_to",
            relationship_family: "supply_chain_operations",
            status: "published",
            stage_from: "SC-02",
            stage_from_name: "SC-02 Materials",
            stage_to: "SC-06",
            stage_to_name: "SC-06 Manufacturing",
            chain_side: "upstream",
            tier: "unknown",
            materiality: "high",
            substitutability: 35,
            geography: ["TW", "US"],
            capacity: "unknown",
            amount: "unknown",
            time: {
              observed_at: "2026-06-19T00:00:00Z",
              valid_from: null,
              valid_to: null
            },
            evidence_count: 2,
            unknown_fields: ["tier", "amount", "capacity"],
            synthetic: true,
            fixture_notice: "Synthetic fixture for API hydration test."
          }
        ],
        unknowns: [
          {
            relationship_id: "rel-supply-metadata-1",
            field: "tier",
            status: "unknown",
            message: "tier is unknown; treat unknown as unknown, not zero."
          },
          {
            relationship_id: "rel-supply-metadata-1",
            field: "amount",
            status: "unknown",
            message: "amount is unknown; treat unknown as unknown, not zero."
          },
          {
            relationship_id: "rel-supply-metadata-1",
            field: "capacity",
            status: "unknown",
            message: "capacity is unknown; treat unknown as unknown, not zero."
          }
        ],
        coverage: {
          ordered_stage_count: 16,
          covered_stage_count: 2,
          edge_count: 1,
          evidence_source_count: 2,
          all_edges_have_evidence: true,
          edge_metadata_fields: [
            "stage_from",
            "stage_to",
            "tier",
            "materiality",
            "substitutability",
            "geography",
            "time",
            "evidence",
            "unknowns"
          ],
          unknowns_explicit: true
        },
        content_rules: {
          unknown_not_zero: true,
          layout_position_is_not_control: true,
          synthetic_fixture_not_live_fact: true
        },
        data_mode: "synthetic_fixture",
        fixture_notice: "Synthetic fixture for API hydration test."
      }
    });
  });

  await page.goto("/");

  const panel = page.getByTestId("supply-chain-stage-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toHaveAttribute("data-api-contract", "/v1/entities/{entityId}/supply-chain");
  await expect(panel).toHaveAttribute("data-sync-mode", "local_fallback");
  await expect(panel).toHaveAttribute("data-upstream-edge-count", /^[1-9]/);
  await expect(panel).toHaveAttribute("data-downstream-edge-count", /^[1-9]/);
  await expect(panel).toHaveAttribute("data-unknown-not-zero", "true");
  await expect(panel).toHaveAttribute(
    "data-edge-metadata-fields",
    /stage_from,stage_to,tier,materiality,substitutability,geography,time,evidence,unknowns/
  );
  await expect(page.getByTestId("supply-chain-ordered-stages")).toContainText("SC-02");
  await expect(page.getByTestId("supply-chain-ordered-stages")).toContainText("SC-12");
  await expect(page.getByTestId("supply-chain-edge-metadata")).toContainText("Tier");
  await expect(page.getByTestId("supply-chain-edge-metadata")).toContainText("Materiality");
  await expect(page.getByTestId("supply-chain-edge-metadata")).toContainText("Substitutability");
  await expect(page.getByTestId("supply-chain-edge-metadata")).toContainText("Geography");
  await expect(page.getByTestId("supply-chain-edge-metadata")).toContainText("Time");
  await expect(page.getByTestId("supply-chain-edge-metadata")).toContainText("Evidence");
  await expect(page.getByTestId("supply-chain-edge-metadata")).toContainText("Unknowns");
  await expect(page.getByTestId("supply-chain-unknowns")).toContainText("unknown not zero");

  await page.evaluate((baseUrl) => {
    window.localStorage.setItem("eei.productionDataApiBaseUrl.v1", baseUrl);
  }, apiBaseUrl);
  await page.getByTestId("hydrate-production-data").click();
  await expect(panel).toHaveAttribute("data-sync-mode", "server");
  await expect(panel).toHaveAttribute("data-upstream-edge-count", "2");
  await expect(panel).toHaveAttribute("data-downstream-edge-count", "3");
  await expect(panel).toHaveAttribute("data-ordered-stage-count", "16");
  await expect(panel).toHaveAttribute("data-unknown-count", "3");
  await expect(page.getByTestId("supply-chain-edge-metadata")).toHaveAttribute(
    "data-evidence-count",
    "2"
  );
  await expect(page.getByTestId("supply-chain-edge-metadata")).toHaveAttribute(
    "data-unknown-fields",
    "tier,amount,capacity"
  );
  await expect(panel).toHaveAttribute(
    "data-edge-metadata-fields",
    /stage_from,stage_to,tier,materiality,substitutability,geography,time,evidence,unknowns/
  );
});

test("shows capital policy and technology semantic layers", async ({ page }) => {
  const apiBaseUrl = "http://127.0.0.1:45322";
  const amountSemantics = (
    semanticClass: string,
    amount: number | null,
    currency: string | null,
    amountKind: string | null
  ) => ({
    amount,
    currency,
    amount_kind: amountKind,
    unknown_not_zero: amount === null,
    aggregation_rule: "only_same_semantics_currency_period",
    aggregation_key: `${semanticClass}:${amountKind ?? "unknown"}:${currency ?? "unknown"}`,
    summable: amount !== null && amountKind !== null && currency !== null
  });
  const bucket = (
    key: string,
    label: string,
    dimension: string,
    recordCount: number,
    amountRecordCount = 0,
    unknownCount = recordCount === 0 ? 1 : 0
  ) => ({
    key,
    label,
    dimension,
    description: `${label} semantic bucket`,
    record_count: recordCount,
    amount_record_count: amountRecordCount,
    unknown_count: unknownCount,
    required: true
  });

  await page.route(`${apiBaseUrl}/v1/catalogs`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        as_of: "2026-06-19T00:00:00Z",
        catalog_version: "taxonomy-v4.2",
        catalog_count: 10,
        source_of_truth_count: 10,
        total_declared_rows: 363,
        catalogs: []
      }
    });
  });
  await page.route(`${apiBaseUrl}/v1/entities/**/capital**`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        schema_version: "entity-capital-map-v1",
        as_of: "2026-06-19T00:00:00Z",
        focus: {
          id: "00000000-0000-4000-8000-000000000006",
          canonical_name: "NVIDIA Corporation",
          entity_type: "legal_entity"
        },
        relationships: [
          {
            id: "rel-capital-investment",
            relationship_type: "invested_in",
            relationship_family: "capital_financing",
            status: "reported",
            confidence: 0.8,
            semantic_class: "investment",
            semantic_tags: ["investment"],
            direction: "out",
            subject: {
              id: "00000000-0000-4000-8000-000000000006",
              canonical_name: "NVIDIA Corporation",
              entity_type: "legal_entity"
            },
            object: {
              id: "entity-ai-startup",
              canonical_name: "Synthetic AI Startup",
              entity_type: "legal_entity"
            },
            amount_semantics: amountSemantics("investment", null, null, null),
            time: { observed_at: "2026-06-19T00:00:00Z" },
            evidence_count: 1,
            unknown_fields: ["amount", "amount_kind"],
            synthetic: true,
            fixture_notice: "Synthetic capital test."
          },
          {
            id: "rel-capital-acquisition",
            relationship_type: "acquired",
            relationship_family: "mergers_acquisitions",
            status: "reported",
            confidence: 0.8,
            semantic_class: "acquisition",
            semantic_tags: ["acquisition"],
            direction: "out",
            subject: {
              id: "00000000-0000-4000-8000-000000000006",
              canonical_name: "NVIDIA Corporation",
              entity_type: "legal_entity"
            },
            object: {
              id: "entity-target",
              canonical_name: "Synthetic Target",
              entity_type: "legal_entity"
            },
            amount_semantics: amountSemantics("acquisition", null, null, null),
            time: { observed_at: "2026-06-19T00:00:00Z" },
            evidence_count: 1,
            unknown_fields: ["amount", "amount_kind"],
            synthetic: true,
            fixture_notice: "Synthetic M&A test."
          }
        ],
        events: [
          {
            id: "event-capex",
            event_type: "capital_expenditure",
            title: "Synthetic capex event",
            status: "reported",
            semantic_class: "capex",
            semantic_tags: ["capex"],
            amount_semantics: amountSemantics("capex", 1000000000, "USD", "period_capex"),
            time: { observed_at: "2026-06-19T00:00:00Z" },
            evidence_count: 1,
            unknown_fields: [],
            participants: []
          }
        ],
        semantic_buckets: [
          bucket("investment", "Investment", "capital", 1),
          bucket("debt", "Debt", "capital", 0),
          bucket("acquisition", "Acquisition", "ma", 1),
          bucket("commitment", "Commitment", "capital", 0),
          bucket("capex", "Capex", "capital", 1, 1, 0),
          bucket("buyback", "Buyback", "capital", 0),
          bucket("dividend", "Dividend", "capital", 0)
        ],
        coverage: {
          relationship_count: 2,
          event_count: 1,
          semantic_class_count: 3,
          required_semantic_classes: [
            "investment",
            "debt",
            "acquisition",
            "commitment",
            "capex",
            "buyback",
            "dividend"
          ],
          no_silent_summing: true,
          unknown_amount_not_zero: true
        },
        content_rules: {
          amount_unknown_not_zero: true,
          incomparable_amounts_not_summed: true
        },
        data_mode: "synthetic_fixture",
        fixture_notice: "Synthetic capital API hydration test."
      }
    });
  });
  await page.route(`${apiBaseUrl}/v1/entities/**/policy**`, async (route) => {
    await route.fulfill({
      contentType: "application/json",
      json: {
        schema_version: "entity-policy-map-v1",
        as_of: "2026-06-19T00:00:00Z",
        focus: {
          id: "00000000-0000-4000-8000-000000000006",
          canonical_name: "NVIDIA Corporation",
          entity_type: "legal_entity"
        },
        policy_records: [
          {
            id: "rel-policy-award",
            relationship_type: "government_award_to",
            relationship_family: "government_policy",
            status: "reported",
            confidence: 0.8,
            semantic_class: "award",
            semantic_tags: ["award", "ceiling"],
            direction: "in",
            subject: {
              id: "entity-government",
              canonical_name: "Synthetic Government",
              entity_type: "government_body"
            },
            object: {
              id: "00000000-0000-4000-8000-000000000006",
              canonical_name: "NVIDIA Corporation",
              entity_type: "legal_entity"
            },
            amount_semantics: amountSemantics("award", 500000000, "USD", "award_ceiling"),
            time: { observed_at: "2026-06-19T00:00:00Z" },
            evidence_count: 1,
            unknown_fields: [],
            synthetic: true,
            fixture_notice: "Synthetic policy test."
          }
        ],
        technology_records: [
          {
            id: "rel-tech-ip",
            relationship_type: "licenses_ip_to",
            relationship_family: "technology_data_ip",
            status: "reported",
            confidence: 0.8,
            semantic_class: "ip",
            semantic_tags: ["ip", "integration"],
            direction: "out",
            subject: {
              id: "00000000-0000-4000-8000-000000000006",
              canonical_name: "NVIDIA Corporation",
              entity_type: "legal_entity"
            },
            object: {
              id: "entity-integrator",
              canonical_name: "Synthetic Integrator",
              entity_type: "legal_entity"
            },
            amount_semantics: amountSemantics("ip", null, null, null),
            time: { observed_at: "2026-06-19T00:00:00Z" },
            evidence_count: 1,
            unknown_fields: ["amount", "amount_kind"],
            synthetic: true,
            fixture_notice: "Synthetic technology test."
          },
          {
            id: "rel-tech-compute",
            relationship_type: "compute_provider_to",
            relationship_family: "commercial_dependency",
            status: "reported",
            confidence: 0.8,
            semantic_class: "cloud_compute",
            semantic_tags: ["cloud_compute", "data_access"],
            direction: "out",
            subject: {
              id: "00000000-0000-4000-8000-000000000006",
              canonical_name: "NVIDIA Corporation",
              entity_type: "legal_entity"
            },
            object: {
              id: "entity-cloud",
              canonical_name: "Synthetic Cloud",
              entity_type: "legal_entity"
            },
            amount_semantics: amountSemantics("cloud_compute", null, null, null),
            time: { observed_at: "2026-06-19T00:00:00Z" },
            evidence_count: 1,
            unknown_fields: ["amount", "amount_kind"],
            synthetic: true,
            fixture_notice: "Synthetic cloud compute test."
          }
        ],
        events: [
          {
            id: "event-contract-award",
            event_type: "contract_award",
            title: "Synthetic award ceiling",
            status: "reported",
            semantic_class: "award",
            semantic_tags: ["award", "ceiling"],
            amount_semantics: amountSemantics("award", 500000000, "USD", "award_ceiling"),
            time: { observed_at: "2026-06-19T00:00:00Z" },
            evidence_count: 1,
            unknown_fields: [],
            participants: []
          }
        ],
        semantic_buckets: [
          bucket("award", "Award", "policy", 2, 2, 0),
          bucket("obligation", "Obligation", "policy", 0),
          bucket("ceiling", "Ceiling", "policy", 2, 2, 0),
          bucket("regulation", "Regulation", "policy", 0),
          bucket("lobbying", "Lobbying", "policy", 0),
          bucket("trade_restriction", "Trade restriction", "policy", 0),
          bucket("ip", "IP", "technology", 1),
          bucket("standards", "Standards", "technology", 0),
          bucket("data_access", "Data access", "technology", 1),
          bucket("integration", "Integration", "technology", 1),
          bucket("cloud_compute", "Cloud compute", "technology", 1)
        ],
        coverage: {
          policy_record_count: 1,
          technology_record_count: 2,
          event_count: 1,
          policy_semantic_classes: [
            "award",
            "obligation",
            "ceiling",
            "regulation",
            "lobbying",
            "trade_restriction"
          ],
          technology_semantic_classes: [
            "ip",
            "standards",
            "data_access",
            "integration",
            "cloud_compute"
          ],
          unknowns_explicit: true
        },
        content_rules: {
          award_ceiling_is_not_paid_cash: true,
          obligation_ceiling_and_award_are_distinct: true,
          technology_dependency_is_not_control: true
        },
        data_mode: "synthetic_fixture",
        fixture_notice: "Synthetic policy API hydration test."
      }
    });
  });

  await page.goto("/");
  const panel = page.getByTestId("capital-policy-layer-panel");
  await expect(panel).toBeVisible();
  await expect(panel).toHaveAttribute("data-capital-api-contract", "/v1/entities/{entityId}/capital");
  await expect(panel).toHaveAttribute("data-policy-api-contract", "/v1/entities/{entityId}/policy");
  await expect(panel).toHaveAttribute("data-capital-sync-mode", "local_fallback");
  await expect(panel).toHaveAttribute(
    "data-capital-distinguishes",
    /investment,debt,acquisition,commitment,capex,buyback,dividend/
  );
  await expect(panel).toHaveAttribute(
    "data-policy-distinguishes",
    /award,obligation,ceiling,regulation,lobbying,trade_restriction/
  );
  await expect(panel).toHaveAttribute(
    "data-technology-distinguishes",
    /ip,standards,data_access,integration,cloud_compute/
  );
  await expect(page.getByTestId("capital-semantic-buckets")).toContainText("Investment");
  await expect(page.getByTestId("capital-semantic-buckets")).toContainText("Debt");
  await expect(page.getByTestId("policy-semantic-buckets")).toContainText("Ceiling");
  await expect(page.getByTestId("technology-semantic-buckets")).toContainText("Cloud compute");

  await page.evaluate((baseUrl) => {
    window.localStorage.setItem("eei.productionDataApiBaseUrl.v1", baseUrl);
  }, apiBaseUrl);
  await page.getByTestId("hydrate-production-data").click();
  await expect(panel).toHaveAttribute("data-capital-sync-mode", "server");
  await expect(panel).toHaveAttribute("data-policy-sync-mode", "server");
  await expect(panel).toHaveAttribute("data-capital-relationship-count", "2");
  await expect(panel).toHaveAttribute("data-capital-event-count", "1");
  await expect(panel).toHaveAttribute("data-policy-record-count", "1");
  await expect(panel).toHaveAttribute("data-technology-record-count", "2");
  await expect(page.getByTestId("capital-semantic-capex")).toHaveAttribute(
    "data-amount-record-count",
    "1"
  );
  await expect(page.getByTestId("policy-semantic-ceiling")).toHaveAttribute(
    "data-record-count",
    "2"
  );
  await expect(page.getByTestId("technology-semantic-cloud_compute")).toHaveAttribute(
    "data-record-count",
    "1"
  );
});

test("exposes eight company layers and separates structure object types", async ({ page }) => {
  await page.goto("/");

  const layerStrip = page.getByTestId("workspace-layer-strip");
  await expect(layerStrip).toHaveAttribute("data-layer-count", "8");
  await expect(layerStrip).toHaveAttribute(
    "data-required-layers",
    "group_structure,business_segments,supply_chain,capital_network,ma_transactions,control_relationships,policy_environment,strategic_signals"
  );
  for (const layer of [
    "group_structure",
    "business_segments",
    "supply_chain",
    "capital_network",
    "ma_transactions",
    "control_relationships",
    "policy_environment",
    "strategic_signals"
  ]) {
    await expect(page.getByTestId(`workspace-layer-${layer}`)).toBeVisible();
  }
  await page.getByTestId("workspace-layer-business_segments").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "business_segments"
  );

  const structure = page.getByTestId("company-structure-matrix");
  await expect(structure).toHaveAttribute(
    "data-separates",
    "legal_group,business_segment,brand,product,facility"
  );
  await expect(structure).toHaveAttribute("data-commercial-empire-control-claim", "false");
  await expect(structure).toContainText("商业版图不是法律控制声明");
  await expect(page.getByTestId("structure-row-legal_group")).toContainText(
    "NVIDIA Corporation"
  );
  await expect(page.getByTestId("structure-row-business_segment")).toHaveAttribute(
    "data-relationship",
    "segment_of"
  );
  await expect(page.getByTestId("structure-row-brand")).toHaveAttribute(
    "data-scope",
    "missing"
  );
  await expect(page.getByTestId("structure-row-product")).toContainText(
    "AI Accelerator Platform"
  );
  await expect(page.getByTestId("structure-row-facility")).toHaveAttribute(
    "data-scope",
    "adjacent"
  );
  await expect(page.getByTestId("structure-row-facility")).toHaveAttribute(
    "data-control-claim",
    "false"
  );
  await expect(page.getByTestId("structure-row-facility")).toContainText(
    "不表示 NVIDIA 拥有或运营"
  );
});

test("reaches company focus within three actions and keeps home controls keyboard reachable", async ({
  page
}) => {
  await page.goto("/");

  await expect(page.getByTestId("home-global-search")).toHaveAttribute(
    "data-primary-actions-to-focus",
    "2"
  );
  await page.getByTestId("global-search-input").focus();
  await page.getByTestId("global-search-input").fill("tsmc");
  await page.getByTestId("global-search-input").press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");

  await page.getByTestId("home-industry-semiconductors").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");

  await page.getByTestId("home-watchlist-cloud").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Cloud Customer");

  await page.getByTestId("home-recent-equipment").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );

  await page.getByTestId("home-change-policy").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Export Control Context"
  );
});

test("shows watchlist unread changes and restores saved view profile state", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("watchlist-saved-state-cloud")).toContainText("2 unread");
  await expect(page.getByTestId("watchlist-saved-state-cloud")).toContainText("supply_chain");
  await expect(page.getByTestId("watchlist-saved-state-cloud")).toContainText("L2");
  await expect(page.getByTestId("watchlist-saved-state-cloud")).toContainText("Balanced v2");

  await page.getByTestId("lens-capital_transactions").click();
  await page.getByTestId("zoom-L0").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "capital_transactions"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L0");

  await page.getByTestId("home-watchlist-cloud").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Cloud Customer");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "supply_chain"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L2");
});

test("exposes the Objects and Scope navigation screen with counts definitions and exports", async ({
  page
}) => {
  await page.goto("/");
  await page.getByTestId("objects-scope-nav-link").click();

  await expect(page).toHaveURL(/\/objects-scope$/);
  await expect(page.getByTestId("objects-scope-screen")).toBeVisible();
  await expect(page.getByTestId("objects-scope-nav-active")).toHaveAttribute("aria-current", "page");
  await expect(page.getByTestId("object-scope-catalog-count")).toHaveText("10");
  await expect(page.getByTestId("object-scope-total-rows")).toHaveText("363");

  await expect(page.getByTestId("object-scope-coverage-relationship_types")).toContainText("52");
  await expect(page.getByTestId("object-scope-coverage-companies")).toContainText("140");
  await expect(page.getByTestId("object-scope-catalog-relationship")).toContainText("关系类型");
  await expect(page.getByTestId("object-scope-definition-relationship")).toContainText(
    "Fifty-two machine-readable relationship types"
  );
  await expect(page.getByTestId("object-scope-catalog-domain-object")).toContainText(
    "领域对象"
  );
  await expect(page.getByTestId("object-scope-export-relationship-json")).toHaveAttribute(
    "href",
    "/v1/catalogs/relationship"
  );
  await expect(page.getByTestId("object-scope-export-relationship-csv")).toHaveAttribute(
    "href",
    "/v1/catalogs/relationship?format=csv"
  );
  await expect(page.locator("article[data-testid^='object-scope-catalog-']")).toHaveCount(10);

  const screenBox = await boxFor(page.getByTestId("objects-scope-screen"));
  const summaryBox = await boxFor(page.getByLabel("覆盖摘要"));
  const matrixBox = await boxFor(page.getByLabel("目录定义与导出"));
  expect(summaryBox.width / screenBox.width).toBeGreaterThan(0.55);
  expect(matrixBox.height).toBeGreaterThan(400);
});

test("measures visual-first relationship layout and critical relationship layers", async ({ page }) => {
  await page.goto("/");

  const canvasBox = await boxFor(page.getByTestId("visual-canvas"));
  const mapBox = await boxFor(page.getByTestId("ecosystem-map-surface"));
  const visualCoverage = (mapBox.width * mapBox.height) / (canvasBox.width * canvasBox.height);
  expect(visualCoverage).toBeGreaterThanOrEqual(0.6);

  const focus = await boxFor(page.getByTestId("graph-node-nvidia"));
  const materials = await boxFor(page.getByTestId("graph-node-materials"));
  const equipment = await boxFor(page.getByTestId("graph-node-equipment"));
  const foundry = await boxFor(page.getByTestId("graph-node-foundry"));
  const systems = await boxFor(page.getByTestId("graph-node-systems"));
  const cloud = await boxFor(page.getByTestId("graph-node-cloud"));
  const capital = await boxFor(page.getByTestId("graph-node-capital"));
  const policy = await boxFor(page.getByTestId("graph-node-policy"));

  expect(centerX(materials)).toBeLessThan(centerX(focus));
  expect(centerX(equipment)).toBeLessThan(centerX(focus));
  expect(centerX(foundry)).toBeLessThan(centerX(focus));
  expect(centerX(systems)).toBeGreaterThan(centerX(focus));
  expect(centerX(cloud)).toBeGreaterThan(centerX(focus));
  expect(centerY(capital)).toBeLessThan(centerY(focus));
  expect(centerY(policy)).toBeGreaterThan(centerY(focus));

  await expect(page.getByTestId("graph-node-business")).toBeVisible();
  await expect(page.getByTestId("edge-label-nvidia-business")).toContainText("operates business segment");
  await expect(page.getByTestId("edge-label-capital-nvidia")).toContainText("capital and control signal for");
  await expect(page.getByTestId("edge-label-policy-nvidia")).toContainText("policy risk constrains");
  await expect(page.locator(".edge[marker-end='url(#arrow)']")).toHaveCount(11);
});

test("selects node context without changing subject and supports primary inspector actions", async ({
  page
}) => {
  await page.goto("/");

  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");
  await page.getByTestId("graph-node-foundry").click();
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("selected-node-card")).toContainText("SC-06 Manufacturing");
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");

  const actions = page.getByLabel("主体操作");
  await expect(actions.getByTestId("primary-set-center")).toContainText(
    "以 Synthetic Advanced Foundry 为中心"
  );
  for (const action of [
    "展开上游",
    "展开下游",
    "固定节点",
    "加入比较",
    "加入关注",
    "查看路径",
    "打开证据"
  ]) {
    await expect(actions.getByRole("button", { name: action })).toBeVisible();
  }
  await actions.getByTestId("node-action-pin").click();
  await expect(page.getByTestId("pinned-node-list")).toContainText("Synthetic Advanced Foundry");
  await actions.getByTestId("node-action-compare").click();
  await expect(page.getByTestId("comparison-node-list")).toContainText(
    "Synthetic Advanced Foundry"
  );
  await actions.getByTestId("node-action-watchlist").click();
  await expect(page.getByTestId("watchlist-node-list")).toContainText(
    "Synthetic Advanced Foundry"
  );
  await actions.getByTestId("node-action-path").click();
  await expect(page.getByTestId("node-action-status")).toHaveText("path:foundry");
  await actions.getByTestId("node-action-evidence").click();
  await expect(page.getByTestId("node-action-status")).toHaveText("evidence:foundry");
  await expect(page.getByTestId("evidence-detail-drawer")).toBeVisible();
  await page.getByTestId("close-evidence-drawer").click();
  await expect(page.getByTestId("evidence-detail-drawer")).toBeHidden();

  await actions.getByTestId("primary-set-center").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
});

test("traps focus in the evidence detail drawer and restores the trigger", async ({ page }) => {
  await page.goto("/");

  await page.getByTestId("graph-node-foundry").click();
  const evidenceAction = page.getByTestId("node-action-evidence");
  await evidenceAction.focus();
  await expect(evidenceAction).toBeFocused();
  await page.keyboard.press("Enter");

  const drawer = page.getByTestId("evidence-detail-drawer");
  await expect(drawer).toBeVisible();
  await expect(page.getByRole("dialog", { name: "Synthetic Advanced Foundry" })).toBeVisible();
  await expect(drawer).toHaveAttribute("aria-modal", "true");
  await expect(drawer).toHaveAttribute("data-focus-trap", "active");
  await expect(page.getByTestId("evidence-center")).toHaveAttribute("inert", "");
  await expect(page.getByTestId("visual-canvas")).toHaveAttribute("aria-hidden", "true");

  const closeButton = page.getByTestId("close-evidence-drawer");
  await expect(closeButton).toBeFocused();
  await page.keyboard.down("Shift");
  await page.keyboard.press("Tab");
  await page.keyboard.up("Shift");
  await expect(page.getByTestId("refresh-evidence-drawer")).toBeFocused();
  await page.keyboard.press("Tab");
  await expect(closeButton).toBeFocused();

  await page.keyboard.press("Escape");
  await expect(drawer).toBeHidden();
  await expect(evidenceAction).toBeFocused();
  await expect(page.getByTestId("evidence-center")).not.toHaveAttribute("inert", "");
  await expect(page.getByTestId("visual-canvas")).not.toHaveAttribute("aria-hidden", "true");
});

test("switches lenses on the persistent canvas while preserving exploration state", async ({
  page
}) => {
  await page.goto("/");

  await page.getByTestId("graph-node-foundry").click();
  await page.getByTestId("node-action-pin").click();
  await page.getByTestId("node-action-compare").click();
  await page.getByTestId("zoom-L2").click();

  const beforeViewport = await page.getByTestId("workspace-shell").getAttribute("data-viewport-anchor");
  const beforePathLength = await page.getByTestId("workspace-shell").getAttribute("data-path-length");

  await page.getByTestId("lens-capital_transactions").click();

  await expect(page).toHaveURL(/lens=capital_transactions/);
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-workspace-model",
    "recursive-enterprise-map"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-active-lens",
    "capital_transactions"
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L2");
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-viewport-anchor",
    beforeViewport ?? ""
  );
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-path-length",
    beforePathLength ?? ""
  );
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("edge-group-capital-nvidia")).toHaveAttribute(
    "data-lens-state",
    "active"
  );
  await expect(page.getByTestId("edge-group-materials-foundry")).toHaveAttribute(
    "data-lens-state",
    "faded"
  );
  await page.getByTestId("zoom-L3").click();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", "L3");
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("pinned-node-list")).toContainText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("comparison-node-list")).toContainText(
    "Synthetic Advanced Foundry"
  );
});

test("offers a filterable graph table alternative and explicit visual semantics", async ({
  page
}) => {
  await page.goto("/");

  await expect(page.getByTestId("visual-semantics-notice")).toHaveAttribute(
    "data-control-semantics",
    "layout-position-not-control"
  );
  await expect(page.getByTestId("visual-semantics-notice")).toHaveAttribute(
    "data-color-independent-encoding",
    "labels,arrows,stages,roles,evidence"
  );
  await expect(page.locator(".edge[marker-end='url(#arrow)']").first()).toBeVisible();
  await expect(page.getByTestId("edge-label-materials-foundry")).toContainText(
    "material provider to"
  );

  const table = page.getByTestId("graph-table-alternative");
  await expect(table).toBeVisible();
  await expect(table).toHaveAttribute("data-accessibility-equivalent", "graph-relationships");
  await expect(table).toHaveAttribute(
    "data-equivalent-fields",
    "direction,type,evidence_status,observed_at"
  );
  await expect(table).toHaveAttribute(
    "data-color-independent-encoding",
    "labels,arrows,stages,roles,evidence"
  );
  await expect(page.getByTestId("graph-table-row-materials-foundry")).toHaveAttribute(
    "data-direction",
    "materials->foundry"
  );
  await expect(page.getByTestId("graph-table-row-materials-foundry")).toHaveAttribute(
    "data-relationship-type",
    "supply_chain"
  );
  await expect(page.getByTestId("graph-table-row-materials-foundry")).toHaveAttribute(
    "data-evidence-status",
    "fixture-evidence"
  );
  await expect(page.getByTestId("graph-table-row-materials-foundry")).toHaveAttribute(
    "data-observed-at",
    "2026-06-19"
  );
  await expect(page.getByTestId("graph-table-row-materials-foundry")).toContainText(
    "fixture evidence"
  );
  await page.getByTestId("graph-table-filter").selectOption("supply_chain");
  await expect(table.locator("tbody tr").first()).toHaveAttribute("data-lens", "supply_chain");
  expect(await table.locator("tbody tr:not([data-lens='supply_chain'])").count()).toBe(0);
  await expect(table).toContainText("wafer foundry for");
});

test("keeps graph-equivalent controls keyboard reachable with visible focus and target size", async ({
  page
}) => {
  await page.goto("/");

  const foundryNode = page.getByTestId("graph-node-foundry");
  await foundryNode.focus();
  await expect(foundryNode).toBeFocused();
  const foundryBox = await boxFor(foundryNode);
  expect(foundryBox.width).toBeGreaterThanOrEqual(24);
  expect(foundryBox.height).toBeGreaterThanOrEqual(24);
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic Advanced Foundry");

  const primaryAction = page.getByTestId("primary-set-center");
  await primaryAction.focus();
  await expect(primaryAction).toBeFocused();
  const primaryBox = await boxFor(primaryAction);
  expect(primaryBox.width).toBeGreaterThanOrEqual(24);
  expect(primaryBox.height).toBeGreaterThanOrEqual(24);
  await page.keyboard.press("Enter");
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");

  const tableFilter = page.getByTestId("graph-table-filter");
  await tableFilter.focus();
  await expect(tableFilter).toBeFocused();
  const filterBox = await boxFor(tableFilter);
  expect(filterBox.width).toBeGreaterThanOrEqual(24);
  expect(filterBox.height).toBeGreaterThanOrEqual(24);
});

test("implements semantic zoom levels and grouped dense-node list view", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByTestId("semantic-zoom-controls")).toHaveAttribute(
    "data-zoom-contract",
    "L0,L1,L2,L3"
  );

  for (const zoom of ["L0", "L1", "L2", "L3"]) {
    await page.getByTestId(`zoom-${zoom}`).click();
    await expect(page.getByTestId("workspace-shell")).toHaveAttribute("data-semantic-zoom", zoom);
  }

  await expect(page.getByText("fixture evidence").first()).toBeVisible();
  await expect(page.getByText("current focus").first()).toBeVisible();

  await page.getByTestId("zoom-L0").click();
  const groupNode = page.getByTestId("graph-node-systemMakersGroup");
  await expect(groupNode).toBeVisible();
  await expect(groupNode).toHaveAttribute("data-node-kind", "aggregate");
  await expect(groupNode).toHaveAttribute("data-aggregate-count", "8");

  await groupNode.click();
  await expect(page.getByTestId("selected-node-title")).toHaveText("Synthetic System Makers Group");
  await expect(page.getByTestId("primary-set-center")).toBeDisabled();
  await page.getByTestId("open-group-list").click();
  await expect(page.getByTestId("group-list")).toBeVisible();
  await expect(page.getByTestId("group-list").locator("li")).toHaveCount(8);
});

test("keeps the default graph bounded below the first-screen hairball budget", async ({
  page
}) => {
  await page.goto("/");

  const renderedNodeCount = await page.locator("[data-testid^='graph-node-']").count();
  const renderedEdgeCount = await page.locator(".edge").count();

  expect(renderedNodeCount).toBeLessThanOrEqual(42);
  expect(renderedEdgeCount).toBeLessThanOrEqual(40);
  await expect(page.getByTestId("budget-state")).toContainText("max 40 first-screen edges");
  const inclusionPolicy = page.getByTestId("inclusion-truncation-explanation");
  await expect(inclusionPolicy).toBeVisible();
  await expect(inclusionPolicy).toHaveAttribute(
    "data-sort-keys",
    "active-lens,evidence,confidence,observed_at,id"
  );
  await expect(inclusionPolicy).toHaveAttribute(
    "data-truncation-contract",
    "edge_budget,node_budget,returned_counts,continuation"
  );
  await expect(inclusionPolicy).toHaveAttribute(
    "data-continuation-endpoint",
    "/v1/explore/expand"
  );
  await expect(inclusionPolicy).toContainText(
    "Active lens, evidence-bearing edges, confidence, observed time, stable id"
  );
  await expect(inclusionPolicy).toContainText("edge_budget and node_budget");
  await expect(inclusionPolicy).toContainText("/v1/explore/expand");
});

test("preserves directional grammar during reroot and keeps a nonblank fallback state", async ({
  page
}) => {
  await page.goto("/");

  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-layout-grammar",
    "upstream-left focus-center downstream-right capital-top policy-bottom"
  );

  await page.getByRole("button", { name: "以 Synthetic Advanced Foundry 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");

  const focus = await boxFor(page.getByTestId("graph-node-foundry"));
  const materials = await boxFor(page.getByTestId("graph-node-materials"));
  const equipment = await boxFor(page.getByTestId("graph-node-equipment"));
  const nvidia = await boxFor(page.getByTestId("graph-node-nvidia"));

  expect(centerX(materials)).toBeLessThan(centerX(focus));
  expect(centerX(equipment)).toBeLessThan(centerX(focus));
  expect(centerX(nvidia)).toBeGreaterThan(centerX(focus));
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-layout-grammar",
    "upstream-left focus-center downstream-right capital-top policy-bottom"
  );

  await page.evaluate(() => {
    window.dispatchEvent(new CustomEvent("eei:request-center", { detail: "missing-subject" }));
  });
  await expect(page.getByTestId("transition-fallback")).toBeVisible();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
  expect(await page.locator("[data-testid^='graph-node-']").count()).toBeGreaterThan(0);
});

test("uses keyboard or touch-style single actions for primary navigation", async ({ page }) => {
  await page.goto("/");

  const equipment = page.getByTestId("graph-node-equipment");
  await equipment.focus();
  await equipment.press("Enter");
  await expect(page.getByTestId("selected-node-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
  await expect(page.getByTestId("current-focus-title")).toHaveText("NVIDIA");

  await page.getByTestId("primary-set-center").click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
});

test("marks synthetic fixtures and completes NVIDIA recursive supply-chain reroot path", async ({
  page
}) => {
  await page.goto("/");

  const stageCoverage = page.getByLabel("供应链阶段覆盖");
  for (const stage of [
    "SC-02 Materials",
    "SC-04 Equipment",
    "SC-05 Design / IP",
    "SC-06 Manufacturing",
    "SC-09 System",
    "SC-10 Data center / Energy",
    "SC-12 Customer"
  ]) {
    await expect(stageCoverage.getByText(stage)).toBeVisible();
  }

  await expect(page.getByText("Synthetic fixture").first()).toBeVisible();
  await expect(page.getByText("Synthetic fixture for interaction and data-model tests.").first()).toBeVisible();

  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-workspace-model",
    "recursive-enterprise-map"
  );

  await page.getByRole("button", { name: "以 Synthetic Advanced Foundry 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText("Synthetic Advanced Foundry");
  await expect(page.getByTestId("visual-canvas")).toBeVisible();

  await page.getByRole("button", { name: "以 Synthetic Lithography Equipment Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Lithography Equipment Co."
  );
  await expect(page.getByTestId("visual-canvas")).toBeVisible();

  await page.getByRole("button", { name: "以 Synthetic Specialty Materials Co. 为中心" }).click();
  await expect(page.getByTestId("current-focus-title")).toHaveText(
    "Synthetic Specialty Materials Co."
  );
  await expect(page.getByTestId("visual-canvas")).toBeVisible();
  await expect(page.getByTestId("workspace-shell")).toHaveAttribute(
    "data-workspace-model",
    "recursive-enterprise-map"
  );

  const breadcrumb = page.getByTestId("reroot-breadcrumb");
  await expect(breadcrumb).toContainText("NVIDIA");
  await expect(breadcrumb).toContainText("Synthetic Advanced Foundry");
  await expect(breadcrumb).toContainText("Synthetic Lithography Equipment Co.");
  await expect(breadcrumb).toContainText("Synthetic Specialty Materials Co.");
  await expect(page.getByText("Live facts: disabled")).toBeVisible();
});
