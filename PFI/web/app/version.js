(() => {
  const VERSION_INFO = Object.freeze({
    schema: "PFIV024Stage1VersionInfoV1",
    targetVersion: "v0.2.4",
    sourcePackageVersion: "v0.2.3-repair",
    repairLabel: "PFI v0.2.3 Repair",
    buildId: "pfi-v024-stage1-phase12",
    bundleVersion: "20260630.1",
    uiContractVersion: "PFI-V024-STAGE1-SHELL-INTEGRITY",
    shellIntegrityContract: "PFI-V024-STAGE1-SHELL-INTEGRITY",
    stage: "Stage 1",
    phase: "1.2",
  });

  function readPFIStage1Version() {
    return VERSION_INFO;
  }

  window.PFI_STAGE1_VERSION = VERSION_INFO;
  window.PFI_READ_STAGE1_VERSION = readPFIStage1Version;
})();
