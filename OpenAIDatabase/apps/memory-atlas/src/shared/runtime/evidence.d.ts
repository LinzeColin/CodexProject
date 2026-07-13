import { DEFAULT_TIMELINE_RENDERER_MODE, TIMELINE_RENDERER_FEATURE_FLAG_VERSION, type GalaxyRendererMode, type TimelineRendererMode } from "../../config/visualFlags";
import type { AtlasNode, ViewKey } from "../../types";
import { type SharedAtlasState } from "../../state/sharedAtlasState";
import { STARFIELD_MAPPING_VERSION, type StarfieldMappingResult } from "../../models/starfieldMapping";
import { CLIO_LIKE_VISUALS_VERSION, COMMAND_API_VERSION, COMMAND_PALETTE_VERSION, COMMAND_WORKFLOW_VERSION, CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION, CommandExecutionStatus, CrossBoardSharedStateSurface, DATA_MAP_DETAIL_PANEL_VERSION, DATA_MAP_PROPOSAL_ENTRY_VERSION, DATA_MAP_RELATION_EXPLANATION_VERSION, DATA_MAP_STRUCTURE_MODEL_VERSION, ECONOMIC_LIKE_VISUALS_VERSION, GLOBAL_CHINESE_UX_VERSION, HUMAN_QUESTION_MAP_VERSION, INSPECTOR_EXPLANATION_LAYER_VERSION, LOCAL_APP_HANDOFF_URL, MACHINE_DETAIL_FOLDING_VERSION, OWNER_DAILY_API_VERSION, OWNER_DAILY_UI_VERSION, OwnerDailyResult, PROPOSAL_API_VERSION, PROPOSAL_WORKFLOW_VERSION, REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION, REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION, S12P1CommandId, S12P1CoreCommandId, S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID, S12_P3_CHATGPT_DEEP_EXPLORE_VERSION, SEARCH_2_0_RUNTIME_VERSION, SEARCH_2_0_SESSION_SUMMARY_VERSION, STARFIELD_INTEGRATION_VERSION, SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION, SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION, WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION } from "../atlas/constants";
import { ClioLikeVisualId, EconomicLikeVisualId, HumanQuestionMapVisualId, ReviewPanelId, SummaryClosurePanelId, TimelineTimeRangeSelection, WorkflowLatentGovernanceVisualId } from "../atlas/contracts";
import { DataMapStructureLayerId } from "../atlas/layoutContracts";



declare global {
  interface Window {
    __memoryAtlasStage4Phase3?: () => {
      integrationVersion: typeof STARFIELD_INTEGRATION_VERSION;
      mappingVersion: typeof STARFIELD_MAPPING_VERSION;
      rendererMode: GalaxyRendererMode;
      mappingSource: StarfieldMappingResult["source"];
      mappedParticleCount: number;
      snapshotMappedCount: number;
      fallbackCount: number;
      safety: StarfieldMappingResult["safety"];
      formulas: StarfieldMappingResult["formulas"];
    };
    __memoryAtlasStage5Phase3?: () => {
      integrationVersion: typeof TIMELINE_RENDERER_FEATURE_FLAG_VERSION;
      rendererMode: TimelineRendererMode;
      defaultRendererMode: typeof DEFAULT_TIMELINE_RENDERER_MODE;
      legacyRollbackEnabled: true;
      visibleEventCount: number;
      totalEventCount: number;
      selectedRangeActive: boolean;
      selectedRange: TimelineTimeRangeSelection | null;
      evidenceLayers: string[];
      levelCounts: Record<string, number>;
      feedback: {
        reducedMotion: boolean;
        pseudoHaptic: boolean;
        audio: boolean;
      };
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasStage6Phase1?: () => {
      structureModelVersion: typeof DATA_MAP_STRUCTURE_MODEL_VERSION;
      relationExplanationVersion: typeof DATA_MAP_RELATION_EXPLANATION_VERSION;
      layers: DataMapStructureLayerId[];
      visibleNodeCount: number;
      relationCount: number;
      selectedRelationId: string | null;
      defaultCollapsed: true;
      boundary: "No Phase 6.2 editing";
      rawPrivateDataIncluded: false;
      directActiveMemoryWriteback: false;
      proposalWrite: false;
    };
    __memoryAtlasStage6Phase2?: () => {
      detailPanelVersion: typeof DATA_MAP_DETAIL_PANEL_VERSION;
      proposalEntryVersion: typeof DATA_MAP_PROPOSAL_ENTRY_VERSION;
      selectedNodeId: string | null;
      selectedNodeKind: AtlasNode["kind"] | null;
      detailFields: string[];
      proposalOnly: true;
      directActiveMemoryWriteback: false;
      rawPrivateDataIncluded: false;
    };
    __memoryAtlasStage7Phase1?: () => {
      runtimeVersion: typeof SEARCH_2_0_RUNTIME_VERSION;
      sessionSummaryVersion: typeof SEARCH_2_0_SESSION_SUMMARY_VERSION;
      query: string;
      resultCount: number;
      hasMatchedReason: boolean;
      hasEvidenceRefs: boolean;
      jumpActions: Array<"starfield" | "river" | "inspector">;
      zeroResultRecoveryVisible: boolean;
      proposalCandidateCount: number;
      directActiveMemoryWriteback: false;
      rawPrivateDataIncluded: false;
    };
    __memoryAtlasStage7Phase2?: () => {
      runtimeVersion: typeof REVIEW_SUMMARY_ITERATION_RUNTIME_VERSION;
      reviewSchemaVersion: typeof REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION;
      questionCount: number;
      panelIds: ReviewPanelId[];
      iterationItemCount: number;
      proposalCandidate: boolean;
      hasEvidenceRefs: boolean;
      directActiveMemoryWriteback: false;
      rawPrivateDataIncluded: false;
    };
    __memoryAtlasStage8Phase1?: () => {
      runtimeVersion: typeof SUMMARY_ITERATION_CLOSURE_RUNTIME_VERSION;
      closureSchemaVersion: typeof SUMMARY_ITERATION_CLOSURE_SCHEMA_VERSION;
      sourceReviewSchemaVersion: typeof REVIEW_SUMMARY_ITERATION_SCHEMA_VERSION;
      panelIds: SummaryClosurePanelId[];
      changeComparisonCount: number;
      staleConflictSignalCount: number;
      proposalCandidateCount: number;
      proposalOnly: true;
      directActiveMemoryWriteback: false;
      rawPrivateDataIncluded: false;
      proposalWrite: false;
    };
    __memoryAtlasStage9Phase1?: () => {
      runtimeVersion: typeof CROSS_BOARD_SHARED_STATE_RUNTIME_VERSION;
      inspectorLayerVersion: typeof INSPECTOR_EXPLANATION_LAYER_VERSION;
      sharedStateSchemaVersion: SharedAtlasState["schema_version"];
      activeView: ViewKey;
      surfaces: CrossBoardSharedStateSurface[];
      surfaceCount: number;
      synchronizedFilters: SharedAtlasState["filters"];
      shared_state_filters: true;
      synchronized_filters: true;
      focus: SharedAtlasState["focus"];
      sync: SharedAtlasState["sync"];
      visibleNodeCount: number;
      selectedNodeId: string | null;
      inspector_explanation_layer: {
        mounted: boolean;
        formulaCount: number;
        evidenceCount: number;
        safetyNoteCount: number;
        source: "redacted_derived_snapshot";
      };
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS10Phase2?: () => {
      globalChineseUxVersion: typeof GLOBAL_CHINESE_UX_VERSION;
      coreUiDefaultChinese: true;
      machineTermsRequireChineseExplanation: true;
      chineseUxAudit: "atlasctl audit --check chinese-ux";
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS10Phase3?: () => {
      machineDetailFoldingVersion: typeof MACHINE_DETAIL_FOLDING_VERSION;
      defaultHumanReadableFirst: true;
      machineFieldsDefaultCollapsed: true;
      advancedDetailsEntryVisible: true;
      foldedSurfaces: Array<"home_arrival" | "search_session" | "search_result" | "review_session" | "summary_closure" | "inspector">;
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS11Phase1?: () => {
      clioLikeVisualsVersion: typeof CLIO_LIKE_VISUALS_VERSION;
      visualIds: ClioLikeVisualId[];
      visualCount: number;
      clusterCount: number;
      supportsFilters: ["source", "time", "project", "task"];
      activeFilters: {
        source: string;
        time: string;
        project: string;
        task: string;
      };
      chartsAreStaticDecoration: false;
      humanQuestionMapPartial: true;
      pendingLaterVisuals: ["S11 P2", "S11 P3", "S11 P4"];
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS11Phase2?: () => {
      economicLikeVisualsVersion: typeof ECONOMIC_LIKE_VISUALS_VERSION;
      visualIds: EconomicLikeVisualId[];
      visualCount: number;
      taskCount: number;
      supportsFilters: ["source", "time", "project", "task"];
      activeFilters: {
        source: string;
        time: string;
        project: string;
        task: string;
      };
      chartsAreStaticDecoration: false;
      humanQuestionMapPartial: true;
      pendingLaterVisuals: ["S11 P3", "S11 P4"];
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS11Phase3?: () => {
      workflowLatentGovernanceVisualsVersion: typeof WORKFLOW_LATENT_GOVERNANCE_VISUALS_VERSION;
      visualIds: WorkflowLatentGovernanceVisualId[];
      visualCount: number;
      sankeyLinkCount: number;
      frictionCellCount: number;
      latentAxisCount: number;
      evidenceEventCount: number;
      formulaParameterCount: number;
      supportsFilters: ["source", "time", "project", "task"];
      activeFilters: {
        source: string;
        time: string;
        project: string;
        task: string;
      };
      chartsAreStaticDecoration: false;
      humanQuestionMapPartial: true;
      pendingLaterVisuals: ["S11 P4"];
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS11Phase4?: () => {
      humanQuestionMapVersion: typeof HUMAN_QUESTION_MAP_VERSION;
      visualIds: HumanQuestionMapVisualId[];
      visualCount: number;
      p0VisualCount: number;
      failedP0Count: number;
      excludedCandidateCount: number;
      supportsFilters: ["source", "time", "project", "task"];
      activeFilters: {
        source: string;
        time: string;
        project: string;
        task: string;
      };
      visualRoiGatePassAllP0: true;
      allP0HaveHumanQuestionAndAction: true;
      chartsAreStaticDecoration: false;
      humanQuestionMapComplete: true;
      pendingLaterVisuals: ["S11 Review"];
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalWrite: false;
      };
    };
    __memoryAtlasS12Phase1?: () => {
      commandPaletteVersion: typeof COMMAND_PALETTE_VERSION;
      commandIds: S12P1CommandId[];
      commandCount: number;
      acceptedCoreCommandIds: S12P1CoreCommandId[];
      personalizationCommandId: "generate_personalization_prompt";
      personalizationTargets: ["chatgpt", "codex", "other_agent"];
      userTriggerRequired: true;
      automaticSendEnabled: false;
      chatgptDeepExploreEnabled: false;
      unacceptedCommandCount: 0;
      selectedCommandId: S12P1CommandId;
      pendingLaterWork: ["S12 P2", "S12 P3"];
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalApplyExecution: false;
        sendsCookiesTokensSecrets: false;
      };
    };
    __memoryAtlasS12Phase3?: () => {
      taskId: "MA-V12-S12P3";
      acceptanceId: "ACC-MA-V12-S12P3";
      contractVersion: typeof S12_P3_CHATGPT_DEEP_EXPLORE_VERSION;
      commandId: typeof S12_P3_CHATGPT_DEEP_EXPLORE_COMMAND_ID;
      commandVisible: boolean;
      defaultMode: "prefill_only";
      allowedModes: ["prefill_only", "auto_submit"];
      dryRunCommand: string;
      openCommand: string;
      userTriggerRequired: true;
      noSilentSend: true;
      autoSubmitRequiresExplicitConfig: true;
      safety: {
        rawPrivateDataIncluded: false;
        directActiveMemoryWriteback: false;
        proposalApplyExecution: false;
        sendsCookiesTokensSecrets: false;
      };
    };
    __memoryAtlasR3CommandWorkflows?: () => {
      workflowVersion: typeof COMMAND_WORKFLOW_VERSION;
      commandApiVersion: typeof COMMAND_API_VERSION;
      commandIds: S12P1CommandId[];
      runtimeAvailable: boolean;
      selectedCommandId: S12P1CommandId;
      executionStatus: CommandExecutionStatus;
      hostedStaticReadOnly: boolean;
      localAppHandoff: typeof LOCAL_APP_HANDOFF_URL;
      noSilentSend: true;
      canonicalRepoMutation: false;
    };
    __memoryAtlasR4ProposalWorkflow?: () => {
      workflowVersion: typeof PROPOSAL_WORKFLOW_VERSION;
      proposalApiVersion: typeof PROPOSAL_API_VERSION;
      runtimeAvailable: boolean;
      workspaceOpen: boolean;
      proposalCount: number;
      applyReadyCount: number;
      humanApprovalRequired: true;
      rawMutation: false;
      canonicalRepoMutation: false;
      remotePush: false;
    };
    __memoryAtlasR5OwnerDaily?: () => {
      uiVersion: typeof OWNER_DAILY_UI_VERSION;
      ownerDailyApiVersion: typeof OWNER_DAILY_API_VERSION;
      runtimeAvailable: boolean;
      workspaceOpen: boolean;
      resultStatus: OwnerDailyResult["status"] | "idle";
      completedCount: number;
      failedCount: number;
      hostedStaticReadOnly: boolean;
      canonicalRepoMutation: false;
      remotePush: false;
    };
  }
}
