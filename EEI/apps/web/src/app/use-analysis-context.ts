"use client";

import { useEffect, useState } from "react";
import {
  ACTIVE_ANALYSIS_CONTEXT,
  ANALYSIS_PREVIEW_STORAGE_KEY,
  PREVIEW_ANALYSIS_CONTEXT,
  type AnalysisContext
} from "./analysis-contract";

export function useAnalysisContext() {
  const [analysisContext, setAnalysisContext] = useState<AnalysisContext>(ACTIVE_ANALYSIS_CONTEXT);

  useEffect(() => {
    const stored = window.localStorage.getItem(ANALYSIS_PREVIEW_STORAGE_KEY);
    if (stored === PREVIEW_ANALYSIS_CONTEXT.profileVersion) {
      setAnalysisContext(PREVIEW_ANALYSIS_CONTEXT);
    }
  }, []);

  function applyPreview() {
    window.localStorage.setItem(
      ANALYSIS_PREVIEW_STORAGE_KEY,
      PREVIEW_ANALYSIS_CONTEXT.profileVersion
    );
    setAnalysisContext(PREVIEW_ANALYSIS_CONTEXT);
  }

  function clearPreview() {
    window.localStorage.removeItem(ANALYSIS_PREVIEW_STORAGE_KEY);
    setAnalysisContext(ACTIVE_ANALYSIS_CONTEXT);
  }

  function applyServerContext(nextContext: AnalysisContext) {
    window.localStorage.removeItem(ANALYSIS_PREVIEW_STORAGE_KEY);
    setAnalysisContext(nextContext);
  }

  return {
    analysisContext,
    applyPreview,
    applyServerContext,
    clearPreview,
    isPreviewActive: analysisContext.profileVersion === PREVIEW_ANALYSIS_CONTEXT.profileVersion
  };
}
