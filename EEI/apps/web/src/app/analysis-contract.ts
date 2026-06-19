export type AnalysisContext = {
  contractVersion: string;
  modelVersion: string;
  profileVersion: string;
  profileLabel: string;
  dataSnapshot: string;
  scoreSnapshot: string;
  formulaRegistryVersion: string;
  parameterCatalogVersion: string;
  thresholdRegistryVersion: string;
  defaultAsOf: "2026-06-01" | "2026-06-12" | "2026-06-19";
};

export const ANALYSIS_PREVIEW_STORAGE_KEY = "eei.analysisPreview.v1";

export const ACTIVE_ANALYSIS_CONTEXT: AnalysisContext = {
  contractVersion: "analysis-context-v1",
  modelVersion: "business-empire-model-v2",
  profileVersion: "balanced-v2@2",
  profileLabel: "Balanced v2",
  dataSnapshot: "fixture-v1",
  scoreSnapshot: "score-fixture-v1",
  formulaRegistryVersion: "formula-registry-v4.2",
  parameterCatalogVersion: "parameter-catalog-v4.2",
  thresholdRegistryVersion: "threshold-registry-v4.2",
  defaultAsOf: "2026-06-19"
};

export const PREVIEW_ANALYSIS_CONTEXT: AnalysisContext = {
  ...ACTIVE_ANALYSIS_CONTEXT,
  profileVersion: "supply-chain-preview@draft",
  profileLabel: "Supply chain preview",
  scoreSnapshot: "score-preview-session-v1"
};
