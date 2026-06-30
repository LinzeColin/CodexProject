(() => {
  const VERSION_INFO = Object.freeze({
    schema: "PFIV024Stage2EntryVersionInfoV1",
    compatibilitySchemas: ["PFIV024Stage1VersionInfoV1"],
    targetVersion: "v0.2.4",
    sourcePackageVersion: "v0.2.3-repair",
    repairLabel: "PFI v0.2.3 Repair",
    buildId: "pfi-v024-stage2-phase22",
    bundleVersion: "20260630.2",
    uiContractVersion: "PFI-V024-STAGE2-ENTRY-CONSISTENCY",
    shellIntegrityContract: "PFI-V024-STAGE1-SHELL-INTEGRITY",
    entryConsistencyContract: "PFI-V024-STAGE2-ENTRY-CONSISTENCY",
    stage: "Stage 2",
    phase: "2.2",
    visibleFields: ["repairLabel", "buildId", "webBundleHash", "uiContractVersion"],
  });

  function readPFIStage1Version() {
    return VERSION_INFO;
  }

  function readPFIStage2EntryVersion() {
    return VERSION_INFO;
  }

  window.PFI_STAGE1_VERSION = VERSION_INFO;
  window.PFI_READ_STAGE1_VERSION = readPFIStage1Version;
  window.PFI_STAGE2_ENTRY_VERSION = VERSION_INFO;
  window.PFI_READ_STAGE2_ENTRY_VERSION = readPFIStage2EntryVersion;
})();
