from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

from jsonschema import Draft202012Validator
import pytest

from pfi_os.application.read_models.metric_state import (
    METRIC_CONTRACT_VERSION,
    METRIC_STATUSES,
    NON_READY_STATUSES,
    dependency_set_hash,
    validate_metric_state,
)
from pfi_os.application.read_models.unified import (
    ACCEPTANCE_ID,
    PHASE_ID,
    SURFACE_IDS,
    TASK_IDS,
    build_current_unified_read_model,
    build_phase43_contract,
    rebuild_read_model_hash,
)
from pfi_v02.stage_v021_runtime_api import (
    build_v025_stage4_read_model_status,
    stable_v025_read_model_hash,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PFI_ROOT = REPO_ROOT / "PFI"
SCHEMA_ROOT = PFI_ROOT / "docs" / "pfi_v025" / "stage_4"
REPORT_ROOT = PFI_ROOT / "reports" / "pfi_v025" / "stage_4" / "phase_4_3"
TASKPACK = Path.home() / "Downloads" / "PFI_v0.2.5_Production_Truth_Human_Workflow_TaskPack.zip"
SHA_A = "sha256:" + "a" * 64
SHA_B = "sha256:" + "b" * 64
SHA_C = "sha256:" + "c" * 64


def _json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _complete_zero_metric() -> dict[str, object]:
    dependencies = {"contract_test_source": SHA_A}
    return {
        "metric_contract_version": METRIC_CONTRACT_VERSION,
        "metric_id": "contract_test_zero_cny",
        "value": 0,
        "currency": "CNY",
        "status": "confirmed_zero",
        "source_ids": ["SRC-CONTRACT-TEST"],
        "record_count": 1,
        "coverage_start": "2026-07-01",
        "coverage_end": "2026-07-14",
        "data_as_of": "2026-07-14",
        "valued_at": "2026-07-14T00:00:00Z",
        "fx_snapshot_id": None,
        "formula_id": "FORM-CONTRACT-TEST",
        "formula_version": "contract-test-v1",
        "formula_hash": SHA_A,
        "parameter_hash": SHA_B,
        "data_hash": SHA_C,
        "read_model_hash": SHA_A,
        "dependency_hashes": dependencies,
        "dependency_set_hash": dependency_set_hash(dependencies),
        "classification_confidence": 100,
        "source_coverage": 1,
        "reconciliation_coverage": 1,
        "valuation_coverage": 1,
        "model_validation": "validated",
        "report_completeness": "complete",
        "blocking_reason_zh": None,
        "calculation_state": "confirmed",
    }


def test_phase_contract_is_exactly_phase_43_and_stops_before_whole_stage_review() -> None:
    contract = build_phase43_contract()

    assert contract["version"] == "v0.2.5"
    assert contract["stage"] == 4
    assert contract["phase_id"] == PHASE_ID == "V025-S4-P4.3"
    assert contract["task_ids"] == list(TASK_IDS) == [
        "S4-P3-T1",
        "S4-P3-T2",
        "S4-P3-T3",
        "S4-P3-T4",
    ]
    assert contract["acceptance_id"] == ACCEPTANCE_ID == "ACC-PFI-V025-S4-P43-METRIC-CONSISTENCY"
    assert contract["surface_ids"] == list(SURFACE_IDS)
    assert contract["current_phase_only"] is True
    assert contract["finder_used"] is False
    assert contract["stage_4_whole_stage_review_done"] is False
    assert any(item.startswith("Stage 4 whole-stage") for item in contract["explicitly_not_done"])


def test_taskpack_metric_schema_is_preserved_and_strict_extension_covers_every_status() -> None:
    canonical = _json(SCHEMA_ROOT / "metric_state.schema.json")
    strict = _json(SCHEMA_ROOT / "metric_state_strict.schema.json")
    Draft202012Validator.check_schema(canonical)
    Draft202012Validator.check_schema(strict)

    if TASKPACK.is_file():
        with zipfile.ZipFile(TASKPACK) as archive:
            upstream = json.loads(
                archive.read("PFI_v0.2.5_TaskPack/schemas/metric_state.schema.json")
            )
        assert canonical == upstream

    assert tuple(canonical["properties"]["status"]["enum"]) == METRIC_STATUSES
    assert tuple(strict["properties"]["status"]["enum"]) == METRIC_STATUSES
    assert set(NON_READY_STATUSES) == set(METRIC_STATUSES) - {"ready", "confirmed_zero"}


@pytest.mark.parametrize("status", NON_READY_STATUSES)
def test_every_non_ready_state_rejects_financial_zero(status: str) -> None:
    metric = _complete_zero_metric()
    metric["status"] = status
    metric["blocking_reason_zh"] = "依赖未满足"

    with pytest.raises(ValueError, match="non-ready metric value must be null"):
        validate_metric_state(metric)


def test_confirmed_zero_requires_complete_evidence_and_accepts_only_exact_zero() -> None:
    complete = _complete_zero_metric()
    validate_metric_state(complete)
    Draft202012Validator(_json(SCHEMA_ROOT / "metric_state_strict.schema.json")).validate(complete)

    for field in (
        "source_ids",
        "record_count",
        "coverage_start",
        "coverage_end",
        "data_as_of",
        "formula_hash",
        "parameter_hash",
        "data_hash",
        "classification_confidence",
        "source_coverage",
        "reconciliation_coverage",
        "valuation_coverage",
    ):
        incomplete = deepcopy(complete)
        incomplete[field] = [] if field == "source_ids" else None
        with pytest.raises(ValueError, match="confirmed_zero"):
            validate_metric_state(incomplete)

    nonzero = deepcopy(complete)
    nonzero["value"] = 1
    with pytest.raises(ValueError, match="confirmed_zero value must be numeric zero"):
        validate_metric_state(nonzero)


def test_current_unified_read_model_is_fail_closed_and_rebuildable() -> None:
    read_model = build_current_unified_read_model(REPO_ROOT, observed_at="2026-07-14T13:00:00Z")
    strict_validator = Draft202012Validator(_json(SCHEMA_ROOT / "metric_state_strict.schema.json"))

    assert read_model["schema"] == "PFIV025UnifiedReadModelV1"
    assert read_model["status"] == "not_loaded"
    assert read_model["surface_ids"] == list(SURFACE_IDS)
    assert read_model["financial_values_emitted"] == 0
    assert read_model["confirmed_zero_count"] == 0
    assert read_model["non_ready_value_count"] == 0
    assert read_model["read_model_hash"] == rebuild_read_model_hash(read_model)
    assert read_model["dependency_set_hash"] == dependency_set_hash(read_model["dependency_hashes"])
    assert {metric["metric_id"] for metric in read_model["metrics"]} == {
        "net_worth_cny",
        "account_assets_cny",
        "cash_balance_cny",
        "liabilities_cny",
        "investment_market_value_cny",
        "investment_cost_basis_cny",
        "investment_unrealized_pnl_cny",
    }
    for metric in read_model["metrics"]:
        validate_metric_state(metric)
        strict_validator.validate(metric)
        assert metric["status"] == "not_loaded"
        assert metric["value"] is None
        assert metric["formula_hash"].startswith("sha256:")
        assert metric["read_model_hash"] == read_model["read_model_hash"]


def test_hash_excludes_observation_time_and_changes_when_a_dependency_changes() -> None:
    first = build_current_unified_read_model(REPO_ROOT, observed_at="2026-07-14T13:00:00Z")
    second = build_current_unified_read_model(REPO_ROOT, observed_at="2026-07-14T14:00:00Z")
    assert first["read_model_hash"] == second["read_model_hash"]

    changed = deepcopy(first)
    changed["dependency_hashes"]["stage3_event_read_model"] = SHA_C
    changed["dependency_set_hash"] = dependency_set_hash(changed["dependency_hashes"])
    assert rebuild_read_model_hash(changed) != first["read_model_hash"]


def test_five_surfaces_share_one_hash_and_identical_metric_fingerprints() -> None:
    read_model = build_current_unified_read_model(REPO_ROOT)
    surfaces = read_model["surfaces"]

    assert tuple(surfaces) == SURFACE_IDS
    assert {surface["read_model_hash"] for surface in surfaces.values()} == {
        read_model["read_model_hash"]
    }
    assert {tuple(surface["metric_ids"]) for surface in surfaces.values()} == {
        tuple(read_model["metric_ids"])
    }
    assert {tuple(surface["metric_fingerprints"]) for surface in surfaces.values()} == {
        tuple(read_model["metric_fingerprints"])
    }
    assert read_model["cross_page_difference_count"] == 0


def test_runtime_status_and_frontend_views_bind_the_unified_contract() -> None:
    runtime = build_v025_stage4_read_model_status(PFI_ROOT, observed_at="2026-07-14T13:00:00Z")
    assert runtime == build_current_unified_read_model(
        REPO_ROOT, observed_at="2026-07-14T13:00:00Z"
    )
    assert "sha256:" + stable_v025_read_model_hash(runtime) == runtime["read_model_hash"]

    node = shutil.which("node")
    if node is None:
        pytest.skip("node is unavailable")
    incomplete_zero = _complete_zero_metric()
    incomplete_zero["coverage_start"] = None
    script = """
const state = require('./PFI/web/app/data_state.js');
const payload = JSON.parse(process.argv[1]);
const incomplete = JSON.parse(process.argv[2]);
const complete = JSON.parse(process.argv[3]);
const views = state.buildSurfaceMetricViews(payload);
console.log(JSON.stringify({
  statuses: state.v025Statuses,
  sharedSurfaces: state.v025SharedSurfaces,
  hashes: state.v025SharedSurfaces.map((id) => views.surfaces[id].read_model_hash),
  fingerprints: state.v025SharedSurfaces.map((id) => views.surfaces[id].metric_fingerprints),
  missingDisplays: views.surfaces.homepage.metrics.map((metric) => metric.display_value),
  legacyHomeHash: views.surfaces.home.read_model_hash,
  legacyInsightsHash: views.surfaces.insights.read_model_hash,
  incompleteZero: state.renderMetricValueZh(incomplete),
  completeZero: state.renderMetricValueZh(complete),
}));
"""
    completed = subprocess.run(
        [
            node,
            "-e",
            script,
            json.dumps(runtime, ensure_ascii=False),
            json.dumps(incomplete_zero, ensure_ascii=False),
            json.dumps(_complete_zero_metric(), ensure_ascii=False),
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    result = json.loads(completed.stdout)

    assert tuple(result["statuses"]) == METRIC_STATUSES
    assert tuple(result["sharedSurfaces"]) == SURFACE_IDS
    assert set(result["hashes"]) == {runtime["read_model_hash"]}
    assert len({tuple(items) for items in result["fingerprints"]}) == 1
    assert all("CNY 0.00" not in value for value in result["missingDisplays"])
    assert result["legacyHomeHash"] == runtime["read_model_hash"]
    assert result["legacyInsightsHash"] == runtime["read_model_hash"]
    assert "CNY 0.00" not in result["incompleteZero"]
    assert result["completeZero"] == "CNY 0.00"


def test_tracked_phase_43_evidence_matches_runtime_and_stops_before_stage_review() -> None:
    evidence = _json(REPORT_ROOT / "evidence.json")
    read_model = build_current_unified_read_model(
        REPO_ROOT, observed_at=str(evidence["observed_at"])
    )

    assert _json(REPORT_ROOT / "read_model_status.json") == read_model
    core = _json(REPORT_ROOT / "core_metric_states.json")
    hashes = _json(REPORT_ROOT / "cross_page_hashes.json")
    no_false_zero = _json(REPORT_ROOT / "no_false_zero_result.json")
    assert core["metrics"] == read_model["metrics"]
    assert hashes["status"] == "pass"
    assert hashes["difference_count"] == 0
    assert hashes["read_model_hash"] == read_model["read_model_hash"]
    assert no_false_zero["result"] == "pass"
    assert no_false_zero["non_ready_value_count"] == 0
    assert no_false_zero["confirmed_zero_count"] == 0
    assert evidence["status"] == "candidate_pass"
    assert evidence["requires_user_acceptance"] is True
    assert evidence["stage_4_whole_stage_review_done"] is False
    assert evidence["stage_5_started"] is False
    assert evidence["contains_private_values"] is False
