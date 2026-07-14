import type { PropsWithChildren } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { emptyAtlas, loadMemoryAtlas } from "../data/atlas";
import type { MemoryAtlas } from "../types";

export interface AtlasDataContextValue {
  atlas: MemoryAtlas;
  lifecycle: "载入中" | "已同步" | "读取失败";
  loadError: string;
  loadState: "loading" | "ready" | "error";
  revision: number;
  runStartedAt: Date;
  snapshotLoadedAt: Date | null;
  reloadAtlas: () => Promise<MemoryAtlas>;
}

const AtlasDataContext = createContext<AtlasDataContextValue | null>(null);

export function AtlasDataProvider({ children }: PropsWithChildren) {
  const [atlas, setAtlas] = useState<MemoryAtlas>(emptyAtlas);
  const [loadState, setLoadState] = useState<AtlasDataContextValue["loadState"]>("loading");
  const [loadError, setLoadError] = useState("");
  const [revision, setRevision] = useState(0);
  const [runStartedAt, setRunStartedAt] = useState(() => new Date());
  const [snapshotLoadedAt, setSnapshotLoadedAt] = useState<Date | null>(null);
  const [lifecycle, setLifecycle] = useState<AtlasDataContextValue["lifecycle"]>("载入中");
  const activeControllerRef = useRef<AbortController | null>(null);
  const activeRequestIdRef = useRef(0);
  const hasSnapshotRef = useRef(false);

  const beginRequest = useCallback(() => {
    activeControllerRef.current?.abort();
    const controller = new AbortController();
    activeControllerRef.current = controller;
    const requestId = activeRequestIdRef.current + 1;
    activeRequestIdRef.current = requestId;
    return { controller, requestId };
  }, []);

  const acceptAtlas = useCallback((loadedAtlas: MemoryAtlas, requestId: number) => {
    if (requestId !== activeRequestIdRef.current) return false;
    setAtlas(loadedAtlas);
    setLoadError("");
    setLoadState("ready");
    setSnapshotLoadedAt(new Date());
    setLifecycle("已同步");
    setRevision((current) => current + 1);
    hasSnapshotRef.current = true;
    return true;
  }, []);

  const reloadAtlas = useCallback(async () => {
    const { controller, requestId } = beginRequest();
    try {
      const loadedAtlas = await loadMemoryAtlas(controller.signal);
      if (!acceptAtlas(loadedAtlas, requestId)) throw new DOMException("Stale Memory Atlas request", "AbortError");
      return loadedAtlas;
    } catch (error) {
      const isCurrent = requestId === activeRequestIdRef.current;
      const isAbort = error instanceof DOMException && error.name === "AbortError";
      if (isCurrent && !isAbort && !hasSnapshotRef.current) {
        setLoadError(error instanceof Error ? error.message : "未知 Memory Atlas 读取错误");
        setLoadState("error");
        setSnapshotLoadedAt(null);
        setLifecycle("读取失败");
      }
      throw error;
    }
  }, [acceptAtlas, beginRequest]);

  useEffect(() => {
    let cancelled = false;
    const { controller, requestId } = beginRequest();
    setRunStartedAt(new Date());
    setSnapshotLoadedAt(null);
    setLifecycle("载入中");
    loadMemoryAtlas(controller.signal)
      .then((loadedAtlas) => {
        if (!cancelled) acceptAtlas(loadedAtlas, requestId);
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") return;
        if (cancelled || requestId !== activeRequestIdRef.current) return;
        setLoadError(error instanceof Error ? error.message : "未知 Memory Atlas 读取错误");
        setLoadState("error");
        setSnapshotLoadedAt(null);
        setLifecycle("读取失败");
      });
    return () => {
      cancelled = true;
      controller.abort();
      if (activeControllerRef.current === controller) activeControllerRef.current = null;
    };
  }, [acceptAtlas, beginRequest]);

  const value = useMemo<AtlasDataContextValue>(
    () => ({ atlas, lifecycle, loadError, loadState, reloadAtlas, revision, runStartedAt, snapshotLoadedAt }),
    [atlas, lifecycle, loadError, loadState, reloadAtlas, revision, runStartedAt, snapshotLoadedAt],
  );

  return <AtlasDataContext.Provider value={value}>{children}</AtlasDataContext.Provider>;
}

export function useAtlasData(): AtlasDataContextValue {
  const context = useContext(AtlasDataContext);
  if (!context) throw new Error("useAtlasData must be used within AtlasDataProvider");
  return context;
}
