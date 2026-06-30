(() => {
  const FALLBACK_BUILD_ID = "pfi-v024-stage2-phase22";
  const FALLBACK_UI_CONTRACT = "PFI-V024-STAGE2-ENTRY-CONSISTENCY";

  function readJsonConfig(id) {
    try {
      const node = document.getElementById(id);
      const parsed = JSON.parse(node?.textContent || "{}");
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (_error) {
      return {};
    }
  }

  function readStage2EntryAudit() {
    const runtime = readJsonConfig("pfi-runtime-config");
    const body = document.body?.dataset || {};
    const query = new URLSearchParams(window.location.search || "");
    const version =
      typeof window.PFI_READ_STAGE2_ENTRY_VERSION === "function"
        ? window.PFI_READ_STAGE2_ENTRY_VERSION()
        : window.PFI_STAGE2_ENTRY_VERSION || {};

    return Object.freeze({
      schema: "PFIV024Stage2EntryAuditReadModelV1",
      targetVersion: runtime.targetVersion || version.targetVersion || "v0.2.4",
      sourcePackageVersion: runtime.sourcePackageVersion || version.sourcePackageVersion || "v0.2.3-repair",
      repairLabel: runtime.repairLabel || version.repairLabel || body.pfiRepairLabel || "PFI v0.2.3 Repair",
      buildId: runtime.buildId || version.buildId || body.pfiBuildId || FALLBACK_BUILD_ID,
      bundleVersion: runtime.bundleVersion || version.bundleVersion || body.pfiBundleVersion || "20260630.2",
      uiContractVersion:
        runtime.uiContractVersion || version.uiContractVersion || body.pfiUiContractVersion || FALLBACK_UI_CONTRACT,
      webBundleHash: runtime.webBundleHash || body.pfiWebBundleHash || "",
      webIndexSha256: runtime.webIndexSha256 || body.pfiWebIndexSha256 || "",
      tokensCssSha256: runtime.tokensCssSha256 || body.pfiTokensCssSha256 || "",
      shellJsSha256: runtime.shellJsSha256 || body.pfiShellJsSha256 || "",
      versionJsSha256: runtime.versionJsSha256 || body.pfiVersionJsSha256 || "",
      entryAuditJsSha256: runtime.entryAuditJsSha256 || body.pfiEntryAuditJsSha256 || "",
      projectRoot: runtime.projectRoot || body.pfiProjectRoot || "",
      appPath: runtime.appPath || body.pfiAppPath || query.get("pfi_app_path") || "",
      localhostUrl: window.location.origin || "",
      currentUrl: window.location.href || "",
      entrySource: query.get("pfi_entry") || body.pfiEntrySource || "browser",
      queryBuildId: query.get("pfi_build") || "",
      queryUiContractVersion: query.get("pfi_ui_contract") || "",
      stage: runtime.stage || version.stage || body.pfiStage || "Stage 2",
      phase: runtime.phase || version.phase || body.pfiPhase || "2.2",
    });
  }

  const audit = readStage2EntryAudit();
  window.PFI_STAGE2_ENTRY_AUDIT = audit;
  window.PFI_READ_STAGE2_ENTRY_AUDIT = readStage2EntryAudit;
})();
