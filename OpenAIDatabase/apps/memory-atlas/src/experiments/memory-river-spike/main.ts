import * as d3 from "d3";
import {
  memoryRiverFixture,
  type RiverBandFixture,
  type RiverEventFixture,
  type RiverLaneFixture,
  type RiverMarkerFixture,
} from "./fixture";

type RiverMetrics = {
  laneCount: number;
  eventCount: number;
  zoomK: number;
  brushRange: [string, string] | null;
  hoveredId: string | null;
  reducedMotion: boolean;
  consoleErrors: number;
  d3ScaleUtc: boolean;
  d3Zoom: boolean;
  d3Brush: boolean;
};

declare global {
  interface Window {
    __memoryRiverSpike?: {
      metrics: RiverMetrics;
      fixture: typeof memoryRiverFixture;
      api: {
        reset: () => void;
        setReducedMotion: (value: boolean) => void;
      };
    };
  }
}

const app = requireElement<HTMLDivElement>("app");
const laneCountElement = requireElement<HTMLElement>("laneCount");
const eventCountElement = requireElement<HTMLElement>("eventCount");
const zoomReadoutElement = requireElement<HTMLElement>("zoomReadout");
const brushReadoutElement = requireElement<HTMLElement>("brushReadout");
const statusLine = requireElement<HTMLElement>("statusLine");
const hoverCard = requireElement<HTMLElement>("hoverCard");
const modeControl = requireElement<HTMLSelectElement>("modeControl");
const reducedMotionControl = requireElement<HTMLInputElement>("reducedMotionControl");
const resetButton = requireElement<HTMLButtonElement>("resetButton");
const smokeStatus = requireElement<HTMLElement>("smokeStatus");

const smokeMode = new URLSearchParams(window.location.search).get("smoke") === "1";
const dateFormat = d3.utcFormat("%Y-%m-%d");
const tickFormat = d3.utcFormat("%b %d");
const monthFormat = d3.utcFormat("%b");
const margin = { top: 168, right: 96, bottom: 118, left: 190 };
const brushHeight = 54;
const lanes = memoryRiverFixture.lanes;
const events = memoryRiverFixture.events;
const bands = memoryRiverFixture.blackHoleBands;
const protoStars = memoryRiverFixture.protoStars;

const metrics: RiverMetrics = {
  laneCount: lanes.length,
  eventCount: events.length,
  zoomK: 1,
  brushRange: null,
  hoveredId: null,
  reducedMotion: false,
  consoleErrors: 0,
  d3ScaleUtc: true,
  d3Zoom: true,
  d3Brush: true,
};

window.addEventListener("error", () => {
  metrics.consoleErrors += 1;
  syncMetrics();
});

window.__memoryRiverSpike = {
  metrics,
  fixture: memoryRiverFixture,
  api: {
    reset,
    setReducedMotion,
  },
};

const svg = d3
  .select(app)
  .append("svg")
  .attr("class", "river-svg")
  .attr("role", "img")
  .attr("aria-label", "Memory River interactive spike")
  .node();

if (!svg) {
  throw new Error("Failed to create river SVG");
}

const svgSelection = d3.select<SVGSVGElement, unknown>(svg);
const defs = svgSelection.append("defs");
const backdropGroup = svgSelection.append("g").attr("data-layer", "density-backdrop");
const bandGroup = svgSelection.append("g").attr("data-layer", "black-hole-band");
const laneGroup = svgSelection.append("g").attr("data-layer", "theme-lanes");
const currentGroup = svgSelection.append("g").attr("data-layer", "river-currents");
const markerGroup = svgSelection.append("g").attr("data-layer", "markers");
const eventGroup = svgSelection.append("g").attr("data-layer", "event-pulses");
const axisGroup = svgSelection.append("g").attr("data-layer", "axis");
const brushGroup = svgSelection.append("g").attr("data-layer", "brush");
const feedbackGroup = svgSelection.append("g").attr("data-layer", "feedback");

let width = window.innerWidth;
let height = window.innerHeight;
let innerWidth = 0;
let innerHeight = 0;
let laneStep = 0;
let currentX = d3.scaleUtc();
let baseX = d3.scaleUtc();
let activeBrushRange: [Date, Date] | null = null;
let movingBrush = false;

const fullDomain = computeFullDomain();
currentX = d3.scaleUtc().domain(fullDomain);
baseX = d3.scaleUtc().domain(fullDomain);

const zoomBehavior = d3
  .zoom<SVGSVGElement, unknown>()
  .scaleExtent([1, 10])
  .filter((event: Event) => {
    const target = event.target as Element | null;
    return !target?.closest(".brush");
  })
  .on("zoom", (event: d3.D3ZoomEvent<SVGSVGElement, unknown>) => {
    currentX = event.transform.rescaleX(baseX);
    metrics.zoomK = Number(event.transform.k.toFixed(2));
    renderScene();
    syncMetrics();
  });

const brushBehavior = d3
  .brushX<unknown>()
  .on("brush end", (event: d3.D3BrushEvent<unknown>) => {
    if (movingBrush) {
      return;
    }
    if (!event.selection) {
      activeBrushRange = null;
      metrics.brushRange = null;
      statusLine.textContent = "Brush cleared. 时间河恢复为全窗口可读状态。";
      syncMetrics();
      return;
    }
    const [x0, x1] = event.selection as [number, number];
    const start = currentX.invert(x0);
    const end = currentX.invert(x1);
    activeBrushRange = start <= end ? [start, end] : [end, start];
    metrics.brushRange = [dateFormat(activeBrushRange[0]), dateFormat(activeBrushRange[1])];
    statusLine.textContent = `Brush locked ${dateFormat(activeBrushRange[0])} -> ${dateFormat(activeBrushRange[1])}`;
    pulseFeedback(selectionCrossesSignal(activeBrushRange));
    syncMetrics();
  });

svgSelection.call(zoomBehavior);
resetButton.addEventListener("click", reset);
reducedMotionControl.addEventListener("change", () => setReducedMotion(reducedMotionControl.checked));
modeControl.addEventListener("change", () => renderScene());
window.addEventListener("resize", () => {
  resize();
  renderScene();
});

resize();
renderScene();
syncMetrics();

if (smokeMode) {
  const smokeStart = new Date("2026-03-01T00:00:00Z");
  const smokeEnd = new Date("2026-05-01T00:00:00Z");
  activeBrushRange = [smokeStart, smokeEnd];
  metrics.brushRange = [dateFormat(smokeStart), dateFormat(smokeEnd)];
  moveBrushToRange(activeBrushRange);
  statusLine.textContent = "Smoke brush range applied.";
  syncMetrics();
}

function resize() {
  width = window.innerWidth;
  height = window.innerHeight;
  innerWidth = Math.max(360, width - margin.left - margin.right);
  innerHeight = Math.max(300, height - margin.top - margin.bottom);
  laneStep = innerHeight / Math.max(1, lanes.length);
  const currentDomain = currentX.domain();
  baseX = d3.scaleUtc().domain(fullDomain).range([margin.left, width - margin.right]);
  currentX = d3.scaleUtc().domain(currentDomain).range([margin.left, width - margin.right]);
  svgSelection.attr("viewBox", `0 0 ${width} ${height}`);
  zoomBehavior.translateExtent([
    [margin.left, margin.top],
    [width - margin.right, height - margin.bottom],
  ]);
  brushBehavior.extent([
    [margin.left, height - margin.bottom + 26],
    [width - margin.right, height - margin.bottom + 26 + brushHeight],
  ]);
}

function renderScene() {
  drawDefs();
  drawDensityBackdrop();
  drawBlackHoleBands();
  drawLanes();
  drawRiverCurrents();
  drawProtoStars();
  drawEvents();
  drawAxis();
  drawBrush();
  syncMetrics();
}

function drawDefs() {
  defs.selectAll("*").remove();
  for (const lane of lanes) {
    const gradient = defs
      .append("linearGradient")
      .attr("id", `${lane.id}-gradient`)
      .attr("x1", "0%")
      .attr("x2", "100%")
      .attr("y1", "0%")
      .attr("y2", "0%");

    gradient.append("stop").attr("offset", "0%").attr("stop-color", lane.color).attr("stop-opacity", 0.05);
    gradient.append("stop").attr("offset", "45%").attr("stop-color", lane.color).attr("stop-opacity", 0.46);
    gradient.append("stop").attr("offset", "100%").attr("stop-color", lane.color).attr("stop-opacity", 0.1);
  }

  const protoGradient = defs.append("radialGradient").attr("id", "proto-glow");
  protoGradient.append("stop").attr("offset", "0%").attr("stop-color", "#ffef9a").attr("stop-opacity", 0.92);
  protoGradient.append("stop").attr("offset", "100%").attr("stop-color", "#ffef9a").attr("stop-opacity", 0);
}

function drawDensityBackdrop() {
  const months = d3.utcMonth.range(fullDomain[0], d3.utcMonth.offset(fullDomain[1], 1));
  const maxDensity = Math.max(...months.map(monthDensity), 1);
  const monthWidth = Math.max(10, innerWidth / Math.max(1, months.length));

  const rects = backdropGroup.selectAll<SVGRectElement, Date>("rect").data(months, (date) => date.toISOString());
  rects.exit().remove();
  rects
    .enter()
    .append("rect")
    .merge(rects)
    .attr("x", (date) => currentX(date))
    .attr("y", margin.top - 34)
    .attr("width", monthWidth)
    .attr("height", innerHeight + 56)
    .attr("fill", "#8fd3ff")
    .attr("opacity", (date) => 0.03 + (monthDensity(date) / maxDensity) * 0.12);
}

function drawBlackHoleBands() {
  const bandSelection = bandGroup.selectAll<SVGGElement, RiverBandFixture>("g").data(bands, (band) => band.id);
  bandSelection.exit().remove();
  const entered = bandSelection.enter().append("g").attr("class", "black-hole-band");
  entered.append("rect");
  entered.append("text");

  entered
    .merge(bandSelection)
    .on("pointerover", (_event, band) => showBandCard(band))
    .on("pointerout", clearHover)
    .select("rect")
    .attr("x", (band) => currentX(new Date(band.startAt)))
    .attr("y", margin.top - 24)
    .attr("width", (band) => Math.max(8, currentX(new Date(band.endAt)) - currentX(new Date(band.startAt))))
    .attr("height", innerHeight + 42)
    .attr("fill", "#130914")
    .attr("stroke", "#ff7b7b")
    .attr("stroke-width", 1)
    .attr("opacity", (band) => 0.32 + band.intensity * 0.24);

  entered
    .merge(bandSelection)
    .select("text")
    .attr("x", (band) => currentX(new Date(band.startAt)) + 10)
    .attr("y", margin.top - 8)
    .attr("fill", "#ffb0b0")
    .attr("font-size", 12)
    .attr("font-weight", 700)
    .text((band) => band.label);
}

function drawLanes() {
  const laneSelection = laneGroup.selectAll<SVGGElement, RiverLaneFixture>("g").data(lanes, (lane) => lane.id);
  laneSelection.exit().remove();
  const entered = laneSelection.enter().append("g").attr("class", "lane-row");
  entered.append("line");
  entered.append("text").attr("class", "lane-label");
  entered.append("text").attr("class", "lane-level");

  const merged = entered
    .merge(laneSelection)
    .attr("transform", (_lane, index) => `translate(0 ${laneCenter(index)})`)
    .on("pointerover", (_event, lane) => showLaneCard(lane))
    .on("pointerout", clearHover);

  merged
    .select("line")
    .attr("x1", margin.left)
    .attr("x2", width - margin.right)
    .attr("y1", 0)
    .attr("y2", 0)
    .attr("stroke", "rgba(180, 221, 255, 0.16)")
    .attr("stroke-width", 1);

  merged
    .select(".lane-label")
    .attr("x", 24)
    .attr("y", -4)
    .text((lane) => lane.label);

  merged
    .select(".lane-level")
    .attr("x", 24)
    .attr("y", 13)
    .text((lane) => `${lane.level} · ${lane.evidenceCount} evidence`);
}

function drawRiverCurrents() {
  const area = d3
    .area<{ date: Date; width: number }>()
    .curve(d3.curveCatmullRom.alpha(0.5))
    .x((sample) => currentX(sample.date))
    .y0((sample) => sample.width * -1)
    .y1((sample) => sample.width);

  const laneSelection = currentGroup.selectAll<SVGPathElement, RiverLaneFixture>("path").data(lanes, (lane) => lane.id);
  laneSelection.exit().remove();
  laneSelection
    .enter()
    .append("path")
    .attr("class", "river-current")
    .merge(laneSelection)
    .attr("transform", (_lane, index) => `translate(0 ${laneCenter(index)})`)
    .attr("d", (lane) => area(laneSamples(lane)) ?? "")
    .attr("fill", (lane) => `url(#${lane.id}-gradient)`)
    .attr("stroke", (lane) => lane.color)
    .attr("stroke-width", 1.3)
    .attr("stroke-opacity", 0.55)
    .attr("stroke-dasharray", "18 54");
}

function drawProtoStars() {
  const markerSelection = markerGroup.selectAll<SVGGElement, RiverMarkerFixture>("g").data(protoStars, (marker) => marker.id);
  markerSelection.exit().remove();
  const entered = markerSelection.enter().append("g").attr("class", "proto-star-marker");
  entered.append("circle").attr("class", "proto-glow");
  entered.append("path").attr("class", "proto-symbol");
  entered.append("text");

  const merged = entered
    .merge(markerSelection)
    .attr("transform", (marker) => `translate(${currentX(new Date(marker.occurredAt))} ${laneCenter(laneIndex(marker.laneId))})`)
    .on("pointerover", (_event, marker) => showMarkerCard(marker))
    .on("pointerout", clearHover);

  merged.select(".proto-glow").attr("r", 25).attr("fill", "url(#proto-glow)");
  merged
    .select(".proto-symbol")
    .attr("d", "M0,-14 L5,-4 L16,0 L5,4 L0,14 L-5,4 L-16,0 L-5,-4 Z")
    .attr("fill", "#ffef9a")
    .attr("stroke", "#fff9c8")
    .attr("stroke-width", 1.2);
  merged
    .select("text")
    .attr("x", 16)
    .attr("y", -18)
    .attr("fill", "#fff3ad")
    .attr("font-size", 12)
    .attr("font-weight", 700)
    .text((marker) => marker.label);
}

function drawEvents() {
  const eventSelection = eventGroup.selectAll<SVGGElement, RiverEventFixture>("g").data(events, (event) => event.id);
  eventSelection.exit().remove();
  const entered = eventSelection.enter().append("g").attr("class", "event-pulse");
  entered.append("line");
  entered.append("circle");
  entered.append("text");

  const merged = entered
    .merge(eventSelection)
    .attr("transform", (event) => `translate(${currentX(new Date(event.occurredAt))} ${laneCenter(laneIndex(event.laneId))})`)
    .on("pointerover", (_event, event) => showEventCard(event))
    .on("pointerout", clearHover);

  merged
    .select("line")
    .attr("x1", 0)
    .attr("x2", 0)
    .attr("y1", -22)
    .attr("y2", 22)
    .attr("stroke", "#eef6ff")
    .attr("stroke-opacity", 0.18)
    .attr("stroke-width", 1);

  merged
    .select("circle")
    .attr("r", (event) => 5 + event.intensity * 9)
    .attr("fill", (event) => laneById(event.laneId).color)
    .attr("fill-opacity", 0.72)
    .attr("stroke", "#eef6ff")
    .attr("stroke-width", 1.1);

  merged
    .select("text")
    .attr("x", 11)
    .attr("y", -14)
    .attr("fill", "#dcecff")
    .attr("font-size", 11)
    .attr("opacity", metrics.zoomK >= 1.7 || modeControl.value === "analysis" ? 1 : 0)
    .text((event) => event.label);
}

function drawAxis() {
  axisGroup.attr("transform", `translate(0 ${height - margin.bottom + 14})`);
  const ticks = width < 780 ? 5 : 8;
  axisGroup.call(
    d3
      .axisBottom<Date>(currentX)
      .ticks(ticks)
      .tickFormat((date) => tickFormat(date)),
  );
  axisGroup.selectAll("path,line").attr("stroke", "rgba(210, 235, 255, 0.32)");
  axisGroup.selectAll("text").attr("fill", "#c5d9ec").attr("font-size", 11);

  const monthTicks = d3.utcMonth.range(fullDomain[0], d3.utcMonth.offset(fullDomain[1], 1));
  const labels = axisGroup.selectAll<SVGTextElement, Date>(".month-label").data(monthTicks, (date) => date.toISOString());
  labels.exit().remove();
  labels
    .enter()
    .append("text")
    .attr("class", "month-label")
    .merge(labels)
    .attr("x", (date) => currentX(date))
    .attr("y", 38)
    .attr("fill", "#6f859a")
    .attr("font-size", 10)
    .text((date) => monthFormat(date));
}

function drawBrush() {
  brushGroup.call(brushBehavior);
  brushGroup.selectAll(".overlay").attr("cursor", "crosshair").attr("fill", "transparent");
  brushGroup.selectAll(".selection").attr("fill", "rgba(143, 211, 255, 0.22)").attr("stroke", "#8fd3ff");
  brushGroup.selectAll(".handle").attr("fill", "#8fd3ff");
  if (activeBrushRange) {
    moveBrushToRange(activeBrushRange);
  }
}

function moveBrushToRange(range: [Date, Date]) {
  movingBrush = true;
  brushGroup.call(brushBehavior.move, range.map((date) => currentX(date)) as [number, number]);
  movingBrush = false;
}

function reset() {
  activeBrushRange = null;
  metrics.brushRange = null;
  metrics.zoomK = 1;
  currentX = baseX.copy();
  svgSelection.call(zoomBehavior.transform, d3.zoomIdentity);
  brushGroup.call(brushBehavior.move, null);
  statusLine.textContent = "Zoom and brush reset.";
  renderScene();
}

function setReducedMotion(value: boolean) {
  reducedMotionControl.checked = value;
  metrics.reducedMotion = value;
  document.body.dataset.reducedMotion = value ? "true" : "false";
  statusLine.textContent = value ? "Reduced motion enabled. 连续河流动画已关闭。" : "Reduced motion disabled. 河流反馈动画恢复。";
  syncMetrics();
}

function laneSamples(lane: RiverLaneFixture) {
  const samples = d3.utcWeek.range(fullDomain[0], d3.utcDay.offset(fullDomain[1], 7));
  const laneEvents = events.filter((event) => event.laneId === lane.id);
  return samples.map((date) => {
    const widthScore = laneEvents.reduce((sum, event) => {
      const days = Math.abs(differenceDays(date, new Date(event.occurredAt)));
      return sum + event.intensity * Math.exp(-days / 28);
    }, 0);
    return {
      date,
      width: 10 + Math.min(1, widthScore) * (laneStep * 0.28),
    };
  });
}

function computeFullDomain(): [Date, Date] {
  const dates = [
    new Date(memoryRiverFixture.window.startAt),
    new Date(memoryRiverFixture.window.endAt),
    ...events.map((event) => new Date(event.occurredAt)),
    ...bands.flatMap((band) => [new Date(band.startAt), new Date(band.endAt)]),
    ...protoStars.map((marker) => new Date(marker.occurredAt)),
  ];
  const extent = d3.extent(dates);
  if (!extent[0] || !extent[1]) {
    return [new Date("2026-01-01T00:00:00Z"), new Date("2026-06-30T00:00:00Z")];
  }
  return [d3.utcDay.offset(extent[0], -7), d3.utcDay.offset(extent[1], 7)];
}

function laneCenter(index: number) {
  return margin.top + laneStep * index + laneStep / 2;
}

function laneIndex(laneId: string) {
  return Math.max(0, lanes.findIndex((lane) => lane.id === laneId));
}

function laneById(laneId: string) {
  const lane = lanes.find((candidate) => candidate.id === laneId);
  if (!lane) {
    throw new Error(`Unknown lane id: ${laneId}`);
  }
  return lane;
}

function monthDensity(month: Date) {
  return events.reduce((sum, event) => {
    const eventDate = new Date(event.occurredAt);
    return eventDate.getUTCFullYear() === month.getUTCFullYear() && eventDate.getUTCMonth() === month.getUTCMonth()
      ? sum + event.intensity
      : sum;
  }, 0.15);
}

function differenceDays(left: Date, right: Date) {
  return (left.getTime() - right.getTime()) / 86_400_000;
}

function selectionCrossesSignal(range: [Date, Date]) {
  const crossesBand = bands.some((band) => {
    const start = new Date(band.startAt);
    const end = new Date(band.endAt);
    return start <= range[1] && end >= range[0];
  });
  const crossesProtoStar = protoStars.some((marker) => {
    const date = new Date(marker.occurredAt);
    return date >= range[0] && date <= range[1];
  });
  return crossesBand || crossesProtoStar;
}

function pulseFeedback(active: boolean) {
  feedbackGroup.selectAll("*").remove();
  if (!active) {
    return;
  }
  feedbackGroup
    .append("rect")
    .attr("class", "feedback-pulse")
    .attr("x", margin.left)
    .attr("y", margin.top - 34)
    .attr("width", innerWidth)
    .attr("height", innerHeight + 56)
    .attr("fill", "none")
    .attr("stroke", "#ffef9a")
    .attr("stroke-width", 2)
    .attr("stroke-opacity", 0.62);
}

function showLaneCard(lane: RiverLaneFixture) {
  metrics.hoveredId = lane.id;
  hoverCard.dataset.empty = "false";
  hoverCard.innerHTML = `<h2>${lane.label}</h2><p>${lane.summary}</p><p>Level: ${lane.level} · Evidence: ${lane.evidenceCount}</p>`;
  syncMetrics();
}

function showEventCard(event: RiverEventFixture) {
  metrics.hoveredId = event.id;
  hoverCard.dataset.empty = "false";
  hoverCard.innerHTML = `<h2>${event.label}</h2><p>${event.summary}</p><p>${dateFormat(new Date(event.occurredAt))} · Kind: ${event.kind} · Confidence: ${Math.round(event.confidence * 100)}% · Evidence: ${event.evidenceCount}</p>`;
  syncMetrics();
}

function showBandCard(band: RiverBandFixture) {
  metrics.hoveredId = band.id;
  hoverCard.dataset.empty = "false";
  hoverCard.innerHTML = `<h2>${band.label}</h2><p>${band.summary}</p><p>${dateFormat(new Date(band.startAt))} -> ${dateFormat(new Date(band.endAt))} · Suggested action: ${band.suggestedAction} · Evidence: ${band.evidenceCount}</p>`;
  syncMetrics();
}

function showMarkerCard(marker: RiverMarkerFixture) {
  metrics.hoveredId = marker.id;
  hoverCard.dataset.empty = "false";
  hoverCard.innerHTML = `<h2>${marker.label}</h2><p>${marker.summary}</p><p>${dateFormat(new Date(marker.occurredAt))} · Proto-Star confidence: ${Math.round(marker.confidence * 100)}% · Evidence: ${marker.evidenceCount}</p>`;
  syncMetrics();
}

function clearHover() {
  metrics.hoveredId = null;
  hoverCard.dataset.empty = "true";
  hoverCard.innerHTML = "<h2>Hover river element</h2><p>悬停 event pulse、theme lane、Black Hole band 或 Proto-Star marker，可查看 redacted 摘要与 evidence count。</p>";
  syncMetrics();
}

function syncMetrics() {
  laneCountElement.textContent = String(metrics.laneCount);
  eventCountElement.textContent = String(metrics.eventCount);
  zoomReadoutElement.textContent = `${metrics.zoomK.toFixed(2)}x`;
  brushReadoutElement.textContent = metrics.brushRange ? `${metrics.brushRange[0]} -> ${metrics.brushRange[1]}` : "none";
  smokeStatus.textContent = JSON.stringify({
    ready: true,
    metrics,
    sourceSafety: {
      rawPrivateDataIncluded: memoryRiverFixture.rawPrivateDataIncluded,
      plaintextSecretsIncluded: memoryRiverFixture.plaintextSecretsIncluded,
      localAbsolutePathsIncluded: memoryRiverFixture.localAbsolutePathsIncluded,
      writebackAllowed: memoryRiverFixture.writebackAllowed,
    },
  });
}

function requireElement<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Missing element #${id}`);
  }
  return element as T;
}
