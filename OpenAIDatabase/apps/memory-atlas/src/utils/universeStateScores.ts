export type WeightGroup = Record<string, number>;

export type UniverseStateScoreParameters = {
  schemaVersion: "universe_state_params.v1";
  parameterSource: "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml";
  scores: {
    blackHole: {
      interactionWeight: number;
      recencyWeight: number;
      repetitionWeight: number;
      roiPenaltyWeight: number;
      growthPenaltyWeight: number;
    };
    protoStar: {
      recencyGrowthWeight: number;
      crossSignalWeight: number;
      capabilityRelationWeight: number;
      roiPotentialWeight: number;
      uncertaintyPenaltyWeight: number;
    };
    stale: {
      inactiveDaysWeight: number;
      lowRecentUsageWeight: number;
      confidenceDecayWeight: number;
    };
  };
  weather: {
    stormConflictThreshold: number;
    blackHoleWarningThreshold: number;
    protoStarNoticeThreshold: number;
  };
  thresholds: {
    blackHole: {
      watchBelow: number;
      warningFrom: number;
      criticalFrom: number;
    };
    protoStar: {
      weakBelow: number;
      candidateFrom: number;
      visibleFrom: number;
    };
    stale: {
      watchFrom: number;
      reviewFrom: number;
    };
  };
  diagnostics: {
    missingPositiveSignalFallback: number;
    missingUncertaintyFallback: number;
    requireDriverSignalIds: boolean;
  };
};

export type BlackHoleSignals = {
  interactionSignal: number;
  recencySignal: number;
  repetitionSignal: number;
  roiPenaltySignal: number;
  growthPenaltySignal: number;
};

export type ProtoStarSignals = {
  recencyGrowthSignal: number;
  crossSignal: number;
  capabilityRelationSignal: number;
  roiPotentialSignal: number;
  uncertaintyPenalty: number;
};

export type StaleSignals = {
  inactiveDaysSignal: number;
  lowRecentUsageSignal: number;
  confidenceDecaySignal: number;
};

export type WeatherInput = {
  maxBlackHoleScore: number;
  maxProtoStarScore: number;
  maxStaleScore: number;
  maxConflictScore: number;
};

export type WeatherLabel =
  | "clear"
  | "storm_conflict"
  | "black_hole_warning"
  | "proto_star_cloud"
  | "cold_stale"
  | "mixed_front";

export const DEFAULT_UNIVERSE_STATE_PARAMETERS: UniverseStateScoreParameters = {
  schemaVersion: "universe_state_params.v1",
  parameterSource: "OpenAIDatabase/config/visualization/model_parameters.universe_state.yaml",
  scores: {
    blackHole: {
      interactionWeight: 0.28,
      recencyWeight: 0.22,
      repetitionWeight: 0.25,
      roiPenaltyWeight: 0.15,
      growthPenaltyWeight: 0.1,
    },
    protoStar: {
      recencyGrowthWeight: 0.3,
      crossSignalWeight: 0.2,
      capabilityRelationWeight: 0.25,
      roiPotentialWeight: 0.2,
      uncertaintyPenaltyWeight: 0.05,
    },
    stale: {
      inactiveDaysWeight: 0.55,
      lowRecentUsageWeight: 0.25,
      confidenceDecayWeight: 0.2,
    },
  },
  weather: {
    stormConflictThreshold: 0.72,
    blackHoleWarningThreshold: 0.65,
    protoStarNoticeThreshold: 0.58,
  },
  thresholds: {
    blackHole: {
      watchBelow: 0.45,
      warningFrom: 0.45,
      criticalFrom: 0.65,
    },
    protoStar: {
      weakBelow: 0.45,
      candidateFrom: 0.45,
      visibleFrom: 0.58,
    },
    stale: {
      watchFrom: 0.45,
      reviewFrom: 0.65,
    },
  },
  diagnostics: {
    missingPositiveSignalFallback: 0,
    missingUncertaintyFallback: 0.5,
    requireDriverSignalIds: true,
  },
};

export function clamp01(value: number): number {
  if (!Number.isFinite(value)) return 0;
  return Math.min(1, Math.max(0, value));
}

export function safeDiv(numerator: number, denominator: number): number {
  return denominator <= 0 ? 0 : numerator / denominator;
}

export function normCount(value: number, p95: number): number {
  return clamp01(safeDiv(value, Math.max(1, p95)));
}

export function recencySignal(days: number, halfLifeDays: number): number {
  return clamp01(0.5 ** safeDiv(Math.max(0, days), Math.max(1, halfLifeDays)));
}

export function stalenessSignal(days: number, thresholdDays: number): number {
  return clamp01(safeDiv(Math.max(0, days), Math.max(1, thresholdDays)));
}

export function blackHoleScore(
  signals: BlackHoleSignals,
  parameters: UniverseStateScoreParameters = DEFAULT_UNIVERSE_STATE_PARAMETERS,
): number {
  const weights = parameters.scores.blackHole;
  return roundScore(
    clamp01(
      clamp01(signals.interactionSignal) * weights.interactionWeight +
        clamp01(signals.recencySignal) * weights.recencyWeight +
        clamp01(signals.repetitionSignal) * weights.repetitionWeight +
        clamp01(signals.roiPenaltySignal) * weights.roiPenaltyWeight +
        clamp01(signals.growthPenaltySignal) * weights.growthPenaltyWeight,
    ),
  );
}

export function protoStarScore(
  signals: ProtoStarSignals,
  parameters: UniverseStateScoreParameters = DEFAULT_UNIVERSE_STATE_PARAMETERS,
): number {
  const weights = parameters.scores.protoStar;
  return roundScore(
    clamp01(
      clamp01(signals.recencyGrowthSignal) * weights.recencyGrowthWeight +
        clamp01(signals.crossSignal) * weights.crossSignalWeight +
        clamp01(signals.capabilityRelationSignal) * weights.capabilityRelationWeight +
        clamp01(signals.roiPotentialSignal) * weights.roiPotentialWeight -
        clamp01(signals.uncertaintyPenalty) * weights.uncertaintyPenaltyWeight,
    ),
  );
}

export function staleScore(
  signals: StaleSignals,
  parameters: UniverseStateScoreParameters = DEFAULT_UNIVERSE_STATE_PARAMETERS,
): number {
  const weights = parameters.scores.stale;
  return roundScore(
    clamp01(
      clamp01(signals.inactiveDaysSignal) * weights.inactiveDaysWeight +
        clamp01(signals.lowRecentUsageSignal) * weights.lowRecentUsageWeight +
        clamp01(signals.confidenceDecaySignal) * weights.confidenceDecayWeight,
    ),
  );
}

export function blackHoleSeverity(
  score: number,
  parameters: UniverseStateScoreParameters = DEFAULT_UNIVERSE_STATE_PARAMETERS,
): "watch" | "warning" | "critical" {
  if (score >= parameters.thresholds.blackHole.criticalFrom) return "critical";
  if (score >= parameters.thresholds.blackHole.warningFrom) return "warning";
  return "watch";
}

export function protoStarStatus(
  score: number,
  parameters: UniverseStateScoreParameters = DEFAULT_UNIVERSE_STATE_PARAMETERS,
): "weak_signal" | "candidate" | "proto_star" {
  if (score >= parameters.thresholds.protoStar.visibleFrom) return "proto_star";
  if (score >= parameters.thresholds.protoStar.candidateFrom) return "candidate";
  return "weak_signal";
}

export function staleStatus(
  score: number,
  parameters: UniverseStateScoreParameters = DEFAULT_UNIVERSE_STATE_PARAMETERS,
): "current" | "watch" | "review" {
  if (score >= parameters.thresholds.stale.reviewFrom) return "review";
  if (score >= parameters.thresholds.stale.watchFrom) return "watch";
  return "current";
}

export function selectWeatherLabel(
  input: WeatherInput,
  parameters: UniverseStateScoreParameters = DEFAULT_UNIVERSE_STATE_PARAMETERS,
): WeatherLabel {
  if (input.maxConflictScore >= parameters.weather.stormConflictThreshold) return "storm_conflict";
  if (input.maxBlackHoleScore >= parameters.weather.stormConflictThreshold) return "storm_conflict";
  if (input.maxBlackHoleScore >= parameters.weather.blackHoleWarningThreshold) return "black_hole_warning";
  if (
    input.maxProtoStarScore >= parameters.weather.protoStarNoticeThreshold &&
    input.maxBlackHoleScore >= parameters.thresholds.blackHole.warningFrom
  ) {
    return "mixed_front";
  }
  if (input.maxProtoStarScore >= parameters.weather.protoStarNoticeThreshold) return "proto_star_cloud";
  if (input.maxStaleScore >= parameters.thresholds.stale.reviewFrom) return "cold_stale";
  return "clear";
}

export function assertWeightGroups(parameters: UniverseStateScoreParameters = DEFAULT_UNIVERSE_STATE_PARAMETERS) {
  const groups: Array<[string, WeightGroup]> = [
    ["black_hole", parameters.scores.blackHole],
    ["proto_star", parameters.scores.protoStar],
    ["stale", parameters.scores.stale],
  ];
  return groups.map(([name, group]) => ({
    name,
    sum: roundScore(Object.values(group).reduce((total, value) => total + value, 0)),
  }));
}

function roundScore(value: number): number {
  return Math.round(value * 10000) / 10000;
}
