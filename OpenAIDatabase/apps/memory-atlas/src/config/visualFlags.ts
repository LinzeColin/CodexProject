export type GalaxyRendererMode = "memory-starfield" | "legacy";

export const DEFAULT_GALAXY_RENDERER_MODE: GalaxyRendererMode = "memory-starfield";
export const GALAXY_RENDERER_STORAGE_KEY = "memory-atlas.galaxy-renderer";

export function getInitialGalaxyRendererMode(): GalaxyRendererMode {
  const urlMode = readUrlMode();
  if (urlMode) return urlMode;

  const storedMode = readStoredMode();
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

function readUrlMode(): GalaxyRendererMode | null {
  if (typeof window === "undefined") return null;
  const params = new URLSearchParams(window.location.search);
  return normalizeGalaxyRendererMode(params.get("galaxyRenderer") ?? params.get("galaxy"));
}

function readStoredMode(): GalaxyRendererMode | null {
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
