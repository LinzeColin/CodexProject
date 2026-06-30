import memoryStarfieldParamsYaml from "../../../../config/visualization/model_parameters.memory_starfield.yaml?raw";

export type StarfieldQuality = "high" | "mid" | "low";
export type MemoryTerrainType = "ridge" | "valley" | "basin" | "fault-line" | "shoreline";

export interface StarfieldQualitySetting {
  maxNodes: number;
  ambientParticles: number;
  haloParticles: number;
  flowTrailCount: number;
}

export interface MemoryStarfieldParameters {
  schemaVersion: string;
  productTarget: string;
  parameterSource: string;
  layout: {
    seed: number;
    lodTiers: {
      coreMaxClusters: number;
      midMaxClusters: number;
      outerMaxClusters: number;
      dustMinWeight: number;
    };
  };
  forces: {
    gravityConstant: number;
    clusterRepulsion: number;
    orbitalStability: number;
    curlNoiseFrequency: number;
    curlNoiseAmplitude: number;
    curlNoiseOctaves: number;
  };
  visual: {
    bloomStrength: number;
    trailFade: number;
    particleBaseSize: number;
    nebulaOpacity: number;
    blackHoleDarkness: number;
    protoStarEnergy: number;
  };
  mapping: {
    importanceToMassScale: number;
    recencyHalfLifeDays: number;
    interactionDensityScale: number;
    confidenceNoiseAmplitude: number;
    clusterMass: {
      tierCore: number;
      tierMid: number;
      tierOuter: number;
      kindTheme: number;
      kindDecision: number;
      kindProject: number;
      roiMultiplier: number;
      importanceHigh: number;
      importanceMedium: number;
      importanceLow: number;
      recencyMultiplier: number;
      usageSqrtMultiplier: number;
    };
    particleAttributes: {
      baseSize: number;
      massSizeScale: number;
      recencyBrightnessBoost: number;
      recencySizeBoost: number;
      confidenceHigh: number;
      confidenceMedium: number;
      confidenceLow: number;
      confidenceColorDesaturation: number;
      interactionTrailScale: number;
    };
    terrain: {
      ridgeRoiThreshold: number;
      valleyRecentThreshold: number;
      basinStaleStatus: string;
      faultConflictPattern: string;
      shorelineRecentMin: number;
    };
  };
  performance: {
    desktopTargetFps: number;
    desktopMinFps: number;
    particleCountHigh: number;
    particleCountMid: number;
    particleCountLow: number;
  };
  qualitySettings: Record<StarfieldQuality, StarfieldQualitySetting>;
}

export const MEMORY_STARFIELD_PARAMETER_SOURCE = "config/visualization/model_parameters.memory_starfield.yaml";
export const memoryStarfieldParameterYaml = memoryStarfieldParamsYaml;

const yamlScalars = parseYamlScalarPaths(memoryStarfieldParamsYaml);

export const MEMORY_STARFIELD_PARAMS: MemoryStarfieldParameters = {
  schemaVersion: stringAt("schema_version", "memory_starfield_params.v1"),
  productTarget: stringAt("product_target", "Memory Atlas v1.1.5"),
  parameterSource: MEMORY_STARFIELD_PARAMETER_SOURCE,
  layout: {
    seed: numberAt("layout.seed", 20260628),
    lodTiers: {
      coreMaxClusters: numberAt("layout.lod_tiers.core_max_clusters", 24),
      midMaxClusters: numberAt("layout.lod_tiers.mid_max_clusters", 48),
      outerMaxClusters: numberAt("layout.lod_tiers.outer_max_clusters", 96),
      dustMinWeight: numberAt("layout.lod_tiers.dust_min_weight", 0.05),
    },
  },
  forces: {
    gravityConstant: numberAt("forces.gravity_constant", 0.82),
    clusterRepulsion: numberAt("forces.cluster_repulsion", 0.18),
    orbitalStability: numberAt("forces.orbital_stability", 0.64),
    curlNoiseFrequency: numberAt("forces.curl_noise_frequency", 0.42),
    curlNoiseAmplitude: numberAt("forces.curl_noise_amplitude", 0.76),
    curlNoiseOctaves: numberAt("forces.curl_noise_octaves", 3),
  },
  visual: {
    bloomStrength: numberAt("visual.bloom_strength", 1.2),
    trailFade: numberAt("visual.trail_fade", 0.92),
    particleBaseSize: numberAt("visual.particle_base_size", 1),
    nebulaOpacity: numberAt("visual.nebula_opacity", 0.72),
    blackHoleDarkness: numberAt("visual.black_hole_darkness", 0.88),
    protoStarEnergy: numberAt("visual.proto_star_energy", 1.35),
  },
  mapping: {
    importanceToMassScale: numberAt("mapping.importance_to_mass_scale", 1),
    recencyHalfLifeDays: numberAt("mapping.recency_half_life_days", 45),
    interactionDensityScale: numberAt("mapping.interaction_density_scale", 0.8),
    confidenceNoiseAmplitude: numberAt("mapping.confidence_noise_amplitude", 0.35),
    clusterMass: {
      tierCore: numberAt("mapping.cluster_mass.tier_core", 8),
      tierMid: numberAt("mapping.cluster_mass.tier_mid", 4.8),
      tierOuter: numberAt("mapping.cluster_mass.tier_outer", 1.6),
      kindTheme: numberAt("mapping.cluster_mass.kind_theme", 6),
      kindDecision: numberAt("mapping.cluster_mass.kind_decision", 4),
      kindProject: numberAt("mapping.cluster_mass.kind_project", 3),
      roiMultiplier: numberAt("mapping.cluster_mass.roi_multiplier", 7),
      importanceHigh: numberAt("mapping.cluster_mass.importance_high", 4),
      importanceMedium: numberAt("mapping.cluster_mass.importance_medium", 2),
      importanceLow: numberAt("mapping.cluster_mass.importance_low", 0.5),
      recencyMultiplier: numberAt("mapping.cluster_mass.recency_multiplier", 2.4),
      usageSqrtMultiplier: numberAt("mapping.cluster_mass.usage_sqrt_multiplier", 1),
    },
    particleAttributes: {
      baseSize: numberAt("mapping.particle_attributes.base_size", 6),
      massSizeScale: numberAt("mapping.particle_attributes.mass_size_scale", 0.42),
      recencyBrightnessBoost: numberAt("mapping.particle_attributes.recency_brightness_boost", 0.18),
      recencySizeBoost: numberAt("mapping.particle_attributes.recency_size_boost", 1.2),
      confidenceHigh: numberAt("mapping.particle_attributes.confidence_high", 1),
      confidenceMedium: numberAt("mapping.particle_attributes.confidence_medium", 0.82),
      confidenceLow: numberAt("mapping.particle_attributes.confidence_low", 0.64),
      confidenceColorDesaturation: numberAt("mapping.particle_attributes.confidence_color_desaturation", 0.34),
      interactionTrailScale: numberAt("mapping.particle_attributes.interaction_trail_scale", 0.045),
    },
    terrain: {
      ridgeRoiThreshold: numberAt("mapping.terrain.ridge_roi_threshold", 0.72),
      valleyRecentThreshold: numberAt("mapping.terrain.valley_recent_threshold", 0.18),
      basinStaleStatus: stringAt("mapping.terrain.basin_stale_status", "stale_short_term"),
      faultConflictPattern: stringAt("mapping.terrain.fault_conflict_pattern", "conflict|contradiction|冲突|矛盾"),
      shorelineRecentMin: numberAt("mapping.terrain.shoreline_recent_min", 0.42),
    },
  },
  performance: {
    desktopTargetFps: numberAt("performance.desktop_target_fps", 60),
    desktopMinFps: numberAt("performance.desktop_min_fps", 45),
    particleCountHigh: numberAt("performance.particle_count_high", 60000),
    particleCountMid: numberAt("performance.particle_count_mid", 25000),
    particleCountLow: numberAt("performance.particle_count_low", 8000),
  },
  qualitySettings: {
    high: qualitySettingAt("high", { maxNodes: 900, ambientParticles: 11200, haloParticles: 2600, flowTrailCount: 190 }),
    mid: qualitySettingAt("mid", { maxNodes: 720, ambientParticles: 9400, haloParticles: 2100, flowTrailCount: 150 }),
    low: qualitySettingAt("low", { maxNodes: 420, ambientParticles: 5200, haloParticles: 1200, flowTrailCount: 84 }),
  },
};

function qualitySettingAt(quality: StarfieldQuality, fallback: StarfieldQualitySetting): StarfieldQualitySetting {
  const basePath = `performance.quality_settings.${quality}`;
  return {
    maxNodes: numberAt(`${basePath}.max_nodes`, fallback.maxNodes),
    ambientParticles: numberAt(`${basePath}.ambient_particles`, fallback.ambientParticles),
    haloParticles: numberAt(`${basePath}.halo_particles`, fallback.haloParticles),
    flowTrailCount: numberAt(`${basePath}.flow_trail_count`, fallback.flowTrailCount),
  };
}

function numberAt(path: string, fallback: number): number {
  const rawValue = yamlScalars[path];
  if (rawValue === undefined) return fallback;
  const value = Number(rawValue);
  return Number.isFinite(value) ? value : fallback;
}

function stringAt(path: string, fallback: string): string {
  return yamlScalars[path] ?? fallback;
}

function parseYamlScalarPaths(source: string): Record<string, string> {
  const values: Record<string, string> = {};
  const stack: Array<{ indent: number; key: string }> = [];

  for (const line of source.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || trimmed.startsWith("-")) continue;
    const match = line.match(/^(\s*)([A-Za-z0-9_-]+):(?:\s*(.*))?$/);
    if (!match) continue;

    const indent = match[1].length;
    const key = match[2];
    const value = stripYamlScalar(match[3] ?? "");

    while (stack.length && indent <= stack[stack.length - 1].indent) {
      stack.pop();
    }

    const path = [...stack.map((entry) => entry.key), key].join(".");
    if (value) {
      values[path] = value;
    } else {
      stack.push({ indent, key });
    }
  }

  return values;
}

function stripYamlScalar(value: string): string {
  const withoutComment = value.replace(/\s+#.*$/, "").trim();
  if (
    (withoutComment.startsWith('"') && withoutComment.endsWith('"')) ||
    (withoutComment.startsWith("'") && withoutComment.endsWith("'"))
  ) {
    return withoutComment.slice(1, -1);
  }
  return withoutComment;
}
