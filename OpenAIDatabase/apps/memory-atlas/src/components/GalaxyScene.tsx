import { RotateCcw, ZoomIn, ZoomOut } from "lucide-react";
import type { CSSProperties } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import {
  AdditiveBlending,
  BufferGeometry,
  CanvasTexture,
  Color,
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
  Vector2,
  Vector3,
  WebGLRenderer,
} from "three";
import { normalizeMemoryTier } from "../data/atlas";
import type { AtlasEdge, AtlasNode } from "../types";

interface GalaxySceneProps {
  nodes: AtlasNode[];
  edges: AtlasEdge[];
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

declare global {
  interface Window {
    __memoryAtlasGalaxySignal?: () => GalaxySignal;
    __memoryAtlasGalaxyDebugTargets?: () => Array<{ id: string; x: number; y: number; linkedCount: number }>;
  }
}

const MAX_RENDERED_NODES = 900;
const MAX_FOCUS_PRIMARY_NEIGHBORS = 10;
const MAX_FOCUS_SECONDARY_NEIGHBORS = 18;
const MAX_FOCUS_VISIBLE_NEIGHBORS = MAX_FOCUS_PRIMARY_NEIGHBORS + MAX_FOCUS_SECONDARY_NEIGHBORS;
const MAX_PULSE_NEIGHBORS = MAX_FOCUS_VISIBLE_NEIGHBORS;
const GALAXY_ARM_COLORS = ["#bcdfff", "#d7e8ff", "#a7ecff", "#e5d6ff", "#c8f7e7", "#f7c8dd"];
const GALAXY_ARM_COUNT = 6;

export function GalaxyScene({ nodes, edges, selectedNode, onSelectNode }: GalaxySceneProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const nebulaCanvasRef = useRef<HTMLCanvasElement | null>(null);
  const pointerRef = useRef<PointerState>({ dragging: false, moved: false, x: 0, y: 0 });
  const rotationRef = useRef({ x: -0.14, y: 0.42 });
  const zoomRef = useRef(1);
  const selectedIdRef = useRef<string | null>(selectedNode?.id ?? null);
  const hoveredIdRef = useRef<string | null>(null);
  const [renderError, setRenderError] = useState("");
  const [hoverPreview, setHoverPreview] = useState<HoverPreview | null>(null);

  const renderNodes = useMemo(() => nodes.slice(0, MAX_RENDERED_NODES), [nodes]);
  const renderItems = useMemo<SceneNode[]>(
    () => renderNodes.map((node) => ({ node, position: galaxyPosition(node) })),
    [renderNodes],
  );
  const nodeById = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);
  const renderableNodeIds = useMemo(() => new Set(renderNodes.map((node) => node.id)), [renderNodes]);
  const degreeById = useMemo(() => degreeMap(edges), [edges]);
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
      opacity: 0.86,
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
    for (let i = 0; i < 7600; i += 1) {
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
      const color = new Color(node.visual?.color ?? "#8fd3ff");
      const brightness = node.visual?.brightness ?? 0.72;
      positions.push(position.x, position.y, position.z);
      colors.push(color.r * brightness, color.g * brightness, color.b * brightness);
      sizes.push(node.visual?.size ?? 6);
      nodeIndexByPoint.push(node.id);
    });
    geometry.setAttribute("position", new Float32BufferAttribute(positions, 3));
    geometry.setAttribute("color", new Float32BufferAttribute(colors, 3));
    geometry.setAttribute("size", new Float32BufferAttribute(sizes, 1));

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
        const sourceColor = new Color(renderItems.find((item) => item.node.id === edge.source)?.node.visual?.color ?? "#8fd3ff");
        const targetColor = new Color(renderItems.find((item) => item.node.id === edge.target)?.node.visual?.color ?? "#8fd3ff");
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
    for (let i = 0; i < 1800; i += 1) {
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
      if (!isProminentBody(node)) return;
      const position = item.position;
      const color = new Color(node.visual?.color ?? "#8fd3ff");
      const materialForNode = new MeshBasicMaterial({
        color,
        transparent: true,
        opacity: Math.max(0.22, (node.visual?.brightness ?? 0.72) * 0.44),
        blending: AdditiveBlending,
        depthWrite: false,
      });
      const mesh = new Mesh(nodeSphereGeometry, materialForNode);
      mesh.position.set(position.x, position.y, position.z);
      mesh.scale.setScalar(Math.max(0.9, (node.visual?.size ?? 6) * 0.22));
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
    let frame = 0;
    let raf = 0;

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
      selectedMarker.scale.setScalar(Math.max(6, (renderItems[selectedIndex]?.node.visual?.size ?? 8) * 0.72));
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
            const sourceColor = new Color(sceneItemById.get(focusId)?.node.visual?.color ?? "#8fd3ff");
            const targetColor = new Color(sceneItemById.get(neighbor.id)?.node.visual?.color ?? "#8fd3ff");
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
        const color = target.selected ? new Color("#ffffff") : new Color(sceneItem.node.visual?.color ?? "#8fd3ff");
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
      if (!pulseItems.length) return;
      const time = frame * 0.075;
      for (const item of pulseItems) {
        const wave = (Math.sin(time + item.phase) + 1) / 2;
        const amplitude = item.selected ? 0.16 : 0.28;
        item.mesh.scale.setScalar(item.baseScale * (1 + wave * amplitude));
        item.material.opacity = item.selected ? 0.28 + wave * 0.18 : 0.08 + wave * 0.22;
      }
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

    function render() {
      frame += 1;
      const autoMotion = prefersReducedMotion ? 0 : 0.0016;
      galaxyGroup.rotation.x = rotationRef.current.x;
      galaxyGroup.rotation.y = rotationRef.current.y + frame * autoMotion;
      galaxyGroup.updateMatrixWorld(true);
      updateCameraFocus();
      updateSelectedMarker();
      updateFocusEdgeHighlight();
      rebuildNeighborPulses();
      updateNeighborPulse();
      renderer.clear(true, true, true);
      renderer.render(scene, camera);
      renderer.domElement.dataset.frame = String(frame);
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
      ambientGeometry.dispose();
      haloGeometry.dispose();
      galaxyPlaneGeometry.dispose();
      galaxyPlaneMaterial.dispose();
      galaxyTexture.dispose();
      coreGeometry.dispose();
      coreMaterial.dispose();
      selectedMarkerGeometry.dispose();
      material.dispose();
      ambient.material.dispose();
      halo.material.dispose();
      nodeSphereGeometry.dispose();
      for (const nodeMaterial of nodeMaterials) nodeMaterial.dispose();
      selectedMarkerMaterial.dispose();
      renderer.dispose();
      renderer.domElement.remove();
      if (window.__memoryAtlasGalaxySignal === readGalaxySignal) {
        delete window.__memoryAtlasGalaxySignal;
      }
      if (window.__memoryAtlasGalaxyDebugTargets === readGalaxyDebugTargets) {
        delete window.__memoryAtlasGalaxyDebugTargets;
      }
    };
  }, [degreeById, edges, onSelectNode, renderItems, renderNodes]);

  function resetGalaxyView() {
    rotationRef.current = { x: -0.14, y: 0.42 };
    zoomRef.current = 1;
  }

  function zoomGalaxy(delta: number) {
    zoomRef.current = Math.min(2.4, Math.max(0.58, zoomRef.current + delta));
  }

  return (
    <div className="galaxy-scene" ref={containerRef}>
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
      </div>
      {renderError ? (
        <div className="galaxy-fallback" title={renderError}>
          <strong>WebGL 不可用</strong>
          <span>已启用静态星云 fallback，仍可点击星体查看记忆。</span>
        </div>
      ) : null}
    </div>
  );
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

function isProminentBody(node: AtlasNode): boolean {
  return (
    node.kind === "theme" ||
    node.kind === "project" ||
    node.kind === "decision" ||
    normalizeMemoryTier(node.memory_tier) === "核心画像" ||
    node.importance === "高" ||
    (node.metrics?.roi?.leverage_score ?? 0) >= 0.72
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
