import { dataMapFixture, type DataMapCardFixture, type DataMapLayerId } from "./fixture";

type DataMapMetrics = {
  layerCount: number;
  cardCount: number;
  edgeCount: number;
  selectedCardId: string | null;
  mode: "presentation" | "analysis";
  reducedMotion: boolean;
  consoleErrors: number;
  sourceSafety: {
    rawPrivateDataIncluded: boolean;
    plaintextSecretsIncluded: boolean;
    localAbsolutePathsIncluded: boolean;
    writebackAllowed: boolean;
    proposalOnly: boolean;
  };
};

declare global {
  interface Window {
    __dataMapSpike?: {
      metrics: DataMapMetrics;
      fixture: typeof dataMapFixture;
      api: {
        selectCard: (cardId: string) => void;
        setMode: (mode: "presentation" | "analysis") => void;
        setReducedMotion: (value: boolean) => void;
      };
    };
  }
}

const app = requireElement<HTMLDivElement>("app");
const layerCountElement = requireElement<HTMLElement>("layerCount");
const cardCountElement = requireElement<HTMLElement>("cardCount");
const edgeCountElement = requireElement<HTMLElement>("edgeCount");
const selectedReadout = requireElement<HTMLElement>("selectedReadout");
const modeControl = requireElement<HTMLSelectElement>("modeControl");
const reducedMotionControl = requireElement<HTMLInputElement>("reducedMotionControl");
const inspectorTitle = requireElement<HTMLElement>("inspectorTitle");
const inspectorSummary = requireElement<HTMLElement>("inspectorSummary");
const inspectorMeta = requireElement<HTMLElement>("inspectorMeta");
const smokeStatus = requireElement<HTMLElement>("smokeStatus");

const layers = dataMapFixture.layers;
const cards = dataMapFixture.cards;
const edges = dataMapFixture.edges;
const cardsById = new Map(cards.map((card) => [card.card_id, card]));
const layerOrder: DataMapLayerId[] = ["source_layer", "topic_layer", "asset_layer", "action_layer"];
const smokeMode = new URLSearchParams(window.location.search).get("smoke") === "1";

const metrics: DataMapMetrics = {
  layerCount: layers.length,
  cardCount: cards.length,
  edgeCount: edges.length,
  selectedCardId: null,
  mode: "analysis",
  reducedMotion: false,
  consoleErrors: 0,
  sourceSafety: {
    rawPrivateDataIncluded: dataMapFixture.rawPrivateDataIncluded,
    plaintextSecretsIncluded: dataMapFixture.plaintextSecretsIncluded,
    localAbsolutePathsIncluded: dataMapFixture.localAbsolutePathsIncluded,
    writebackAllowed: dataMapFixture.writebackAllowed,
    proposalOnly: dataMapFixture.proposalOnly,
  },
};

window.addEventListener("error", () => {
  metrics.consoleErrors += 1;
  syncMetrics();
});

window.__dataMapSpike = {
  metrics,
  fixture: dataMapFixture,
  api: {
    selectCard,
    setMode,
    setReducedMotion,
  },
};

modeControl.addEventListener("change", () => setMode(modeControl.value === "presentation" ? "presentation" : "analysis"));
reducedMotionControl.addEventListener("change", () => setReducedMotion(reducedMotionControl.checked));
window.addEventListener("resize", render);

render();
selectCard(smokeMode ? "action-build-map-prototype" : "topic-data-to-action");
syncMetrics();

function render() {
  app.replaceChildren();
  const surface = document.createElement("section");
  surface.className = "data-map-surface";
  surface.setAttribute("aria-label", "Data Map 2.0 isolated spike");

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "edge-canvas");
  svg.setAttribute("aria-hidden", "true");
  surface.appendChild(svg);
  app.appendChild(surface);

  const cardPositions = layoutCards(surface);
  requestAnimationFrame(() => drawEdges(svg, cardPositions));
}

function layoutCards(surface: HTMLElement): Map<string, { x: number; y: number; width: number; height: number }> {
  const positions = new Map<string, { x: number; y: number; width: number; height: number }>();

  for (const layerId of layerOrder) {
    const layer = layers.find((item) => item.id === layerId);
    const column = document.createElement("section");
    column.className = "map-layer";
    column.dataset.layer = layerId;
    column.setAttribute("aria-label", layer?.label ?? layerId);

    const header = document.createElement("header");
    header.className = "layer-header";
    header.innerHTML = `<span>${layer?.label ?? layerId}</span><strong>${cards.filter((card) => card.layer === layerId).length}</strong>`;
    column.appendChild(header);

    for (const card of cards.filter((item) => item.layer === layerId)) {
      const button = document.createElement("button");
      button.type = "button";
      button.className = `map-card trend-${card.trend}`;
      button.dataset.cardId = card.card_id;
      button.dataset.mapCard = "true";
      button.setAttribute("aria-label", `${card.label} ${card.type}`);
      button.addEventListener("mouseenter", () => selectCard(card.card_id));
      button.addEventListener("focus", () => selectCard(card.card_id));
      button.addEventListener("click", () => selectCard(card.card_id));

      const handoffs = [
        "open_inspector",
        "jump_to_search",
        "jump_to_review",
        card.proposal_candidate ? "proposal_candidate" : "proposal_only",
      ];

      button.innerHTML = `
        <span class="card-type">${card.type}</span>
        <strong>${card.label}</strong>
        <span class="card-summary">${card.summary}</span>
        <span class="card-metrics">
          <span>strength ${formatPercent(card.strength)}</span>
          <span>${card.trend}</span>
          <span>${card.evidence_count} evidence</span>
          <span>${card.action_count} actions</span>
        </span>
        <span class="handoffs">${handoffs.map((item) => `<i>${item}</i>`).join("")}</span>
      `;
      column.appendChild(button);
    }

    surface.appendChild(column);
  }

  for (const element of surface.querySelectorAll<HTMLElement>(".map-card")) {
    const rect = element.getBoundingClientRect();
    const parentRect = surface.getBoundingClientRect();
    positions.set(element.dataset.cardId ?? "", {
      x: rect.left - parentRect.left,
      y: rect.top - parentRect.top,
      width: rect.width,
      height: rect.height,
    });
  }

  return positions;
}

function drawEdges(svg: SVGSVGElement, positions: Map<string, { x: number; y: number; width: number; height: number }>) {
  const surfaceRect = app.getBoundingClientRect();
  svg.setAttribute("viewBox", `0 0 ${surfaceRect.width} ${surfaceRect.height}`);
  svg.replaceChildren();

  const defs = document.createElementNS("http://www.w3.org/2000/svg", "defs");
  defs.innerHTML = `
    <marker id="arrow" markerHeight="8" markerWidth="8" orient="auto" refX="7" refY="4">
      <path d="M0,0 L8,4 L0,8 Z" fill="rgba(221,239,255,0.72)"></path>
    </marker>
  `;
  svg.appendChild(defs);

  for (const edge of edges) {
    const source = positions.get(edge.source_card_id);
    const target = positions.get(edge.target_card_id);
    if (!source || !target) continue;

    const startX = source.x + source.width;
    const startY = source.y + source.height / 2;
    const endX = target.x;
    const endY = target.y + target.height / 2;
    const bend = Math.max(48, (endX - startX) * 0.42);
    const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
    path.setAttribute("class", `flow-edge ${edge.kind}`);
    path.dataset.edgeKind = edge.kind;
    path.dataset.matchedReason = edge.matched_reason;
    path.setAttribute("d", `M ${startX} ${startY} C ${startX + bend} ${startY}, ${endX - bend} ${endY}, ${endX} ${endY}`);
    path.setAttribute("stroke-width", String(1.5 + edge.strength * 4));
    path.setAttribute("opacity", metrics.reducedMotion ? "0.5" : String(0.42 + edge.confidence * 0.4));
    path.setAttribute("marker-end", "url(#arrow)");
    svg.appendChild(path);
  }
}

function selectCard(cardId: string) {
  const card = cardsById.get(cardId);
  if (!card) return;
  metrics.selectedCardId = card.card_id;
  selectedReadout.textContent = card.label;
  inspectorTitle.textContent = card.label;
  inspectorSummary.textContent = card.summary;
  inspectorMeta.replaceChildren(...buildInspectorMeta(card));

  for (const node of app.querySelectorAll<HTMLElement>(".map-card")) {
    node.dataset.selected = node.dataset.cardId === card.card_id ? "true" : "false";
  }

  syncMetrics();
}

function buildInspectorMeta(card: DataMapCardFixture): HTMLElement[] {
  const rows = [
    ["type", card.type],
    ["layer", card.layer],
    ["strength", formatPercent(card.strength)],
    ["trend", card.trend],
    ["confidence", formatPercent(card.confidence)],
    ["evidence_count", String(card.evidence_count)],
    ["action_count", String(card.action_count)],
    ["matched_reason", card.matched_reason],
    ["inspector_link", card.inspector_link],
    ["handoff", "open_inspector / jump_to_search / jump_to_review"],
    ["proposal_candidate", String(card.proposal_candidate)],
    ["source_scope", card.source_scope],
  ];

  return rows.map(([label, value]) => {
    const row = document.createElement("p");
    row.innerHTML = `<span>${label}</span><strong>${value}</strong>`;
    return row;
  });
}

function setMode(mode: "presentation" | "analysis") {
  metrics.mode = mode;
  document.body.dataset.mode = mode;
  syncMetrics();
}

function setReducedMotion(value: boolean) {
  metrics.reducedMotion = value;
  document.body.dataset.reducedMotion = String(value);
  render();
  if (metrics.selectedCardId) selectCard(metrics.selectedCardId);
  syncMetrics();
}

function syncMetrics() {
  layerCountElement.textContent = String(metrics.layerCount);
  cardCountElement.textContent = String(metrics.cardCount);
  edgeCountElement.textContent = String(metrics.edgeCount);
  smokeStatus.textContent = JSON.stringify({
    status: metrics.consoleErrors === 0 ? "ready" : "console_error",
    data_to_action_flow: dataMapFixture.workflow.data_to_action_flow,
    selectedCardId: metrics.selectedCardId,
    ...metrics.sourceSafety,
  });
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`;
}

function requireElement<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing required element: ${id}`);
  }
  return element as T;
}
