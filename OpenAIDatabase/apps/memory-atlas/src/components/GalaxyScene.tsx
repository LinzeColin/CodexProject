import { Gauge, Layers, Pause, Play, RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import type { CSSProperties } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  AdditiveBlending,
  BufferGeometry,
  CanvasTexture,
  Color,
  DynamicDrawUsage,
  Float32BufferAttribute,
  Group,
  LinearFilter,
  LineBasicMaterial,
  LineSegments,
  Mesh,
  MeshBasicMaterial,
  PerspectiveCamera,
  PlaneGeometry,
  Points,
  PointsMaterial,
  Raycaster,
  Scene,
  SphereGeometry,
  TorusGeometry,
  Vector2,
  Vector3,
  WebGLRenderer,
} from "three";
import {
  MEMORY_STARFIELD_PARAMS,
  type MemoryTerrainType,
  type StarfieldQuality,
} from "../config/memoryStarfieldParameters";
import type { GalaxyRendererMode } from "../config/visualFlags";
import { normalizeMemoryTier } from "../data/atlas";
import type { AtlasEdge, AtlasNode } from "../types";

interface GalaxySceneProps {
  nodes: AtlasNode[];
  edges: AtlasEdge[];
  rendererMode: GalaxyRendererMode;
  selectedNode: AtlasNode | null;
  onSelectNode: (node: AtlasNode) => void;
}

interface PointerState {
  dragging: boolean;
  moved: boolean;
  x: number;
  y: number;
}

interface GalaxySignal {
  frame: number;
  renderTicks: number;
  fps: number;
  averageFrameMs: number;
  sampleSeconds: number;
  lit: number;
  alpha: number;
  max: number;
  hash: number;
  width: number;
  height: number;
  sampleWidth: number;
  sampleHeight: number;
  calls: number;
  triangles: number;
  points: number;
  focusNodeId: string | null;
  highlightedNeighborCount: number;
  focusVisibleNeighborCount: number;
  focusHiddenNeighborCount: number;
  focusPrimaryNeighborCount: number;
  focusSecondaryNeighborCount: number;
  cameraX: number;
  cameraY: number;
  cameraZ: number;
  cameraDistance: number;
  rendererMode: GalaxyRendererMode;
  quality: StarfieldQuality;
  targetFps: number;
  minFps: number;
  adaptiveQualityEnabled: boolean;
  adaptiveQualityDecision: AdaptiveQualityDecision;
  flowFieldStrength: number;
  flowPaused: boolean;
  starfieldMode: StarfieldViewMode;
  terrainFeatureCount: number;
  parameterSource: string;
  fallbackMode: "webgl" | "low-quality" | "legacy";
}

type AdaptiveQualityDecision = "hold" | "downgrade-to-mid" | "downgrade-to-low" | "upgrade-to-mid" | "upgrade-to-high";

interface GalaxyPerformanceSnapshot {
  fps: number;
  averageFrameMs: number;
  sampleSeconds: number;
  quality: StarfieldQuality;
  targetFps: number;
  minFps: number;
  adaptiveQualityEnabled: boolean;
  adaptiveQualityDecision: AdaptiveQualityDecision;
}

interface GalaxyLifecycleSignal {
  mountedAt: number;
  disposedAt: number | null;
  activeRaf: boolean;
  rafCancelled: boolean;
  rendererDisposed: boolean;
  webglContextLost: boolean;
  workersClosed: boolean;
  audioContextClosed: boolean;
  frameAtDispose: number | null;
  renderTicksAtDispose: number | null;
}

interface SceneNode {
  node: AtlasNode;
  position: { x: number; y: number; z: number };
}

interface HoverPreview {
  node: AtlasNode;
  x: number;
  y: number;
  linkedCount: number;
  visibleNeighborCount: number;
  hiddenNeighborCount: number;
}

type FocusNeighborLayer = "primary" | "secondary";
type StarfieldViewMode = "presentation" | "analysis";

interface FocusNeighbor {
  id: string;
  weight: number;
  rank: number;
  layer: FocusNeighborLayer;
}

interface FocusNeighborhood {
  focusId: string;
  totalNeighborCount: number;
  visibleNeighborCount: number;
  hiddenNeighborCount: number;
  primaryNeighborCount: number;
  secondaryNeighborCount: number;
  neighbors: FocusNeighbor[];
  visibleNeighborIds: Set<string>;
}

interface MemoryStarfieldParticleAttributes {
  mass: number;
  size: number;
  brightness: number;
  color: string;
  recencyScore: number;
  confidenceScore: number;
  interactionScore: number;
  trailStrength: number;
  terrainType: MemoryTerrainType | null;
}

interface TerrainSummaryRow {
  type: MemoryTerrainType;
  label: string;
  explanation: string;
  count: number;
  sampleLabels: string[];
  semanticRole: string;
  intensity: number;
  averageRoi: number;
  capabilitySignal: string;
}

interface TerrainSummary {
  total: number;
  rows: TerrainSummaryRow[];
  semanticCoverage: number;
  dominantLabel: string;
  analysisNote: string;
}

interface GalaxyRoiGradientRow {
  id: string;
  label: string;
  count: number;
  averageRoi: number;
  intensity: number;
}

interface GalaxyRoiGradientSummary {
  averageRoi: number;
  highValueCount: number;
  capabilityGrowthCount: number;
  rows: GalaxyRoiGradientRow[];
  note: string;
}

declare global {
  interface Window {
    __memoryAtlasGalaxySignal?: () => GalaxySignal;
    __memoryAtlasGalaxyDebugTargets?: () => Array<{ id: string; x: number; y: number; linkedCount: number }>;
    __memoryAtlasGalaxyLifecycle?: GalaxyLifecycleSignal;
  }
}

const MAX_RENDERED_NODES = 900;
const MAX_FOCUS_PRIMARY_NEIGHBORS = 10;
const MAX_FOCUS_SECONDARY_NEIGHBORS = 18;
const MAX_FOCUS_VISIBLE_NEIGHBORS = MAX_FOCUS_PRIMARY_NEIGHBORS + MAX_FOCUS_SECONDARY_NEIGHBORS;
const MAX_PULSE_NEIGHBORS = MAX_FOCUS_VISIBLE_NEIGHBORS;
const GALAXY_ARM_COLORS = ["#bcdfff", "#d7e8ff", "#a7ecff", "#e5d6ff", "#c8f7e7", "#f7c8dd"];
const GALAXY_ARM_COUNT = 6;
const STARFIELD_QUALITY_SETTINGS = MEMORY_STARFIELD_PARAMS.qualitySettings;
const STAGE7_PERFORMANCE_THRESHOLDS = {
  highMinFps: 45,
  midMinFps: 30,
  adaptiveUpgradeFps: 52,
  sampleWindowMs: 1200,
  adaptiveWarmupMs: 2400,
  adaptiveCooldownMs: 4200,
};
const MEMORY_TERRAIN_ORDER: MemoryTerrainType[] = ["ridge", "shoreline", "valley", "basin", "fault-line"];
const MEMORY_TERRAIN_VISUALS: Record<MemoryTerrainType, { label: string; explanation: string; color: string; opacity: number }> = {
  ridge: {
    label: "山脉 / Ridge",
    explanation: "persistent high-ROI theme",
    color: "#7ee8d4",
    opacity: 0.2,
  },
  shoreline: {
    label: "城市/图书馆岸线 / Shoreline",
    explanation: "boundary between mature and emerging topics",
    color: "#bcdfff",
    opacity: 0.16,
  },
  valley: {
    label: "河谷 / Valley",
    explanation: "underdeveloped or inactive area",
    color: "#8fd3ff",
    opacity: 0.12,
  },
  basin: {
    label: "遗迹盆地 / Basin",
    explanation: "repeated low-value loop",
    color: "#94a3b8",
    opacity: 0.14,
  },
  "fault-line": {
    label: "工业断层 / Fault line",
    explanation: "contradiction or conflict zone",
    color: "#f48fb1",
    opacity: 0.18,
  },
};

function performanceMinFps(quality: StarfieldQuality): number {
  if (quality === "high") return STAGE7_PERFORMANCE_THRESHOLDS.highMinFps;
  if (quality === "mid") return STAGE7_PERFORMANCE_THRESHOLDS.midMinFps;
  return 1;
}

function createPerformanceSnapshot(
  quality: StarfieldQuality,
  adaptiveQualityEnabled: boolean,
  fps = 0,
  averageFrameMs = 0,
  sampleSeconds = 0,
  adaptiveQualityDecision: AdaptiveQualityDecision = "hold",
): GalaxyPerformanceSnapshot {
  return {
    fps: Number(fps.toFixed(1)),
    averageFrameMs: Number(averageFrameMs.toFixed(2)),
    sampleSeconds: Number(sampleSeconds.toFixed(2)),
    quality,
    targetFps: MEMORY_STARFIELD_PARAMS.performance.desktopTargetFps,
    minFps: performanceMinFps(quality),
    adaptiveQualityEnabled,
    adaptiveQualityDecision,
  };
}

function nextAdaptiveQualityDecision(
  quality: StarfieldQuality,
  fps: number,
  elapsedMs: number,
  msSinceLastChange: number,
): { decision: AdaptiveQualityDecision; nextQuality: StarfieldQuality | null } {
  if (
    elapsedMs < STAGE7_PERFORMANCE_THRESHOLDS.adaptiveWarmupMs
    || msSinceLastChange < STAGE7_PERFORMANCE_THRESHOLDS.adaptiveCooldownMs
  ) {
    return { decision: "hold", nextQuality: null };
  }
  if (quality === "high" && fps < STAGE7_PERFORMANCE_THRESHOLDS.highMinFps) {
    return { decision: "downgrade-to-mid", nextQuality: "mid" };
  }
  if (quality === "mid" && fps < STAGE7_PERFORMANCE_THRESHOLDS.midMinFps) {
    return { decision: "downgrade-to-low", nextQuality: "low" };
  }
  if (quality === "low" && fps >= STAGE7_PERFORMANCE_THRESHOLDS.highMinFps) {
    return { decision: "upgrade-to-mid", nextQuality: "mid" };
  }
  if (quality === "mid" && fps >= STAGE7_PERFORMANCE_THRESHOLDS.adaptiveUpgradeFps) {
    return { decision: "upgrade-to-high", nextQuality: "high" };
  }
  return { decision: "hold", nextQuality: null };
}

export function GalaxyScene({ nodes, edges, rendererMode, selectedNode, onSelectNode }: GalaxySceneProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const nebulaCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const pointerRef = useRef<PointerState>({ dragging: false, moved: false, x: 0, y: 0 });
  const rotationRef = useRef({ x: -0.14, y: 0.42 });
  const zoomRef = useRef(1);
  const selectedIdRef = useRef<string | null>(selectedNode?.id ?? null);
  const hoveredIdRef = useRef<string | null>(null);
  const flowFieldStrengthRef = useRef(1);
  const flowPausedRef = useRef(false);
  const starfieldModeRef = useRef<StarfieldViewMode>("presentation");
  const adaptiveQualityEnabledRef = useRef(true);
  const [renderError, setRenderError] = useState("");
  const [hoverPreview, setHoverPreview] = useState<HoverPreview | null>(null);
  const [starfieldQuality, setStarfieldQuality] = useState<StarfieldQuality>("mid");
  const [adaptiveQualityEnabled, setAdaptiveQualityEnabled] = useState(true);
  const [performanceSnapshot, setPerformanceSnapshot] = useState<GalaxyPerformanceSnapshot>(() => createPerformanceSnapshot("mid", true));
  const [flowFieldStrength, setFlowFieldStrength] = useState(1);
  const [flowPaused, setFlowPaused] = useState(false);
  const [starfieldMode, setStarfieldMode] = useState<StarfieldViewMode>("presentation");

  const qualitySettings = STARFIELD_QUALITY_SETTINGS[starfieldQuality];
  const renderNodeLimit = rendererMode === "memory-starfield" ? qualitySettings.maxNodes : MAX_RENDERED_NODES;
  const renderNodes = useMemo(() => nodes.slice(0, renderNodeLimit), [nodes, renderNodeLimit]);
  const renderItems = useMemo<SceneNode[]>(
    () => renderNodes.map((node) => ({ node, position: galaxyPosition(node) })),
    [renderNodes],
  );
  const nodeById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const renderableNodeIds = useMemo(() => new Set(renderNodes.map((node) => node.id)), [renderNodes]);
  const degreeById = useMemo(() => degreeMap(edges), [edges]);
  const latestNodeTime = useMemo(() => latestNodeTimestamp(nodes), [nodes]);
  const terrainSummary = useMemo(
    () => buildTerrainSummary(renderNodes, degreeById, latestNodeTime),
    [degreeById, latestNodeTime, renderNodes],
  );
  const roiGradientSummary = useMemo(
    () => buildGalaxyRoiGradientSummary(renderNodes),
    [renderNodes],
  );
  const selectedNeighborhood = useMemo(
    () => selectedNode ? buildFocusedNeighborhood(selectedNode.id, edges, renderableNodeIds) : emptyFocusedNeighborhood(""),
    [edges, renderableNodeIds, selectedNode?.id],
  );
  const selectedNeighborIds = selectedNeighborhood.visibleNeighborIds;
  const selectedEdgeCount = selectedNeighborhood.totalNeighborCount;
  const primaryNeighborCards = useMemo(
    () =>
      selectedNeighborhood.neighbors
        .filter((neighbor) => neighbor.layer === "primary")
        .map((neighbor) => ({ neighbor, node: nodeById.get(neighbor.id) }))
        .filter((item): item is { neighbor: FocusNeighbor; node: AtlasNode } => Boolean(item.node))
        .slice(0, MAX_FOCUS_PRIMARY_NEIGHBORS),
    [nodeById, selectedNeighborhood],
  );

  useEffect(() => {
    selectedIdRef.current = selectedNode?.id ?? null;
  }, [selectedNode?.id]);

  useEffect(() => {
    flowFieldStrengthRef.current = flowFieldStrength;
  }, [flowFieldStrength]);

  useEffect(() => {
    flowPausedRef.current = flowPaused;
  }, [flowPaused]);

  useEffect(() => {
    starfieldModeRef.current = starfieldMode;
  }, [starfieldMode]);

  useEffect(() => {
    adaptiveQualityEnabledRef.current = adaptiveQualityEnabled;
    setPerformanceSnapshot((snapshot) => ({
      ...snapshot,
      adaptiveQualityEnabled,
      quality: starfieldQuality,
      minFps: performanceMinFps(starfieldQuality),
    }));
  }, [adaptiveQualityEnabled, starfieldQuality]);

  useEffect(() => {
    const canvas = containerRef.current?.querySelector<HTMLCanvasElement>(".galaxy-webgl-canvas");
    if (!canvas) return;
    canvas.dataset.flowFrozen = rendererMode === "memory-starfield" && flowPaused ? "true" : "false";
    canvas.dataset.starfieldMode = rendererMode === "memory-starfield" ? starfieldMode : "legacy";
  }, [flowPaused, rendererMode, starfieldMode]);

  useEffect(() => {
    hoveredIdRef.current = null;
    setHoverPreview(null);
  }, [renderItems]);

  useEffect(() => {
    const containerElement = containerRef.current;
    const canvas = nebulaCanvasRef.current;
    if (!renderError || !containerElement || !canvas) return;
    const canvasElement = canvas;

    function draw() {
      renderNebulaCanvas(canvasElement, renderItems, edges);
    }

    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(containerElement);
    return () => observer.disconnect();
  }, [edges, renderError, renderItems]);

  useEffect(() => {
    const containerElement = containerRef.current;
    if (!containerElement) return;

    let renderer: WebGLRenderer;
    try {
      renderer = new WebGLRenderer({
        antialias: false,
        alpha: false,
        powerPreference: "high-performance",
        preserveDrawingBuffer: true,
      });
    } catch (error) {
      setRenderError(error instanceof Error ? `WebGL 渲染器初始化失败：${error.message}` : "WebGL 渲染器初始化失败。");
      return;
    }

    setRenderError("");
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(0x020308, 1);
    renderer.autoClear = true;
    renderer.domElement.className = "galaxy-webgl-canvas";
    renderer.domElement.dataset.nebulaTexture = "spiral-dust-cloud";
    renderer.domElement.dataset.rendererMode = rendererMode;
    renderer.domElement.dataset.quality = rendererMode === "memory-starfield" ? starfieldQuality : "legacy";
    renderer.domElement.dataset.adaptiveQuality = rendererMode === "memory-starfield" && adaptiveQualityEnabledRef.current ? "enabled" : "manual";
    renderer.domElement.dataset.flowField = rendererMode === "memory-starfield" ? "enabled" : "legacy-off";
    renderer.domElement.dataset.flowFrozen = rendererMode === "memory-starfield" && flowPaused ? "true" : "false";
    renderer.domElement.dataset.starfieldMode = rendererMode === "memory-starfield" ? starfieldMode : "legacy";
    containerElement.appendChild(renderer.domElement);

    const scene = new Scene();
    scene.background = new Color("#020308");
    const galaxyGroup = new Group();
    scene.add(galaxyGroup);
    const camera = new PerspectiveCamera(52, 1, 0.1, 1500);
    camera.position.set(0, 0, 285);
    camera.lookAt(0, 0, 0);

    const galaxyTexture = createWebglGalaxyTexture();
    const galaxyPlaneGeometry = new PlaneGeometry(470, 330);
    const galaxyPlaneMaterial = new MeshBasicMaterial({
      map: galaxyTexture,
      transparent: true,
      opacity: 0.58 + MEMORY_STARFIELD_PARAMS.visual.nebulaOpacity * 0.34,
      depthWrite: false,
      depthTest: false,
    });
    const galaxyPlane = new Mesh(galaxyPlaneGeometry, galaxyPlaneMaterial);
    galaxyPlane.position.set(0, 0, -54);
    galaxyPlane.rotation.z = -0.11;
    galaxyPlane.renderOrder = -10;
    galaxyGroup.add(galaxyPlane);

    const ambientPositions: number[] = [];
    const ambientColors: number[] = [];
    const armColors = GALAXY_ARM_COLORS;
    const ambientParticleCount = rendererMode === "memory-starfield" ? qualitySettings.ambientParticles : 7600;
    for (let i = 0; i < ambientParticleCount; i += 1) {
      const arm = i % armColors.length;
      const radius = 14 + Math.pow(stableUnit(`ambient-${i}`, "radius"), 0.72) * 226;
      const angle = (arm / armColors.length) * Math.PI * 2 + radius * 0.029 + (stableUnit(`ambient-${i}`, "angle") - 0.5) * 0.48;
      const thickness = (stableUnit(`ambient-${i}`, "thickness") - 0.5) * (12 + radius * 0.07);
      const z = (stableUnit(`ambient-${i}`, "depth") - 0.5) * (18 + radius * 0.36);
      ambientPositions.push(
        Math.cos(angle) * radius + Math.cos(angle + Math.PI / 2) * thickness,
        Math.sin(angle) * radius * 0.68 + Math.sin(angle + Math.PI / 2) * thickness,
        z,
      );
      const color = new Color(armColors[arm]);
      const fade = Math.max(0.12, 1 - radius / 282);
      ambientColors.push(color.r * fade, color.g * fade, color.b * fade);
    }
    const ambientGeometry = new BufferGeometry();
    ambientGeometry.setAttribute("position", new Float32BufferAttribute(ambientPositions, 3));
    ambientGeometry.setAttribute("color", new Float32BufferAttribute(ambientColors, 3));
    const ambient = new Points(
      ambientGeometry,
      new PointsMaterial({
        size: 1.38,
        vertexColors: true,
        transparent: true,
        opacity: 0.42,
        blending: AdditiveBlending,
        depthWrite: false,
      }),
    );
    galaxyGroup.add(ambient);

    const geometry = new BufferGeometry();
    const positions: number[] = [];
    const colors: number[] = [];
    const sizes: number[] = [];
    const nodeIndexByPoint: string[] = [];
    const scenePositionById = new Map(renderItems.map((item) => [item.node.id, item.position]));
    renderItems.forEach((item) => {
      const node = item.node;
      const position = item.position;
      const attributes = memoryStarfieldParticleAttributes(node, degreeById, latestNodeTime);
      const color = new Color(attributes.color);
      const brightness = attributes.brightness;
      positions.push(position.x, position.y, position.z);
      colors.push(color.r * brightness, color.g * brightness, color.b * brightness);
      sizes.push(attributes.size);
      nodeIndexByPoint.push(node.id);
    });
    const baseNodePositions = new Float32Array(positions);
    const flowPhases = renderItems.map((item) => stableUnit(item.node.id, "memory-starfield-flow-phase") * Math.PI * 2);
    const flowMasses = renderItems.map((item) => memoryStarfieldMass(item.node, degreeById, latestNodeTime));
    geometry.setAttribute("position", new Float32BufferAttribute(positions, 3));
    geometry.setAttribute("color", new Float32BufferAttribute(colors, 3));
    geometry.setAttribute("size", new Float32BufferAttribute(sizes, 1));
    if (rendererMode === "memory-starfield") {
      (geometry.getAttribute("position") as Float32BufferAttribute).setUsage(DynamicDrawUsage);
    }

    const material = new PointsMaterial({
      size: 2.15,
      sizeAttenuation: true,
      vertexColors: true,
      transparent: true,
      opacity: 0.32,
      blending: AdditiveBlending,
      depthWrite: false,
    });
    const points = new Points(geometry, material);
    points.name = rendererMode === "memory-starfield" ? "Production Memory Starfield Flow Field" : "Legacy Galaxy Points";
    galaxyGroup.add(points);

    const edgePositions: number[] = [];
    const edgeColors: number[] = [];
    const sceneItemById = new Map(renderItems.map((item) => [item.node.id, item]));
    const renderableNodeIds = new Set(renderItems.map((item) => item.node.id));
    edges
      .filter((edge) => edge.weight >= 0.5)
      .slice(0, 140)
      .forEach((edge) => {
        const source = scenePositionById.get(edge.source);
        const target = scenePositionById.get(edge.target);
        if (!source || !target) return;
        edgePositions.push(source.x, source.y, source.z, target.x, target.y, target.z);
        const sourceNode = renderItems.find((item) => item.node.id === edge.source)?.node;
        const targetNode = renderItems.find((item) => item.node.id === edge.target)?.node;
        const sourceColor = new Color(sourceNode ? memoryStarfieldParticleAttributes(sourceNode, degreeById, latestNodeTime).color : "#8fd3ff");
        const targetColor = new Color(targetNode ? memoryStarfieldParticleAttributes(targetNode, degreeById, latestNodeTime).color : "#8fd3ff");
        const alpha = Math.max(0.018, Math.min(0.07, edge.weight * 0.08));
        edgeColors.push(sourceColor.r * alpha, sourceColor.g * alpha, sourceColor.b * alpha, targetColor.r * alpha, targetColor.g * alpha, targetColor.b * alpha);
      });
    const edgeGeometry = new BufferGeometry();
    edgeGeometry.setAttribute("position", new Float32BufferAttribute(edgePositions, 3));
    edgeGeometry.setAttribute("color", new Float32BufferAttribute(edgeColors, 3));
    const edgeMaterial = new LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.055,
      blending: AdditiveBlending,
      depthWrite: false,
    });
    const edgeLines = new LineSegments(edgeGeometry, edgeMaterial);
    galaxyGroup.add(edgeLines);

    const flowTrailGeometry = new BufferGeometry();
    const flowTrailSegments = rendererMode === "memory-starfield"
      ? createFlowTrailSegments(renderItems, degreeById, latestNodeTime, qualitySettings.flowTrailCount)
      : { positions: [], colors: [] };
    flowTrailGeometry.setAttribute("position", new Float32BufferAttribute(flowTrailSegments.positions, 3));
    flowTrailGeometry.setAttribute("color", new Float32BufferAttribute(flowTrailSegments.colors, 3));
    const flowTrailMaterial = new LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: rendererMode === "memory-starfield" ? 0.28 : 0,
      blending: AdditiveBlending,
      depthWrite: false,
    });
    const flowTrailLines = new LineSegments(flowTrailGeometry, flowTrailMaterial);
    flowTrailLines.name = "memory-starfield-flow-field-trajectories";
    flowTrailLines.renderOrder = 3;
    galaxyGroup.add(flowTrailLines);

    const focusEdgeGeometry = new BufferGeometry();
    focusEdgeGeometry.setAttribute("position", new Float32BufferAttribute([], 3));
    focusEdgeGeometry.setAttribute("color", new Float32BufferAttribute([], 3));
    const focusEdgeMaterial = new LineBasicMaterial({
      vertexColors: true,
      transparent: true,
      opacity: 0.72,
      blending: AdditiveBlending,
      depthWrite: false,
    });
    const focusEdgeLines = new LineSegments(focusEdgeGeometry, focusEdgeMaterial);
    focusEdgeLines.renderOrder = 8;
    galaxyGroup.add(focusEdgeLines);
    let lastFocusEdgeId = "";
    let activeFocusedNeighborhood = emptyFocusedNeighborhood("");

    const haloPositions: number[] = [];
    const haloColors: number[] = [];
    const haloParticleCount = rendererMode === "memory-starfield" ? qualitySettings.haloParticles : 1800;
    for (let i = 0; i < haloParticleCount; i += 1) {
      const radius = 170 + Math.pow(stableUnit(`halo-${i}`, "radius"), 0.52) * 130;
      const angle = stableUnit(`halo-${i}`, "angle") * Math.PI * 2;
      const z = (stableUnit(`halo-${i}`, "z") - 0.5) * 150;
      haloPositions.push(Math.cos(angle) * radius, Math.sin(angle) * radius * 0.48, z);
      const color = new Color(stableUnit(`halo-${i}`, "warm") > 0.68 ? "#a7ecff" : "#d7e8ff");
      const fade = 0.18 + stableUnit(`halo-${i}`, "fade") * 0.24;
      haloColors.push(color.r * fade, color.g * fade, color.b * fade);
    }
    const haloGeometry = new BufferGeometry();
    haloGeometry.setAttribute("position", new Float32BufferAttribute(haloPositions, 3));
    haloGeometry.setAttribute("color", new Float32BufferAttribute(haloColors, 3));
    const halo = new Points(
      haloGeometry,
      new PointsMaterial({
        size: 0.92,
        vertexColors: true,
        transparent: true,
        opacity: 0.22,
        blending: AdditiveBlending,
        depthWrite: false,
      }),
    );
    galaxyGroup.add(halo);

    const coreGeometry = new SphereGeometry(12, 28, 18);
    const coreMaterial = new MeshBasicMaterial({
      color: "#8fd3ff",
      transparent: true,
      opacity: 0.5,
      blending: AdditiveBlending,
      depthWrite: false,
    });
    const core = new Mesh(coreGeometry, coreMaterial);
    core.position.set(0, 0, 0);
    galaxyGroup.add(core);

    const nodeSphereGeometry = new SphereGeometry(1, 12, 8);
    const nodeMaterials: MeshBasicMaterial[] = [];
    renderItems.forEach((item) => {
      const node = item.node;
      if (!isProminentBody(node, degreeById, latestNodeTime)) return;
      const position = item.position;
      const attributes = memoryStarfieldParticleAttributes(node, degreeById, latestNodeTime);
      const color = new Color(attributes.color);
      const materialForNode = new MeshBasicMaterial({
        color,
        transparent: true,
        opacity: Math.max(0.22, attributes.brightness * 0.44),
        blending: AdditiveBlending,
        depthWrite: false,
      });
      const mesh = new Mesh(nodeSphereGeometry, materialForNode);
      mesh.position.set(position.x, position.y, position.z);
      mesh.scale.setScalar(Math.max(0.9, attributes.size * 0.22));
      mesh.frustumCulled = false;
      nodeMaterials.push(materialForNode);
      galaxyGroup.add(mesh);
    });

    const selectedMarkerGeometry = new SphereGeometry(1, 18, 12);
    const selectedMarkerMaterial = new MeshBasicMaterial({
      color: "#ffffff",
      wireframe: true,
      transparent: true,
      opacity: 0,
      depthWrite: false,
    });
    const selectedMarker = new Mesh(selectedMarkerGeometry, selectedMarkerMaterial);
    galaxyGroup.add(selectedMarker);

    const signalSphereGeometry = new SphereGeometry(1, 24, 14);
    const signalRingGeometry = new TorusGeometry(1.7, 0.055, 8, 48);
    const signalMaterials: MeshBasicMaterial[] = [];
    const signalMeshes: Mesh[] = [];
    if (rendererMode === "memory-starfield") {
      renderItems
        .filter((item) => Boolean(memoryStarfieldSignalKind(item.node, degreeById, latestNodeTime)))
        .slice(0, 18)
        .forEach((item) => {
          const signal = memoryStarfieldSignalKind(item.node, degreeById, latestNodeTime);
          if (!signal) return;
          const color = signal === "black-hole" ? "#111827" : signal === "proto-star" ? "#ffef9a" : "#74c0fc";
          const materialForSignal = new MeshBasicMaterial({
            color,
            transparent: true,
            opacity: signal === "black-hole" ? 0.48 : 0.36,
            blending: AdditiveBlending,
            depthWrite: false,
          });
          const position = item.position;
          const sphere = new Mesh(signalSphereGeometry, materialForSignal);
          sphere.position.set(position.x, position.y, position.z + (signal === "proto-star" ? 6 : 0));
          sphere.scale.setScalar(signal === "black-hole" ? 7.4 : signal === "proto-star" ? 5.8 : 4.6);
          sphere.frustumCulled = false;
          const ringMaterial = materialForSignal.clone();
          const ring = new Mesh(signalRingGeometry, ringMaterial);
          ring.position.copy(sphere.position);
          ring.rotation.x = signal === "black-hole" ? 1.3 : 1.08;
          ring.rotation.y = signal === "black-hole" ? 0.22 : -0.16;
          ring.scale.setScalar(signal === "black-hole" ? 4.4 : 3.4);
          ring.frustumCulled = false;
          signalMaterials.push(materialForSignal, ringMaterial);
          signalMeshes.push(sphere, ring);
          galaxyGroup.add(sphere);
          galaxyGroup.add(ring);
        });
    }

    const terrainRingGeometry = new TorusGeometry(1, 0.04, 8, 64);
    const terrainMaterials: MeshBasicMaterial[] = [];
    const terrainMeshes: Mesh[] = [];
    if (rendererMode === "memory-starfield") {
      renderItems
        .map((item) => ({
          item,
          attributes: memoryStarfieldParticleAttributes(item.node, degreeById, latestNodeTime),
        }))
        .filter(({ attributes }) => Boolean(attributes.terrainType))
        .sort((a, b) => b.attributes.mass - a.attributes.mass)
        .slice(0, MEMORY_STARFIELD_PARAMS.layout.lodTiers.midMaxClusters)
        .forEach(({ item, attributes }) => {
          if (!attributes.terrainType) return;
          const terrainVisual = terrainVisualStyle(attributes.terrainType);
          const terrainMaterial = new MeshBasicMaterial({
            color: terrainVisual.color,
            transparent: true,
            opacity: terrainVisual.opacity,
            blending: AdditiveBlending,
            depthWrite: false,
            wireframe: true,
          });
          const terrainRing = new Mesh(terrainRingGeometry, terrainMaterial);
          terrainRing.name = `memory-starfield-terrain-layer-${attributes.terrainType}`;
          terrainRing.position.set(item.position.x, item.position.y, item.position.z - 3);
          terrainRing.rotation.x = attributes.terrainType === "fault-line" ? 1.32 : 1.12;
          terrainRing.rotation.y = (stableUnit(item.node.id, "terrain-y") - 0.5) * 0.34;
          terrainRing.rotation.z = stableUnit(item.node.id, "terrain-z") * Math.PI;
          terrainRing.scale.setScalar(5.8 + Math.min(14, attributes.mass * 0.34));
          terrainRing.frustumCulled = false;
          terrainMaterials.push(terrainMaterial);
          terrainMeshes.push(terrainRing);
          galaxyGroup.add(terrainRing);
        });
    }

    const pulseSphereGeometry = new SphereGeometry(1, 22, 12);
    const neighborPulseGroup = new Group();
    neighborPulseGroup.renderOrder = 12;
    galaxyGroup.add(neighborPulseGroup);
    const pulseItems: Array<{ id: string; mesh: Mesh; material: MeshBasicMaterial; baseScale: number; phase: number; selected: boolean }> = [];
    const activeNeighborIds = new Set<string>();
    let lastPulseFocusId = "";

    const raycaster = new Raycaster();
    raycaster.params.Points = { threshold: 7 };
    const pointer = new Vector2();
    const prefersReducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const cameraTargetPosition = new Vector3(0, 0, 285);
    const cameraLookAt = new Vector3(0, 0, 0);
    const cameraTargetLookAt = new Vector3(0, 0, 0);
    const focusWorldPosition = new Vector3();
    const baseLookAt = new Vector3(0, 0, 0);
    const performanceStartedAt = performance.now();
    let lastFpsSampleAt = performanceStartedAt;
    let lastFpsSampleTick = 0;
    let lastQualityChangeAt = performanceStartedAt;
    let latestPerformanceSnapshot = createPerformanceSnapshot(starfieldQuality, adaptiveQualityEnabledRef.current);
    const lifecycleSignal: GalaxyLifecycleSignal = {
      mountedAt: Date.now(),
      disposedAt: null,
      activeRaf: true,
      rafCancelled: false,
      rendererDisposed: false,
      webglContextLost: false,
      workersClosed: true,
      audioContextClosed: true,
      frameAtDispose: null,
      renderTicksAtDispose: null,
    };
    let frame = 0;
    let renderTicks = 0;
    let raf = 0;
    window.__memoryAtlasGalaxyLifecycle = lifecycleSignal;

    function readGalaxySignal(): GalaxySignal {
      const gl = renderer.getContext();
      gl.flush();
      const width = gl.drawingBufferWidth;
      const height = gl.drawingBufferHeight;
      const sampleWidth = Math.max(1, Math.min(width, 320));
      const sampleHeight = Math.max(1, Math.min(height, 220));
      const sampleX = Math.max(0, Math.floor((width - sampleWidth) / 2));
      const sampleY = Math.max(0, Math.floor((height - sampleHeight) / 2));
      const pixels = new Uint8Array(4 * sampleWidth * sampleHeight);
      gl.readPixels(sampleX, sampleY, sampleWidth, sampleHeight, gl.RGBA, gl.UNSIGNED_BYTE, pixels);
      let lit = 0;
      let alpha = 0;
      let max = 0;
      let hash = 2166136261;
      for (let index = 0; index < pixels.length; index += 4) {
        const sum = pixels[index] + pixels[index + 1] + pixels[index + 2];
        const pixelAlpha = pixels[index + 3];
        if (sum > 42) lit += 1;
        if (pixelAlpha > 0) alpha += 1;
        if (sum > max) max = sum;
        if (sum > 0 || pixelAlpha > 0) {
          hash ^= (pixels[index] << 16) + (pixels[index + 1] << 8) + pixels[index + 2] + pixelAlpha;
          hash = Math.imul(hash, 16777619) >>> 0;
        }
      }
      return {
        frame,
        renderTicks,
        fps: latestPerformanceSnapshot.fps,
        averageFrameMs: latestPerformanceSnapshot.averageFrameMs,
        sampleSeconds: latestPerformanceSnapshot.sampleSeconds,
        lit,
        alpha,
        max,
        hash,
        width,
        height,
        sampleWidth,
        sampleHeight,
        calls: renderer.info.render.calls,
        triangles: renderer.info.render.triangles,
        points: renderer.info.render.points,
        focusNodeId: selectedIdRef.current,
        highlightedNeighborCount: activeNeighborIds.size,
        focusVisibleNeighborCount: activeFocusedNeighborhood.visibleNeighborCount,
        focusHiddenNeighborCount: activeFocusedNeighborhood.hiddenNeighborCount,
        focusPrimaryNeighborCount: activeFocusedNeighborhood.primaryNeighborCount,
        focusSecondaryNeighborCount: activeFocusedNeighborhood.secondaryNeighborCount,
        cameraX: Number(camera.position.x.toFixed(3)),
        cameraY: Number(camera.position.y.toFixed(3)),
        cameraZ: Number(camera.position.z.toFixed(3)),
        cameraDistance: Number(camera.position.length().toFixed(3)),
        rendererMode,
        quality: starfieldQuality,
        targetFps: latestPerformanceSnapshot.targetFps,
        minFps: latestPerformanceSnapshot.minFps,
        adaptiveQualityEnabled: latestPerformanceSnapshot.adaptiveQualityEnabled,
        adaptiveQualityDecision: latestPerformanceSnapshot.adaptiveQualityDecision,
        flowFieldStrength: Number(flowFieldStrengthRef.current.toFixed(2)),
        flowPaused: flowPausedRef.current,
        starfieldMode: starfieldModeRef.current,
        terrainFeatureCount: terrainSummary.total,
        parameterSource: MEMORY_STARFIELD_PARAMS.parameterSource,
        fallbackMode: rendererMode === "legacy" ? "legacy" : starfieldQuality === "low" ? "low-quality" : "webgl",
      };
    }

    function readGalaxyDebugTargets(): Array<{ id: string; x: number; y: number; linkedCount: number }> {
      const rect = renderer.domElement.getBoundingClientRect();
      galaxyGroup.updateMatrixWorld(true);
      camera.updateMatrixWorld(true);
      return renderItems
        .map((item) => {
          const projected = new Vector3(item.position.x, item.position.y, item.position.z);
          galaxyGroup.localToWorld(projected);
          projected.project(camera);
          return {
            id: item.node.id,
            x: rect.left + ((projected.x + 1) / 2) * rect.width,
            y: rect.top + ((1 - projected.y) / 2) * rect.height,
            linkedCount: degreeById.get(item.node.id) ?? 0,
          };
        })
        .filter((target) => target.linkedCount > 0 && target.x >= rect.left && target.x <= rect.right && target.y >= rect.top && target.y <= rect.bottom)
        .sort((a, b) => b.linkedCount - a.linkedCount)
        .slice(0, 24);
    }

    window.__memoryAtlasGalaxySignal = readGalaxySignal;
    window.__memoryAtlasGalaxyDebugTargets = readGalaxyDebugTargets;

    function resize() {
      const rect = containerRef.current?.getBoundingClientRect() ?? renderer.domElement.getBoundingClientRect();
      const width = Math.max(1, Math.floor(rect.width));
      const height = Math.max(1, Math.floor(rect.height));
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
      renderer.setSize(width, height, false);
    }

    function updateSelectedMarker() {
      const selectedIndex = renderNodes.findIndex((node) => node.id === selectedIdRef.current);
      if (selectedIndex < 0) {
        selectedMarker.material.opacity = 0;
        return;
      }
      selectedMarker.material.opacity = 0.72;
      const source = renderItems[selectedIndex]?.position ?? { x: 0, y: 0, z: 0 };
      selectedMarker.position.set(source.x, source.y, source.z);
      const selectedAttributes = renderItems[selectedIndex]
        ? memoryStarfieldParticleAttributes(renderItems[selectedIndex].node, degreeById, latestNodeTime)
        : null;
      selectedMarker.scale.setScalar(Math.max(6, (selectedAttributes?.size ?? 8) * 0.72));
    }

    function updateFocusEdgeHighlight() {
      const focusId = selectedIdRef.current ?? hoveredIdRef.current ?? "";
      if (focusId === lastFocusEdgeId) return;
      lastFocusEdgeId = focusId;
      const focusPositions: number[] = [];
      const focusColors: number[] = [];
      activeFocusedNeighborhood = focusId ? buildFocusedNeighborhood(focusId, edges, renderableNodeIds) : emptyFocusedNeighborhood("");
      if (focusId) {
        const focusPosition = scenePositionById.get(focusId);
        if (focusPosition) {
          activeFocusedNeighborhood.neighbors.forEach((neighbor) => {
            const target = localNeighborhoodPosition(focusPosition, neighbor, activeFocusedNeighborhood);
            focusPositions.push(focusPosition.x, focusPosition.y, focusPosition.z, target.x, target.y, target.z);
            const focusNode = sceneItemById.get(focusId)?.node;
            const targetNode = sceneItemById.get(neighbor.id)?.node;
            const sourceColor = new Color(focusNode ? memoryStarfieldParticleAttributes(focusNode, degreeById, latestNodeTime).color : "#8fd3ff");
            const targetColor = new Color(targetNode ? memoryStarfieldParticleAttributes(targetNode, degreeById, latestNodeTime).color : "#8fd3ff");
            const alpha = neighbor.layer === "primary" ? 0.96 : 0.42;
            focusColors.push(
              sourceColor.r * alpha,
              sourceColor.g * alpha,
              sourceColor.b * alpha,
              targetColor.r * alpha,
              targetColor.g * alpha,
              targetColor.b * alpha,
            );
          });
        }
      }
      focusEdgeGeometry.setAttribute("position", new Float32BufferAttribute(focusPositions, 3));
      focusEdgeGeometry.setAttribute("color", new Float32BufferAttribute(focusColors, 3));
      focusEdgeGeometry.computeBoundingSphere();
    }

    function rebuildNeighborPulses() {
      const focusId = selectedIdRef.current ?? "";
      if (focusId === lastPulseFocusId) return;
      lastPulseFocusId = focusId;
      activeNeighborIds.clear();
      while (pulseItems.length) {
        const item = pulseItems.pop();
        if (!item) continue;
        neighborPulseGroup.remove(item.mesh);
        item.material.dispose();
      }
      if (!focusId || !scenePositionById.has(focusId)) return;
      const focusPosition = scenePositionById.get(focusId);
      const neighborhood = buildFocusedNeighborhood(focusId, edges, renderableNodeIds);
      activeFocusedNeighborhood = neighborhood;
      const pulseTargets = [
        { id: focusId, weight: 1.35, selected: true, layer: "primary" as FocusNeighborLayer, rank: -1 },
        ...neighborhood.neighbors
          .slice(0, MAX_PULSE_NEIGHBORS)
          .map((neighbor) => ({ ...neighbor, selected: false })),
      ];
      for (const target of pulseTargets) {
        const position = target.selected
          ? focusPosition
          : focusPosition
            ? localNeighborhoodPosition(focusPosition, target, neighborhood)
            : scenePositionById.get(target.id);
        const sceneItem = sceneItemById.get(target.id);
        if (!position || !sceneItem) continue;
        if (!target.selected) activeNeighborIds.add(target.id);
        const color = target.selected ? new Color("#ffffff") : new Color(memoryStarfieldParticleAttributes(sceneItem.node, degreeById, latestNodeTime).color);
        const materialForPulse = new MeshBasicMaterial({
          color,
          transparent: true,
          opacity: target.selected ? 0.32 : target.layer === "primary" ? 0.16 : 0.1,
          blending: AdditiveBlending,
          depthWrite: false,
          wireframe: true,
        });
        const mesh = new Mesh(pulseSphereGeometry, materialForPulse);
        mesh.position.set(position.x, position.y, position.z);
        mesh.frustumCulled = false;
        const nodeSize = sceneItem.node.visual?.size ?? 6;
        const layerScale = target.selected ? 0.56 : target.layer === "primary" ? 0.36 : 0.24;
        const rawScale = nodeSize * layerScale * (0.78 + target.weight * 0.18);
        const baseScale = clamp(
          rawScale,
          target.selected ? 5.8 : target.layer === "primary" ? 2.8 : 2.0,
          target.selected ? 10.5 : target.layer === "primary" ? 5.8 : 4.2,
        );
        mesh.scale.setScalar(baseScale);
        neighborPulseGroup.add(mesh);
        pulseItems.push({
          id: target.id,
          mesh,
          material: materialForPulse,
          baseScale,
          phase: stableUnit(`${focusId}:${target.id}`, "pulse-phase") * Math.PI * 2,
          selected: target.selected,
        });
      }
    }

    function updateNeighborPulse() {
      if (flowPausedRef.current) return;
      if (!pulseItems.length) return;
      const time = frame * 0.075;
      for (const item of pulseItems) {
        const wave = (Math.sin(time + item.phase) + 1) / 2;
        const amplitude = item.selected ? 0.16 : 0.28;
        item.mesh.scale.setScalar(item.baseScale * (1 + wave * amplitude));
        item.material.opacity = item.selected ? 0.28 + wave * 0.18 : 0.08 + wave * 0.22;
      }
    }

    function updateMemoryStarfieldFlow() {
      if (rendererMode !== "memory-starfield") return;
      if (flowPausedRef.current) return;
      const positionAttribute = geometry.getAttribute("position") as Float32BufferAttribute;
      const positionArray = positionAttribute.array as Float32Array;
      const time = frame * 0.016;
      const reducedScale = prefersReducedMotion ? 0.25 : 1;
      const flowScale = flowFieldStrengthRef.current * reducedScale;
      for (let index = 0; index < renderItems.length; index += 1) {
        const offset = index * 3;
        const baseX = baseNodePositions[offset];
        const baseY = baseNodePositions[offset + 1];
        const baseZ = baseNodePositions[offset + 2];
        const phase = flowPhases[index];
        const mass = flowMasses[index];
        const curlX = Math.sin(baseY * 0.028 + time + phase) * 3.4;
        const curlY = Math.cos((baseX + baseZ) * 0.018 + time * 0.82 + phase) * 1.65;
        const curlZ = Math.sin(baseX * 0.02 - time * 1.12 + phase) * 2.9;
        const orbital = 0.012 + mass * 0.0045;
        positionArray[offset] = baseX + (curlX - baseY * orbital) * flowScale;
        positionArray[offset + 1] = baseY + (curlY + baseX * orbital * 0.34) * flowScale;
        positionArray[offset + 2] = baseZ + curlZ * flowScale;
      }
      positionAttribute.needsUpdate = true;
      flowTrailLines.rotation.z = Math.sin(time * 0.7) * 0.035;
      signalMeshes.forEach((mesh, index) => {
        mesh.rotation.z += index % 2 === 0 ? 0.008 : -0.006;
      });
      terrainMeshes.forEach((mesh, index) => {
        mesh.rotation.z += index % 2 === 0 ? 0.0025 : -0.0018;
      });
    }

    function updateCameraFocus() {
      const focusId = selectedIdRef.current;
      const focusPosition = focusId ? scenePositionById.get(focusId) : undefined;
      const baseZ = 285 / zoomRef.current;
      if (!focusId || !focusPosition) {
        cameraTargetPosition.set(0, 0, baseZ);
        cameraTargetLookAt.copy(baseLookAt);
      } else {
        focusWorldPosition.set(focusPosition.x, focusPosition.y, focusPosition.z);
        galaxyGroup.localToWorld(focusWorldPosition);
        const focusZ = Math.max(96, baseZ * 0.58 + Math.abs(focusWorldPosition.z) * 0.18);
        cameraTargetPosition.set(focusWorldPosition.x * 0.48, focusWorldPosition.y * 0.48, focusZ);
        cameraTargetLookAt.copy(focusWorldPosition);
      }
      const speed = prefersReducedMotion ? 1 : focusId ? 0.095 : 0.075;
      camera.position.lerp(cameraTargetPosition, speed);
      cameraLookAt.lerp(cameraTargetLookAt, speed * 1.12);
      camera.lookAt(cameraLookAt);
    }

    function samplePerformance(now: number) {
      const sampleMs = now - lastFpsSampleAt;
      if (sampleMs < STAGE7_PERFORMANCE_THRESHOLDS.sampleWindowMs) return;

      const sampleTicks = renderTicks - lastFpsSampleTick;
      const sampleSeconds = sampleMs / 1000;
      const fps = sampleTicks > 0 ? sampleTicks / sampleSeconds : 0;
      const averageFrameMs = sampleTicks > 0 ? sampleMs / sampleTicks : 0;
      const elapsedMs = now - performanceStartedAt;
      const adaptiveQualityEnabled = rendererMode === "memory-starfield" && adaptiveQualityEnabledRef.current;
      const { decision, nextQuality } = adaptiveQualityEnabled
        ? nextAdaptiveQualityDecision(starfieldQuality, fps, elapsedMs, now - lastQualityChangeAt)
        : { decision: "hold" as AdaptiveQualityDecision, nextQuality: null };

      latestPerformanceSnapshot = createPerformanceSnapshot(
        starfieldQuality,
        adaptiveQualityEnabled,
        fps,
        averageFrameMs,
        sampleSeconds,
        decision,
      );
      renderer.domElement.dataset.fps = String(latestPerformanceSnapshot.fps);
      renderer.domElement.dataset.averageFrameMs = String(latestPerformanceSnapshot.averageFrameMs);
      renderer.domElement.dataset.adaptiveQuality = adaptiveQualityEnabled ? "enabled" : "manual";
      renderer.domElement.dataset.adaptiveDecision = decision;
      setPerformanceSnapshot(latestPerformanceSnapshot);

      if (nextQuality && nextQuality !== starfieldQuality) {
        lastQualityChangeAt = now;
        setStarfieldQuality(nextQuality);
      }
      lastFpsSampleAt = now;
      lastFpsSampleTick = renderTicks;
    }

    function render() {
      const now = performance.now();
      renderTicks += 1;
      const frozen = rendererMode === "memory-starfield" && flowPausedRef.current;
      if (!frozen) frame += 1;
      const autoMotion = prefersReducedMotion || frozen ? 0 : 0.0016;
      galaxyGroup.rotation.x = rotationRef.current.x;
      galaxyGroup.rotation.y = rotationRef.current.y + frame * autoMotion;
      galaxyGroup.updateMatrixWorld(true);
      updateCameraFocus();
      updateSelectedMarker();
      updateMemoryStarfieldFlow();
      updateFocusEdgeHighlight();
      rebuildNeighborPulses();
      updateNeighborPulse();
      renderer.clear(true, true, true);
      renderer.render(scene, camera);
      renderer.domElement.dataset.frame = String(frame);
      samplePerformance(now);
      raf = window.requestAnimationFrame(render);
    }

    function eventToPointer(event: PointerEvent) {
      const rect = renderer.domElement.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
    }

    function pickNearestNode(event: PointerEvent) {
      eventToPointer(event);
      raycaster.setFromCamera(pointer, camera);
      const intersections = raycaster.intersectObject(points);
      if (!intersections.length) return null;
      const index = intersections[0].index ?? -1;
      const nodeId = nodeIndexByPoint[index];
      return sceneItemById.get(nodeId) ?? null;
    }

    function updateHoverPreview(event: PointerEvent) {
      const item = pickNearestNode(event);
      if (!item) {
        hoveredIdRef.current = null;
        setHoverPreview(null);
        return;
      }
      const rect = renderer.domElement.getBoundingClientRect();
      const hoverNeighborhood = buildFocusedNeighborhood(item.node.id, edges, renderableNodeIds);
      hoveredIdRef.current = item.node.id;
      setHoverPreview({
        node: item.node,
        x: clamp(event.clientX - rect.left + 16, 12, Math.max(12, rect.width - 282)),
        y: clamp(event.clientY - rect.top + 16, 12, Math.max(12, rect.height - 146)),
        linkedCount: degreeById.get(item.node.id) ?? 0,
        visibleNeighborCount: hoverNeighborhood.visibleNeighborCount,
        hiddenNeighborCount: hoverNeighborhood.hiddenNeighborCount,
      });
    }

    function clearHoverPreview() {
      hoveredIdRef.current = null;
      setHoverPreview(null);
    }

    function onPointerDown(event: PointerEvent) {
      clearHoverPreview();
      pointerRef.current = { dragging: true, moved: false, x: event.clientX, y: event.clientY };
      try {
        renderer.domElement.setPointerCapture(event.pointerId);
      } catch {
        // Some browsers can throw if the pointer is already released.
      }
    }

    function onPointerMove(event: PointerEvent) {
      const current = pointerRef.current;
      if (current.dragging) {
        const dx = event.clientX - current.x;
        const dy = event.clientY - current.y;
        const moved = current.moved || Math.abs(dx) + Math.abs(dy) > 3;
        rotationRef.current.y += dx * 0.006;
        rotationRef.current.x += dy * 0.004;
        pointerRef.current = { dragging: true, moved, x: event.clientX, y: event.clientY };
        return;
      }
      updateHoverPreview(event);
    }

    function endDrag(event?: PointerEvent) {
      const current = pointerRef.current;
      pointerRef.current = { dragging: false, moved: false, x: event?.clientX ?? current.x, y: event?.clientY ?? current.y };
      if (event && renderer.domElement.hasPointerCapture(event.pointerId)) {
        try {
          renderer.domElement.releasePointerCapture(event.pointerId);
        } catch {
          // Pointer capture can already be gone after OS gestures or tab switches.
        }
      }
      return current.moved;
    }

    function onPointerUp(event: PointerEvent) {
      const moved = pointerRef.current.moved;
      endDrag(event);
      if (moved) return;
      const item = pickNearestNode(event);
      if (item) onSelectNode(item.node);
    }

    function onPointerCancel(event: PointerEvent) {
      endDrag(event);
    }

    function onWheel(event: WheelEvent) {
      event.preventDefault();
      const next = zoomRef.current + (event.deltaY > 0 ? -0.08 : 0.08);
      zoomRef.current = Math.min(2.4, Math.max(0.58, next));
    }

    resize();
    render();
    const observer = new ResizeObserver(resize);
    observer.observe(containerElement);
    renderer.domElement.addEventListener("pointerdown", onPointerDown);
    renderer.domElement.addEventListener("pointermove", onPointerMove);
    renderer.domElement.addEventListener("pointerup", onPointerUp);
    renderer.domElement.addEventListener("pointercancel", onPointerCancel);
    renderer.domElement.addEventListener("lostpointercapture", onPointerCancel);
    renderer.domElement.addEventListener("pointerleave", clearHoverPreview);
    renderer.domElement.addEventListener("wheel", onWheel, { passive: false });

    return () => {
      window.cancelAnimationFrame(raf);
      lifecycleSignal.activeRaf = false;
      lifecycleSignal.rafCancelled = true;
      observer.disconnect();
      endDrag();
      renderer.domElement.removeEventListener("pointerdown", onPointerDown);
      renderer.domElement.removeEventListener("pointermove", onPointerMove);
      renderer.domElement.removeEventListener("pointerup", onPointerUp);
      renderer.domElement.removeEventListener("pointercancel", onPointerCancel);
      renderer.domElement.removeEventListener("lostpointercapture", onPointerCancel);
      renderer.domElement.removeEventListener("pointerleave", clearHoverPreview);
      renderer.domElement.removeEventListener("wheel", onWheel);
      geometry.dispose();
      edgeGeometry.dispose();
      edgeMaterial.dispose();
      focusEdgeGeometry.dispose();
      focusEdgeMaterial.dispose();
      pulseSphereGeometry.dispose();
      for (const item of pulseItems) item.material.dispose();
      flowTrailGeometry.dispose();
      flowTrailMaterial.dispose();
      ambientGeometry.dispose();
      haloGeometry.dispose();
      galaxyPlaneGeometry.dispose();
      galaxyPlaneMaterial.dispose();
      galaxyTexture.dispose();
      coreGeometry.dispose();
      coreMaterial.dispose();
      selectedMarkerGeometry.dispose();
      signalSphereGeometry.dispose();
      signalRingGeometry.dispose();
      for (const signalMaterial of signalMaterials) signalMaterial.dispose();
      terrainRingGeometry.dispose();
      for (const terrainMaterial of terrainMaterials) terrainMaterial.dispose();
      material.dispose();
      ambient.material.dispose();
      halo.material.dispose();
      nodeSphereGeometry.dispose();
      for (const nodeMaterial of nodeMaterials) nodeMaterial.dispose();
      selectedMarkerMaterial.dispose();
      renderer.dispose();
      lifecycleSignal.rendererDisposed = true;
      try {
        renderer.forceContextLoss();
        lifecycleSignal.webglContextLost = true;
      } catch {
        lifecycleSignal.webglContextLost = false;
      }
      lifecycleSignal.disposedAt = Date.now();
      lifecycleSignal.frameAtDispose = frame;
      lifecycleSignal.renderTicksAtDispose = renderTicks;
      renderer.domElement.remove();
      if (window.__memoryAtlasGalaxySignal === readGalaxySignal) {
        delete window.__memoryAtlasGalaxySignal;
      }
      if (window.__memoryAtlasGalaxyDebugTargets === readGalaxyDebugTargets) {
        delete window.__memoryAtlasGalaxyDebugTargets;
      }
    };
  }, [degreeById, edges, latestNodeTime, onSelectNode, qualitySettings, renderItems, renderNodes, rendererMode, starfieldQuality, terrainSummary.total]);

  function resetGalaxyView() {
    rotationRef.current = { x: -0.14, y: 0.42 };
    zoomRef.current = 1;
  }

  function zoomGalaxy(delta: number) {
    zoomRef.current = Math.min(2.4, Math.max(0.58, zoomRef.current + delta));
  }

  function updateStarfieldQuality(nextQuality: StarfieldQuality) {
    setAdaptiveQualityEnabled(false);
    setStarfieldQuality(nextQuality);
  }

  function updateStarfieldMode(nextMode: StarfieldViewMode) {
    setStarfieldMode(nextMode);
  }

  return (
    <div
      className="galaxy-scene"
      data-renderer-mode={rendererMode}
      data-starfield-mode={starfieldMode}
      data-starfield-quality={starfieldQuality}
      data-adaptive-quality={adaptiveQualityEnabled ? "enabled" : "manual"}
      data-galaxy-fps={performanceSnapshot.fps}
      ref={containerRef}
    >
      {renderError ? <canvas className="nebula-canvas" ref={nebulaCanvasRef} aria-hidden="true" /> : null}
      {renderError ? (
        <div className="star-overlay" aria-label="可点击记忆星体层">
          {renderItems.map((item) => (
            <button
              aria-label={item.node.label}
              className={[
                "star-dot",
                item.node.id === selectedNode?.id ? "selected" : "",
                selectedNeighborIds.has(item.node.id) ? "neighbor" : "",
              ].filter(Boolean).join(" ")}
              key={item.node.id}
              onClick={() => onSelectNode(item.node)}
              style={starStyle(item)}
              type="button"
            />
          ))}
        </div>
      ) : null}
      {!renderError ? (
        <div className="galaxy-controls" aria-label="银河视角控制">
          <span className="galaxy-renderer-chip">{rendererMode === "memory-starfield" ? "Flow Field" : "Legacy"}</span>
          {rendererMode === "memory-starfield" ? (
            <div className="galaxy-quality-tabs" aria-label="Flow Field quality selector">
              {(["high", "mid", "low"] as StarfieldQuality[]).map((quality) => (
                <button
                  aria-label={`${quality} quality`}
                  aria-pressed={starfieldQuality === quality}
                  key={quality}
                  title={quality === "low" ? "低质量 fallback 模式" : `${quality} quality`}
                  type="button"
                  onClick={() => updateStarfieldQuality(quality)}
                >
                  {quality}
                </button>
              ))}
            </div>
          ) : null}
          {rendererMode === "memory-starfield" ? (
            <button
              aria-label={adaptiveQualityEnabled ? "Disable Adaptive Quality" : "Enable Adaptive Quality"}
              aria-pressed={adaptiveQualityEnabled}
              className="galaxy-adaptive-quality-toggle"
              title={adaptiveQualityEnabled ? "Disable Adaptive Quality" : "Enable Adaptive Quality"}
              type="button"
              onClick={() => setAdaptiveQualityEnabled((enabled) => !enabled)}
            >
              Auto
            </button>
          ) : null}
          {rendererMode === "memory-starfield" ? (
            <label className="galaxy-flow-control" title="Flow Field strength">
              <Gauge size={15} />
              <input
                aria-label="Flow Field strength"
                max="1.4"
                min="0"
                onChange={(event) => setFlowFieldStrength(Number(event.target.value))}
                step="0.05"
                type="range"
                value={flowFieldStrength}
              />
            </label>
          ) : null}
          {rendererMode === "memory-starfield" ? (
            <button
              aria-label={flowPaused ? "Resume Flow Field" : "Freeze Flow Field"}
              aria-pressed={flowPaused}
              title={flowPaused ? "Resume Flow Field" : "Freeze Flow Field"}
              type="button"
              onClick={() => setFlowPaused((paused) => !paused)}
            >
              {flowPaused ? <Play size={16} /> : <Pause size={16} />}
            </button>
          ) : null}
          {rendererMode === "memory-starfield" ? (
            <div className="galaxy-mode-tabs" aria-label="Starfield mode selector">
              {(["presentation", "analysis"] as StarfieldViewMode[]).map((mode) => (
                <button
                  aria-label={`${mode} mode`}
                  aria-pressed={starfieldMode === mode}
                  key={mode}
                  title={mode === "presentation" ? "Presentation Mode" : "Analysis Mode"}
                  type="button"
                  onClick={() => updateStarfieldMode(mode)}
                >
                  {mode === "presentation" ? "Present" : "Analysis"}
                </button>
              ))}
            </div>
          ) : null}
          <button aria-label="放大银河视角" title="放大" type="button" onClick={() => zoomGalaxy(0.14)}>
            <ZoomIn size={16} />
          </button>
          <button aria-label="缩小银河视角" title="缩小" type="button" onClick={() => zoomGalaxy(-0.14)}>
            <ZoomOut size={16} />
          </button>
          <button aria-label="重置银河视角" title="重置视角" type="button" onClick={resetGalaxyView}>
            <RotateCcw size={16} />
          </button>
        </div>
      ) : null}
      {rendererMode === "memory-starfield" && starfieldMode === "analysis" ? (
        <div className="galaxy-performance-overlay" data-performance-overlay="true" aria-label="Galaxy performance metrics">
          <div>
            <strong>{Math.round(performanceSnapshot.fps)}</strong>
            <span>FPS</span>
          </div>
          <div>
            <strong>{performanceSnapshot.quality.toUpperCase()}</strong>
            <span>{performanceSnapshot.adaptiveQualityEnabled ? "AUTO" : "MANUAL"}</span>
          </div>
          <div>
            <strong>{performanceSnapshot.averageFrameMs.toFixed(1)}ms</strong>
            <span>FRAME</span>
          </div>
          <div>
            <strong>{performanceSnapshot.minFps}</strong>
            <span>MIN</span>
          </div>
        </div>
      ) : null}
      {rendererMode === "memory-starfield" && starfieldMode === "analysis" ? (
        <div
          className="galaxy-terrain-panel"
          data-memory-terrain-v2="analysis-only"
          data-terrain-semantic-coverage={terrainSummary.semanticCoverage.toFixed(2)}
          aria-label="Memory Terrain v2 analysis panel"
        >
          <div className="terrain-panel-heading">
            <strong><Layers size={14} /> Memory Terrain v2</strong>
            <span>{terrainSummary.total.toLocaleString()} mapped features · {terrainSummary.dominantLabel}</span>
          </div>
          <div className="terrain-formula-grid" aria-label="Starfield formula summary">
            <div>
              <b>mass</b>
              <span>tier + kind + ROI + importance + recency + usage</span>
            </div>
            <div>
              <b>particle</b>
              <span>size / brightness / color = mass + recency + confidence</span>
            </div>
            <div>
              <b>flow</b>
              <span>{flowPaused ? "frozen for reading" : "animated by interaction density"}</span>
            </div>
            <div>
              <b>terrain</b>
              <span>{terrainSummary.analysisNote}</span>
            </div>
          </div>
          <div className="terrain-row-list">
            {terrainSummary.rows.map((row) => (
              <div
                className="terrain-row"
                data-terrain-type={row.type}
                data-terrain-v2-role={row.semanticRole}
                data-terrain-intensity={row.intensity.toFixed(2)}
                key={row.type}
                style={{ "--terrain-intensity": `${Math.round(row.intensity * 100)}%` } as CSSProperties}
              >
                <b>{row.label}</b>
                <span>{row.count.toLocaleString()} nodes · ROI {formatScore(row.averageRoi)}</span>
                <em>{row.explanation}</em>
                <small>{row.capabilitySignal} · {row.sampleLabels.length ? row.sampleLabels.join(" / ") : "No current sample"}</small>
              </div>
            ))}
          </div>
          <div className="terrain-inspector-strip" aria-label="Analysis inspector summary">
            <b>Inspector</b>
            <span>
              {selectedNode
                ? `${galaxyPreviewTitle(selectedNode)} / ${normalizeMemoryTier(selectedNode.memory_tier)} / ${selectedEdgeCount.toLocaleString()} links`
                : "Select a cluster to inspect focus, neighbors and formula context"}
            </span>
          </div>
        </div>
      ) : null}
      {rendererMode === "memory-starfield" && starfieldMode === "analysis" ? (
        <div
          className="galaxy-roi-gradient-panel"
          data-roi-gradient="galaxy-analysis"
          aria-label="ROI capability gradient overlay"
        >
          <div className="terrain-panel-heading">
            <strong>ROI Capability Gradient</strong>
            <span>{roiGradientSummary.highValueCount.toLocaleString()} high-value · avg {formatScore(roiGradientSummary.averageRoi)}</span>
          </div>
          <div className="galaxy-roi-gradient-strip" aria-label="Galaxy ROI gradient by semantic bucket">
            {roiGradientSummary.rows.map((row) => (
              <span
                data-roi-gradient-row={row.id}
                key={row.id}
                style={{ "--roi-intensity": `${Math.round(row.intensity * 100)}%` } as CSSProperties}
                title={`${row.label} · ${row.count} nodes · ROI ${formatScore(row.averageRoi)}`}
              >
                <b>{row.label}</b>
                <em>{formatScore(row.averageRoi)}</em>
              </span>
            ))}
          </div>
          <small>{roiGradientSummary.note}</small>
        </div>
      ) : null}
      {hoverPreview && !renderError ? (
        <div
          className="galaxy-hover-preview"
          style={{ "--preview-x": `${hoverPreview.x}px`, "--preview-y": `${hoverPreview.y}px` } as CSSProperties}
        >
          <strong>{galaxyPreviewTitle(hoverPreview.node)}</strong>
          <span>{galaxyPreviewSummary(hoverPreview.node)}</span>
          <em>
            {normalizeMemoryTier(hoverPreview.node.memory_tier)} / {hoverPreview.node.category || translateKind(hoverPreview.node.kind)} / 关联 {hoverPreview.linkedCount.toLocaleString()}
            {" / "}聚焦显示 {hoverPreview.visibleNeighborCount.toLocaleString()}
            {hoverPreview.hiddenNeighborCount ? ` / 折叠 ${hoverPreview.hiddenNeighborCount.toLocaleString()}` : ""}
          </em>
        </div>
      ) : null}
      {selectedNode && primaryNeighborCards.length ? (
        <div className="galaxy-neighbor-cards" aria-label="内环邻居快速跳转">
          <div className="neighbor-card-heading">
            <strong>内环邻居</strong>
            <span>{primaryNeighborCards.length}/{selectedNeighborhood.totalNeighborCount.toLocaleString()}</span>
          </div>
          <div className="neighbor-card-list">
            {primaryNeighborCards.map(({ neighbor, node }) => (
              <button
                key={neighbor.id}
                onClick={() => onSelectNode(node)}
                title={`${galaxyPreviewTitle(node)} · 关联权重 ${neighbor.weight.toFixed(2)}`}
                type="button"
              >
                <b>{galaxyPreviewTitle(node)}</b>
                <span>{normalizeMemoryTier(node.memory_tier)} / {node.category || translateKind(node.kind)}</span>
                <em>#{neighbor.rank + 1} · {neighbor.weight.toFixed(2)}</em>
              </button>
            ))}
          </div>
          {selectedNeighborhood.hiddenNeighborCount ? (
            <small>另折叠 {selectedNeighborhood.hiddenNeighborCount.toLocaleString()} 个低优先级邻居</small>
          ) : null}
        </div>
      ) : null}
      <div className="galaxy-hud">
        <div>
          <strong>{renderItems.length}</strong>
          <span>渲染节点</span>
        </div>
        <div>
          <strong>{selectedNode ? normalizeMemoryTier(selectedNode.memory_tier) : "未选择"}</strong>
          <span>当前选择</span>
        </div>
        <div>
          <strong>{selectedEdgeCount.toLocaleString()}</strong>
          <span>选中关联边</span>
        </div>
        <div>
          <strong>{selectedNode ? `${selectedNeighborhood.visibleNeighborCount.toLocaleString()}/${selectedEdgeCount.toLocaleString()}` : "未聚焦"}</strong>
          <span>局部邻域</span>
        </div>
        <div>
          <strong>{selectedNode ? (selectedNeighborhood.hiddenNeighborCount ? `折叠 ${selectedNeighborhood.hiddenNeighborCount.toLocaleString()}` : "无折叠") : "未折叠"}</strong>
          <span>高连接保护</span>
        </div>
        <div>
          <strong>{terrainSummary.total.toLocaleString()}</strong>
          <span>Terrain 映射</span>
        </div>
      </div>
      {renderError ? (
        <div className="galaxy-fallback" title={renderError}>
          <strong>WebGL 不可用</strong>
          <span>已启用静态星云 fallback，仍可点击星体查看记忆；也可通过 Galaxy feature flag 回到 Legacy。</span>
        </div>
      ) : null}
    </div>
  );
}

function createFlowTrailSegments(
  items: SceneNode[],
  degreeById: Map<string, number>,
  latestNodeTime: number,
  limit: number,
): { positions: number[]; colors: number[] } {
  const positions: number[] = [];
  const colors: number[] = [];
  const candidates = [...items]
    .sort((a, b) => memoryStarfieldMass(b.node, degreeById, latestNodeTime) - memoryStarfieldMass(a.node, degreeById, latestNodeTime))
    .slice(0, limit);
  for (const item of candidates) {
    const position = item.position;
    const attributes = memoryStarfieldParticleAttributes(item.node, degreeById, latestNodeTime);
    const phase = stableUnit(item.node.id, "flow-trail-phase") * Math.PI * 2;
    const flow = flowVectorFor(position, phase, attributes.mass * attributes.trailStrength);
    const sourceColor = new Color(attributes.color);
    const alpha = 0.12 + Math.min(0.52, attributes.trailStrength * 0.38);
    positions.push(
      position.x - flow.x * 0.72,
      position.y - flow.y * 0.72,
      position.z - flow.z * 0.28,
      position.x + flow.x,
      position.y + flow.y,
      position.z + flow.z * 0.42,
    );
    colors.push(sourceColor.r * alpha, sourceColor.g * alpha, sourceColor.b * alpha, sourceColor.r * 0.04, sourceColor.g * 0.04, sourceColor.b * 0.04);
  }
  return { positions, colors };
}

function flowVectorFor(position: { x: number; y: number; z: number }, phase: number, mass: number): { x: number; y: number; z: number } {
  const strength = 4.5 + Math.min(13, mass * MEMORY_STARFIELD_PARAMS.forces.curlNoiseAmplitude * 1.6);
  return {
    x: Math.sin(position.y * 0.025 + phase) * strength - position.y * 0.018,
    y: Math.cos((position.x + position.z) * 0.016 + phase) * strength * 0.42 + position.x * 0.006,
    z: Math.sin(position.x * 0.018 - phase) * strength * 0.62,
  };
}

function memoryStarfieldMass(node: AtlasNode, degreeById: Map<string, number>, latestNodeTime: number): number {
  const params = MEMORY_STARFIELD_PARAMS.mapping.clusterMass;
  const tier = normalizeMemoryTier(node.memory_tier);
  const tierMass = tier === "核心画像" ? params.tierCore : tier === "一般" ? params.tierMid : params.tierOuter;
  const roiMass = (node.metrics?.roi?.leverage_score ?? 0) * params.roiMultiplier;
  const importanceMass = node.importance === "高" ? params.importanceHigh : node.importance === "中" ? params.importanceMedium : params.importanceLow;
  const kindMass = node.kind === "theme" ? params.kindTheme : node.kind === "decision" ? params.kindDecision : node.kind === "project" ? params.kindProject : 0;
  const recencyMass = memoryStarfieldRecencyScore(node, latestNodeTime) * params.recencyMultiplier;
  const usageMass = Math.sqrt(degreeById.get(node.id) ?? 0) * params.usageSqrtMultiplier;
  return (tierMass + roiMass + importanceMass + kindMass + recencyMass + usageMass) * MEMORY_STARFIELD_PARAMS.mapping.importanceToMassScale;
}

function memoryStarfieldParticleAttributes(
  node: AtlasNode,
  degreeById: Map<string, number>,
  latestNodeTime: number,
): MemoryStarfieldParticleAttributes {
  const params = MEMORY_STARFIELD_PARAMS.mapping.particleAttributes;
  const mass = memoryStarfieldMass(node, degreeById, latestNodeTime);
  const recencyScore = memoryStarfieldRecencyScore(node, latestNodeTime);
  const confidenceScore = memoryStarfieldConfidenceScore(node);
  const interactionScore = Math.sqrt(degreeById.get(node.id) ?? 0) * MEMORY_STARFIELD_PARAMS.mapping.interactionDensityScale;
  const terrainType = memoryTerrainType(node, degreeById, latestNodeTime);
  const baseColor = terrainType ? terrainVisualStyle(terrainType).color : nodeColor(node);
  const recencyColor = mixColor(baseColor, "#ffffff", recencyScore * 0.13);
  const color = confidenceScore < params.confidenceMedium
    ? mixColor(recencyColor, "#94a3b8", (1 - confidenceScore) * params.confidenceColorDesaturation)
    : recencyColor;
  const brightness = clamp(
    (node.visual?.brightness ?? 0.68) +
      recencyScore * params.recencyBrightnessBoost +
      (confidenceScore - params.confidenceMedium) * MEMORY_STARFIELD_PARAMS.mapping.confidenceNoiseAmplitude,
    0.22,
    1.24,
  );
  const size = clamp(
    Math.max(node.visual?.size ?? 0, params.baseSize) +
      mass * params.massSizeScale +
      recencyScore * params.recencySizeBoost,
    2.2,
    19,
  );
  const trailStrength = clamp(
    interactionScore * params.interactionTrailScale +
      recencyScore * 0.22 +
      confidenceScore * 0.18,
    0.12,
    1.36,
  );
  return {
    mass,
    size,
    brightness,
    color,
    recencyScore,
    confidenceScore,
    interactionScore,
    trailStrength,
    terrainType,
  };
}

function memoryStarfieldRecencyScore(node: AtlasNode, latestNodeTime: number): number {
  const nodeTime = nodeTimestamp(node);
  if (!nodeTime || !latestNodeTime) return 0.32;
  const ageDays = Math.max(0, (latestNodeTime - nodeTime) / 86_400_000);
  return clamp(Math.pow(0.5, ageDays / MEMORY_STARFIELD_PARAMS.mapping.recencyHalfLifeDays), 0, 1);
}

function memoryStarfieldConfidenceScore(node: AtlasNode): number {
  const confidence = `${node.confidence ?? ""} ${node.statement ?? ""}`.toLowerCase();
  const params = MEMORY_STARFIELD_PARAMS.mapping.particleAttributes;
  if (/high|高|confirmed|strong/.test(confidence)) return params.confidenceHigh;
  if (/low|低|weak|uncertain|不确定/.test(confidence)) return params.confidenceLow;
  return params.confidenceMedium;
}

function memoryTerrainType(node: AtlasNode, degreeById: Map<string, number>, latestNodeTime: number): MemoryTerrainType | null {
  const params = MEMORY_STARFIELD_PARAMS.mapping.terrain;
  const text = `${node.label} ${node.statement ?? ""} ${node.source_label ?? ""}`;
  const roiScore = node.metrics?.roi?.leverage_score ?? 0;
  const recencyScore = memoryStarfieldRecencyScore(node, latestNodeTime);
  const degree = degreeById.get(node.id) ?? 0;
  const faultPattern = safeRegex(params.faultConflictPattern, /conflict|contradiction|冲突|矛盾/i);

  if (faultPattern.test(text)) return "fault-line";
  if (
    node.metrics?.roi?.staleness_status === params.basinStaleStatus ||
    /低价值循环|重复|过时|废弃|shadow|standalone/i.test(text)
  ) {
    return "basin";
  }
  if (
    roiScore >= params.ridgeRoiThreshold ||
    (node.kind === "theme" && degree >= 4) ||
    (normalizeMemoryTier(node.memory_tier) === "核心画像" && node.importance === "高")
  ) {
    return "ridge";
  }
  if (recencyScore <= params.valleyRecentThreshold && degree <= 2 && roiScore < 0.42) return "valley";
  if (
    recencyScore >= params.shorelineRecentMin &&
    (node.kind === "project" || node.kind === "decision" || /机会|上升|proto|新生|增长|下一步|emerging/i.test(text))
  ) {
    return "shoreline";
  }
  if (node.category === "workflow" || node.category === "project_context") return "shoreline";
  return null;
}

function memoryStarfieldSignalKind(node: AtlasNode, degreeById: Map<string, number>, latestNodeTime: number): "black-hole" | "proto-star" | "terrain" | null {
  const text = `${node.label} ${node.statement ?? ""} ${node.source_label ?? ""}`;
  if (
    node.category === "deprecated_info" ||
    node.metrics?.roi?.staleness_status === MEMORY_STARFIELD_PARAMS.mapping.terrain.basinStaleStatus ||
    /过时|旧电脑|shadow|standalone|低价值循环/i.test(text)
  ) {
    return "black-hole";
  }
  if (
    (node.metrics?.roi?.leverage_score ?? 0) >= MEMORY_STARFIELD_PARAMS.mapping.terrain.ridgeRoiThreshold ||
    /机会|上升|proto|新生|增长|下一步/i.test(text)
  ) {
    return "proto-star";
  }
  if (memoryTerrainType(node, degreeById, latestNodeTime)) return "terrain";
  return null;
}

function buildTerrainSummary(nodes: AtlasNode[], degreeById: Map<string, number>, latestNodeTime: number): TerrainSummary {
  const grouped = new Map<MemoryTerrainType, AtlasNode[]>();
  for (const terrainType of MEMORY_TERRAIN_ORDER) grouped.set(terrainType, []);
  for (const node of nodes) {
    const terrainType = memoryTerrainType(node, degreeById, latestNodeTime);
    if (!terrainType) continue;
    grouped.get(terrainType)?.push(node);
  }

  const rows = MEMORY_TERRAIN_ORDER.map((terrainType) => {
    const nodesForTerrain = grouped.get(terrainType) ?? [];
    const visual = terrainVisualStyle(terrainType);
    const averageRoi = averageRoiScore(nodesForTerrain);
    const intensity = clamp(nodes.length ? nodesForTerrain.length / Math.max(1, nodes.length * 0.18) : 0, 0, 1);
    return {
      type: terrainType,
      label: visual.label,
      explanation: visual.explanation,
      count: nodesForTerrain.length,
      sampleLabels: nodesForTerrain
        .sort((a, b) => (b.metrics?.roi?.leverage_score ?? 0) - (a.metrics?.roi?.leverage_score ?? 0))
        .slice(0, 2)
        .map((node) => galaxyPreviewTitle(node)),
      semanticRole: terrainSemanticRole(terrainType),
      intensity,
      averageRoi,
      capabilitySignal: terrainCapabilitySignal(terrainType, nodesForTerrain.length, averageRoi),
    };
  });

  const dominantRow = [...rows].sort((a, b) => b.count - a.count || b.averageRoi - a.averageRoi)[0];
  const mappedCount = rows.reduce((sum, row) => sum + row.count, 0);
  return {
    total: mappedCount,
    rows,
    semanticCoverage: nodes.length ? mappedCount / nodes.length : 0,
    dominantLabel: dominantRow?.count ? dominantRow.label : "no dominant terrain",
    analysisNote: `${formatScore(nodes.length ? mappedCount / nodes.length : 0)} mapped · analysis-only rollback`,
  };
}

function terrainVisualStyle(terrainType: MemoryTerrainType): { label: string; explanation: string; color: string; opacity: number } {
  return MEMORY_TERRAIN_VISUALS[terrainType];
}

function terrainSemanticRole(terrainType: MemoryTerrainType): string {
  if (terrainType === "ridge") return "capability-anchor";
  if (terrainType === "shoreline") return "emerging-boundary";
  if (terrainType === "valley") return "underdeveloped-memory";
  if (terrainType === "basin") return "low-value-loop";
  return "conflict-review-zone";
}

function terrainCapabilitySignal(terrainType: MemoryTerrainType, count: number, averageRoi: number): string {
  if (!count) return "no active semantic signal";
  if (terrainType === "ridge") return averageRoi >= 0.6 ? "strong capability anchor" : "capability anchor needs reinforcement";
  if (terrainType === "shoreline") return "emerging work boundary";
  if (terrainType === "valley") return "inactive area for pruning or evidence";
  if (terrainType === "basin") return "candidate for compression";
  return "requires contradiction review";
}

function buildGalaxyRoiGradientSummary(nodes: AtlasNode[]): GalaxyRoiGradientSummary {
  const rows = [
    {
      id: "core-capability",
      label: "Core",
      nodes: nodes.filter((node) => normalizeMemoryTier(node.memory_tier) === "核心画像"),
    },
    {
      id: "project-decision",
      label: "Project",
      nodes: nodes.filter((node) => node.category === "project_context" || node.category === "decision" || node.kind === "project" || node.kind === "decision"),
    },
    {
      id: "workflow-action",
      label: "Workflow",
      nodes: nodes.filter((node) => node.category === "workflow" || node.metrics?.roi?.recommended_action === "use"),
    },
    {
      id: "review-compress",
      label: "Review",
      nodes: nodes.filter((node) => /review|stale|needs/i.test(`${node.metrics?.roi?.recommended_action ?? ""} ${node.metrics?.roi?.staleness_status ?? ""}`)),
    },
  ].map((row) => {
    const averageRoi = averageRoiScore(row.nodes);
    return {
      id: row.id,
      label: row.label,
      count: row.nodes.length,
      averageRoi,
      intensity: clamp(averageRoi * 0.72 + Math.min(1, row.nodes.length / Math.max(1, nodes.length * 0.18)) * 0.28, 0, 1),
    };
  });
  const averageRoi = averageRoiScore(nodes);
  const highValueCount = nodes.filter((node) => (node.metrics?.roi?.leverage_score ?? 0) >= MEMORY_STARFIELD_PARAMS.mapping.terrain.ridgeRoiThreshold).length;
  const capabilityGrowthCount = nodes.filter((node) => {
    const text = `${node.label} ${node.statement ?? ""} ${node.source_label ?? ""}`;
    return (node.metrics?.roi?.leverage_score ?? 0) >= 0.54 || /机会|增长|下一步|project|decision|workflow|capability/i.test(text);
  }).length;
  return {
    averageRoi,
    highValueCount,
    capabilityGrowthCount,
    rows,
    note: `${capabilityGrowthCount.toLocaleString()} growth-capable signals are shown as an analysis overlay; Presentation mode stays uncluttered.`,
  };
}

function averageRoiScore(nodes: AtlasNode[]): number {
  if (!nodes.length) return 0;
  return nodes.reduce((sum, node) => sum + (node.metrics?.roi?.leverage_score ?? 0), 0) / nodes.length;
}

function formatScore(value: number | undefined): string {
  if (typeof value !== "number" || !Number.isFinite(value)) return "0.00";
  return value.toFixed(2);
}

function latestNodeTimestamp(nodes: AtlasNode[]): number {
  return nodes.reduce((latest, node) => Math.max(latest, nodeTimestamp(node) ?? 0), 0);
}

function nodeTimestamp(node: AtlasNode): number | null {
  if (!node.date) return null;
  const parsed = Date.parse(node.date);
  return Number.isFinite(parsed) ? parsed : null;
}

function safeRegex(pattern: string, fallback: RegExp): RegExp {
  try {
    return new RegExp(pattern, "i");
  } catch {
    return fallback;
  }
}

function renderNebulaCanvas(canvas: HTMLCanvasElement, items: SceneNode[], edges: AtlasEdge[]) {
  const parent = canvas.parentElement;
  if (!parent) return;
  const rect = parent.getBoundingClientRect();
  const width = Math.max(1, Math.floor(rect.width));
  const height = Math.max(1, Math.floor(rect.height));
  const dpr = Math.min(window.devicePixelRatio || 1, 2);
  if (canvas.width !== Math.floor(width * dpr) || canvas.height !== Math.floor(height * dpr)) {
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
  }
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;

  const ctx = canvas.getContext("2d");
  if (!ctx) return;
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, width, height);

  const centerX = width * 0.52;
  const centerY = height * 0.54;
  const scale = Math.min(width / 520, height / 330);
  const maxRadius = Math.min(width, height) * 0.56;
  const armColors = GALAXY_ARM_COLORS;

  const background = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius * 1.15);
  background.addColorStop(0, "rgba(126, 224, 248, 0.055)");
  background.addColorStop(0.18, "rgba(126, 232, 212, 0.035)");
  background.addColorStop(0.48, "rgba(9, 14, 24, 0.12)");
  background.addColorStop(1, "rgba(2, 3, 8, 1)");
  ctx.fillStyle = background;
  ctx.fillRect(0, 0, width, height);

  drawDeepSpaceStars(ctx, width, height);
  drawGalaxyHalo(ctx, centerX, centerY, scale, maxRadius);

  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  for (let arm = 0; arm < armColors.length; arm += 1) {
    drawSpiralBand(ctx, centerX, centerY, scale, arm, armColors[arm], 34, 0.026, 0.42);
    drawSpiralBand(ctx, centerX, centerY, scale, arm, armColors[arm], 12, 0.052, 0.22);
    drawSpiralBand(ctx, centerX, centerY, scale, arm, armColors[arm], 3.4, 0.11, 0.08);
  }

  for (let i = 0; i < 21000; i += 1) {
    const arm = i % armColors.length;
    const radius = 7 + Math.pow(stableUnit(`dust-${i}`, "radius"), 0.7) * 250;
    const angle = (arm / armColors.length) * Math.PI * 2 + radius * 0.034 + (stableUnit(`dust-${i}`, "angle") - 0.5) * 0.62;
    const spread = (stableUnit(`dust-${i}`, "spread") - 0.5) * (20 + radius * 0.15);
    const x = centerX + (Math.cos(angle) * radius + Math.cos(angle + Math.PI / 2) * spread) * scale;
    const y = centerY + (Math.sin(angle) * radius * 0.62 + Math.sin(angle + Math.PI / 2) * spread) * scale;
    const twinkle = stableUnit(`dust-${i}`, "twinkle");
    const size = twinkle > 0.997 ? 1.52 : twinkle > 0.986 ? 0.82 : 0.3;
    const opacity = Math.max(0.026, (1 - radius / 330) * 0.22 + stableUnit(`dust-${i}`, "alpha") * 0.17);
    const color = twinkle > 0.988 ? mixColor(armColors[arm], "#ffffff", 0.72) : mixColor(armColors[arm], "#dbeafe", 0.38);
    ctx.fillStyle = rgba(color, opacity);
    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    ctx.fill();
  }

  const themeItems = items.filter((item) => item.node.kind === "theme");
  for (const item of themeItems) {
    const point = sceneToCanvas(item.position, centerX, centerY, scale);
    drawNebulaCloud(ctx, point.x, point.y, nodeColor(item.node), 56 + item.node.label.length * 0.55, 0.072);
  }

  ctx.globalCompositeOperation = "multiply";
  for (let arm = 0; arm < armColors.length; arm += 1) {
    drawDustLane(ctx, centerX, centerY, scale, arm);
  }
  drawRiftDust(ctx, centerX, centerY, scale);

  ctx.globalCompositeOperation = "lighter";
  const byId = new Map(items.map((item) => [item.node.id, item]));
  edges
    .filter((edge) => edge.weight >= 0.5)
    .slice(0, 96)
    .forEach((edge, index) => {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target) return;
      const from = sceneToCanvas(source.position, centerX, centerY, scale);
      const to = sceneToCanvas(target.position, centerX, centerY, scale);
      const color = nodeColor(source.node);
      ctx.strokeStyle = rgba(color, Math.min(0.055, 0.012 + edge.weight * 0.022));
      ctx.lineWidth = Math.max(0.18, edge.weight * 0.42);
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      const bend = (stableUnit(`${edge.id}-${index}`, "edge-bend") - 0.5) * 60 * scale;
      ctx.quadraticCurveTo((from.x + to.x) / 2 + bend, (from.y + to.y) / 2 - bend * 0.45, to.x, to.y);
      ctx.stroke();
    });

  const sortedItems = [...items]
    .sort((a, b) => (b.node.metrics?.roi?.leverage_score ?? 0) - (a.node.metrics?.roi?.leverage_score ?? 0))
    .slice(0, 360);
  for (const item of sortedItems) {
    drawDataBody(ctx, item, centerX, centerY, scale);
  }

  const core = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 62 * scale);
  core.addColorStop(0, "rgba(226, 247, 255, 0.86)");
  core.addColorStop(0.13, "rgba(126, 224, 248, 0.5)");
  core.addColorStop(0.36, "rgba(126, 232, 212, 0.15)");
  core.addColorStop(1, "rgba(126, 224, 248, 0)");
  ctx.fillStyle = core;
  ctx.beginPath();
  ctx.ellipse(centerX, centerY, 78 * scale, 46 * scale, -0.12, 0, Math.PI * 2);
  ctx.fill();
  drawCoreBurst(ctx, centerX, centerY, scale);
  ctx.restore();
}

function createWebglGalaxyTexture(): CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = 1024;
  canvas.height = 720;
  const ctx = canvas.getContext("2d");
  if (!ctx) {
    return new CanvasTexture(canvas);
  }

  const centerX = 512;
  const centerY = 360;
  const scale = 1.36;
  const maxRadius = 372;
  const armColors = GALAXY_ARM_COLORS;

  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.save();
  const halo = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius * 1.12);
  halo.addColorStop(0, "rgba(226, 247, 255, 0.46)");
  halo.addColorStop(0.08, "rgba(126, 224, 248, 0.28)");
  halo.addColorStop(0.24, "rgba(126, 232, 212, 0.11)");
  halo.addColorStop(0.56, "rgba(188, 223, 255, 0.052)");
  halo.addColorStop(1, "rgba(2, 3, 8, 0)");
  ctx.fillStyle = halo;
  ctx.beginPath();
  ctx.ellipse(centerX, centerY, maxRadius * 1.02, maxRadius * 0.46, -0.11, 0, Math.PI * 2);
  ctx.fill();

  ctx.globalCompositeOperation = "lighter";
  for (let arm = 0; arm < armColors.length; arm += 1) {
    drawSpiralBand(ctx, centerX, centerY, scale, arm, armColors[arm], 48, 0.032, 0.5);
    drawSpiralBand(ctx, centerX, centerY, scale, arm, armColors[arm], 20, 0.07, 0.3);
    drawSpiralBand(ctx, centerX, centerY, scale, arm, armColors[arm], 5.5, 0.18, 0.11);
  }

  for (let i = 0; i < 28000; i += 1) {
    const arm = i % armColors.length;
    const radius = 8 + Math.pow(stableUnit(`webgl-dust-${i}`, "radius"), 0.68) * 260;
    const angle = (arm / armColors.length) * Math.PI * 2 + radius * 0.034 + (stableUnit(`webgl-dust-${i}`, "angle") - 0.5) * 0.68;
    const spread = (stableUnit(`webgl-dust-${i}`, "spread") - 0.5) * (22 + radius * 0.16);
    const x = centerX + (Math.cos(angle) * radius + Math.cos(angle + Math.PI / 2) * spread) * scale;
    const y = centerY + (Math.sin(angle) * radius * 0.62 + Math.sin(angle + Math.PI / 2) * spread) * scale;
    const twinkle = stableUnit(`webgl-dust-${i}`, "twinkle");
    const size = twinkle > 0.997 ? 1.8 : twinkle > 0.985 ? 0.92 : 0.32;
    const opacity = Math.max(0.018, (1 - radius / 340) * 0.17 + stableUnit(`webgl-dust-${i}`, "alpha") * 0.12);
    const color = twinkle > 0.988 ? mixColor(armColors[arm], "#ffffff", 0.72) : mixColor(armColors[arm], "#dbeafe", 0.36);
    ctx.fillStyle = rgba(color, opacity);
    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    ctx.fill();
  }

  for (let arm = 0; arm < armColors.length; arm += 1) {
    for (let knot = 0; knot < 3; knot += 1) {
      const radius = 62 + knot * 58 + stableUnit(`webgl-cloud-${arm}-${knot}`, "radius") * 32;
      const angle = (arm / armColors.length) * Math.PI * 2 + radius * 0.034 + (stableUnit(`webgl-cloud-${arm}-${knot}`, "angle") - 0.5) * 0.34;
      const x = centerX + Math.cos(angle) * radius * scale;
      const y = centerY + Math.sin(angle) * radius * 0.62 * scale;
      drawNebulaCloud(ctx, x, y, armColors[arm], 62 + stableUnit(`webgl-cloud-${arm}-${knot}`, "size") * 42, 0.078);
    }
  }

  ctx.globalCompositeOperation = "source-over";
  for (let arm = 0; arm < armColors.length; arm += 1) {
    drawDustLane(ctx, centerX, centerY, scale, arm);
  }
  drawRiftDust(ctx, centerX, centerY, scale);

  ctx.globalCompositeOperation = "lighter";
  const core = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, 72 * scale);
  core.addColorStop(0, "rgba(235, 250, 255, 0.94)");
  core.addColorStop(0.16, "rgba(126, 224, 248, 0.58)");
  core.addColorStop(0.42, "rgba(126, 232, 212, 0.18)");
  core.addColorStop(1, "rgba(126, 224, 248, 0)");
  ctx.fillStyle = core;
  ctx.beginPath();
  ctx.ellipse(centerX, centerY, 86 * scale, 50 * scale, -0.12, 0, Math.PI * 2);
  ctx.fill();
  drawCoreBurst(ctx, centerX, centerY, scale);
  ctx.restore();

  const texture = new CanvasTexture(canvas);
  texture.minFilter = LinearFilter;
  texture.magFilter = LinearFilter;
  texture.needsUpdate = true;
  return texture;
}

function drawSpiralBand(
  ctx: CanvasRenderingContext2D,
  centerX: number,
  centerY: number,
  scale: number,
  arm: number,
  color: string,
  lineWidth: number,
  alpha: number,
  jitter: number,
) {
  ctx.save();
  ctx.strokeStyle = rgba(color, alpha);
  ctx.lineWidth = lineWidth * scale;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.shadowColor = rgba(color, alpha * 2.1);
  ctx.shadowBlur = (32 + lineWidth * 0.7) * scale;
  ctx.beginPath();
  for (let step = 0; step < 138; step += 1) {
    const radius = 6 + step * 1.93;
    const turbulence = (stableUnit(`band-${arm}-${step}`, "jitter") - 0.5) * jitter;
    const angle = (arm / GALAXY_ARM_COUNT) * Math.PI * 2 + radius * 0.034 + turbulence;
    const lift = (stableUnit(`band-${arm}-${step}`, "lift") - 0.5) * 5.5 * scale;
    const x = centerX + Math.cos(angle) * radius * scale;
    const y = centerY + Math.sin(angle) * radius * 0.61 * scale + lift;
    if (step === 0) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.restore();
}

function drawGalaxyHalo(ctx: CanvasRenderingContext2D, centerX: number, centerY: number, scale: number, maxRadius: number) {
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  const halo = ctx.createRadialGradient(centerX, centerY, 0, centerX, centerY, maxRadius * 1.08);
  halo.addColorStop(0, "rgba(255, 236, 180, 0.12)");
  halo.addColorStop(0.22, "rgba(188, 223, 255, 0.08)");
  halo.addColorStop(0.52, "rgba(199, 167, 255, 0.045)");
  halo.addColorStop(1, "rgba(8, 11, 20, 0)");
  ctx.fillStyle = halo;
  ctx.beginPath();
  ctx.ellipse(centerX, centerY, maxRadius * 1.08, maxRadius * 0.48, -0.11, 0, Math.PI * 2);
  ctx.fill();

  for (let ring = 0; ring < 4; ring += 1) {
    ctx.strokeStyle = `rgba(188, 223, 255, ${0.028 - ring * 0.004})`;
    ctx.lineWidth = (1.2 + ring * 0.55) * scale;
    ctx.beginPath();
    ctx.ellipse(centerX, centerY, (132 + ring * 34) * scale, (58 + ring * 14) * scale, -0.12, 0, Math.PI * 2);
    ctx.stroke();
  }
  ctx.restore();
}

function drawDeepSpaceStars(ctx: CanvasRenderingContext2D, width: number, height: number) {
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  for (let i = 0; i < 2400; i += 1) {
    const x = stableUnit(`field-${i}`, "x") * width;
    const y = stableUnit(`field-${i}`, "y") * height;
    const twinkle = stableUnit(`field-${i}`, "twinkle");
    const size = twinkle > 0.996 ? 1.15 : twinkle > 0.985 ? 0.68 : 0.32;
    const alpha = twinkle > 0.985 ? 0.42 : 0.11 + stableUnit(`field-${i}`, "alpha") * 0.13;
    ctx.fillStyle = rgba(twinkle > 0.994 ? "#fff7d6" : "#dbeafe", alpha);
    ctx.beginPath();
    ctx.arc(x, y, size, 0, Math.PI * 2);
    ctx.fill();
  }
  ctx.restore();
}

function drawDustLane(ctx: CanvasRenderingContext2D, centerX: number, centerY: number, scale: number, arm: number) {
  ctx.save();
  ctx.strokeStyle = "rgba(0, 0, 0, 0.52)";
  ctx.lineWidth = 9.5 * scale;
  ctx.lineCap = "round";
  ctx.beginPath();
  for (let step = 8; step < 128; step += 1) {
    const radius = 12 + step * 1.96;
    const jitter = (stableUnit(`lane-${arm}-${step}`, "rift") - 0.5) * 0.13;
    const angle = (arm / GALAXY_ARM_COUNT) * Math.PI * 2 + radius * 0.034 + 0.13 + jitter;
    const x = centerX + Math.cos(angle) * radius * scale;
    const y = centerY + Math.sin(angle) * radius * 0.61 * scale;
    if (step === 8) ctx.moveTo(x, y);
    else ctx.lineTo(x, y);
  }
  ctx.stroke();
  ctx.restore();
}

function drawRiftDust(ctx: CanvasRenderingContext2D, centerX: number, centerY: number, scale: number) {
  ctx.save();
  ctx.globalAlpha = 0.62;
  for (let lane = 0; lane < 7; lane += 1) {
    ctx.strokeStyle = `rgba(0, 0, 0, ${0.18 + lane * 0.018})`;
    ctx.lineWidth = (2.8 + stableUnit(`rift-${lane}`, "width") * 5.5) * scale;
    ctx.lineCap = "round";
    ctx.beginPath();
    for (let step = 0; step < 76; step += 1) {
      const radius = 24 + step * 2.55;
      const angle = (lane / 7) * Math.PI * 2 + radius * 0.03 + Math.sin(step * 0.12 + lane) * 0.11;
      const x = centerX + Math.cos(angle) * radius * scale;
      const y = centerY + Math.sin(angle) * radius * 0.55 * scale + (stableUnit(`rift-${lane}-${step}`, "y") - 0.5) * 5 * scale;
      if (step === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
  }
  ctx.restore();
}

function drawNebulaCloud(ctx: CanvasRenderingContext2D, x: number, y: number, color: string, radius: number, alpha: number) {
  ctx.save();
  ctx.translate(x, y);
  ctx.rotate((stableUnit(`${x}:${y}`, "cloud-rotate") - 0.5) * 0.8);
  ctx.scale(1.55, 0.74);
  const gradient = ctx.createRadialGradient(0, 0, radius * 0.08, 0, 0, radius);
  gradient.addColorStop(0, rgba(mixColor(color, "#ffffff", 0.28), alpha * 0.86));
  gradient.addColorStop(0.36, rgba(color, alpha * 0.42));
  gradient.addColorStop(0.7, rgba(color, alpha * 0.12));
  gradient.addColorStop(1, rgba(color, 0));
  ctx.fillStyle = gradient;
  ctx.beginPath();
  ctx.arc(0, 0, radius, 0, Math.PI * 2);
  ctx.fill();
  ctx.restore();
}

function drawDataBody(
  ctx: CanvasRenderingContext2D,
  item: SceneNode,
  centerX: number,
  centerY: number,
  scale: number,
) {
  const point = sceneToCanvas(item.position, centerX, centerY, scale);
  const color = nodeColor(item.node);
  const score = item.node.metrics?.roi?.leverage_score ?? 0.3;
  const tier = normalizeMemoryTier(item.node.memory_tier);
  const radius =
    item.node.kind === "theme"
      ? 7.5
      : item.node.kind === "decision"
        ? 6.8
        : tier === "核心画像"
          ? 7.2
          : tier === "一般"
            ? 4.2
            : 1.75;
  const prominent = isProminentBody(item.node);
  const glowRadius = (radius * (prominent ? 3.3 : 1.8) + score * (prominent ? 10 : 3)) * scale;
  const bodyRadius = radius * (prominent ? 0.68 : 0.46) * scale;

  const glow = ctx.createRadialGradient(point.x, point.y, 0, point.x, point.y, glowRadius);
  glow.addColorStop(0, rgba(mixColor(color, "#ffffff", 0.35), prominent ? 0.42 : 0.16));
  glow.addColorStop(0.26, rgba(color, prominent ? 0.18 : 0.055));
  glow.addColorStop(1, rgba(color, 0));
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.arc(point.x, point.y, glowRadius, 0, Math.PI * 2);
  ctx.fill();

  ctx.fillStyle = rgba(mixColor(color, "#ffffff", prominent ? 0.22 : 0.08), prominent ? 0.82 : 0.32);
  ctx.beginPath();
  ctx.arc(point.x, point.y, bodyRadius, 0, Math.PI * 2);
  ctx.fill();

  if (item.node.kind === "decision" || tier === "核心画像") {
    ctx.strokeStyle = rgba("#ffffff", 0.58);
    ctx.lineWidth = 1.1;
    ctx.beginPath();
    ctx.ellipse(point.x, point.y, bodyRadius * 1.95, bodyRadius * 0.75, -0.38, 0, Math.PI * 2);
    ctx.stroke();
  }

  if (prominent) {
    ctx.strokeStyle = rgba(mixColor(color, "#ffffff", 0.4), item.node.kind === "theme" ? 0.34 : 0.22);
    ctx.lineWidth = Math.max(0.45, 0.85 * scale);
    ctx.beginPath();
    ctx.ellipse(point.x, point.y, bodyRadius * 2.7, bodyRadius * 0.95, -0.26, 0, Math.PI * 2);
    ctx.stroke();
  }
}

function drawCoreBurst(ctx: CanvasRenderingContext2D, centerX: number, centerY: number, scale: number) {
  ctx.save();
  ctx.globalCompositeOperation = "lighter";
  for (let ray = 0; ray < 28; ray += 1) {
    const angle = (ray / 28) * Math.PI * 2 + (stableUnit(`core-ray-${ray}`, "angle") - 0.5) * 0.11;
    const length = (34 + stableUnit(`core-ray-${ray}`, "length") * 62) * scale;
    const inner = 8 * scale;
    const gradient = ctx.createLinearGradient(
      centerX + Math.cos(angle) * inner,
      centerY + Math.sin(angle) * inner * 0.62,
      centerX + Math.cos(angle) * length,
      centerY + Math.sin(angle) * length * 0.62,
    );
    gradient.addColorStop(0, "rgba(226, 247, 255, 0.26)");
    gradient.addColorStop(1, "rgba(126, 224, 248, 0)");
    ctx.strokeStyle = gradient;
    ctx.lineWidth = (0.8 + stableUnit(`core-ray-${ray}`, "width") * 1.4) * scale;
    ctx.beginPath();
    ctx.moveTo(centerX + Math.cos(angle) * inner, centerY + Math.sin(angle) * inner * 0.62);
    ctx.lineTo(centerX + Math.cos(angle) * length, centerY + Math.sin(angle) * length * 0.62);
    ctx.stroke();
  }
  ctx.restore();
}

function sceneToCanvas(
  position: { x: number; y: number; z: number },
  centerX: number,
  centerY: number,
  scale: number,
): { x: number; y: number } {
  return {
    x: centerX + position.x * scale,
    y: centerY - position.y * scale + position.z * 0.08 * scale,
  };
}

function galaxyPreviewTitle(node: AtlasNode): string {
  return truncate(
    node.label
      .replace(/^(核心画像|一般|临时|重要中长期|一般短期)\s*·\s*/, "")
      .replace(/\s*·\s*/g, " / "),
    74,
  );
}

function galaxyPreviewSummary(node: AtlasNode): string {
  const statement = node.statement
    ?.replace(/^静态图谱低敏摘要[：:]\s*/, "")
    .replace(/层级=/g, "层级 ")
    .replace(/分类=/g, "分类 ")
    .replace(/重要性=/g, "重要性 ")
    .replace(/有效期=/g, "有效期 ")
    .replace(/主题=/g, "主题 ");
  return truncate(statement || node.source_label || translateKind(node.kind), 104);
}

function degreeMap(edges: AtlasEdge[]): Map<string, number> {
  const counts = new Map<string, number>();
  for (const edge of edges) {
    counts.set(edge.source, (counts.get(edge.source) ?? 0) + 1);
    counts.set(edge.target, (counts.get(edge.target) ?? 0) + 1);
  }
  return counts;
}

function emptyFocusedNeighborhood(focusId: string): FocusNeighborhood {
  return {
    focusId,
    totalNeighborCount: 0,
    visibleNeighborCount: 0,
    hiddenNeighborCount: 0,
    primaryNeighborCount: 0,
    secondaryNeighborCount: 0,
    neighbors: [],
    visibleNeighborIds: new Set<string>(),
  };
}

function buildFocusedNeighborhood(nodeId: string, edges: AtlasEdge[], allowedNodeIds?: Set<string>): FocusNeighborhood {
  const allNeighbors = directNeighborList(nodeId, edges);
  const renderableNeighbors = allowedNodeIds
    ? allNeighbors.filter((neighbor) => allowedNodeIds.has(neighbor.id))
    : allNeighbors;
  const visibleNeighbors = renderableNeighbors.slice(0, MAX_FOCUS_VISIBLE_NEIGHBORS).map((neighbor, index) => ({
    ...neighbor,
    rank: index,
    layer: index < MAX_FOCUS_PRIMARY_NEIGHBORS ? "primary" as const : "secondary" as const,
  }));
  const primaryNeighborCount = visibleNeighbors.filter((neighbor) => neighbor.layer === "primary").length;
  const secondaryNeighborCount = visibleNeighbors.length - primaryNeighborCount;
  return {
    focusId: nodeId,
    totalNeighborCount: allNeighbors.length,
    visibleNeighborCount: visibleNeighbors.length,
    hiddenNeighborCount: Math.max(0, allNeighbors.length - visibleNeighbors.length),
    primaryNeighborCount,
    secondaryNeighborCount,
    neighbors: visibleNeighbors,
    visibleNeighborIds: new Set(visibleNeighbors.map((neighbor) => neighbor.id)),
  };
}

function directNeighborList(nodeId: string, edges: AtlasEdge[]): Array<{ id: string; weight: number }> {
  const neighbors = new Map<string, number>();
  for (const edge of edges) {
    if (edge.source !== nodeId && edge.target !== nodeId) continue;
    const neighborId = edge.source === nodeId ? edge.target : edge.source;
    neighbors.set(neighborId, Math.max(neighbors.get(neighborId) ?? 0, edge.weight ?? 0));
  }
  return [...neighbors.entries()]
    .map(([id, weight]) => ({ id, weight }))
    .sort((a, b) => b.weight - a.weight);
}

function localNeighborhoodPosition(
  focusPosition: { x: number; y: number; z: number },
  neighbor: Pick<FocusNeighbor, "id" | "rank" | "layer" | "weight">,
  neighborhood: FocusNeighborhood,
): { x: number; y: number; z: number } {
  const layerPeers = neighbor.layer === "primary" ? neighborhood.primaryNeighborCount : neighborhood.secondaryNeighborCount;
  const layerRank = neighbor.layer === "primary" ? neighbor.rank : neighbor.rank - MAX_FOCUS_PRIMARY_NEIGHBORS;
  const safePeers = Math.max(1, layerPeers);
  const phaseOffset = neighbor.layer === "primary" ? 0 : Math.PI / safePeers;
  const angle = (layerRank / safePeers) * Math.PI * 2 + phaseOffset + (stableUnit(`${neighborhood.focusId}:${neighbor.id}`, "lens-angle") - 0.5) * 0.22;
  const radiusBase = neighbor.layer === "primary" ? 17 : 31;
  const radiusWeight = (1 - Math.min(1, Math.max(0, neighbor.weight))) * (neighbor.layer === "primary" ? 5 : 8);
  const radius = radiusBase + radiusWeight + stableUnit(`${neighborhood.focusId}:${neighbor.id}`, "lens-radius") * 4;
  return {
    x: focusPosition.x + Math.cos(angle) * radius,
    y: focusPosition.y + Math.sin(angle) * radius * 0.62,
    z: focusPosition.z + (neighbor.layer === "primary" ? 14 : 7) + (stableUnit(`${neighborhood.focusId}:${neighbor.id}`, "lens-z") - 0.5) * 5,
  };
}

function translateKind(kind: AtlasNode["kind"]): string {
  return { theme: "主题", project: "项目", decision: "决策", memory: "记忆", category: "分类", tier: "层级", timeline_event: "事件" }[kind] ?? "节点";
}

function truncate(value: string, maxLength: number): string {
  const clean = value.replace(/\s+/g, " ").trim();
  return clean.length > maxLength ? `${clean.slice(0, maxLength - 1)}…` : clean;
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function starStyle(item: SceneNode): CSSProperties {
  const position = item.position;
  const size = Math.max(14, Math.min(22, (item.node.visual?.size ?? 7) * 1.8));
  const left = Math.max(5, Math.min(95, 50 + position.x * 0.2));
  const top = Math.max(8, Math.min(92, 50 - position.y * 0.28));
  return {
    "--star-color": item.node.visual?.color ?? "#8fd3ff",
    height: `${size}px`,
    left: `${left}%`,
    top: `${top}%`,
    width: `${size}px`,
    zIndex: Math.round(100 + position.z),
  } as CSSProperties;
}

function galaxyPosition(node: AtlasNode): { x: number; y: number; z: number } {
  if (node.kind === "theme") {
    const index = clusterIndex(node);
    const angle = (index / 8) * Math.PI * 2 - Math.PI / 2;
    return {
      x: Math.cos(angle) * 68,
      y: Math.sin(angle) * 46,
      z: (stableUnit(node.id, "theme-depth") - 0.5) * 16,
    };
  }
  const cluster = clusterIndex(node);
  const armCount = 6;
  const armAngle = (cluster % armCount) / armCount * Math.PI * 2;
  const tier = normalizeMemoryTier(node.memory_tier);
  const baseRadius =
    tier === "核心画像"
      ? 18 + stableUnit(node.id, "core-radius") * 28
      : tier === "一般"
        ? 58 + stableUnit(node.id, "mid-radius") * 74
        : node.kind === "decision"
          ? 44 + stableUnit(node.id, "decision-radius") * 90
          : 118 + stableUnit(node.id, "short-radius") * 72;
  const spiral = armAngle + baseRadius * 0.033 + (stableUnit(node.id, "spiral-jitter") - 0.5) * 0.34;
  const offPlane = (stableUnit(node.id, "plane") - 0.5) * (tier === "临时" ? 76 : 38);
  const x = Math.cos(spiral) * baseRadius;
  const y = Math.sin(spiral) * baseRadius * 0.68;
  return {
    x,
    y,
    z: offPlane,
  };
}

function clusterIndex(node: AtlasNode): number {
  const source = node.visual?.cluster ?? node.category ?? node.id;
  return Math.floor(stableUnit(source, "cluster") * 8);
}

function nodeColor(node: AtlasNode): string {
  if (node.kind === "decision") return "#f48fb1";
  if (node.kind === "project") return "#8fd3ff";
  const tier = normalizeMemoryTier(node.memory_tier);
  if (tier === "核心画像") return "#7ee8d4";
  if (tier === "一般") return node.visual?.color ?? "#8fd3ff";
  return node.visual?.color ?? "#94a3b8";
}

function isProminentBody(node: AtlasNode, degreeById?: Map<string, number>, latestNodeTime = 0): boolean {
  const parameterMass = degreeById ? memoryStarfieldMass(node, degreeById, latestNodeTime) : 0;
  return (
    node.kind === "theme" ||
    node.kind === "project" ||
    node.kind === "decision" ||
    normalizeMemoryTier(node.memory_tier) === "核心画像" ||
    node.importance === "高" ||
    (node.metrics?.roi?.leverage_score ?? 0) >= MEMORY_STARFIELD_PARAMS.mapping.terrain.ridgeRoiThreshold ||
    parameterMass >= 15
  );
}

function rgba(hex: string, alpha: number): string {
  const color = hex.replace("#", "");
  const value = Number.parseInt(color.length === 3 ? color.split("").map((item) => item + item).join("") : color, 16);
  const r = (value >> 16) & 255;
  const g = (value >> 8) & 255;
  const b = value & 255;
  return `rgba(${r}, ${g}, ${b}, ${Math.max(0, Math.min(1, alpha)).toFixed(3)})`;
}

function mixColor(from: string, to: string, amount: number): string {
  const a = parseHex(from);
  const b = parseHex(to);
  const t = Math.max(0, Math.min(1, amount));
  return `#${[0, 1, 2]
    .map((index) => Math.round(a[index] + (b[index] - a[index]) * t).toString(16).padStart(2, "0"))
    .join("")}`;
}

function parseHex(hex: string): [number, number, number] {
  const color = hex.replace("#", "");
  const normalized = color.length === 3 ? color.split("").map((item) => item + item).join("") : color.padEnd(6, "0").slice(0, 6);
  const value = Number.parseInt(normalized, 16);
  return [(value >> 16) & 255, (value >> 8) & 255, value & 255];
}

function stableUnit(value: string, salt: string): number {
  let hash = 2166136261;
  const input = `${salt}:${value}`;
  for (let index = 0; index < input.length; index += 1) {
    hash ^= input.charCodeAt(index);
    hash = Math.imul(hash, 16777619) >>> 0;
  }
  return (hash % 1000000) / 1000000;
}
