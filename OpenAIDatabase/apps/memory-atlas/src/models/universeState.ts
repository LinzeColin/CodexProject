import {
  DEFAULT_UNIVERSE_STATE_PARAMETERS,
  blackHoleScore,
  blackHoleSeverity,
  clamp01,
  normCount,
  protoStarScore,
  protoStarStatus,
  recencySignal,
  selectWeatherLabel,
  staleScore,
  staleStatus,
  stalenessSignal,
  type UniverseStateScoreParameters,
  type WeatherLabel,
} from "../utils/universeStateScores.ts";

export type RedactedSourceScope = "all" | "chatgpt" | "codex";

export type RedactedUniverseStateInput = {
  schema_version: "memory_atlas_universe_state_fixture.v1";
  generated_at: string;
  source_scope: RedactedSourceScope;
  time_range: { start: string; end: string };
  redaction_mode: "public_redacted_read_only_visualization";
  source_safety: {
    raw_private_data_included: false;
    plaintext_secrets_included: false;
    local_absolute_paths_included: false;
    writeback_allowed: false;
  };
  clusters: RedactedClusterInput[];
  conflict_zones: RedactedConflictInput[];
  black_hole_candidates: RedactedBlackHoleInput[];
  proto_star_candidates: RedactedProtoStarInput[];
  activity: RedactedActivityInput;
};

export type RedactedClusterInput = {
  cluster_id: string;
  label: string;
  theme_id: string;
  source_scope: RedactedSourceScope;
  mass_score: number;
  evidence_count: number;
  growth_score: number;
  recent_signal_count: number;
  decline_score: number;
  inactive_days: number;
  latest_signal_date: string;
  confidence: number;
  recommended_action: string;
  relation_count: number;
  roi_potential: number;
};

export type RedactedConflictInput = {
  zone_id: string;
  related_cluster_ids: string[];
  conflict_score: number;
  evidence_count: number;
  inspector_summary: string;
};

export type RedactedBlackHoleInput = {
  black_hole_id: string;
  related_cluster_ids: string[];
  time_band: { start: string; end: string };
  evidence_count: number;
  recommended_reduction_action: string;
  signals: {
    interaction_signal: number;
    latest_event_days_ago: number;
    repetition_signal: number;
    roi_penalty_signal: number;
    growth_penalty_signal: number;
  };
};

export type RedactedProtoStarInput = {
  proto_star_id: string;
  related_cluster_ids: string[];
  first_seen_date: string;
  evidence_count: number;
  validation_action: string;
  uncertainty: number;
  signals: {
    recency_growth_signal: number;
    cross_signal: number;
    capability_relation_signal: number;
    roi_potential_signal: number;
  };
};

export type RedactedActivityInput = {
  recent_window_days: number;
  activity_density: number;
  dominant_lane_ids: string[];
  recent_event_count: number;
};

export type UniverseStateSnapshot = {
  schema_version: "universe_state_snapshot.v1";
  generated_at: string;
  source_snapshot: {
    schema_version: string;
    generated_at: string;
    source_scope: RedactedSourceScope;
    time_range: { start: string; end: string };
    redaction_mode: "public_redacted_read_only_visualization";
  };
  state: {
    memory_weather: MemoryWeather;
    dominant_clusters: DominantCluster[];
    rising_clusters: RisingCluster[];
    declining_clusters: DecliningCluster[];
    conflict_zones: ConflictZone[];
    black_holes: BlackHoleState[];
    proto_stars: ProtoStarState[];
    stale_orbits: StaleOrbit[];
    memory_terrain: MemoryTerrain[];
    river_pulse: RiverPulse;
    mini_starfield: MiniStarfield;
    recommended_next_actions: RecommendedNextAction[];
  };
  consumer_map: Record<string, string[]>;
  diagnostics: {
    lifecycle_state: "draft_generated";
    privacy_status: {
      raw_private_data_included: false;
      plaintext_secrets_included: false;
      local_absolute_paths_included: false;
      writeback_allowed: false;
    };
    parameter_source: UniverseStateScoreParameters["parameterSource"];
    formula_version: UniverseStateScoreParameters["schemaVersion"];
    missing_inputs: string[];
    score_weight_sums: Array<{ name: string; sum: number }>;
  };
};

export type MemoryWeather = {
  label: WeatherLabel;
  summary: string;
  drivers: string[];
  confidence: number;
  coverage: {
    source_scope: RedactedSourceScope;
    time_range: { start: string; end: string };
  };
};

export type DominantCluster = {
  cluster_id: string;
  label: string;
  theme_id: string;
  mass_score: number;
  evidence_count: number;
  source_scope: RedactedSourceScope;
  recommended_action: string;
};

export type RisingCluster = {
  cluster_id: string;
  growth_score: number;
  recent_signal_count: number;
  related_proto_star_ids: string[];
  explanation: string;
};

export type DecliningCluster = {
  cluster_id: string;
  decline_score: number;
  inactive_days: number;
  stale_orbit_id: string;
  recommended_action: string;
};

export type ConflictZone = {
  zone_id: string;
  related_cluster_ids: string[];
  conflict_score: number;
  evidence_count: number;
  inspector_summary: string;
};

export type BlackHoleState = {
  black_hole_id: string;
  score: number;
  severity: "watch" | "warning" | "critical";
  related_cluster_ids: string[];
  time_band: { start: string; end: string };
  recommended_reduction_action: string;
  evidence_count: number;
};

export type ProtoStarState = {
  proto_star_id: string;
  score: number;
  status: "weak_signal" | "candidate" | "proto_star";
  uncertainty: number;
  related_cluster_ids: string[];
  first_seen_date: string;
  validation_action: string;
  evidence_count: number;
};

export type StaleOrbit = {
  stale_orbit_id: string;
  cluster_id: string;
  stale_score: number;
  status: "current" | "watch" | "review";
  inactive_days: number;
  recommended_action: string;
};

export type MemoryTerrain = {
  terrain_id: string;
  terrain_type: "ridge" | "valley" | "basin" | "fault_line" | "shoreline";
  related_cluster_ids: string[];
  strength: number;
  presentation_hint: string;
  analysis_explanation: string;
};

export type RiverPulse = {
  recent_window_days: number;
  activity_density: number;
  dominant_lane_ids: string[];
  black_hole_band_ids: string[];
  proto_star_marker_ids: string[];
  summary: string;
};

export type MiniStarfield = {
  preview_cluster_ids: string[];
  black_hole_ids: string[];
  proto_star_ids: string[];
  density_hint: number;
  target_view: "memory_starfield";
};

export type RecommendedNextAction = {
  action_id: string;
  action_type: "continue" | "review" | "consolidate" | "explore" | "defer";
  label: string;
  reason: string;
  linked_state_ids: string[];
  proposal_only: true;
};

export function adaptUniverseStateFixture(input: RedactedUniverseStateInput) {
  assertSafeSource(input);
  return {
    clusters: input.clusters.map((cluster) => ({
      ...cluster,
      mass_score: clamp01(cluster.mass_score),
      growth_score: clamp01(cluster.growth_score),
      decline_score: clamp01(cluster.decline_score),
      confidence: clamp01(cluster.confidence),
      roi_potential: clamp01(cluster.roi_potential),
    })),
    conflictZones: input.conflict_zones.map((zone) => ({
      ...zone,
      conflict_score: clamp01(zone.conflict_score),
    })),
    blackHoleCandidates: input.black_hole_candidates,
    protoStarCandidates: input.proto_star_candidates,
    activity: {
      ...input.activity,
      activity_density: clamp01(input.activity.activity_density),
    },
  };
}

export function generateUniverseStateSnapshot(
  input: RedactedUniverseStateInput,
  parameters: UniverseStateScoreParameters = DEFAULT_UNIVERSE_STATE_PARAMETERS,
): UniverseStateSnapshot {
  const adapted = adaptUniverseStateFixture(input);
  const dominantClusters = adapted.clusters
    .filter((cluster) => cluster.mass_score >= 0.62)
    .sort((left, right) => right.mass_score - left.mass_score)
    .slice(0, 3)
    .map<DominantCluster>((cluster) => ({
      cluster_id: cluster.cluster_id,
      label: cluster.label,
      theme_id: cluster.theme_id,
      mass_score: round4(cluster.mass_score),
      evidence_count: cluster.evidence_count,
      source_scope: cluster.source_scope,
      recommended_action: cluster.recommended_action,
    }));

  const protoStars = adapted.protoStarCandidates.map<ProtoStarState>((candidate) => {
    const score = protoStarScore(
      {
        recencyGrowthSignal: candidate.signals.recency_growth_signal,
        crossSignal: candidate.signals.cross_signal,
        capabilityRelationSignal: candidate.signals.capability_relation_signal,
        roiPotentialSignal: candidate.signals.roi_potential_signal,
        uncertaintyPenalty: candidate.uncertainty,
      },
      parameters,
    );
    return {
      proto_star_id: candidate.proto_star_id,
      score,
      status: protoStarStatus(score, parameters),
      uncertainty: round4(clamp01(candidate.uncertainty)),
      related_cluster_ids: candidate.related_cluster_ids,
      first_seen_date: candidate.first_seen_date,
      validation_action: candidate.validation_action,
      evidence_count: candidate.evidence_count,
    };
  });

  const staleOrbits = adapted.clusters
    .filter((cluster) => cluster.inactive_days >= 30 || cluster.decline_score >= 0.45)
    .map<StaleOrbit>((cluster) => {
      const score = staleScore(
        {
          inactiveDaysSignal: stalenessSignal(cluster.inactive_days, 180),
          lowRecentUsageSignal: 1 - clamp01(cluster.growth_score),
          confidenceDecaySignal: 1 - clamp01(cluster.confidence),
        },
        parameters,
      );
      return {
        stale_orbit_id: `stale-${cluster.cluster_id}`,
        cluster_id: cluster.cluster_id,
        stale_score: score,
        status: staleStatus(score, parameters),
        inactive_days: cluster.inactive_days,
        recommended_action: cluster.decline_score >= 0.62 ? "review_or_archive" : "refresh_or_defer",
      };
    });

  const risingClusters = adapted.clusters
    .filter((cluster) => cluster.growth_score >= 0.55)
    .sort((left, right) => right.growth_score - left.growth_score)
    .map<RisingCluster>((cluster) => ({
      cluster_id: cluster.cluster_id,
      growth_score: round4(cluster.growth_score),
      recent_signal_count: cluster.recent_signal_count,
      related_proto_star_ids: protoStars
        .filter((protoStar) => protoStar.related_cluster_ids.includes(cluster.cluster_id))
        .map((protoStar) => protoStar.proto_star_id),
      explanation: `${cluster.label} has recent redacted growth signals and ${cluster.evidence_count} evidence items.`,
    }));

  const decliningClusters = adapted.clusters
    .filter((cluster) => cluster.decline_score >= 0.45)
    .sort((left, right) => right.decline_score - left.decline_score)
    .map<DecliningCluster>((cluster) => ({
      cluster_id: cluster.cluster_id,
      decline_score: round4(cluster.decline_score),
      inactive_days: cluster.inactive_days,
      stale_orbit_id: `stale-${cluster.cluster_id}`,
      recommended_action: cluster.decline_score >= 0.62 ? "review_for_archive" : "refresh_or_lower_priority",
    }));

  const conflictZones = adapted.conflictZones.map<ConflictZone>((zone) => ({
    zone_id: zone.zone_id,
    related_cluster_ids: zone.related_cluster_ids,
    conflict_score: round4(zone.conflict_score),
    evidence_count: zone.evidence_count,
    inspector_summary: zone.inspector_summary,
  }));

  const blackHoles = adapted.blackHoleCandidates.map<BlackHoleState>((candidate) => {
    const score = blackHoleScore(
      {
        interactionSignal: candidate.signals.interaction_signal,
        recencySignal: recencySignal(candidate.signals.latest_event_days_ago, 45),
        repetitionSignal: candidate.signals.repetition_signal,
        roiPenaltySignal: candidate.signals.roi_penalty_signal,
        growthPenaltySignal: candidate.signals.growth_penalty_signal,
      },
      parameters,
    );
    return {
      black_hole_id: candidate.black_hole_id,
      score,
      severity: blackHoleSeverity(score, parameters),
      related_cluster_ids: candidate.related_cluster_ids,
      time_band: candidate.time_band,
      recommended_reduction_action: candidate.recommended_reduction_action,
      evidence_count: candidate.evidence_count,
    };
  });

  const memoryTerrain = buildMemoryTerrain(dominantClusters, conflictZones, blackHoles, protoStars, staleOrbits);
  const weather = buildMemoryWeather(input, {
    blackHoles,
    protoStars,
    staleOrbits,
    conflictZones,
    parameters,
  });
  const riverPulse: RiverPulse = {
    recent_window_days: adapted.activity.recent_window_days,
    activity_density: round4(adapted.activity.activity_density),
    dominant_lane_ids: adapted.activity.dominant_lane_ids,
    black_hole_band_ids: blackHoles.map((blackHole) => blackHole.black_hole_id),
    proto_star_marker_ids: protoStars.map((protoStar) => protoStar.proto_star_id),
    summary: `${adapted.activity.recent_event_count} redacted events in the recent window; ${protoStars.length} opportunities and ${blackHoles.length} risk bands are visible.`,
  };

  const miniStarfield: MiniStarfield = {
    preview_cluster_ids: dominantClusters.map((cluster) => cluster.cluster_id),
    black_hole_ids: blackHoles.map((blackHole) => blackHole.black_hole_id),
    proto_star_ids: protoStars.map((protoStar) => protoStar.proto_star_id),
    density_hint: round4(adapted.activity.activity_density),
    target_view: "memory_starfield",
  };

  return {
    schema_version: "universe_state_snapshot.v1",
    generated_at: input.generated_at,
    source_snapshot: {
      schema_version: input.schema_version,
      generated_at: input.generated_at,
      source_scope: input.source_scope,
      time_range: input.time_range,
      redaction_mode: input.redaction_mode,
    },
    state: {
      memory_weather: weather,
      dominant_clusters: dominantClusters,
      rising_clusters: risingClusters,
      declining_clusters: decliningClusters,
      conflict_zones: conflictZones,
      black_holes: blackHoles,
      proto_stars: protoStars,
      stale_orbits: staleOrbits,
      memory_terrain: memoryTerrain,
      river_pulse: riverPulse,
      mini_starfield: miniStarfield,
      recommended_next_actions: buildNextActions(blackHoles, protoStars, staleOrbits, dominantClusters),
    },
    consumer_map: {
      memory_overview: ["memory_weather", "dominant_clusters", "proto_stars", "black_holes", "river_pulse", "recommended_next_actions"],
      memory_starfield: ["dominant_clusters", "rising_clusters", "declining_clusters", "black_holes", "proto_stars", "stale_orbits", "memory_terrain"],
      memory_river: ["river_pulse", "dominant_clusters", "black_holes", "proto_stars", "conflict_zones", "stale_orbits"],
      inspector: ["memory_weather", "conflict_zones", "black_holes", "proto_stars", "stale_orbits", "memory_terrain"],
      roi_dashboard: ["dominant_clusters", "rising_clusters", "declining_clusters", "black_holes", "recommended_next_actions"],
    },
    diagnostics: {
      lifecycle_state: "draft_generated",
      privacy_status: input.source_safety,
      parameter_source: parameters.parameterSource,
      formula_version: parameters.schemaVersion,
      missing_inputs: [],
      score_weight_sums: [
        { name: "black_hole", sum: round4(Object.values(parameters.scores.blackHole).reduce((total, value) => total + value, 0)) },
        { name: "proto_star", sum: round4(Object.values(parameters.scores.protoStar).reduce((total, value) => total + value, 0)) },
        { name: "stale", sum: round4(Object.values(parameters.scores.stale).reduce((total, value) => total + value, 0)) },
      ],
    },
  };
}

function assertSafeSource(input: RedactedUniverseStateInput) {
  const safety = input.source_safety;
  if (
    safety.raw_private_data_included ||
    safety.plaintext_secrets_included ||
    safety.local_absolute_paths_included ||
    safety.writeback_allowed
  ) {
    throw new Error("Universe State generator only accepts redacted, read-only fixture inputs");
  }
}

function buildMemoryWeather(
  input: RedactedUniverseStateInput,
  state: {
    blackHoles: BlackHoleState[];
    protoStars: ProtoStarState[];
    staleOrbits: StaleOrbit[];
    conflictZones: ConflictZone[];
    parameters: UniverseStateScoreParameters;
  },
): MemoryWeather {
  const maxBlackHoleScore = maxScore(state.blackHoles.map((blackHole) => blackHole.score));
  const maxProtoStarScore = maxScore(state.protoStars.map((protoStar) => protoStar.score));
  const maxStaleScore = maxScore(state.staleOrbits.map((stale) => stale.stale_score));
  const maxConflictScore = maxScore(state.conflictZones.map((zone) => zone.conflict_score));
  const label = selectWeatherLabel({ maxBlackHoleScore, maxProtoStarScore, maxStaleScore, maxConflictScore }, state.parameters);
  const drivers = [
    ...state.blackHoles.filter((item) => item.score === maxBlackHoleScore).map((item) => item.black_hole_id),
    ...state.protoStars.filter((item) => item.score === maxProtoStarScore).map((item) => item.proto_star_id),
    ...state.conflictZones.filter((item) => item.conflict_score === maxConflictScore).map((item) => item.zone_id),
  ].slice(0, 4);

  return {
    label,
    summary: weatherSummary(label),
    drivers,
    confidence: round4(clamp01((maxBlackHoleScore + maxProtoStarScore + maxStaleScore + maxConflictScore) / 4 + 0.18)),
    coverage: {
      source_scope: input.source_scope,
      time_range: input.time_range,
    },
  };
}

function buildMemoryTerrain(
  dominantClusters: DominantCluster[],
  conflictZones: ConflictZone[],
  blackHoles: BlackHoleState[],
  protoStars: ProtoStarState[],
  staleOrbits: StaleOrbit[],
): MemoryTerrain[] {
  const terrain: MemoryTerrain[] = [];
  for (const cluster of dominantClusters) {
    terrain.push({
      terrain_id: `terrain-ridge-${cluster.cluster_id}`,
      terrain_type: "ridge",
      related_cluster_ids: [cluster.cluster_id],
      strength: cluster.mass_score,
      presentation_hint: "stable ridge",
      analysis_explanation: `${cluster.label} has dominant mass and repeated redacted evidence.`,
    });
  }
  for (const conflict of conflictZones) {
    terrain.push({
      terrain_id: `terrain-fault-${conflict.zone_id}`,
      terrain_type: "fault_line",
      related_cluster_ids: conflict.related_cluster_ids,
      strength: conflict.conflict_score,
      presentation_hint: "subtle fault line",
      analysis_explanation: conflict.inspector_summary,
    });
  }
  for (const blackHole of blackHoles) {
    terrain.push({
      terrain_id: `terrain-basin-${blackHole.black_hole_id}`,
      terrain_type: "basin",
      related_cluster_ids: blackHole.related_cluster_ids,
      strength: blackHole.score,
      presentation_hint: "dark basin",
      analysis_explanation: "Black Hole score marks a repeated low-value loop or scope sink.",
    });
  }
  for (const protoStar of protoStars) {
    terrain.push({
      terrain_id: `terrain-shoreline-${protoStar.proto_star_id}`,
      terrain_type: "shoreline",
      related_cluster_ids: protoStar.related_cluster_ids,
      strength: protoStar.score,
      presentation_hint: "bright shoreline",
      analysis_explanation: "Proto-Star score marks an emerging opportunity near mature clusters.",
    });
  }
  for (const stale of staleOrbits.filter((item) => item.status === "review")) {
    terrain.push({
      terrain_id: `terrain-valley-${stale.stale_orbit_id}`,
      terrain_type: "valley",
      related_cluster_ids: [stale.cluster_id],
      strength: stale.stale_score,
      presentation_hint: "low valley",
      analysis_explanation: "Stale score indicates an inactive or decaying cluster that needs review.",
    });
  }
  return terrain;
}

function buildNextActions(
  blackHoles: BlackHoleState[],
  protoStars: ProtoStarState[],
  staleOrbits: StaleOrbit[],
  dominantClusters: DominantCluster[],
): RecommendedNextAction[] {
  const actions: RecommendedNextAction[] = [];
  const topBlackHole = [...blackHoles].sort((left, right) => right.score - left.score)[0];
  if (topBlackHole) {
    actions.push({
      action_id: `action-reduce-${topBlackHole.black_hole_id}`,
      action_type: "review",
      label: "Review top Black Hole risk",
      reason: topBlackHole.recommended_reduction_action,
      linked_state_ids: [topBlackHole.black_hole_id],
      proposal_only: true,
    });
  }
  const topProtoStar = [...protoStars].sort((left, right) => right.score - left.score)[0];
  if (topProtoStar) {
    actions.push({
      action_id: `action-explore-${topProtoStar.proto_star_id}`,
      action_type: "explore",
      label: "Validate strongest Proto-Star",
      reason: topProtoStar.validation_action,
      linked_state_ids: [topProtoStar.proto_star_id],
      proposal_only: true,
    });
  }
  const topStale = [...staleOrbits].sort((left, right) => right.stale_score - left.stale_score)[0];
  if (topStale) {
    actions.push({
      action_id: `action-refresh-${topStale.stale_orbit_id}`,
      action_type: "defer",
      label: "Refresh or lower stale orbit",
      reason: topStale.recommended_action,
      linked_state_ids: [topStale.stale_orbit_id],
      proposal_only: true,
    });
  }
  const topDominant = dominantClusters[0];
  if (topDominant) {
    actions.push({
      action_id: `action-continue-${topDominant.cluster_id}`,
      action_type: "continue",
      label: "Continue strongest dominant cluster",
      reason: topDominant.recommended_action,
      linked_state_ids: [topDominant.cluster_id],
      proposal_only: true,
    });
  }
  return actions;
}

function weatherSummary(label: WeatherLabel): string {
  switch (label) {
    case "storm_conflict":
      return "Conflict or Black Hole risk is high enough to require review before expansion.";
    case "black_hole_warning":
      return "A repeated low-value loop is visible and should be reduced or bounded.";
    case "proto_star_cloud":
      return "A new opportunity is forming and should be validated with bounded evidence.";
    case "cold_stale":
      return "Stale orbits dominate; review inactive clusters before adding complexity.";
    case "mixed_front":
      return "Opportunity and risk are both elevated; continue selectively and reduce drag.";
    case "clear":
      return "The current memory state is coherent and actionable.";
  }
}

function maxScore(values: number[]): number {
  return values.length ? Math.max(...values) : 0;
}

function round4(value: number): number {
  return Math.round(value * 10000) / 10000;
}

export const universeStateFormulaHelpers = {
  clamp01,
  normCount,
  recencySignal,
  stalenessSignal,
};
