export type GalaxyRendererMode = "memory-starfield" | "legacy";
export type TimelineRendererMode = "memory-river" | "legacy";

export const GALAXY_RENDERER_FEATURE_FLAG_VERSION = "memory_starfield_integration.v1_1_7_stage4_phase3";
export const DEFAULT_GALAXY_RENDERER_MODE: GalaxyRendererMode = "memory-starfield";
export const DEFAULT_TIMELINE_RENDERER_MODE: TimelineRendererMode = "memory-river";
export const GALAXY_RENDERER_STORAGE_KEY = "memory-atlas.galaxy-renderer";
export const TIMELINE_RENDERER_STORAGE_KEY = "memory-atlas.timeline-renderer";

export function getInitialGalaxyRendererMode(): GalaxyRendererMode {
  const urlMode = readGalaxyUrlMode();
  if (urlMode) return urlMode;

  const storedMode = readStoredGalaxyMode();
  if (storedMode) return storedMode;

  const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
  const envMode = normalizeGalaxyRendererMode(env?.VITE_MEMORY_ATLAS_GALAXY_RENDERER);
  return envMode ?? DEFAULT_GALAXY_RENDERER_MODE;
}

export function persistGalaxyRendererMode(mode: GalaxyRendererMode): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(GALAXY_RENDERER_STORAGE_KEY, mode);
  } catch {
    // Storage can be unavailable in locked-down local previews.
  }
}

export function getInitialTimelineRendererMode(): TimelineRendererMode {
  const urlMode = readTimelineUrlMode();
  if (urlMode) return urlMode;

  const storedMode = readStoredTimelineMode();
  if (storedMode) return storedMode;

  const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
  const envMode = normalizeTimelineRendererMode(env?.VITE_MEMORY_ATLAS_TIMELINE_RENDERER);
  return envMode ?? DEFAULT_TIMELINE_RENDERER_MODE;
}

export function persistTimelineRendererMode(mode: TimelineRendererMode): void {
  if (typeof window === "undefined") return;
  try {
    window.localStorage.setItem(TIMELINE_RENDERER_STORAGE_KEY, mode);
  } catch {
    // Storage can be unavailable in locked-down local previews.
  }
}

function readGalaxyUrlMode(): GalaxyRendererMode | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  return normalizeGalaxyRendererMode(params.get("galaxyRenderer") ?? params.get("galaxy"));
}

function readStoredGalaxyMode(): GalaxyRendererMode | null {
  if (typeof window === "undefined") return null;
  try {
    return normalizeGalaxyRendererMode(window.localStorage.getItem(GALAXY_RENDERER_STORAGE_KEY));
  } catch {
    return null;
  }
}

function normalizeGalaxyRendererMode(value: string | null | undefined): GalaxyRendererMode | null {
  if (value === "memory-starfield" || value === "starfield" || value === "new") return "memory-starfield";
  if (value === "legacy" || value === "old") return "legacy";
  return null;
}

function readTimelineUrlMode(): TimelineRendererMode | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  return normalizeTimelineRendererMode(params.get("timelineRenderer") ?? params.get("timeline"));
}

function readStoredTimelineMode(): TimelineRendererMode | null {
  if (typeof window === "undefined") return null;
  try {
    return normalizeTimelineRendererMode(window.localStorage.getItem(TIMELINE_RENDERER_STORAGE_KEY));
  } catch {
    return null;
  }
}

function normalizeTimelineRendererMode(value: string | null | undefined): TimelineRendererMode | null {
  if (value === "memory-river" || value === "river" || value === "new") return "memory-river";
  if (value === "legacy" || value === "old" || value === "timeline") return "legacy";
  return null;
}
