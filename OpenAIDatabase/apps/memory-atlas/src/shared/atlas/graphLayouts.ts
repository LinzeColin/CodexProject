import type { AtlasEdge, AtlasNode } from "../../types";
import { clusterIndex, degreeMap, expandGraphIds, kindRank, nodeColor, nodeRadius, shortNodeLabel } from "./contributionModels";
import { LayoutEdge, LayoutGroup, LayoutNode } from "./layoutContracts";
import { stableUnit } from "./utils";



export function buildMapLayout(nodes: AtlasNode[], edges: AtlasEdge[], limit: number): { nodes: LayoutNode[]; edges: LayoutEdge[]; groups: LayoutGroup[] } {
  const degree = degreeMap(edges);
  const themes = nodes.filter((node) => node.kind === "theme");
  const displayNodes = nodes
    .filter((node) => ["theme", "project", "decision", "memory"].includes(node.kind))
    .sort((a, b) => (degree.get(b.id) ?? 0) - (degree.get(a.id) ?? 0))
    .slice(0, limit);
  const themeIds = new Map(themes.map((node, index) => [node.id.replace("theme:", ""), index]));
  const layoutNodes = displayNodes.map((node, index): LayoutNode => {
    const cluster = node.visual?.cluster ?? node.id.replace("theme:", "");
    const groupIndex = themeIds.get(cluster) ?? index % Math.max(themes.length, 1);
    const groupAngle = (groupIndex / Math.max(themes.length, 1)) * Math.PI * 2 - Math.PI / 2;
    const groupX = 500 + Math.cos(groupAngle) * 265;
    const groupY = 310 + Math.sin(groupAngle) * 205;
    const localAngle = stableUnit(node.id, "map-angle") * Math.PI * 2;
    const localRadius = node.kind === "theme" ? 0 : 28 + stableUnit(node.id, "map-radius") * 82;
    return {
      node,
      x: node.kind === "theme" ? groupX : groupX + Math.cos(localAngle) * localRadius,
      y: node.kind === "theme" ? groupY : groupY + Math.sin(localAngle) * localRadius,
      r: nodeRadius(node, degree.get(node.id) ?? 0),
      color: nodeColor(node),
      label: shortNodeLabel(node, node.kind === "theme" ? 20 : 12),
      degree: degree.get(node.id) ?? 0,
    };
  });
  const byId = new Map(layoutNodes.map((node) => [node.node.id, node]));
  const layoutEdges = edges
    .map((edge): LayoutEdge | null => {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target) return null;
      return { id: edge.id, source, target, weight: edge.weight, color: source.color };
    })
    .filter((edge): edge is LayoutEdge => Boolean(edge))
    .slice(0, 420);
  const groups = themes.map((theme, index): LayoutGroup => {
    const angle = (index / Math.max(themes.length, 1)) * Math.PI * 2 - Math.PI / 2;
    return {
      id: theme.id,
      label: shortNodeLabel(theme, 18),
      x: 500 + Math.cos(angle) * 265,
      y: 310 + Math.sin(angle) * 205,
      r: 112,
      color: nodeColor(theme),
    };
  });
  return { nodes: layoutNodes, edges: layoutEdges, groups };
}



export function buildObsidianLayout(
  nodes: AtlasNode[],
  edges: AtlasEdge[],
  selectedNode: AtlasNode | null,
  localOnly: boolean,
  depth: number,
): { nodes: LayoutNode[]; edges: LayoutEdge[] } {
  const visibleIds = localOnly && selectedNode ? expandGraphIds(selectedNode.id, edges, depth) : new Set(nodes.map((node) => node.id));
  const filteredNodes = nodes
    .filter((node) => visibleIds.has(node.id))
    .sort((a, b) => kindRank(a.kind) - kindRank(b.kind))
    .slice(0, 220);
  const filteredNodeIds = new Set(filteredNodes.map((node) => node.id));
  const filteredEdges = edges.filter((edge) => filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)).slice(0, 650);
  const degree = degreeMap(filteredEdges);
  const count = filteredNodes.length || 1;
  const layoutNodes = filteredNodes.map((node, index): LayoutNode => {
    const clusterSeed = clusterIndex(node);
    const ring = node.kind === "theme" ? 120 : node.kind === "memory" ? 225 : 175;
    const angle = (index / count) * Math.PI * 2 + clusterSeed * 0.38;
    const jitter = (stableUnit(node.id, "obsidian-radius") - 0.5) * 72;
    return {
      node,
      x: 500 + Math.cos(angle) * (ring + jitter),
      y: 300 + Math.sin(angle) * (ring * 0.72 + jitter * 0.45),
      r: nodeRadius(node, degree.get(node.id) ?? 0),
      color: nodeColor(node),
      label: (degree.get(node.id) ?? 0) > 6 || node.kind !== "memory" ? shortNodeLabel(node, 14) : "",
      degree: degree.get(node.id) ?? 0,
    };
  });
  const byId = new Map(layoutNodes.map((node) => [node.node.id, node]));
  const layoutEdges = filteredEdges
    .map((edge): LayoutEdge | null => {
      const source = byId.get(edge.source);
      const target = byId.get(edge.target);
      if (!source || !target) return null;
      return { id: edge.id, source, target, weight: edge.weight, color: edge.kind === "belongs_to_theme" ? target.color : "rgba(244,241,232,0.7)" };
    })
    .filter((edge): edge is LayoutEdge => Boolean(edge));
  return { nodes: layoutNodes, edges: layoutEdges };
}
