#!/usr/bin/env python3
"""Fail-closed verifier for the PFI v0.2.5 Stage 1 whole review.

The verifier deliberately replays historical Phase bindings with ``git show``.
It does not execute an old verifier from the current checkout, because those
verifiers were intentionally HEAD-bound and are not cross-commit replay tools.

Without ``--candidate`` the script verifies either a direct binding commit at
HEAD or the binding payload in the working tree while HEAD is the pinned
remediation-content commit.  ``--require-attestation`` additionally requires a
post-commit JSON attestation below the repository common Git directory.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import plistlib
import re
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path, PurePosixPath
from typing import Any, Iterable

from jsonschema import Draft202012Validator, FormatChecker


sys.dont_write_bytecode = True

SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = Path(
    subprocess.check_output(
        ["git", "-C", str(SCRIPT_PATH.parent), "rev-parse", "--show-toplevel"],
        text=True,
    ).strip()
)
PFI_ROOT = REPO_ROOT / "PFI"
REVIEW_DIR = "PFI/reports/pfi_v025/stage_1/whole_stage_review"

# Pinned graph.  Only the final binding commit is intentionally derived from
# --candidate/HEAD because a commit cannot record its own SHA in tracked data.
STAGE_BASE = "9380fdf4a500f48a2b15859044ab7926b4924391"
WHOLE_REVIEW_BASE = "96305405dcf7eb56246d2cede2f5b50b2b1be101"
INITIAL_REMEDIATION_CONTENT_COMMIT = "9c4fb71f67084d48c31b7aab404bbeed0ebf047c"
SECOND_REMEDIATION_CONTENT_COMMIT = "2009d36d9280940f71d44f339240faaa03ed5377"
THIRD_REMEDIATION_CONTENT_COMMIT = "498571095e50c13be4261c341889b514dfc6638f"
FOURTH_REMEDIATION_CONTENT_COMMIT = "5b0667ef926210728e026d6b671070d6d1fe0d0d"
INTERMEDIATE_REMEDIATION_CONTENT_COMMIT = "2ef60871ba425cd4011bd8f62d4f41422e0a854a"
FINANCIAL_CONTROL_CONTENT_COMMIT = "0ffe6909b338858177117a2d1590b766404489df"
RAW_MANIFEST_CONTENT_COMMIT = "c6091e98361871524a1cdedd6b95afb2f0728a33"
STRUCTURAL_TRACE_CONTENT_COMMIT = "ca6ce4aecd24c1bd8e1ebd0ab3bc6781459fd351"
LIVE_PRIVACY_CONTENT_COMMIT = "c980fef513a82b895d4870a5d357e2413e89eda6"
ACCESSIBILITY_CONTENT_COMMIT = "e412b1da0525d33dab4dcb8392aa8734f4261b28"
PREVIOUS_REMEDIATION_CONTENT_COMMIT = "7348eff2e7ef0492931d651b851e80daa6036d76"
C12_REMEDIATION_CONTENT_COMMIT = "8df58316b87a497953cae25848af8aa1be8c9ce1"
C13_REMEDIATION_CONTENT_COMMIT = "bb4243a45435f6ec6bc26aa6e7fe2244ad79656e"
C14_REMEDIATION_CONTENT_COMMIT = "e6d6de541a593677a2312dbf32278782a07395e8"
C15_REMEDIATION_CONTENT_COMMIT = "de661af5bd6d513634663226fc672b45c2969bd3"
C16_REMEDIATION_CONTENT_COMMIT = "a8ac008d99742c21d6dba63193c4df34be1b539b"
C17_REMEDIATION_CONTENT_COMMIT = "6d93b3572e7e5c9791a2b2fc5c7d55b24ce456cb"
C18_REMEDIATION_CONTENT_COMMIT = "0ac610290f3f4b596b49af8c7c479a3e40f86e6b"
C19_REMEDIATION_CONTENT_COMMIT = "8c27dfb85dd145af5eadc99f468a05519784b838"
REMEDIATION_CONTENT_COMMIT = "04390bcf17c18de107eb2f1b4ce051c83638f98c"
ROADMAP_SHA256 = "fc2f406eef45d9a09f852aad1a2234b2c37547f8ae9c002d6230c54f7ca1071b"
TASK_PACK_SHA256 = "591c839992963a631e079498ec98f6e83a5686ead4ce4ea2c8aea39ab3346dd2"
ACTIVE_REQUIREMENTS_SHA256 = "b77e1ac78e8842d9a58d76d07a491f80e7a010b3cc91fb4ca7cf24ba10457d37"
STANDING_AUTHORIZATION_SHA256 = "368c90a5dd949bc09807c604cea23d05de476fe69e64ad723ced49bab3b5e3ac"
AUTHORIZATION_ID = "PFI-V025-INTERIM-STAGE-TRANSITION-AUTH-20260712"
ACCEPTANCE_ID = "ACC-PFI-V025-STAGE1-WHOLE-REVIEW"
CONTRACT_ID = "PFI-V025-STAGE1-WHOLE-REVIEW"
SCOPE_OVERRIDE_ID = "PFI-V025-STAGE1-WHOLE-REVIEW-REMEDIATION-SCOPE-20260713"
SCOPE_OVERRIDE_SOURCE = "conversation_user_decision_2026-07-13_all_interim_actions_authorized_no_reprompt"
ROADMAP_TASK_IDS = tuple(
    f"S1-P{phase}-T{task}" for phase in (1, 2, 3) for task in range(1, 5)
)
OVERRIDDEN_STAGE1_TASK_IDS = frozenset({"S1-P3-T1", "S1-P3-T3"})
STOP_CONDITION_IDS = (
    "S1-STOP-01-SOURCE-DIRECTORY-UNKNOWN",
    "S1-STOP-02-UNKNOWN-USER-FILE-OVERWRITE",
    "S1-STOP-03-FOUR-WAY-IDENTITY-MISMATCH",
    "S1-STOP-04-MANUAL-HISTORY-CLEAR-REQUIRED",
)
ACCEPTANCE_CRITERIA_IDS = tuple(f"S1-AC-{number:02d}" for number in range(1, 7))
TASK_EVIDENCE_REFS = {
    "S1-P1-T1": ("PFI/config/release_manifest.json",),
    "S1-P1-T2": ("PFI/reports/pfi_v025/stage_1/phase_1_1/app_info_plist.json",),
    "S1-P1-T3": ("PFI/reports/pfi_v025/stage_1/phase_1_1/identity_matrix.json",),
    "S1-P1-T4": ("PFI/reports/pfi_v025/stage_1/phase_1_1/mismatch_chinese_error.png",),
    "S1-P2-T1": ("PFI/reports/pfi_v025/stage_1/phase_1_2/cache_audit.md",),
    "S1-P2-T2": ("PFI/reports/pfi_v025/stage_1/phase_1_2/cache_headers.json",),
    "S1-P2-T3": ("PFI/reports/pfi_v025/stage_1/phase_1_2/service_worker_audit.md",),
    "S1-P2-T4": ("PFI/reports/pfi_v025/stage_1/phase_1_2/browser_validation.json",),
    "S1-P3-T1": (
        f"{REVIEW_DIR}/candidate_app.json",
        f"{REVIEW_DIR}/launchservices_open_capture.json",
    ),
    "S1-P3-T2": (f"{REVIEW_DIR}/browser_validation.json",),
    "S1-P3-T3": (f"{REVIEW_DIR}/entry_matrix.json",),
    "S1-P3-T4": (f"{REVIEW_DIR}/evidence.json",),
}
CRITERIA_EVIDENCE_REFS = {
    "S1-AC-01": ("PFI/config/release_manifest.json", f"{REVIEW_DIR}/browser_validation.json"),
    "S1-AC-02": (f"{REVIEW_DIR}/frontend_source_identity.json", f"{REVIEW_DIR}/browser_validation.json"),
    "S1-AC-03": (f"{REVIEW_DIR}/browser_validation.json",),
    "S1-AC-04": (f"{REVIEW_DIR}/runtime_api_evidence.json",),
    "S1-AC-05": (
        f"{REVIEW_DIR}/candidate_app.json",
        f"{REVIEW_DIR}/launchservices_open_capture.json",
        f"{REVIEW_DIR}/entry_matrix.json",
    ),
    "S1-AC-06": (f"{REVIEW_DIR}/browser_validation.json",),
}
STOP_EVIDENCE_REFS = {
    STOP_CONDITION_IDS[0]: (
        f"{REVIEW_DIR}/candidate_app.json",
        f"{REVIEW_DIR}/launchservices_open_capture.json",
    ),
    STOP_CONDITION_IDS[1]: (f"{REVIEW_DIR}/entry_matrix.json", f"{REVIEW_DIR}/protected_metadata.json"),
    STOP_CONDITION_IDS[2]: ("PFI/config/release_manifest.json", f"{REVIEW_DIR}/browser_validation.json"),
    STOP_CONDITION_IDS[3]: (f"{REVIEW_DIR}/browser_validation.json",),
}

ROADMAP = Path(
    os.environ.get(
        "PFI_V025_ROADMAP",
        Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_Roadmap.md",
    )
)
TASK_PACK = Path(
    os.environ.get(
        "PFI_V025_TASK_PACK",
        Path.home() / "Downloads/PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip",
    )
)

PHASES: tuple[dict[str, Any], ...] = (
    {
        "phase": "1.1",
        "base": STAGE_BASE,
        "content": "a9592b8ce457492fd0e6817f74388f146ca657c6",
        "binding": "1a995226d34822b5e98191a716bca665136e300f",
        "evidence": "PFI/reports/pfi_v025/stage_1/phase_1_1/evidence.json",
        "evidence_sha256": "b70e5f37fd2028335b5c71f2787169f3fb1d9fd77f90e67ab7ba4b52814fb133",
        "verifier": "PFI/scripts/v025/verify_stage1_phase11.py",
        "verifier_sha256": "bc38e3e4e2e9cefa52d911c8a220acfe308baeb5eef53c76282f1d4d83f40b9d",
        "changed_files_sha256": "e281eb91113bbbf0cc67676810bedcc1d855175066153ea563457b4c5a9309cf",
        "attestation_name": "phase_1_1_attestation.json",
        "attestation_sha256": "0a7ca8543ea55410d50063fd1ce6fccdca779bdbf566772b36c2f4f66b3acd67",
        "binding_field": "identity_binding_commit",
    },
    {
        "phase": "1.2",
        "base": "1a995226d34822b5e98191a716bca665136e300f",
        "content": "b3885f15cd2e983c0839be6a20d7e4a9391c6324",
        "binding": "4065146761859b002f61b03387fa2c724a8ddf8a",
        "evidence": "PFI/reports/pfi_v025/stage_1/phase_1_2/evidence.json",
        "evidence_sha256": "b06ff710c3a95722de1b4c4292f4434ecb7f1b4ac1fb795ca344c6e49d2b957e",
        "verifier": "PFI/scripts/v025/verify_stage1_phase12.py",
        "verifier_sha256": "f0a74a19635cbd025091487fe1c811775842ff1576804ae84a3b17deb85f376c",
        "changed_files_sha256": "85e4215e3970f2f83eeeadc53278f4e8c96a6ab226f8a285e9d3421a6d2c8112",
        "attestation_name": "phase_1_2_attestation.json",
        "attestation_sha256": "79aefc3d523994327f4a9d357ebb76a5a2d5e5383c56ce6170c37d83edb60f85",
        "binding_field": "cache_binding_commit",
    },
    {
        "phase": "1.3",
        "base": "4065146761859b002f61b03387fa2c724a8ddf8a",
        "content": "128c6b889c91f5d7f64c7cd9635466fa2caf0275",
        "binding": WHOLE_REVIEW_BASE,
        "evidence": "PFI/reports/pfi_v025/stage_1/phase_1_3/evidence.json",
        "evidence_sha256": "77b549fc506d4e60492f8b1097487934f1537e413a000aa0a3c10598d9673de9",
        "verifier": "PFI/scripts/v025/verify_stage1_phase13.py",
        "verifier_sha256": "d57713c80aa61dbe27ccea7f982e62639923e23e9c35a0719315895fe0e0244a",
        "changed_files_sha256": "a6a243c02b4abb8f31d52725a0bf3ffc09cb8a3216ba96a3966095367c8d9431",
        "attestation_name": "phase_1_3_attestation.json",
        "attestation_sha256": "bf9461d320e522e0b5cc23c6348fcc4fa5abf5d08f8a21d13958c203bd7f69b6",
        "binding_field": "isolated_app_binding_commit",
    },
)

CONTENT_PATH_STATUS = {
    "PFI/StartPFI.command": "M",
    "PFI/scripts/pfiReleaseIdentity.sh": "M",
    "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
    "PFI/scripts/v025/release_cache_contract.py": "M",
    "PFI/scripts/v025/run_streamlit_with_release_cache.py": "M",
    "PFI/scripts/v025/stage1_phase13_candidate.py": "M",
    "PFI/scripts/v025/stage1_phase13_candidate_env.sh": "M",
    "PFI/src/pfi_os/app/isolated_candidate_app.py": "D",
    "PFI/src/pfi_os/app/streamlit_app.py": "M",
    "PFI/src/pfi_v02/stage_v021_runtime_api.py": "M",
    "PFI/tests/test_v025_stage1_cache_policy.py": "M",
    "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
    "PFI/tests/test_v025_stage1_release_identity.py": "M",
    "PFI/tests/test_v025_stage1_whole_review_remediation.py": "A",
    "PFI/web/app/shell.js": "M",
    "PFI/web/index.html": "M",
    "PFI/web/tests/v025/stage1_release_identity.test.mjs": "M",
}
CONTENT_PATHS = tuple(sorted(CONTENT_PATH_STATUS))
SCOPE_OVERRIDE_CONTENT_PATHS = frozenset(
    {
        "PFI/src/pfi_os/app/isolated_candidate_app.py",
        "PFI/src/pfi_os/app/streamlit_app.py",
        "PFI/src/pfi_v02/stage_v021_runtime_api.py",
        "PFI/web/app/shell.js",
        "PFI/web/index.html",
    }
)

CONTENT_EDGE_PATH_STATUS = (
    (
        WHOLE_REVIEW_BASE,
        INITIAL_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/StartPFI.command": "M",
            "PFI/scripts/pfiReleaseIdentity.sh": "M",
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/scripts/v025/release_cache_contract.py": "M",
            "PFI/scripts/v025/run_streamlit_with_release_cache.py": "M",
            "PFI/scripts/v025/stage1_phase13_candidate.py": "M",
            "PFI/scripts/v025/stage1_phase13_candidate_env.sh": "M",
            "PFI/src/pfi_os/app/isolated_candidate_app.py": "D",
            "PFI/src/pfi_os/app/streamlit_app.py": "M",
            "PFI/src/pfi_v02/stage_v021_runtime_api.py": "M",
            "PFI/tests/test_v025_stage1_cache_policy.py": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
            "PFI/tests/test_v025_stage1_whole_review_remediation.py": "A",
            "PFI/web/app/shell.js": "M",
        },
    ),
    (
        INITIAL_REMEDIATION_CONTENT_COMMIT,
        SECOND_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/src/pfi_v02/stage_v021_runtime_api.py": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
            "PFI/tests/test_v025_stage1_release_identity.py": "M",
            "PFI/tests/test_v025_stage1_whole_review_remediation.py": "M",
        },
    ),
    (
        SECOND_REMEDIATION_CONTENT_COMMIT,
        THIRD_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
            "PFI/web/app/shell.js": "M",
            "PFI/web/index.html": "M",
        },
    ),
    (
        THIRD_REMEDIATION_CONTENT_COMMIT,
        FOURTH_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
            "PFI/tests/test_v025_stage1_whole_review_remediation.py": "M",
        },
    ),
    (
        FOURTH_REMEDIATION_CONTENT_COMMIT,
        INTERMEDIATE_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
        },
    ),
    (
        INTERMEDIATE_REMEDIATION_CONTENT_COMMIT,
        FINANCIAL_CONTROL_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
        },
    ),
    (
        FINANCIAL_CONTROL_CONTENT_COMMIT,
        RAW_MANIFEST_CONTENT_COMMIT,
        {
            "PFI/src/pfi_v02/stage_v021_runtime_api.py": "M",
            "PFI/tests/test_v025_stage1_cache_policy.py": "M",
            "PFI/tests/test_v025_stage1_release_identity.py": "M",
            "PFI/tests/test_v025_stage1_whole_review_remediation.py": "M",
        },
    ),
    (
        RAW_MANIFEST_CONTENT_COMMIT,
        STRUCTURAL_TRACE_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
        },
    ),
    (
        STRUCTURAL_TRACE_CONTENT_COMMIT,
        LIVE_PRIVACY_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
        },
    ),
    (
        LIVE_PRIVACY_CONTENT_COMMIT,
        ACCESSIBILITY_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
        },
    ),
    (
        ACCESSIBILITY_CONTENT_COMMIT,
        PREVIOUS_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
        },
    ),
    (
        PREVIOUS_REMEDIATION_CONTENT_COMMIT,
        C12_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/src/pfi_os/app/streamlit_app.py": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
            "PFI/tests/test_v025_stage1_whole_review_remediation.py": "M",
            "PFI/web/app/shell.js": "M",
            "PFI/web/index.html": "M",
            "PFI/web/tests/v025/stage1_release_identity.test.mjs": "M",
        },
    ),
    (
        C12_REMEDIATION_CONTENT_COMMIT,
        C13_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
        },
    ),
    (
        C13_REMEDIATION_CONTENT_COMMIT,
        C14_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
        },
    ),
    (
        C14_REMEDIATION_CONTENT_COMMIT,
        C15_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
        },
    ),
    (
        C15_REMEDIATION_CONTENT_COMMIT,
        C16_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
        },
    ),
    (
        C16_REMEDIATION_CONTENT_COMMIT,
        C17_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/web/index.html": "M",
        },
    ),
    (
        C17_REMEDIATION_CONTENT_COMMIT,
        C18_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
        },
    ),
    (
        C18_REMEDIATION_CONTENT_COMMIT,
        C19_REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/web/index.html": "M",
        },
    ),
    (
        C19_REMEDIATION_CONTENT_COMMIT,
        REMEDIATION_CONTENT_COMMIT,
        {
            "PFI/scripts/v025/browser_validate_stage1_phase13.mjs": "M",
            "PFI/scripts/v025/stage1_phase13_candidate.py": "M",
            "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": "M",
        },
    ),
)

CORE_GOVERNANCE_PATHS = frozenset(
    {
        "PFI/CHANGELOG.md",
        "PFI/docs/governance/DEVELOPMENT_LEDGER.md",
        "PFI/docs/governance/OWNER_STATUS.md",
        "PFI/docs/governance/STATUS.md",
        "PFI/docs/governance/TRACEABILITY_MATRIX.csv",
        "PFI/docs/governance/VERSION_MATRIX.yaml",
        "PFI/docs/governance/delivery_tasks.yaml",
        "PFI/docs/governance/development_events.jsonl",
        "PFI/docs/governance/project.yaml",
        "PFI/docs/governance/roadmap.yaml",
        "PFI/功能清单.md",
        "PFI/开发记录.md",
        "PFI/模型参数文件.md",
    }
)
SYNC_COMPANION_PATHS = frozenset(
    {
        "PFI/docs/governance/MODEL_SPEC.md",
        "PFI/docs/governance/model_registry.yaml",
        "PFI/docs/governance/formula_registry.yaml",
        "PFI/docs/governance/parameter_registry.csv",
    }
)
REQUIRED_BINDING_PATHS = frozenset(
    {
        *CORE_GOVERNANCE_PATHS,
        "PFI/config/release_manifest.json",
        "PFI/web/index.html",
        "PFI/scripts/v025/verify_stage1_whole_review.py",
        "PFI/docs/pfi_v025/stage_1/STAGE_1_WHOLE_STAGE_REVIEW.md",
        "PFI/docs/pfi_v025/stage_1/stage_1_transition_authorization.json",
        f"{REVIEW_DIR}/accessibility_tree.json",
        f"{REVIEW_DIR}/browser_official_ui.png",
        f"{REVIEW_DIR}/browser_release_identity.png",
        f"{REVIEW_DIR}/browser_validation.json",
        f"{REVIEW_DIR}/candidate_app.json",
        f"{REVIEW_DIR}/changed_files.txt",
        f"{REVIEW_DIR}/entry_matrix.json",
        f"{REVIEW_DIR}/evidence.json",
        f"{REVIEW_DIR}/launchservices_open_capture.json",
        f"{REVIEW_DIR}/frontend_source_identity.json",
        f"{REVIEW_DIR}/launchservices_cleanup.json",
        f"{REVIEW_DIR}/playwright_trace.zip",
        f"{REVIEW_DIR}/privacy_boundary.json",
        f"{REVIEW_DIR}/privacy_scan.txt",
        f"{REVIEW_DIR}/protected_metadata.json",
        f"{REVIEW_DIR}/review_audit.json",
        f"{REVIEW_DIR}/risk_and_rollback.md",
        f"{REVIEW_DIR}/runtime_api_evidence.json",
        f"{REVIEW_DIR}/terminal.log",
    }
)
ALLOWED_BINDING_PATHS = REQUIRED_BINDING_PATHS | SYNC_COMPANION_PATHS
PREBINDING_REVIEW_EXCLUDED_PATHS = frozenset(
    {
        f"{REVIEW_DIR}/review_audit.json",
        f"{REVIEW_DIR}/evidence.json",
        "PFI/docs/pfi_v025/stage_1/stage_1_transition_authorization.json",
    }
)
PNG_PRIVACY_PATHS = {
    "browser_official_ui": f"{REVIEW_DIR}/browser_official_ui.png",
    "browser_release_identity": f"{REVIEW_DIR}/browser_release_identity.png",
}

BACKEND_FILES = (
    "PFI/StartPFI.command",
    "PFI/macos/PFI_launcher.c",
    "PFI/scripts/pfiReleaseIdentity.sh",
    "PFI/scripts/pfiRuntime.sh",
    "PFI/scripts/v025/release_cache_contract.py",
    "PFI/scripts/v025/run_streamlit_with_release_cache.py",
    "PFI/scripts/v025/stage1_phase13_candidate_env.sh",
    "PFI/src/pfi_os/app/streamlit_app.py",
    "PFI/src/pfi_os/application/read_model_status.py",
    "PFI/src/pfi_os/system/shutdown_monitor.py",
    "PFI/src/pfi_v02/stage_v021_runtime_api.py",
    "PFI/src/pfi_v02/stage_v024_stage2_entry_consistency.py",
)
FRONTEND_FILES = (
    "PFI/web/index.html",
    "PFI/web/styles/tokens.css",
    "PFI/web/styles.css",
    "PFI/web/app/version.js",
    "PFI/web/app/entry_audit.js",
    "PFI/web/app/navigation.js",
    "PFI/web/app/routes.js",
    "PFI/web/app/data_state.js",
    "PFI/web/app/pages/stage4Subpages.js",
    "PFI/web/app/pages/stage5Subpages.js",
    "PFI/web/app/ux_state.js",
    "PFI/web/app/pages/home.js",
    "PFI/web/app/pages/reports.js",
    "PFI/web/app/shell.js",
)

P12_MISSING_EVENT_PATHS = frozenset(
    {
        "PFI/reports/pfi_v025/stage_1/phase_1_2/asset_identity.json",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/bfcache_mismatch.png",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/browser_validation.json",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/cache_audit.md",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/cache_headers.json",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/changed_files.txt",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/playwright_trace.zip",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/privacy_scan.txt",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/risk_and_rollback.md",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/service_worker_audit.md",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/streamlit_cache_policy.json",
        "PFI/reports/pfi_v025/stage_1/phase_1_2/terminal.log",
        "PFI/web/tests/v025/stage1_release_identity.test.mjs",
    }
)
P12_CORRECTION_EVENT_ID = "EVENT-20260713-PFI-V025-S1-P12-FILES-COVERAGE-CORRECTION"
P12_CORRECTION_ID = "PFI-V025-S1-P12-EVENT-COVERAGE-CORRECTION"
P12_PHASE_PATH_LIST_SHA256 = "85e4215e3970f2f83eeeadc53278f4e8c96a6ab226f8a285e9d3421a6d2c8112"
P12_MISSING_PATH_LIST_SHA256 = "698c078de406f5304ab620986368f9086bdf395bdb81bedd14f69f199c42d5a1"

REQUIRED_BROWSER_CHECKS = frozenset(
    {
        "official_shell_contract_verified",
        "frontend_source_set_exact_14",
        "frontend_source_bytes_match",
        "frontend_bundle_hash_recomputed",
        "frontend_bundle_hash_cross_surface_match",
        "frontend_modules_executed",
        "three_loopback_endpoints_owned",
        "fresh_profile_initially_empty",
        "manifest_api_real",
        "cache_policy_api_real",
        "read_model_status_api_real",
        "read_model_status_drives_ui",
        "running_backend_header_verified",
        "ordinary_reload_revalidated",
        "cache_cleared_reload_revalidated",
        "back_forward_revalidated",
        "pageshow_real_observed",
        "pageshow_persisted_guard_verified",
        "service_worker_and_cache_storage_empty",
        "legacy_query_official_isolated_verified",
        "primary_route_matrix_verified",
        "primary_route_identity_verified",
        "primary_route_visible_dom_privacy_verified",
        "primary_route_live_controls_verified",
        "isolated_fx_badge_not_loaded_verified",
        "visible_release_identity_chip_verified",
        "complete_release_identity_details_verified",
        "accessibility_tree_captured",
        "accessibility_contract_verified",
        "network_allowlist_exact",
        "no_console_page_request_http_ws_errors",
        "isolated_empty_runtime_verified",
        "isolated_candidate_availability_truthful",
        "visible_dom_privacy_verified",
        "no_private_runtime_leakage",
        "screenshot_bracketed_by_identical_state",
    }
)
PRIMARY_ROUTE_IDENTITIES = (
    ("/home", "home"),
    ("/accounts", "accounts"),
    ("/ledger", "ledger"),
    ("/investment", "investment"),
    ("/consumption", "consumption"),
    ("/sources-upload", "sync"),
    ("/review", "recommendations"),
    ("/reports", "insights"),
    ("/market-research", "market_research"),
    ("/settings", "settings"),
)
ROUTE_AUDIT_KEYS = frozenset(
    {
        "route_visit_count",
        "route_alias_sha256",
        "workspace_sha256",
        "active_route_match_count",
        "identity_match_count",
        "identity_field_visible_count",
        "visible_dom_safe_count",
        "live_control_safe_count",
        "isolated_fx_badge_safe_count",
        "official_shell_safe_count",
        "failed_check_count",
        "visible_text_sha256",
        "full_html_sha256",
        "visible_dom_finding_count",
        "visible_control_count",
        "sensitive_control_count",
        "live_control_finding_count",
        "live_control_structure_sha256",
        "release_identity_sha256",
        "fx_badge_sha256",
    }
)
REQUIRED_API_HEADERS = {
    "X-PFI-Running-Backend-SHA256",
    "X-PFI-Release-Manifest-SHA256",
    "X-PFI-Streamlit-Cache-Key",
    "X-PFI-Read-Model-SHA256",
    "X-PFI-Data-Boundary",
}
REVIEW_LANES = {
    "core_implementation",
    "roadmap_acceptance",
    "evidence_governance_privacy",
}
HEX64 = re.compile(r"^[0-9a-f]{64}$")


def run(*args: str, input_bytes: bytes | None = None, check: bool = True) -> bytes:
    result = subprocess.run(
        args,
        cwd=REPO_ROOT,
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {' '.join(args)}\n"
            f"stdout={result.stdout.decode(errors='replace')}\n"
            f"stderr={result.stderr.decode(errors='replace')}"
        )
    return result.stdout


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def stable_json_sha256(value: Any) -> str:
    return sha256_bytes(
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    )


def repo_bytes(path: str, candidate: str | None) -> bytes:
    if candidate:
        return run("git", "show", f"{candidate}:{path}")
    return (REPO_ROOT / path).read_bytes()


def repo_text(path: str, candidate: str | None) -> str:
    return repo_bytes(path, candidate).decode("utf-8")


def repo_json(path: str, candidate: str | None) -> dict[str, Any]:
    payload = json.loads(repo_text(path, candidate))
    assert isinstance(payload, dict), path
    return payload


def git_show_bytes(commit: str, path: str) -> bytes:
    return run("git", "show", f"{commit}:{path}")


def full_commit(ref: str) -> str:
    return run("git", "rev-parse", f"{ref}^{{commit}}").decode().strip()


def commit_parents(commit: str) -> list[str]:
    values = run("git", "rev-list", "--parents", "-n", "1", commit).decode().split()
    assert values and values[0] == commit
    return values[1:]


def common_dir() -> Path:
    raw = Path(run("git", "rev-parse", "--git-common-dir").decode().strip())
    return raw.resolve() if raw.is_absolute() else (REPO_ROOT / raw).resolve()


def path_list_sha256(paths: Iterable[str]) -> str:
    payload = "".join(f"{path}\n" for path in sorted(paths)).encode("utf-8")
    return sha256_bytes(payload)


def reviewable_payload_sha256(paths: Iterable[str], candidate: str | None) -> str:
    reviewable_paths = sorted(set(paths) - set(PREBINDING_REVIEW_EXCLUDED_PATHS))
    records = [
        f"{path}\0{sha256_bytes(repo_bytes(path, candidate))}\n".encode("utf-8")
        for path in reviewable_paths
    ]
    return sha256_bytes(b"".join(records))


def safe_external_path(relative: str) -> Path:
    pure = PurePosixPath(relative)
    assert pure.as_posix() == relative and not pure.is_absolute() and ".." not in pure.parts
    root = common_dir()
    path = root
    for part in pure.parts:
        path = path / part
        assert not path.is_symlink(), path
    resolved = path.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise AssertionError("external review path escaped the Git common directory") from error
    return resolved


def load_external_json(relative: str, expected_sha256: str) -> dict[str, Any]:
    path = safe_external_path(relative)
    assert path.is_file() and not path.is_symlink(), path
    raw = path.read_bytes()
    assert sha256_bytes(raw) == expected_sha256, path
    payload = json.loads(raw)
    assert isinstance(payload, dict), path
    return payload


def split_nul(payload: bytes) -> list[str]:
    if not payload:
        return []
    assert payload.endswith(b"\0")
    return payload[:-1].decode("utf-8").split("\0")


def diff_paths(base: str, candidate: str | None) -> list[str]:
    if candidate:
        return sorted(
            split_nul(
                run("git", "diff", "--no-renames", "--name-only", "-z", f"{base}..{candidate}")
            )
        )
    tracked = split_nul(run("git", "diff", "--no-renames", "--name-only", "-z", base))
    untracked = split_nul(run("git", "ls-files", "--others", "--exclude-standard", "-z"))
    return sorted(set([*tracked, *untracked]))


def diff_status(base: str, candidate: str) -> dict[str, str]:
    result: dict[str, str] = {}
    fields = split_nul(
        run("git", "diff", "--no-renames", "--name-status", "-z", f"{base}..{candidate}")
    )
    assert len(fields) % 2 == 0
    for index in range(0, len(fields), 2):
        status, path = fields[index : index + 2]
        assert status in {"A", "M", "D"}, (status, path)
        result[path] = status
    return result


PRIVACY_EXACT_TEST_FIXTURES = {
    "PFI/tests/test_v025_stage1_isolated_app_acceptance.py": (
        b'Path("/private/' + b'tmp/unused")',
    ),
}


def whole_review_added_text_bytes(path: str, candidate: str | None) -> bytes:
    """Return only text bytes introduced since the pinned whole-review base.

    Historical governance files are append-only and already contain local-path
    evidence from older releases.  Re-scanning their complete current bytes
    would both misattribute baseline facts to this review and require an
    illegal history rewrite.  The privacy gate therefore scans every added
    line from ``WHOLE_REVIEW_BASE`` through the binding candidate, while binary
    evidence is verified by its dedicated structural and visual gates.
    """

    if candidate:
        diff = run(
            "git",
            "diff",
            "--no-ext-diff",
            "--no-renames",
            "--unified=0",
            f"{WHOLE_REVIEW_BASE}..{candidate}",
            "--",
            path,
        )
    else:
        untracked = set(
            split_nul(run("git", "ls-files", "--others", "--exclude-standard", "-z"))
        )
        if path in untracked:
            return repo_bytes(path, None)
        diff = run(
            "git",
            "diff",
            "--no-ext-diff",
            "--no-renames",
            "--unified=0",
            WHOLE_REVIEW_BASE,
            "--",
            path,
        )
    payload = b"".join(
        line[1:]
        for line in diff.splitlines(keepends=True)
        if line.startswith(b"+") and not line.startswith(b"+++")
    )
    for fixture in PRIVACY_EXACT_TEST_FIXTURES.get(path, ()):
        payload = payload.replace(fixture, b'Path("${EXACT_TEST_FIXTURE_TMP}")')
    return payload


def resolve_candidate(requested: str | None) -> str | None:
    if requested:
        return full_commit(requested)
    head = full_commit("HEAD")
    if head == REMEDIATION_CONTENT_COMMIT:
        return None
    if commit_parents(head) == [REMEDIATION_CONTENT_COMMIT]:
        assert run("git", "status", "--porcelain") == b""
        return head
    raise AssertionError(
        "HEAD must be the remediation content commit or its clean direct binding successor"
    )


def parse_yaml(text: str) -> Any:
    ruby = (
        'require "yaml"; require "json"; '
        "print JSON.generate(YAML.safe_load(STDIN.read, permitted_classes: [], "
        "permitted_symbols: [], aliases: true))"
    )
    return json.loads(
        subprocess.check_output(
            ["ruby", "-e", ruby], input=text, text=True, cwd=REPO_ROOT
        )
    )


def assert_hex(value: Any, label: str) -> str:
    assert isinstance(value, str) and HEX64.fullmatch(value), label
    return value


def assert_all_true(mapping: Any, required: Iterable[str], label: str) -> None:
    assert isinstance(mapping, dict), label
    missing = set(required) - set(mapping)
    assert not missing, (label, "missing", sorted(missing))
    failures = {key: mapping[key] for key in required if mapping[key] is not True}
    assert not failures, (label, failures)


def frontend_source_records(commit: str) -> list[dict[str, Any]]:
    index_path = "PFI/web/index.html"
    source = git_show_bytes(commit, index_path).decode("utf-8")
    canonical, count = re.subn(
        r'(<script\s+type="application/json"\s+id="pfi-release-manifest">).*?(</script>)',
        r"\1{}\2",
        source,
        count=1,
        flags=re.DOTALL,
    )
    assert count == 1
    script_refs = re.findall(r'<script\s+src="\./([^"?#]+)"', source)
    paths = {
        index_path,
        "PFI/web/styles/tokens.css",
        "PFI/web/styles.css",
        *(f"PFI/web/{ref}" for ref in script_refs),
    }
    assert tuple(sorted(paths)) == tuple(sorted(FRONTEND_FILES))
    records: list[dict[str, Any]] = []
    for path in FRONTEND_FILES:
        payload = canonical.encode() if path == index_path else git_show_bytes(commit, path)
        records.append(
            {"path": path, "sha256": sha256_bytes(payload), "bytes": len(payload)}
        )
    return records


def frontend_identity(commit: str) -> tuple[str, list[str]]:
    source_records = frontend_source_records(commit)
    hash_records = [
        f"{record['path']}\0{record['sha256']}\n".encode()
        for record in sorted(source_records, key=lambda item: item["path"])
    ]
    return sha256_bytes(b"".join(hash_records)), [item["path"] for item in source_records]


def backend_identity(commit: str) -> tuple[str, list[str]]:
    records = [
        f"{path}\0{sha256_bytes(git_show_bytes(commit, path))}\n".encode()
        for path in BACKEND_FILES
    ]
    return sha256_bytes(b"".join(records)), list(BACKEND_FILES)


def embedded_manifest(candidate: str | None) -> dict[str, Any]:
    match = re.search(
        r'<script\s+type="application/json"\s+id="pfi-release-manifest">(.*?)</script>',
        repo_text("PFI/web/index.html", candidate),
        flags=re.DOTALL,
    )
    assert match
    payload = json.loads(match.group(1))
    assert isinstance(payload, dict)
    return payload


def historical_attestation_path(phase: dict[str, Any]) -> Path:
    phase_token = str(phase["phase"]).replace(".", "_")
    return safe_external_path(
        "codex-review/pfi-v025/stage_1/"
        f"phase_{phase_token}/{phase['binding']}/{phase['attestation_name']}"
    )


def verify_historical_phases() -> dict[str, str]:
    results: dict[str, str] = {}
    for phase in PHASES:
        phase_id = str(phase["phase"])
        base = full_commit(str(phase["base"]))
        content = full_commit(str(phase["content"]))
        binding = full_commit(str(phase["binding"]))
        assert run("git", "merge-base", "--is-ancestor", base, content) == b""
        assert commit_parents(binding) == [content]

        evidence_raw = git_show_bytes(binding, str(phase["evidence"]))
        verifier_raw = git_show_bytes(binding, str(phase["verifier"]))
        changed_ref = str(phase["evidence"]).replace("evidence.json", "changed_files.txt")
        changed_raw = git_show_bytes(binding, changed_ref)
        assert sha256_bytes(evidence_raw) == phase["evidence_sha256"]
        assert sha256_bytes(verifier_raw) == phase["verifier_sha256"]
        assert sha256_bytes(changed_raw) == phase["changed_files_sha256"]

        evidence = json.loads(evidence_raw)
        assert evidence["stage"] == 1 and str(evidence["phase"]) == phase_id
        assert evidence["status"] == "candidate_pass"
        assert evidence["release_content_commit"] == content
        actual_paths = diff_paths(base, binding)
        assert sorted(evidence["changed_files"]) == actual_paths
        assert sorted(changed_raw.decode().splitlines()) == actual_paths
        assert evidence["push_performed"] is False
        assert evidence["production_accepted"] is False
        assert evidence["final_human_acceptance"] is False

        attestation_path = historical_attestation_path(phase)
        assert attestation_path.is_file(), attestation_path
        attestation_raw = attestation_path.read_bytes()
        assert sha256_bytes(attestation_raw) == phase["attestation_sha256"]
        attestation = json.loads(attestation_raw)
        assert attestation["release_content_commit"] == content
        assert attestation[str(phase["binding_field"])] == binding
        assert attestation["evidence_sha256"] == phase["evidence_sha256"]
        assert attestation["push_performed"] is False
        assert attestation["production_accepted"] is False
        assert attestation["final_human_acceptance"] is False
        findings = attestation.get("review_findings_after_remediation")
        assert findings == {"critical": 0, "important": 0, "minor": 0}
        results[phase_id] = "PASS"

    assert PHASES[0]["base"] == STAGE_BASE
    assert PHASES[1]["base"] == PHASES[0]["binding"]
    assert PHASES[2]["base"] == PHASES[1]["binding"]
    assert PHASES[2]["binding"] == WHOLE_REVIEW_BASE
    return results


def verify_source_and_authorization(candidate: str | None) -> dict[str, Any]:
    assert ROADMAP.is_file() and sha256_bytes(ROADMAP.read_bytes()) == ROADMAP_SHA256
    assert TASK_PACK.is_file() and sha256_bytes(TASK_PACK.read_bytes()) == TASK_PACK_SHA256
    active_ref = "PFI/config/pfi_v025_active_requirements.json"
    auth_ref = "PFI/docs/pfi_v025/stage_0/interim_stage_transition_authorization.json"
    assert sha256_bytes(repo_bytes(active_ref, candidate)) == ACTIVE_REQUIREMENTS_SHA256
    assert sha256_bytes(repo_bytes(auth_ref, candidate)) == STANDING_AUTHORIZATION_SHA256
    authorization = repo_json(auth_ref, candidate)
    assert authorization["authorization_id"] == AUTHORIZATION_ID
    assert authorization["status"] == "active"
    assert authorization["no_reprompt_before_final"] is True
    assert "1->2" in authorization["authorized_transitions"]
    assert authorization["controls"] == {
        "revocable_by_later_explicit_user_decision": True,
        "waives_technical_gates": False,
        "waives_independent_review": False,
        "waives_evidence_requirements": False,
        "waives_privacy_controls": False,
        "waives_one_phase_per_run": False,
        "authorizes_intermediate_push": False,
        "authorizes_intermediate_app_install": False,
    }
    boundary = authorization["final_acceptance_boundary"]
    assert boundary["is_human_release_acceptance"] is False
    assert boundary["human_acceptance_json_created"] is False
    assert boundary["final_stage_12_human_acceptance_required"] is True
    assert boundary["v025_production_accepted"] is False
    return authorization


def verify_path_sets(candidate: str | None, evidence: dict[str, Any]) -> tuple[list[str], list[str]]:
    assert full_commit(INITIAL_REMEDIATION_CONTENT_COMMIT) == INITIAL_REMEDIATION_CONTENT_COMMIT
    assert full_commit(SECOND_REMEDIATION_CONTENT_COMMIT) == SECOND_REMEDIATION_CONTENT_COMMIT
    assert full_commit(THIRD_REMEDIATION_CONTENT_COMMIT) == THIRD_REMEDIATION_CONTENT_COMMIT
    assert full_commit(FOURTH_REMEDIATION_CONTENT_COMMIT) == FOURTH_REMEDIATION_CONTENT_COMMIT
    assert full_commit(INTERMEDIATE_REMEDIATION_CONTENT_COMMIT) == INTERMEDIATE_REMEDIATION_CONTENT_COMMIT
    assert full_commit(FINANCIAL_CONTROL_CONTENT_COMMIT) == FINANCIAL_CONTROL_CONTENT_COMMIT
    assert full_commit(RAW_MANIFEST_CONTENT_COMMIT) == RAW_MANIFEST_CONTENT_COMMIT
    assert full_commit(STRUCTURAL_TRACE_CONTENT_COMMIT) == STRUCTURAL_TRACE_CONTENT_COMMIT
    assert full_commit(LIVE_PRIVACY_CONTENT_COMMIT) == LIVE_PRIVACY_CONTENT_COMMIT
    assert full_commit(ACCESSIBILITY_CONTENT_COMMIT) == ACCESSIBILITY_CONTENT_COMMIT
    assert full_commit(PREVIOUS_REMEDIATION_CONTENT_COMMIT) == PREVIOUS_REMEDIATION_CONTENT_COMMIT
    assert full_commit(C12_REMEDIATION_CONTENT_COMMIT) == C12_REMEDIATION_CONTENT_COMMIT
    assert full_commit(C13_REMEDIATION_CONTENT_COMMIT) == C13_REMEDIATION_CONTENT_COMMIT
    assert full_commit(C14_REMEDIATION_CONTENT_COMMIT) == C14_REMEDIATION_CONTENT_COMMIT
    assert full_commit(C15_REMEDIATION_CONTENT_COMMIT) == C15_REMEDIATION_CONTENT_COMMIT
    assert full_commit(C16_REMEDIATION_CONTENT_COMMIT) == C16_REMEDIATION_CONTENT_COMMIT
    assert full_commit(C17_REMEDIATION_CONTENT_COMMIT) == C17_REMEDIATION_CONTENT_COMMIT
    assert full_commit(C18_REMEDIATION_CONTENT_COMMIT) == C18_REMEDIATION_CONTENT_COMMIT
    assert full_commit(C19_REMEDIATION_CONTENT_COMMIT) == C19_REMEDIATION_CONTENT_COMMIT
    assert full_commit(REMEDIATION_CONTENT_COMMIT) == REMEDIATION_CONTENT_COMMIT
    assert commit_parents(INITIAL_REMEDIATION_CONTENT_COMMIT) == [WHOLE_REVIEW_BASE]
    assert commit_parents(SECOND_REMEDIATION_CONTENT_COMMIT) == [INITIAL_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(THIRD_REMEDIATION_CONTENT_COMMIT) == [SECOND_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(FOURTH_REMEDIATION_CONTENT_COMMIT) == [THIRD_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(INTERMEDIATE_REMEDIATION_CONTENT_COMMIT) == [FOURTH_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(FINANCIAL_CONTROL_CONTENT_COMMIT) == [INTERMEDIATE_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(RAW_MANIFEST_CONTENT_COMMIT) == [FINANCIAL_CONTROL_CONTENT_COMMIT]
    assert commit_parents(STRUCTURAL_TRACE_CONTENT_COMMIT) == [RAW_MANIFEST_CONTENT_COMMIT]
    assert commit_parents(LIVE_PRIVACY_CONTENT_COMMIT) == [STRUCTURAL_TRACE_CONTENT_COMMIT]
    assert commit_parents(ACCESSIBILITY_CONTENT_COMMIT) == [LIVE_PRIVACY_CONTENT_COMMIT]
    assert commit_parents(PREVIOUS_REMEDIATION_CONTENT_COMMIT) == [ACCESSIBILITY_CONTENT_COMMIT]
    assert commit_parents(C12_REMEDIATION_CONTENT_COMMIT) == [PREVIOUS_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(C13_REMEDIATION_CONTENT_COMMIT) == [C12_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(C14_REMEDIATION_CONTENT_COMMIT) == [C13_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(C15_REMEDIATION_CONTENT_COMMIT) == [C14_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(C16_REMEDIATION_CONTENT_COMMIT) == [C15_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(C17_REMEDIATION_CONTENT_COMMIT) == [C16_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(C18_REMEDIATION_CONTENT_COMMIT) == [C17_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(C19_REMEDIATION_CONTENT_COMMIT) == [C18_REMEDIATION_CONTENT_COMMIT]
    assert commit_parents(REMEDIATION_CONTENT_COMMIT) == [C19_REMEDIATION_CONTENT_COMMIT]
    edge_union: set[str] = set()
    for edge_base, edge_head, expected_status in CONTENT_EDGE_PATH_STATUS:
        assert commit_parents(edge_head) == [edge_base]
        assert diff_status(edge_base, edge_head) == expected_status
        assert set(expected_status) <= set(CONTENT_PATHS)
        assert all(path.startswith("PFI/") for path in expected_status)
        edge_union.update(expected_status)
    assert edge_union == set(CONTENT_PATHS)
    assert diff_status(WHOLE_REVIEW_BASE, REMEDIATION_CONTENT_COMMIT) == CONTENT_PATH_STATUS

    binding_manifest = sorted(
        line
        for line in repo_text(f"{REVIEW_DIR}/changed_files.txt", candidate).splitlines()
        if line
    )
    assert len(binding_manifest) == len(set(binding_manifest))
    assert all(PurePosixPath(path).as_posix() == path and path.startswith("PFI/") for path in binding_manifest)
    actual_binding = diff_paths(REMEDIATION_CONTENT_COMMIT, candidate)
    assert binding_manifest == actual_binding
    assert REQUIRED_BINDING_PATHS <= set(actual_binding)
    assert set(actual_binding) <= ALLOWED_BINDING_PATHS
    sync_companions = set(actual_binding) & SYNC_COMPANION_PATHS
    assert sync_companions in (set(), set(SYNC_COMPANION_PATHS))
    assert all(path.startswith("PFI/") for path in actual_binding)

    actual_whole = diff_paths(WHOLE_REVIEW_BASE, candidate)
    assert set(actual_whole) == set(CONTENT_PATHS) | set(actual_binding)
    assert sorted(evidence["content_changed_files"]) == list(CONTENT_PATHS)
    assert sorted(evidence["binding_changed_files"]) == actual_binding
    assert sorted(evidence["whole_stage_changed_files"]) == actual_whole
    assert sorted(evidence["changed_files"]) == actual_binding
    assert sorted(evidence["governance_sync_companions"]) == sorted(sync_companions)
    assert evidence["governance_sync_companions_change_behavior"] is False

    if candidate:
        assert commit_parents(candidate) == [REMEDIATION_CONTENT_COMMIT]
        assert run("git", "status", "--porcelain") == b""
    else:
        assert full_commit("HEAD") == REMEDIATION_CONTENT_COMMIT
    return actual_binding, actual_whole


def verify_p12_append_only_correction(candidate: str | None) -> dict[str, Any]:
    ref = "PFI/docs/governance/development_events.jsonl"
    historical = git_show_bytes(WHOLE_REVIEW_BASE, ref)
    current = repo_bytes(ref, candidate)
    assert current.startswith(historical)
    actual_phase_paths = set(diff_paths(str(PHASES[1]["base"]), str(PHASES[1]["binding"])))
    historical_events = [
        json.loads(line) for line in historical.decode().splitlines() if line.strip()
    ]
    prior_event_paths: set[str] = set()
    for historical_event in historical_events:
        if historical_event.get("acceptance_id") == "ACC-PFI-V025-S1-P12-CACHE-GOVERNANCE":
            prior_event_paths.update(historical_event.get("files_changed") or [])
    derived_missing_paths = actual_phase_paths - prior_event_paths
    assert len(actual_phase_paths) == 36
    assert len(prior_event_paths) == 23
    assert derived_missing_paths == P12_MISSING_EVENT_PATHS
    assert path_list_sha256(actual_phase_paths) == P12_PHASE_PATH_LIST_SHA256
    assert path_list_sha256(derived_missing_paths) == P12_MISSING_PATH_LIST_SHA256
    appended = current[len(historical) :]
    assert appended.startswith(b"\n") or historical.endswith(b"\n")
    events = [json.loads(line) for line in appended.decode().splitlines() if line.strip()]
    corrections = []
    for event in events:
        corrected_id = (
            event.get("correction_for_event_id")
            or event.get("corrected_event_id")
            or event.get("corrects_event_id")
        )
        if corrected_id == "EVENT-20260712-PFI-V025-S1-P12":
            corrections.append(event)
    assert len(corrections) == 1
    correction = corrections[0]
    assert correction["event_id"] == P12_CORRECTION_EVENT_ID
    assert correction["correction_id"] == P12_CORRECTION_ID
    assert correction["correction_for_event_id"] == "EVENT-20260712-PFI-V025-S1-P12"
    assert correction["iteration_id"] == "ITER-20260712-PFI-V025-S1-P12"
    assert correction["acceptance_id"] == "ACC-PFI-V025-S1-P12-CACHE-GOVERNANCE"
    assert correction["contract_id"] == "PFI-V025-STAGE1-PHASE12-CACHE-GOVERNANCE"
    assert correction["task_ids"] == ["S1-P2-T1", "S1-P2-T2", "S1-P2-T3", "S1-P2-T4"]
    assert correction["change_type"] == "historical_event_files_changed_coverage_correction"
    assert correction["coverage_semantics"] == "historical_phase_range_coverage_only_not_current_file_rewrite"
    assert correction["historical_scope_base"] == PHASES[1]["base"]
    assert correction["historical_scope_head"] == PHASES[1]["binding"]
    assert correction["actual_changed_file_count"] == 36
    assert correction["prior_event_union_count"] == 23
    assert correction["missing_file_count"] == 13
    assert correction["actual_changed_files_sha256"] == P12_PHASE_PATH_LIST_SHA256
    assert correction["missing_files_sha256"] == P12_MISSING_PATH_LIST_SHA256
    assert correction["historical_phase_range_coverage_only"] is True
    assert correction["current_files_rewritten_by_correction"] is False
    corrected_paths = correction["files_changed"]
    assert set(corrected_paths) == derived_missing_paths
    assert len(corrected_paths) == 13
    assert correction["missing_files_added"] == corrected_paths
    assert correction.get("fact_level") == "VERIFIED"
    assert correction.get("push_performed") is False
    assert correction.get("app_install_performed") is False
    assert correction.get("production_accepted") is False
    assert correction.get("runtime_behavior_changed_by_correction") is False
    assert correction.get("model_ids_changed") == []
    assert correction.get("formula_ids_changed") == []
    assert correction.get("parameter_ids_changed") == []
    return correction


def verify_release_identity(candidate: str | None) -> dict[str, Any]:
    candidate_commit = candidate or REMEDIATION_CONTENT_COMMIT
    manifest_raw = repo_bytes("PFI/config/release_manifest.json", candidate)
    manifest = json.loads(manifest_raw)
    embedded = embedded_manifest(candidate)
    assert manifest == embedded
    with zipfile.ZipFile(TASK_PACK) as archive:
        assert archive.testzip() is None
        manifest_schema = json.loads(
            archive.read("PFI_v0.2.5_TaskPack/schemas/release_manifest.schema.json")
        )
    Draft202012Validator(manifest_schema, format_checker=FormatChecker()).validate(manifest)
    assert manifest["product"] == "PFI"
    assert manifest["version"] == "v0.2.5"
    assert manifest["build_id"] == "pfi-v025-s1p1-20260712.1"
    assert manifest["app_short_version"] == "0.2.5"
    assert manifest["app_build_version"] == "20260712.1"
    assert manifest["data_schema_version"] == "PFIV021HoldingsPersistenceV1"
    assert manifest["formula_version"] == "v0.2.3"
    assert manifest["parameter_version"] == "v0.2.2"
    assert manifest["generated_at"] == "2026-07-13T01:19:06Z"
    assert manifest["git_commit"] == REMEDIATION_CONTENT_COMMIT
    info_plist = plistlib.loads(
        git_show_bytes(REMEDIATION_CONTENT_COMMIT, "PFI/macos/PFI.app/Contents/Info.plist")
    )
    assert info_plist["CFBundleShortVersionString"] == manifest["app_short_version"]
    assert info_plist["CFBundleVersion"] == manifest["app_build_version"]

    content_frontend, frontend_files = frontend_identity(REMEDIATION_CONTENT_COMMIT)
    candidate_frontend, candidate_frontend_files = frontend_identity(candidate_commit)
    content_backend, backend_files = backend_identity(REMEDIATION_CONTENT_COMMIT)
    candidate_backend, candidate_backend_files = backend_identity(candidate_commit)
    assert frontend_files == candidate_frontend_files == list(FRONTEND_FILES)
    assert backend_files == candidate_backend_files == list(BACKEND_FILES)
    assert content_frontend == candidate_frontend == manifest["frontend_bundle_hash"]
    assert content_backend == candidate_backend == manifest["backend_build_hash"]
    return {
        "manifest": manifest,
        "manifest_sha256": sha256_bytes(manifest_raw),
        "frontend_files": frontend_files,
        "backend_files": backend_files,
    }


def verify_browser_and_runtime(candidate: str | None, identity: dict[str, Any]) -> dict[str, Any]:
    browser = repo_json(f"{REVIEW_DIR}/browser_validation.json", candidate)
    assert browser["schema"] == "PFIV025Stage1WholeReviewBrowserValidationV1"
    assert browser["acceptance_id"] == ACCEPTANCE_ID
    assert browser["candidate_mode"] is True
    assert browser["launchservices_started_runtime"] is True
    assert browser["canonical_app_install"] is False
    assert browser["checkout_commit"] == REMEDIATION_CONTENT_COMMIT
    assert browser["git_commit"] == REMEDIATION_CONTENT_COMMIT
    assert browser["manifest_sha256"] == identity["manifest_sha256"]
    assert browser["frontend_bundle_hash"] == identity["manifest"]["frontend_bundle_hash"]
    assert browser["backend_build_hash"] == identity["manifest"]["backend_build_hash"]
    assert browser["process_group_member_count"] == 3
    assert browser["listener_endpoint_count"] == 3
    assert browser["requested_port_count"] == 2
    assert len(set(browser["requested_ports"])) == 2
    assert not ({8501, 8502, 8766} & set(browser["requested_ports"]))
    assert_all_true(browser["checks"], REQUIRED_BROWSER_CHECKS, "browser checks")
    for key in (
        "console_error_count",
        "page_error_count",
        "request_failure_count",
        "http_error_count",
        "unexpected_host_count",
        "websocket_error_count",
    ):
        assert browser[key] == 0, key
    assert browser["pageshow_observation_count"] > 0
    assert browser["websocket_count"] > 0
    for path in ("/api/release-manifest", "/api/release-cache-policy", "/api/read-model-status"):
        assert browser["api_response_counts"][path] > 0

    legacy_audit = browser["legacy_query_audit"]
    assert set(legacy_audit) == {
        "visit_count",
        "url_sha256",
        "query_value_sha256",
        "query_value_match_count",
    }
    assert legacy_audit["visit_count"] == legacy_audit["query_value_match_count"] == 1
    assert_hex(legacy_audit["url_sha256"], "legacy query URL hash")
    assert legacy_audit["query_value_sha256"] == sha256_bytes(b"1")

    route_audits = browser["primary_route_audits"]
    assert browser["primary_route_audit_count"] == len(route_audits) == len(PRIMARY_ROUTE_IDENTITIES)
    expected_identity_surface_sha256 = stable_json_sha256(
        {
            "chip_visible": True,
            "details_visible": True,
            "details_panel_visible": True,
            "complete": True,
            "visible_field_count": 5,
            "chip_text": "发布身份详情",
            "version": identity["manifest"]["version"],
            "build_id": identity["manifest"]["build_id"],
            "git_commit": identity["manifest"]["git_commit"],
            "frontend_bundle_hash": identity["manifest"]["frontend_bundle_hash"],
            "backend_build_hash": identity["manifest"]["backend_build_hash"],
        }
    )
    expected_fx_badge_sha256 = stable_json_sha256(
        {
            "text": "AUD/CNY=未加载",
            "source_label": "AUD/CNY=未加载",
            "cache_state": "not_loaded",
            "effective_date": "",
        }
    )
    for audit, (route_alias, workspace) in zip(route_audits, PRIMARY_ROUTE_IDENTITIES, strict=True):
        assert set(audit) == ROUTE_AUDIT_KEYS
        assert all(key.endswith(("_count", "_sha256")) for key in audit)
        assert audit["route_alias_sha256"] == sha256_bytes(route_alias.encode())
        assert audit["workspace_sha256"] == sha256_bytes(workspace.encode())
        for key in (
            "route_visit_count",
            "active_route_match_count",
            "identity_match_count",
            "visible_dom_safe_count",
            "live_control_safe_count",
            "isolated_fx_badge_safe_count",
            "official_shell_safe_count",
        ):
            assert audit[key] == 1, (route_alias, key)
        assert audit["identity_field_visible_count"] == 5, route_alias
        for key in (
            "failed_check_count",
            "visible_dom_finding_count",
            "live_control_finding_count",
        ):
            assert audit[key] == 0, (route_alias, key)
        assert audit["visible_control_count"] >= audit["sensitive_control_count"] >= 0
        for key in (
            "visible_text_sha256",
            "full_html_sha256",
            "live_control_structure_sha256",
            "release_identity_sha256",
            "fx_badge_sha256",
        ):
            assert_hex(audit[key], f"{route_alias} {key}")
        assert audit["release_identity_sha256"] == expected_identity_surface_sha256
        assert audit["fx_badge_sha256"] == expected_fx_badge_sha256

    accessibility = repo_json(f"{REVIEW_DIR}/accessibility_tree.json", candidate)
    assert accessibility["schema"] == "PFIV025Stage1WholeReviewAccessibilityTreeV1"
    assert accessibility["source"] == "Accessibility.getFullAXTree"
    assert accessibility["frame_discovery_source"] == "Page.getFrameTree"
    assert accessibility["frame_url"].startswith("about:srcdoc")
    assert accessibility["frame_url_sha256"] == sha256_bytes(accessibility["frame_url"].encode())
    assert_hex(accessibility["selected_frame_id_sha256"], "selected srcdoc frame ID hash")
    assert accessibility["srcdoc_frame_candidate_count"] > 0
    assert accessibility["node_count"] == len(accessibility["nodes"]) > 0
    ax = accessibility["ax_contract"]
    assert ax["h1_exact_match_count"] > 0
    assert ax["primary_navigation_named_count"] == 10
    assert ax["named_focusable_count"] >= 10
    assert ax["unnamed_focusable_count"] == 0
    interactive_roles = {
        "button",
        "link",
        "textbox",
        "searchbox",
        "combobox",
        "checkbox",
        "radio",
        "switch",
        "slider",
        "spinbutton",
        "menuitem",
        "tab",
        "listbox",
        "option",
        "treeitem",
    }
    interactive_focusable = [
        node
        for node in accessibility["nodes"]
        if node["focusable"] and not node["ignored"] and node["role"] in interactive_roles
    ]
    assert len(interactive_focusable) == ax["named_focusable_count"]
    assert all(node["name"] for node in interactive_focusable)
    dom = accessibility["official_dom_contract"]
    assert dom["shell_schema"] == "PFIOSWebShellContractV1"
    assert dom["h1_text"] == "首页总览 · 财务状态"
    assert len(dom["primary_entries"]) == 10
    assert dom["duplicate_id_count"] == 0
    assert dom["focusable_without_name_count"] == 0
    assert all(dom[key] is True for key in ("header_present", "navigation_present", "main_present", "skip_link_present"))

    frontend = repo_json(f"{REVIEW_DIR}/frontend_source_identity.json", candidate)
    assert frontend["schema"] == "PFIV025Stage1WholeReviewFrontendSourceIdentityV1"
    disk_records = frontend["disk"]["files"]
    assert frontend["disk"]["file_count"] == len(disk_records) == 15
    assert [record["path"] for record in disk_records] == identity["frontend_files"]
    assert disk_records == frontend_source_records(REMEDIATION_CONTENT_COMMIT)
    for record in disk_records:
        assert_hex(record["sha256"], f"frontend disk source {record['path']}")
        assert isinstance(record["bytes"], int) and record["bytes"] > 0
    browser_records = frontend["browser"]["files"]
    assert len(browser_records) == 13
    assert {record["path"] for record in browser_records} == set(identity["frontend_files"]) - {
        "PFI/web/index.html"
    }
    disk_by_path = {record["path"]: record for record in disk_records}
    for record in browser_records:
        assert_hex(record["sha256"], f"frontend browser source {record['path']}")
        assert isinstance(record["bytes"], int) and record["bytes"] > 0
        assert record == disk_by_path[record["path"]]
    assert frontend["browser"]["file_count_with_index"] == 15
    assert frontend["disk"]["sha256"] == frontend["browser"]["sha256"] == identity["manifest"]["frontend_bundle_hash"]

    runtime = repo_json(f"{REVIEW_DIR}/runtime_api_evidence.json", candidate)
    assert runtime["schema"] == "PFIV025Stage1WholeReviewRuntimeAPIEvidenceV1"
    assert set(runtime["required_headers"]) == REQUIRED_API_HEADERS
    assert runtime["runtime_api_port"] == browser["runtime_api_port"]
    assert runtime["initial_node_probe"]["blocked_post"]["status"] == 403
    for api_key in ("manifest", "policy", "read_model_status"):
        probe = runtime["initial_node_probe"][api_key]
        assert probe["status"] == 200
        assert probe["headers"]["x-pfi-running-backend-sha256"] == identity["manifest"]["backend_build_hash"]
    assert runtime["initial_node_probe"]["manifest"]["headers"]["x-pfi-release-manifest-sha256"] == identity["manifest_sha256"]

    privacy = repo_json(f"{REVIEW_DIR}/privacy_boundary.json", candidate)
    assert privacy["schema"] == "PFIV025Stage1WholeReviewPrivacyBoundaryV1"
    assert privacy["candidate_data_mode"] == "isolated_empty"
    assert privacy["write_api_status"] == 403
    assert privacy["checks"]["runtime_payloads_safe"] is True
    assert privacy["checks"]["visible_dom_safe"] is True
    assert privacy["checks"]["external_host_count"] == 0
    assert privacy["primary_route_audit_count"] == len(PRIMARY_ROUTE_IDENTITIES)
    assert privacy["primary_route_audits"] == route_audits
    visible_dom = privacy["visible_dom"]
    assert visible_dom["schema"] == "PFIV025Stage1VisibleDomPrivacyAuditV1"
    assert visible_dom["safe"] is True and visible_dom["finding_count"] == 0
    assert all(value == 0 for value in visible_dom["finding_counts"].values())
    assert_hex(visible_dom["visible_text_sha256"], "visible DOM text hash")
    assert_hex(visible_dom["full_html_sha256"], "visible DOM HTML hash")
    live_controls = visible_dom["live_form_control_audit"]
    assert live_controls["schema"] == "PFIV025Stage1LiveFormControlPrivacyAuditV1"
    assert live_controls["valid"] is True and live_controls["finding_count"] == 0
    assert live_controls["visible_control_count"] >= live_controls["sensitive_control_count"] >= 0
    assert_hex(live_controls["structure_sha256"], "live form-control structure hash")
    png_audits = privacy["png_visual_audits"]
    assert set(png_audits) == set(PNG_PRIVACY_PATHS)
    for artifact_key, artifact_path in PNG_PRIVACY_PATHS.items():
        png_audit = png_audits[artifact_key]
        assert png_audit["artifact_sha256"] == sha256_bytes(repo_bytes(artifact_path, candidate))
        assert png_audit["inspected"] is True
        assert png_audit["inspection_method"] == "visual_inspection_plus_independent_review"
        assert png_audit["finding_counts"] == {
            "private_home_path": 0,
            "private_tmp_path": 0,
            "private_var_path": 0,
            "file_url": 0,
            "account_identifier": 0,
            "financial_amount": 0,
            "credential_or_secret": 0,
        }
    status = privacy["read_model_status"]
    assert status["source"]["storage_mode"] == "isolated_empty"
    assert all(item["value"] is None for item in status["core_metric_states"])

    for artifact_key, artifact in browser["artifacts"].items():
        path = f"{REVIEW_DIR}/{artifact['file']}"
        assert sha256_bytes(repo_bytes(path, candidate)) == artifact["sha256"], artifact_key
    verify_png(
        repo_bytes(f"{REVIEW_DIR}/browser_official_ui.png", candidate),
        "official UI screenshot",
    )
    verify_png(
        repo_bytes(f"{REVIEW_DIR}/browser_release_identity.png", candidate),
        "release identity screenshot",
    )
    return browser


def verify_candidate_cleanup(candidate: str | None) -> None:
    app = repo_json(f"{REVIEW_DIR}/candidate_app.json", candidate)
    assert app["checkout_commit"] == REMEDIATION_CONTENT_COMMIT
    assert app["canonical_app_install"] is False
    assert app["launchservices_runtime_verified"] is True
    assert app["runtime_api_ready"] is True
    assert app["process_group_verified"] is True and app["process_group_member_count"] == 3
    assert app["streamlit_listener_set_verified"] is True and app["streamlit_listener_count"] == 2
    assert app["listener_endpoint_set_verified"] is True and app["listener_endpoint_count"] == 3
    for key in (
        "process_tree_identity_unchanged_before_cleanup",
        "process_group_identity_unchanged_before_cleanup",
        "process_tree_cleanup_verified",
        "process_group_cleanup_verified",
        "listener_owner_port_set_unchanged_before_cleanup",
        "listener_endpoint_set_unchanged_before_cleanup",
        "runtime_process_cleanup_verified",
        "shutdown_monitor_stopped",
        "streamlit_port_released",
        "runtime_api_port_released",
        "heartbeat_port_released",
        "protected_metadata_unchanged",
    ):
        assert app[key] is True, key

    cleanup = repo_json(f"{REVIEW_DIR}/launchservices_cleanup.json", candidate)
    for key in (
        "cleanup_complete",
        "temp_root_deleted",
        "launchservices_registered",
        "launchservices_registration_verified",
        "launchservices_unregistered",
        "launchservices_post_unregister_absent",
        "launchservices_final_absent",
        "post_root_launchservices_absent",
        "registration_absent_after",
        "runtime_process_cleanup_verified",
        "process_tree_cleanup_verified",
        "process_group_cleanup_verified",
        "streamlit_port_released",
        "runtime_api_port_released",
        "heartbeat_port_released",
        "canonical_unchanged",
        "protected_metadata_unchanged",
        "git_status_unchanged",
        "finalization_tombstone_published",
    ):
        assert cleanup[key] is True, key
    assert cleanup["root_retained_for_retry"] is False

    entries = repo_json(f"{REVIEW_DIR}/entry_matrix.json", candidate)
    assert entries["canonical_unchanged"] is True
    assert entries["before"] == entries["after"]
    assert set(entries["before"]) == {"applications", "desktop", "downloads"}
    protected = repo_json(f"{REVIEW_DIR}/protected_metadata.json", candidate)
    assert protected["protected_metadata_unchanged"] is True
    assert protected["git_status_unchanged"] is True
    assert protected["before"] == protected["after"]

    capture_path = f"{REVIEW_DIR}/launchservices_open_capture.json"
    capture = repo_json(capture_path, candidate)
    assert set(capture) == {
        "schema",
        "tool",
        "action",
        "arguments_symbolic",
        "command_record",
        "command_record_sha256",
        "checkout_commit",
        "candidate_path_symbolic",
        "candidate_app_path_sha256",
        "candidate_app_json_sha256",
        "candidate_app_binding",
        "candidate_inspection",
        "launchservices_registration_verified",
        "ui_automation_used",
        "finder_used",
        "privacy",
    }
    assert capture["schema"] == "PFIV025Stage1LaunchServicesOpenCaptureV1"
    assert capture["tool"] == "/usr/bin/open"
    assert capture["action"] == "launch_new_instance"
    assert capture["arguments_symbolic"] == ["-n", "-a", "${ISOLATED_ROOT}/PFI.app"]
    assert capture["checkout_commit"] == REMEDIATION_CONTENT_COMMIT
    assert capture["candidate_path_symbolic"] == "${ISOLATED_ROOT}/PFI.app"
    assert capture["candidate_app_path_sha256"] == app["candidate_app_path_sha256"]
    assert capture["candidate_app_json_sha256"] == sha256_bytes(
        repo_bytes(f"{REVIEW_DIR}/candidate_app.json", candidate)
    )
    command_record = capture["command_record"]
    assert command_record == {
        "tool": "/usr/bin/open",
        "arguments_symbolic": ["-n", "-a", "${ISOLATED_ROOT}/PFI.app"],
        "exit_code": 0,
        "stdout_sha256": sha256_bytes(b""),
        "stderr_sha256": sha256_bytes(b""),
    }
    command_payload = json.dumps(
        command_record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    assert capture["command_record_sha256"] == sha256_bytes(command_payload)

    app_binding = capture["candidate_app_binding"]
    app_binding_keys = {
        "candidate_app_path_sha256",
        "candidate_app_tree_sha256",
        "candidate_bundle_sha256",
        "candidate_executable_sha256",
        "source_app_tree_sha256",
        "copied_app_tree_sha256",
    }
    assert set(app_binding) == app_binding_keys
    for key in app_binding_keys:
        assert app_binding[key] == app[key]
        assert_hex(app_binding[key], f"LaunchServices candidate binding {key}")
    inspection = capture["candidate_inspection"]
    inspection_boolean_keys = {
        "runtime_api_ready",
        "process_group_verified",
        "streamlit_listener_set_verified",
        "listener_endpoint_set_verified",
    }
    inspection_hash_keys = {
        "process_group_identity_sha256",
        "listener_endpoint_set_sha256",
        "launcher_identity_sha256",
    }
    assert set(inspection) == inspection_boolean_keys | inspection_hash_keys
    for key in inspection_boolean_keys:
        assert inspection[key] is True and inspection[key] == app[key]
    for key in inspection_hash_keys:
        assert inspection[key] == app[key]
        assert_hex(inspection[key], f"LaunchServices candidate inspection {key}")
    assert capture["launchservices_registration_verified"] is True
    assert capture["launchservices_registration_verified"] == app[
        "launchservices_registration_verified"
    ]
    assert capture["ui_automation_used"] is False
    assert capture["finder_used"] is False
    assert capture["privacy"] == {
        "absolute_candidate_path_persisted": False,
        "command_output_persisted": False,
        "contains_private_paths": False,
    }


def verify_png(payload: bytes, label: str, *, strict_chunks: bool = False) -> tuple[int, int]:
    assert payload.startswith(b"\x89PNG\r\n\x1a\n"), label
    cursor = 8
    width = height = 0
    saw_end = False
    chunk_types: list[bytes] = []
    while cursor + 12 <= len(payload):
        length = int.from_bytes(payload[cursor : cursor + 4], "big")
        chunk_type = payload[cursor + 4 : cursor + 8]
        data_start = cursor + 8
        data_end = data_start + length
        crc_end = data_end + 4
        assert crc_end <= len(payload), label
        expected_crc = int.from_bytes(payload[data_end:crc_end], "big")
        assert zlib.crc32(payload[cursor + 4 : data_end]) & 0xFFFFFFFF == expected_crc, label
        assert chunk_type not in {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}, label
        chunk_types.append(chunk_type)
        if chunk_type == b"IHDR":
            assert length == 13 and width == height == 0, label
            width = int.from_bytes(payload[data_start : data_start + 4], "big")
            height = int.from_bytes(payload[data_start + 4 : data_start + 8], "big")
        cursor = crc_end
        if chunk_type == b"IEND":
            assert length == 0, label
            saw_end = True
            break
    assert saw_end and cursor == len(payload) and width > 0 and height > 0, label
    if strict_chunks:
        assert set(chunk_types) <= {b"IHDR", b"IDAT", b"IEND"}, label
        assert chunk_types[0] == b"IHDR" and chunk_types[-1] == b"IEND", label
        assert chunk_types.count(b"IHDR") == 1, label
        assert chunk_types.count(b"IDAT") >= 1, label
        assert chunk_types.count(b"IEND") == 1, label
    return width, height


def verify_reviews(candidate: str | None, binding_paths: list[str]) -> dict[str, Any]:
    audit = repo_json(f"{REVIEW_DIR}/review_audit.json", candidate)
    assert audit["schema"] == "PFIV025Stage1WholeReviewAuditV1"
    assert audit["acceptance_id"] == ACCEPTANCE_ID
    assert audit["whole_review_base"] == WHOLE_REVIEW_BASE
    assert audit["remediation_content_commit"] == REMEDIATION_CONTENT_COMMIT
    assert audit["initial_findings"] == {"critical": 1, "important": 3, "minor": 0}
    assert audit["verifier_review_findings_before_remediation"] == {
        "critical": 2,
        "important": 4,
        "minor": 2,
    }
    assert audit["content_rereview_findings_before_remediation"] == {
        "critical": 1,
        "important": 2,
        "minor": 0,
    }
    assert audit["c4_rereview_findings_before_remediation"] == {
        "critical": 1,
        "important": 0,
        "minor": 0,
    }
    assert audit["post_remediation_counts"] == {"critical": 0, "important": 0, "minor": 0}
    stale_cleanup = audit["stale_shadow_worktree_cleanup"]
    assert stale_cleanup["symbolic_path"] == "${PRIVATE_TMP}/pfi-v025-s1p1-shadow.M7gIWF"
    assert stale_cleanup["removed"] is True
    assert stale_cleanup["git_worktree_registration_absent"] is True
    assert stale_cleanup["process_count"] == 0
    assert stale_cleanup["open_handle_count"] == 0
    assert stale_cleanup["launchservices_record_count"] == 0
    reviews = audit["fresh_independent_rereviews"]
    assert isinstance(reviews, list) and len(reviews) == 3
    assert {item["lane"] for item in reviews} == REVIEW_LANES
    assert len({item["reviewer"] for item in reviews}) == 3
    binding_paths_sha256 = path_list_sha256(binding_paths)
    reviewable_sha256 = reviewable_payload_sha256(binding_paths, candidate)
    expected_png_sha256 = {
        key: sha256_bytes(repo_bytes(path, candidate)) for key, path in PNG_PRIVACY_PATHS.items()
    }
    assert audit["prebinding_reviewable_payload_sha256"] == reviewable_sha256
    assert sorted(audit["prebinding_review_excluded_paths"]) == sorted(
        PREBINDING_REVIEW_EXCLUDED_PATHS
    )
    for review in reviews:
        assert review["reviewed_content_commit"] == REMEDIATION_CONTENT_COMMIT
        assert review["reviewed_binding_state"] == "working_tree_prebinding"
        assert review["reviewed_binding_paths_sha256"] == binding_paths_sha256
        assert review["reviewed_payload_sha256"] == reviewable_sha256
        assert review["inspected_png_sha256"] == expected_png_sha256
        assert review["png_visual_privacy_findings"] == 0
        assert review["verdict"] in {"PASS", "PASS_FOR_ATTESTATION", "APPROVED"}
        assert {key: review[key] for key in ("critical", "important", "minor")} == {
            "critical": 0,
            "important": 0,
            "minor": 0,
        }
        report_sha = assert_hex(review["report_sha256"], "fresh review report hash")
        expected_ref = (
            "codex-review/pfi-v025/stage_1/whole_stage_review/prebinding/"
            f"{REMEDIATION_CONTENT_COMMIT}/reviews/{review['lane']}.json"
        )
        assert review["report_ref"] == expected_ref
        report = load_external_json(expected_ref, report_sha)
        assert report["schema"] == "PFIV025Stage1WholeReviewIndependentReviewV1"
        assert report["review_scope"] == "prebinding_working_tree"
        assert report["whole_review_base"] == WHOLE_REVIEW_BASE
        assert report["reviewed_content_commit"] == REMEDIATION_CONTENT_COMMIT
        assert report["reviewed_binding_state"] == "working_tree_prebinding"
        assert report["reviewed_binding_paths_sha256"] == binding_paths_sha256
        assert report["reviewed_payload_sha256"] == reviewable_sha256
        assert sorted(report["reviewed_payload_excluded_paths"]) == sorted(
            PREBINDING_REVIEW_EXCLUDED_PATHS
        )
        assert report["inspected_png_sha256"] == expected_png_sha256
        assert report["png_visual_privacy_findings"] == 0
        for field in ("reviewer", "lane", "verdict", "critical", "important", "minor"):
            assert report[field] == review[field]
        assert report["finding_ids"] == []
    return audit


def verify_evidence_hashes(
    candidate: str | None, evidence: dict[str, Any], binding_paths: list[str]
) -> str:
    evidence_ref = f"{REVIEW_DIR}/evidence.json"
    transition_ref = "PFI/docs/pfi_v025/stage_1/stage_1_transition_authorization.json"
    evidence_sha = sha256_bytes(repo_bytes(evidence_ref, candidate))
    transition = repo_json(transition_ref, candidate)
    assert transition["evidence_sha256"] == evidence_sha

    artifact_hashes = evidence["artifact_hashes"]
    excluded = {evidence_ref, transition_ref}
    assert set(artifact_hashes) == set(binding_paths) - excluded
    for path, expected in artifact_hashes.items():
        assert_hex(expected, f"artifact hash {path}")
        assert sha256_bytes(repo_bytes(path, candidate)) == expected, path

    with zipfile.ZipFile(TASK_PACK) as archive:
        assert archive.testzip() is None
        schema = json.loads(
            archive.read("PFI_v0.2.5_TaskPack/schemas/evidence_pack.schema.json")
        )
    Draft202012Validator(schema, format_checker=FormatChecker()).validate(evidence)
    return evidence_sha


def verify_privacy(candidate: str | None, whole_paths: list[str]) -> dict[str, int]:
    patterns = {
        "private_key": rb"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----",
        "github_token": rb"\bgh[pousr]_[A-Za-z0-9]{20,}\b",
        "aws_access_key": rb"\bAKIA[0-9A-Z]{16}\b",
        "openai_key": rb"\bsk-[A-Za-z0-9]{20,}\b",
        "private_home_path": rb"(?:file:///)?/Users/[A-Za-z0-9._-]+/",
        "private_tmp_path": rb"(?<![A-Za-z0-9._}~-])/(?:private/)?tmp/[A-Za-z0-9._-]+",
        "private_var_path": rb"/private/var/" rb"folders/",
    }
    findings = {name: 0 for name in patterns}
    for path in whole_paths:
        if path.endswith((".png", ".zip")):
            continue
        payload = whole_review_added_text_bytes(path, candidate)
        for name, pattern in patterns.items():
            findings[name] += len(re.findall(pattern, payload, flags=re.IGNORECASE))
    assert all(value == 0 for value in findings.values()), findings

    trace_raw = repo_bytes(f"{REVIEW_DIR}/playwright_trace.zip", candidate)
    with zipfile.ZipFile(io.BytesIO(trace_raw)) as archive:
        assert archive.testzip() is None
        infos = archive.infolist()
        assert 0 < len(infos) <= 10_000
        for info in infos:
            pure = PurePosixPath(info.filename)
            assert not pure.is_absolute() and ".." not in pure.parts
            assert info.file_size <= 96 * 1024 * 1024
            payload = archive.read(info)
            for name, pattern in patterns.items():
                assert re.search(pattern, payload, flags=re.IGNORECASE) is None, (name, info.filename)
    return findings


def verify_canonical_owner_truth(candidate: str | None) -> None:
    project = parse_yaml(repo_text("PFI/docs/governance/project.yaml", candidate))
    assert project["schema_version"] == "codexproject.project.v1"
    assert project["project_id"] == "PFI"
    assert project["version"] == "v0.2.5"
    assert project["current_status"] == "stage_1_candidate_pass_pending_postcommit_attestation"
    predicate = project["completion_predicate"]
    assert predicate["stage_1_tracked_status"] == "candidate_pass_pending_postcommit_attestation"
    assert predicate["stage_1_external_attestation_required"] is True
    assert predicate["stage_2_entry_authorized_after_attestation"] is True
    assert predicate["stage_2_status"] == "not_started"
    assert predicate["canonical_install_gate"] == "S12-P2-T1"
    assert predicate["push_gate"] == "after_S12-P3-T4_explicit_acceptance"
    assert predicate["production_accepted"] is False
    assert predicate["final_human_acceptance"] is False
    features = {item["feature_id"]: item for item in project["features"]}
    assert features["FEAT-PFI-V025-S1-WHOLE"]["status"] == "active"
    assert features["FEAT-PFI-V024-FINAL-DELIVERY"]["status"] == "historical_superseded"

    roadmap = parse_yaml(repo_text("PFI/docs/governance/roadmap.yaml", candidate))
    assert roadmap["current_stage_id"] == "V025-S1"
    assert roadmap["current_phase_id"] == "V025-S1-WHOLE-REVIEW"
    assert roadmap["current_task_id"] == "NOT_APPLICABLE_REVIEW_GATE"
    assert roadmap["next_gate_id"] == "ACC-PFI-V025-STAGE1-WHOLE-REVIEW-EXTERNAL-ATTESTATION"
    stages = {item["stage_id"]: item for item in roadmap["stages"]}
    stage = stages["V025-S1"]
    assert stage["status"] == "candidate_pass_pending_postcommit_attestation"
    assert stage["stage_2_status"] == "not_started"
    roadmap_task_records = [
        task for phase in stage["phases"] for task in phase.get("tasks", [])
    ]
    assert [task["task_id"] for task in roadmap_task_records] == list(ROADMAP_TASK_IDS)
    for task in roadmap_task_records:
        expected_status = (
            "completed_by_isolated_candidate_override"
            if task["task_id"] in OVERRIDDEN_STAGE1_TASK_IDS
            else "completed"
        )
        assert task["status"] == expected_status
        assert tuple(task["evidence_refs"]) == TASK_EVIDENCE_REFS[task["task_id"]]
    historical_delivery = stages["V024-FD"]
    assert historical_delivery["status"] == "historical_superseded"
    assert historical_delivery["superseded_by"] == "V025-S0"
    assert all(phase["status"] == "historical_superseded" for phase in historical_delivery["phases"])
    assert all(
        task["status"] == "historical_superseded"
        for phase in historical_delivery["phases"]
        for task in phase.get("tasks", [])
    )

    required_markers = {
        "PFI/功能清单.md": (
            "FEAT-PFI-V025-S1-WHOLE",
            "candidate_pass_pending_postcommit_attestation",
            "stage_2_status: `not_started`",
        ),
        "PFI/开发记录.md": (
            ACCEPTANCE_ID,
            REMEDIATION_CONTENT_COMMIT,
            "Stage 1: 100.00% candidate",
            "stage_2_status: `not_started`",
        ),
        "PFI/模型参数文件.md": (
            ACCEPTANCE_ID,
            "model_ids_changed=[]",
            "formula_ids_changed=[]",
            "parameter_ids_changed=[]",
        ),
    }
    for path, markers in required_markers.items():
        text = repo_text(path, candidate)
        assert all(marker in text for marker in markers), path
    development_record = repo_text("PFI/开发记录.md", candidate)
    historical_v024 = re.search(
        r"### V024-FD v0\.2\.4 final delivery.*?(?=\n## V025-S1)",
        development_record,
        flags=re.DOTALL,
    )
    assert historical_v024
    assert historical_v024.group(0).count("historical_superseded") >= 3
    assert "in_progress" not in historical_v024.group(0)


def verify_governance_and_boundaries(
    candidate: str | None, evidence: dict[str, Any], evidence_sha: str
) -> None:
    assert evidence["schema"] == "PFIV025Stage1WholeReviewEvidenceV1"
    assert evidence["version"] == "v0.2.5"
    assert evidence["stage"] == 1 and evidence["phase"] == "whole_stage_review"
    assert evidence["acceptance_id"] == ACCEPTANCE_ID
    assert evidence["contract_id"] == CONTRACT_ID
    assert evidence["status"] == "candidate_pass"
    assert evidence["source_hashes"] == {
        "roadmap_sha256": ROADMAP_SHA256,
        "task_pack_sha256": TASK_PACK_SHA256,
    }
    assert evidence["whole_review_base"] == WHOLE_REVIEW_BASE
    assert evidence["remediation_content_commit"] == REMEDIATION_CONTENT_COMMIT
    assert evidence["authorization_id"] == AUTHORIZATION_ID
    scope_override = evidence["remediation_scope_override"]
    assert scope_override["override_id"] == SCOPE_OVERRIDE_ID
    assert scope_override["source"] == SCOPE_OVERRIDE_SOURCE
    assert scope_override["authorization_kind"] == "interim_stage_execution_not_final_acceptance"
    assert set(scope_override["expanded_content_paths"]) == SCOPE_OVERRIDE_CONTENT_PATHS
    assert scope_override["waives_technical_gates"] is False
    assert scope_override["waives_independent_review"] is False
    assert scope_override["waives_privacy_controls"] is False
    assert scope_override["authorizes_push"] is False
    assert scope_override["authorizes_canonical_install"] is False
    task_disposition = evidence["stage_1_task_disposition"]
    assert isinstance(task_disposition, list) and len(task_disposition) == len(ROADMAP_TASK_IDS)
    assert [item["task_id"] for item in task_disposition] == list(ROADMAP_TASK_IDS)
    for item in task_disposition:
        expected_status = (
            "accepted_by_isolated_candidate_override"
            if item["task_id"] in OVERRIDDEN_STAGE1_TASK_IDS
            else "accepted"
        )
        assert item["status"] == expected_status
        assert tuple(item["evidence_refs"]) == TASK_EVIDENCE_REFS[item["task_id"]]
        for evidence_ref in item["evidence_refs"]:
            assert repo_bytes(evidence_ref, candidate)
        if item["task_id"] in OVERRIDDEN_STAGE1_TASK_IDS:
            assert item["override_id"] == "PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE"
            assert item["canonical_install_gate"] == "S12-P2-T1"
        else:
            assert item.get("override_id") is None
    criteria = evidence["stage_1_acceptance_criteria"]
    assert [item["criterion_id"] for item in criteria] == list(ACCEPTANCE_CRITERIA_IDS)
    assert all(item["passed"] is True for item in criteria)
    for item in criteria:
        assert tuple(item["evidence_refs"]) == CRITERIA_EVIDENCE_REFS[item["criterion_id"]]
        for evidence_ref in item["evidence_refs"]:
            assert repo_bytes(evidence_ref, candidate)
    assert criteria[4]["override_id"] == "PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE"
    stops = evidence["stage_1_stop_conditions"]
    assert [item["stop_id"] for item in stops] == list(STOP_CONDITION_IDS)
    assert all(item["triggered"] is False and item["clear"] is True for item in stops)
    for item in stops:
        assert tuple(item["evidence_refs"]) == STOP_EVIDENCE_REFS[item["stop_id"]]
        for evidence_ref in item["evidence_refs"]:
            assert repo_bytes(evidence_ref, candidate)
    assert evidence["stop_conditions_clear"] is True
    pass_gate = evidence["stage_1_pass_gate"]
    assert pass_gate["passed"] is True
    assert pass_gate["launch_method"] == "terminal_open_launchservices_isolated_candidate"
    assert pass_gate["override_id"] == "PFI-V025-OVERRIDE-STAGE1-ISOLATED-CANDIDATE"
    assert evidence["git_commit"] == REMEDIATION_CONTENT_COMMIT
    assert evidence["allowed_files_obeyed"] is True
    assert evidence["requires_user_acceptance"] is True
    assert evidence["review_findings"]["post_remediation_counts"] == {
        "critical": 0,
        "important": 0,
        "minor": 0,
    }
    assert evidence["stage_1_codex_candidate_verdict"] == "PASS_PENDING_POSTCOMMIT_ATTESTATION"
    assert evidence["stage_1_status"] == "candidate_pass_pending_postcommit_attestation"
    assert evidence["stage_2_status"] == "not_started"
    for key in (
        "contains_private_values",
        "push_performed",
        "app_install_performed",
        "canonical_app_install",
        "production_accepted",
        "final_human_acceptance",
    ):
        assert evidence[key] is False, key
    assert evidence["candidate_cleanup_complete"] is True
    assert evidence["canonical_entries_unchanged"] is True
    assert evidence["requires_final_stage12_human_acceptance"] is True
    assert evidence["standing_interim_authorization_applied"] is True
    assert evidence["canonical_install_gate"] == "S12-P2-T1"
    assert evidence["dependency_install_performed"] is False
    assert evidence["model_formula_parameter_behavior_changed"] is False
    assert evidence["model_ids_changed"] == []
    assert evidence["formula_ids_changed"] == []
    assert evidence["parameter_ids_changed"] == []

    assert not any("human_acceptance.json" in path for path in evidence["whole_stage_changed_files"])
    assert not any("stage_2/" in path for path in evidence["whole_stage_changed_files"])
    transition = repo_json(
        "PFI/docs/pfi_v025/stage_1/stage_1_transition_authorization.json",
        candidate,
    )
    assert transition["schema"] == "PFIV025Stage1TransitionAuthorizationV1"
    assert transition["acceptance_id"] == ACCEPTANCE_ID
    assert transition["authorization_id"] == AUTHORIZATION_ID
    assert transition["remediation_scope_override_id"] == SCOPE_OVERRIDE_ID
    assert transition["stage_1_task_ids"] == list(ROADMAP_TASK_IDS)
    assert transition["acceptance_criteria_ids"] == list(ACCEPTANCE_CRITERIA_IDS)
    assert transition["stop_condition_ids"] == list(STOP_CONDITION_IDS)
    assert transition["stop_conditions_clear"] is True
    assert transition["evidence_sha256"] == evidence_sha
    assert transition["stage_1_codex_candidate_verdict"] == "PASS_PENDING_POSTCOMMIT_ATTESTATION"
    assert transition["stage_1_status"] == "candidate_pass_pending_postcommit_attestation"
    assert transition["stage_2_entry_authorized"] is False
    assert transition["stage_2_entry_authorized_after_activation"] is True
    assert transition["activation_condition"] == "matching_external_postcommit_attestation_and_C0_I0_M0"
    assert transition["stage_2_status"] == "not_started"
    assert transition["final_human_acceptance"] is False
    assert transition["human_acceptance_json_created"] is False
    assert transition["production_accepted"] is False
    assert transition["push_performed"] is False
    assert transition["app_install_performed"] is False
    assert transition["canonical_install_gate"] == "S12-P2-T1"

    events = [
        json.loads(line)
        for line in repo_text("PFI/docs/governance/development_events.jsonl", candidate).splitlines()
        if line.strip()
    ]
    whole_events = [event for event in events if event.get("acceptance_id") == ACCEPTANCE_ID]
    assert len(whole_events) == 1
    event = whole_events[0]
    assert event["authorization_id"] == AUTHORIZATION_ID
    assert event["scope_override_id"] == SCOPE_OVERRIDE_ID
    assert event["task_ids"] == list(ROADMAP_TASK_IDS)
    assert event["stop_conditions_clear"] is True
    assert event["result"] == "candidate_pass_pending_postcommit_attestation"
    assert event["push_performed"] is False
    assert event["app_install_performed"] is False
    assert event["production_accepted"] is False
    assert event["final_human_acceptance"] is False
    assert event["model_ids_changed"] == []
    assert event["formula_ids_changed"] == []
    assert event["parameter_ids_changed"] == []

    trace_rows = list(
        csv.DictReader(io.StringIO(repo_text("PFI/docs/governance/TRACEABILITY_MATRIX.csv", candidate)))
    )
    rows = [row for row in trace_rows if row.get("acceptance_id") == ACCEPTANCE_ID or row.get("requirement_id") == "REQ-PFI-V025-S1-WHOLE-REVIEW"]
    assert len(rows) == 1
    assert rows[0]["evidence_ref"] == f"{REVIEW_DIR}/evidence.json"
    assert rows[0]["test_ref"] == "PFI/scripts/v025/verify_stage1_whole_review.py"

    delivery = parse_yaml(repo_text("PFI/docs/governance/delivery_tasks.yaml", candidate))
    contracts = delivery.get("phase_contracts", [])
    matches = [item for item in contracts if item.get("acceptance_id") == ACCEPTANCE_ID]
    assert len(matches) == 1
    contract = matches[0]
    assert contract["authorization_id"] == AUTHORIZATION_ID
    assert contract["launch_method_override_id"] == "PFI-V025-S1-NO-FINDER-20260713"
    assert contract["launch_method"] == "terminal_open_launchservices_isolated_candidate"
    assert contract["push_performed"] is False
    assert contract["app_install_performed"] is False
    assert contract["production_accepted"] is False
    assert contract["stage_2_status"] == "not_started"
    assert contract["lifecycle"] == "candidate_pass_pending_postcommit_attestation"
    assert contract["model_ids_changed"] == []
    assert contract["formula_ids_changed"] == []
    assert contract["parameter_ids_changed"] == []


def locate_whole_attestation(binding: str) -> Path:
    return safe_external_path(
        "codex-review/pfi-v025/stage_1/whole_stage_review/"
        f"{binding}/stage_1_whole_review_attestation.json"
    )


def verify_whole_attestation(
    binding: str,
    evidence_sha: str,
    manifest_sha: str,
    binding_paths: list[str],
) -> dict[str, Any]:
    path = locate_whole_attestation(binding)
    assert path.is_file() and not path.is_symlink()
    attestation = json.loads(path.read_text(encoding="utf-8"))
    assert attestation["schema"] == "PFIV025Stage1WholeReviewExternalAttestationV1"
    assert attestation["whole_review_base"] == WHOLE_REVIEW_BASE
    assert attestation["remediation_content_commit"] == REMEDIATION_CONTENT_COMMIT
    assert attestation["whole_review_binding_commit"] == binding
    assert attestation["whole_review_binding_parent"] == REMEDIATION_CONTENT_COMMIT
    assert attestation["whole_review_binding_parent_count"] == 1
    assert attestation["evidence_sha256"] == evidence_sha
    assert attestation["manifest_sha256"] == manifest_sha
    assert sorted(attestation["binding_changed_files"]) == binding_paths
    assert attestation["verifier_result"] == "PASS"
    assert attestation["review_findings_after_remediation"] == {
        "critical": 0,
        "important": 0,
        "minor": 0,
    }
    reviewers = attestation["independent_reviewers"]
    assert isinstance(reviewers, list) and len(reviewers) == 3
    assert {item["lane"] for item in reviewers} == REVIEW_LANES
    assert len({item["reviewer"] for item in reviewers}) == 3
    binding_paths_sha256 = path_list_sha256(binding_paths)
    expected_png_sha256 = {
        key: sha256_bytes(git_show_bytes(binding, path)) for key, path in PNG_PRIVACY_PATHS.items()
    }
    for item in reviewers:
        assert item["verdict"] in {"PASS", "PASS_FOR_ATTESTATION", "APPROVED"}
        assert item["critical"] == item["important"] == item["minor"] == 0
        assert item["inspected_png_sha256"] == expected_png_sha256
        assert item["png_visual_privacy_findings"] == 0
        report_sha = assert_hex(item["report_sha256"], "postbinding review report hash")
        expected_ref = (
            "codex-review/pfi-v025/stage_1/whole_stage_review/"
            f"{binding}/reviews/{item['lane']}.json"
        )
        assert item["report_ref"] == expected_ref
        report = load_external_json(expected_ref, report_sha)
        assert report["schema"] == "PFIV025Stage1WholeReviewIndependentReviewV1"
        assert report["review_scope"] == "postbinding_commit"
        assert report["whole_review_base"] == WHOLE_REVIEW_BASE
        assert report["reviewed_content_commit"] == REMEDIATION_CONTENT_COMMIT
        assert report["reviewed_binding_commit"] == binding
        assert report["reviewed_binding_parent"] == REMEDIATION_CONTENT_COMMIT
        assert report["reviewed_binding_paths_sha256"] == binding_paths_sha256
        assert report["evidence_sha256"] == evidence_sha
        assert report["manifest_sha256"] == manifest_sha
        assert report["inspected_png_sha256"] == expected_png_sha256
        assert report["png_visual_privacy_findings"] == 0
        for field in ("reviewer", "lane", "verdict", "critical", "important", "minor"):
            assert report[field] == item[field]
        assert report["finding_ids"] == []
    assert attestation["authorization_id"] == AUTHORIZATION_ID
    assert attestation["stage_1_codex_acceptance"] == "PASS"
    assert attestation["stage_1_status"] == "accepted_for_transition"
    assert attestation["stage_2_entry_authorized"] is True
    assert attestation["push_performed"] is False
    assert attestation["app_install_performed"] is False
    assert attestation["canonical_app_install"] is False
    assert attestation["production_accepted"] is False
    assert attestation["final_human_acceptance"] is False
    assert attestation["requires_final_stage12_human_acceptance"] is True
    assert attestation["stage_2_status"] == "not_started"
    return {
        "path": str(path.relative_to(common_dir())),
        "sha256": sha256_bytes(path.read_bytes()),
    }


def verify(requested_candidate: str | None, require_attestation: bool) -> dict[str, Any]:
    if not __debug__:
        raise RuntimeError("optimized Python is forbidden because assertions are the verifier")

    candidate = resolve_candidate(requested_candidate)
    if candidate:
        assert candidate != REMEDIATION_CONTENT_COMMIT
        assert commit_parents(candidate) == [REMEDIATION_CONTENT_COMMIT]

    phases = verify_historical_phases()
    verify_source_and_authorization(candidate)
    evidence = repo_json(f"{REVIEW_DIR}/evidence.json", candidate)
    binding_paths, whole_paths = verify_path_sets(candidate, evidence)
    correction = verify_p12_append_only_correction(candidate)
    identity = verify_release_identity(candidate)
    browser = verify_browser_and_runtime(candidate, identity)
    verify_candidate_cleanup(candidate)
    audit = verify_reviews(candidate, binding_paths)
    evidence_sha = verify_evidence_hashes(candidate, evidence, binding_paths)
    privacy_findings = verify_privacy(candidate, whole_paths)
    verify_canonical_owner_truth(candidate)
    verify_governance_and_boundaries(candidate, evidence, evidence_sha)

    diff_check = (
        run("git", "diff", "--check", f"{REMEDIATION_CONTENT_COMMIT}..{candidate}")
        if candidate
        else run("git", "diff", "--check", REMEDIATION_CONTENT_COMMIT)
    )
    assert diff_check == b""

    attestation: dict[str, Any] | None = None
    if require_attestation:
        assert candidate, "--require-attestation requires a committed binding candidate"
        assert full_commit("HEAD") == candidate
        assert run("git", "status", "--porcelain") == b""
        attestation = verify_whole_attestation(
            candidate,
            evidence_sha,
            str(identity["manifest_sha256"]),
            binding_paths,
        )

    final_attested = attestation is not None
    return {
        "result": "PASS" if final_attested else "CANDIDATE_PASS_PENDING_POSTCOMMIT_ATTESTATION",
        "candidate": candidate or "working_tree",
        "stage_base": STAGE_BASE,
        "whole_review_base": WHOLE_REVIEW_BASE,
        "remediation_content_commit": REMEDIATION_CONTENT_COMMIT,
        "historical_phases": phases,
        "content_paths": len(CONTENT_PATHS),
        "binding_paths": len(binding_paths),
        "whole_stage_paths": len(whole_paths),
        "p12_corrected_paths": len(correction.get("missing_files_added") or correction["files_changed"]),
        "frontend_files": len(identity["frontend_files"]),
        "backend_files": len(identity["backend_files"]),
        "browser_checks": len(browser["checks"]),
        "fresh_review_lanes": len(audit["fresh_independent_rereviews"]),
        "post_remediation": "C0/I0/M0",
        "privacy_high_risk_findings": sum(privacy_findings.values()),
        "evidence_sha256": evidence_sha,
        "attestation": attestation or "not_required",
        "push_performed": False,
        "app_install_performed": False,
        "production_accepted": False,
        "final_human_acceptance": False,
        "stage_1_codex_acceptance": "PASS" if final_attested else "PENDING_POSTCOMMIT_ATTESTATION",
        "stage_1_status": "accepted_for_transition" if final_attested else "candidate_pass_pending_postcommit_attestation",
        "stage_2_entry_authorized": final_attested,
        "stage_2": "not_started",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", help="Committed direct binding successor SHA")
    parser.add_argument("--require-attestation", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            verify(args.candidate, args.require_attestation),
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
