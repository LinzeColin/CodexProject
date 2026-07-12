import type { MemoryTerrainType } from "../config/memoryStarfieldParameters";
import type { AtlasNode } from "../types";
import type { UniverseStateSnapshot } from "./universeState";

export const STARFIELD_MAPPING_VERSION = "memory_starfield_snapshot_mapping.v1_1_7_stage4_phase3" as const;

export type StarfieldMappingSource = "universe_state_snapshot" | "atlas_nodes";

export interface StarfieldParticleMapping {
  nodeId: string;
  source: StarfieldMappingSource;
  sourceClusterId: string;
  label: string;
  massScore: number;
  size: number;
  brightness: number;
  color: string;
  recencyScore: number;
  confidenceScore: number;
  interactionScore: number;
  trailStrength: number;
  terrainType: MemoryTerrainType | null;
  fallback: boolean;
  formulaInputs: {
    mass_score: number;
    roi_potential: number;
    evidence_count: number;
    growth_score: number;
    decline_score: number;
    terrain_strength: number;
  };
}

export interface StarfieldMappingResult {
  version: typeof STARFIELD_MAPPING_VERSION;
  source: StarfieldMappingSource;
  generatedAt: string;
  particleCount: number;
  snapshotMappedCount: number;
  fallbackCount: number;
  safety: {
    redactedSnapshot: boolean;
    rawPrivateDataIncluded: false;
    writebackAllowed: false;
  };
  formulas: {
    mass: string;
    brightness: string;
    color: string;
    trail: string;
  };
  particles: StarfieldParticleMapping[];
}

const terrainColors: Record<MemoryTerrainType, string> = {
  ridge: "#7ee8d4",
  shoreline: "#ffef9a",
  valley: "#8fd3ff",
  basin: "#111827",
  "fault-line": "#f48fb1",
};

const clusterAliases: Record<string, string[]> = {
  "cluster-memory-continuity": ["memory-rag-continuity", "memory-continuity", "long-term-memory"],
  "cluster-codex-workflow": ["codex-agent-workflow", "codex-workflow", "delivery-system"],
  "cluster-visual-ux": ["ai-era-growth", "formal-engineering-delivery", "visual-system"],
  "cluster-agent-governance": ["codex-agent-workflow", "formal-engineering-delivery"],
  "cluster-import-hygiene": ["memory-rag-continuity", "formal-engineering-delivery"],
};

export function mapUniverseStateSnapshotToStarfield(
  snapshot: UniverseStateSnapshot,
  nodes: AtlasNode[],
): StarfieldMappingResult {
  const safety = assertRedactedSnapshot(snapshot);
  const terrainByCluster = buildTerrainByCluster(snapshot);
  const clusterById = new Map(snapshot.state.dominant_clusters.map((cluster) => [cluster.cluster_id, cluster]));

  const particles = nodes.map<StarfieldParticleMapping>((node) => {
    const sourceClusterId = matchSnapshotCluster(node, snapshot) ?? "";
    const cluster = sourceClusterId ? clusterById.get(sourceClusterId) : undefined;
    const terrain = sourceClusterId ? terrainByCluster.get(sourceClusterId) : undefined;
    if (!cluster) return mapAtlasNodeToParticle(node, true);

    const mass_score = clamp01(cluster.mass_score);
    const growth_score = growthScoreForCluster(snapshot, cluster.cluster_id);
    const decline_score = declineScoreForCluster(snapshot, cluster.cluster_id);
    const roi_potential = clamp01(Math.max(node.metrics?.roi?.leverage_score ?? 0, growth_score, mass_score * 0.72));
    const evidence_count = Math.max(1, cluster.evidence_count);
    const terrain_strength = terrain?.strength ?? mass_score;
    const terrainType = terrainTypeFromSnapshot(terrain?.terrain_type);
    const massScore = round2(2 + mass_score * 13 + roi_potential * 4 + Math.log2(evidence_count + 1) * 0.34);
    const confidenceScore = clamp01(0.68 + mass_score * 0.22 + Math.min(0.1, evidence_count / 900));
    const recencyScore = clamp01(0.28 + growth_score * 0.52 + roi_potential * 0.14);
    const interactionScore = clamp01(Math.sqrt(evidence_count) / 14);
    const brightness = round2(clamp(0.28 + mass_score * 0.52 + roi_potential * 0.22 + confidenceScore * 0.18, 0.24, 1.24));
    const size = round2(clamp(3.2 + massScore * 0.5 + recencyScore * 1.4, 2.4, 19));
    const trailStrength = round2(clamp(0.18 + interactionScore * 0.42 + growth_score * 0.36 + (1 - decline_score) * 0.08, 0.12, 1.36));
    const color = terrainType ? terrainColors[terrainType] : node.visual?.color ?? colorFromScore(mass_score, roi_potential);

    return {
      nodeId: node.id,
      source: "universe_state_snapshot",
      sourceClusterId: cluster.cluster_id,
      label: cluster.label,
      massScore,
      size,
      brightness,
      color,
      recencyScore: round2(recencyScore),
      confidenceScore: round2(confidenceScore),
      interactionScore: round2(interactionScore),
      trailStrength,
      terrainType,
      fallback: false,
      formulaInputs: {
        mass_score,
        roi_potential,
        evidence_count,
        growth_score,
        decline_score,
        terrain_strength,
      },
    };
  });

  return {
    version: STARFIELD_MAPPING_VERSION,
    source: "universe_state_snapshot",
    generatedAt: snapshot.generated_at,
    particleCount: particles.length,
    snapshotMappedCount: particles.filter((particle) => !particle.fallback).length,
    fallbackCount: particles.filter((particle) => particle.fallback).length,
    safety,
    formulas: formulaSummary("universe_state_snapshot"),
    particles,
  };
}

export function mapAtlasNodesToStarfield(nodes: AtlasNode[]): StarfieldMappingResult {
  const particles = nodes.map((node) => mapAtlasNodeToParticle(node, false));
  return {
    version: STARFIELD_MAPPING_VERSION,
    source: "atlas_nodes",
    generatedAt: new Date(0).toISOString(),
    particleCount: particles.length,
    snapshotMappedCount: 0,
    fallbackCount: particles.length,
    safety: {
      redactedSnapshot: true,
      rawPrivateDataIncluded: false,
      writebackAllowed: false,
    },
    formulas: formulaSummary("atlas_nodes"),
    particles,
  };
}

function assertRedactedSnapshot(snapshot: UniverseStateSnapshot): StarfieldMappingResult["safety"] {
  const privacy = snapshot.diagnostics.privacy_status;
  const safe =
    snapshot.source_snapshot.redaction_mode === "public_redacted_read_only_visualization" &&
    privacy.raw_private_data_included === false &&
    privacy.plaintext_secrets_included === false &&
    privacy.local_absolute_paths_included === false &&
    privacy.writeback_allowed === false;
  if (!safe) {
    throw new Error("Unsafe universe state snapshot cannot be mapped into Memory Starfield");
  }
  return {
    redactedSnapshot: true,
    rawPrivateDataIncluded: false,
    writebackAllowed: false,
  };
}

function mapAtlasNodeToParticle(node: AtlasNode, fallback: boolean): StarfieldParticleMapping {
  const mass_score = clamp01((node.metrics?.weight_score ?? node.visual?.size ?? 5) / 13);
  const roi_potential = clamp01(node.metrics?.roi?.leverage_score ?? 0.36);
  const evidence_count = Math.max(1, Math.round((node.visual?.size ?? 6) * 8));
  const growth_score = node.importance === "高" ? 0.68 : node.importance === "中" ? 0.48 : 0.32;
  const decline_score = node.metrics?.roi?.staleness_status === "stale_short_term" ? 0.68 : 0.18;
  const terrainType = atlasTerrainType(node);
  const massScore = round2(1.6 + mass_score * 8 + roi_potential * 4);
  return {
    nodeId: node.id,
    source: "atlas_nodes",
    sourceClusterId: node.visual?.cluster ?? node.id,
    label: node.label,
    massScore,
    size: round2(clamp(node.visual?.size ?? 3.8 + massScore * 0.46, 2.4, 19)),
    brightness: round2(clamp((node.visual?.brightness ?? 0.58) + roi_potential * 0.24, 0.24, 1.18)),
    color: terrainType ? terrainColors[terrainType] : node.visual?.color ?? colorFromScore(mass_score, roi_potential),
    recencyScore: round2(clamp01(0.3 + roi_potential * 0.22)),
    confidenceScore: round2(node.confidence === "high" || node.confidence === "高" ? 0.94 : 0.78),
    interactionScore: round2(clamp01(Math.sqrt(evidence_count) / 13)),
    trailStrength: round2(clamp(0.16 + roi_potential * 0.46 + growth_score * 0.22, 0.12, 1.22)),
    terrainType,
    fallback,
    formulaInputs: {
      mass_score,
      roi_potential,
      evidence_count,
      growth_score,
      decline_score,
      terrain_strength: terrainType ? 0.72 : 0.28,
    },
  };
}

function matchSnapshotCluster(node: AtlasNode, snapshot: UniverseStateSnapshot): string | null {
  const nodeCluster = normalizeCluster(node.visual?.cluster ?? node.id);
  const nodeText = normalizeCluster(`${node.label} ${node.statement ?? ""}`);
  for (const cluster of snapshot.state.dominant_clusters) {
    const aliases = [cluster.cluster_id, cluster.theme_id, cluster.label, ...(clusterAliases[cluster.cluster_id] ?? [])].map(normalizeCluster);
    if (aliases.some((alias) => nodeCluster.includes(alias) || alias.includes(nodeCluster))) return cluster.cluster_id;
    if (aliases.some((alias) => alias.length > 4 && nodeText.includes(alias))) return cluster.cluster_id;
  }
  return null;
}

function buildTerrainByCluster(snapshot: UniverseStateSnapshot) {
  const terrainByCluster = new Map<string, UniverseStateSnapshot["state"]["memory_terrain"][number]>();
  for (const terrain of snapshot.state.memory_terrain) {
    for (const clusterId of terrain.related_cluster_ids) {
      const current = terrainByCluster.get(clusterId);
      if (!current || terrain.strength > current.strength) {
        terrainByCluster.set(clusterId, terrain);
      }
    }
  }
  return terrainByCluster;
}

function growthScoreForCluster(snapshot: UniverseStateSnapshot, clusterId: string): number {
  return clamp01(snapshot.state.rising_clusters.find((cluster) => cluster.cluster_id === clusterId)?.growth_score ?? 0.34);
}

function declineScoreForCluster(snapshot: UniverseStateSnapshot, clusterId: string): number {
  return clamp01(snapshot.state.declining_clusters.find((cluster) => cluster.cluster_id === clusterId)?.decline_score ?? 0.12);
}

function terrainTypeFromSnapshot(value: string | undefined): MemoryTerrainType | null {
  if (value === "fault_line") return "fault-line";
  if (value === "ridge" || value === "shoreline" || value === "valley" || value === "basin") return value;
  return null;
}

function atlasTerrainType(node: AtlasNode): MemoryTerrainType | null {
  const text = `${node.label} ${node.statement ?? ""} ${node.metrics?.roi?.recommended_action ?? ""}`;
  if (/conflict|contradiction|冲突|矛盾/i.test(text)) return "fault-line";
  if (/stale|archive|过时|低价值|重复/i.test(text) || node.metrics?.roi?.staleness_status === "stale_short_term") return "basin";
  if ((node.metrics?.roi?.leverage_score ?? 0) >= 0.72 || node.importance === "高") return "ridge";
  if (/机会|新生|增长|proto|next/i.test(text)) return "shoreline";
  return null;
}

function normalizeCluster(value: string): string {
  return value
    .toLowerCase()
    .replace(/^theme:/, "")
    .replace(/^cluster-/, "")
    .replace(/[^a-z0-9\u4e00-\u9fa5]+/g, "-")
    .replace(/^-|-$/g, "");
}

function formulaSummary(source: StarfieldMappingSource): StarfieldMappingResult["formulas"] {
  return {
    mass: `${source}: mass = mass_score + roi_potential + log2(evidence_count)`,
    brightness: `${source}: brightness = mass_score + roi_potential + confidence`,
    color: `${source}: color = terrain_type else score gradient`,
    trail: `${source}: trail = interaction_density + growth_score + stability`,
  };
}

function colorFromScore(mass: number, roi: number): string {
  if (roi >= 0.72) return "#7ee8d4";
  if (mass >= 0.68) return "#8fd3ff";
  if (roi >= 0.48) return "#ffef9a";
  return "#94a3b8";
}

function clamp01(value: number): number {
  return clamp(value, 0, 1);
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, Number.isFinite(value) ? value : min));
}

function round2(value: number): number {
  return Number(value.toFixed(2));
}
