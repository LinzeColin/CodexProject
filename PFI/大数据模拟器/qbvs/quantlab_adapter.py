from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


ADAPTER_PACK_SCHEMA_VERSION = "qbvs-quantlab-readonly-adapter-pack-v1"


@dataclass(frozen=True)
class QuantLabAdapterPackConfig:
    quantlab_root: str = ""
    default_bundle_dir: str = ""
    default_campaign_dir: str = ""
    default_promotion_candidates: str = ""


def build_quantlab_adapter_pack(
    output_dir: Path | str,
    config: QuantLabAdapterPackConfig | None = None,
) -> dict[str, Path]:
    config = config or QuantLabAdapterPackConfig()
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    adapter_path = output / "quantlab_qbvs_readonly_adapter.py"
    test_path = output / "test_quantlab_qbvs_readonly_adapter.py"
    readme_path = output / "README.md"
    manifest_path = output / "adapter_pack_manifest.json"
    request_path = output / "sample_ingestion_request.json"
    verification_path = output / "adapter_pack_verification.json"

    adapter_path.write_text(_adapter_source(), encoding="utf-8")
    test_path.write_text(_adapter_test_source(), encoding="utf-8")
    readme_path.write_text(_adapter_readme(config), encoding="utf-8")
    request_path.write_text(json.dumps(_sample_request(config), ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = _manifest(output, config)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    verification = verify_quantlab_adapter_pack(output)
    verification_path.write_text(json.dumps(verification, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "manifest": manifest_path,
        "adapter": adapter_path,
        "test": test_path,
        "readme": readme_path,
        "request": request_path,
        "verification": verification_path,
    }


def verify_quantlab_adapter_pack(pack_dir: Path | str) -> dict[str, Any]:
    root = Path(pack_dir)
    errors: list[str] = []
    warnings: list[str] = []
    required = [
        "adapter_pack_manifest.json",
        "quantlab_qbvs_readonly_adapter.py",
        "test_quantlab_qbvs_readonly_adapter.py",
        "README.md",
        "sample_ingestion_request.json",
    ]
    for name in required:
        if not (root / name).exists():
            errors.append(f"missing required artifact: {name}")
    manifest: dict[str, Any] = {}
    if (root / "adapter_pack_manifest.json").exists():
        try:
            manifest = json.loads((root / "adapter_pack_manifest.json").read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid adapter_pack_manifest.json: {exc}")
    if manifest:
        if manifest.get("schema_version") != ADAPTER_PACK_SCHEMA_VERSION:
            errors.append("unsupported adapter pack schema_version")
        if manifest.get("writes_quantlab_database") is not False:
            errors.append("adapter pack must not write QuantLab database")
        if manifest.get("modifies_quantlab_source") is not False:
            errors.append("adapter pack must not modify QuantLab source")
        for artifact in manifest.get("artifacts", []):
            if not (root / artifact.get("path", "")).exists():
                errors.append(f"manifest artifact missing on disk: {artifact.get('path')}")
    for py_name in ["quantlab_qbvs_readonly_adapter.py", "test_quantlab_qbvs_readonly_adapter.py"]:
        path = root / py_name
        if path.exists():
            try:
                compile(path.read_text(encoding="utf-8"), str(path), "exec")
            except Exception as exc:
                errors.append(f"{py_name} does not compile: {exc}")
    request_path = root / "sample_ingestion_request.json"
    if request_path.exists():
        try:
            request = json.loads(request_path.read_text(encoding="utf-8"))
            if request.get("ingestion_mode") != "external_evidence_only":
                errors.append("sample request must use external_evidence_only")
        except Exception as exc:
            errors.append(f"invalid sample_ingestion_request.json: {exc}")
    if manifest and not manifest.get("quantlab_alignment", {}).get("independent_validation_module"):
        warnings.append("quantlab independent validation module path not supplied")
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "pack_dir": str(root),
        "checked_at": datetime.now().isoformat(timespec="seconds"),
    }


def _manifest(output: Path, config: QuantLabAdapterPackConfig) -> dict[str, Any]:
    quantlab_root = Path(config.quantlab_root).expanduser() if config.quantlab_root else None
    independent_module = ""
    research_bus_module = ""
    if quantlab_root:
        independent = quantlab_root / "src" / "quantlab" / "integrations" / "independent_validation.py"
        research_bus = quantlab_root / "src" / "quantlab" / "integrations" / "research_bus.py"
        independent_module = str(independent) if independent.exists() else ""
        research_bus_module = str(research_bus) if research_bus.exists() else ""
    return {
        "schema_version": ADAPTER_PACK_SCHEMA_VERSION,
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source_system": "quant_behavior_validation_system",
        "target_system": "quantlab",
        "pack_dir": str(output),
        "writes_quantlab_database": False,
        "modifies_quantlab_source": False,
        "ingestion_mode": "external_evidence_only",
        "quantlab_alignment": {
            "quantlab_root": config.quantlab_root,
            "independent_validation_module": independent_module,
            "research_bus_module": research_bus_module,
            "recommended_quantlab_table": "independent_validation_runs",
        },
        "artifacts": [
            {"path": "adapter_pack_manifest.json", "kind": "manifest"},
            {"path": "quantlab_qbvs_readonly_adapter.py", "kind": "readonly_adapter_source"},
            {"path": "test_quantlab_qbvs_readonly_adapter.py", "kind": "adapter_unit_test"},
            {"path": "README.md", "kind": "instructions"},
            {"path": "sample_ingestion_request.json", "kind": "sample_request"},
        ],
        "consumable_qbvs_inputs": [
            "quantlab_bundle_manifest.json",
            "quantlab_ingestion_payload.json",
            "quantlab_candidate_strategies.csv",
            "campaign_plan.json",
            "campaign_status.csv",
            "promotion_candidates.csv",
        ],
    }


def _sample_request(config: QuantLabAdapterPackConfig) -> dict[str, Any]:
    return {
        "schema_version": ADAPTER_PACK_SCHEMA_VERSION,
        "source_system": "quant_behavior_validation_system",
        "target_system": "quantlab",
        "ingestion_mode": "external_evidence_only",
        "bundle_dir": config.default_bundle_dir,
        "campaign_dir": config.default_campaign_dir,
        "promotion_candidates": config.default_promotion_candidates,
        "required_quantlab_actions": [
            "read_bundle_or_campaign",
            "display_external_evidence",
            "register_independent_validation_review_only",
            "rerun_exact_validation_before_approval",
            "require_user_approval_before_database_write",
        ],
    }


def _adapter_source() -> str:
    return r'''from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def read_qbvs_bundle(bundle_dir: str | Path) -> dict[str, Any]:
    root = Path(bundle_dir)
    manifest = _read_json(root / "quantlab_bundle_manifest.json")
    payload = _read_json(root / "quantlab_ingestion_payload.json")
    candidates = _read_csv(root / "quantlab_candidate_strategies.csv")
    _require_external_only(manifest, payload)
    return {
        "kind": "qbvs_bundle",
        "bundle_dir": str(root),
        "manifest": manifest,
        "payload": payload,
        "candidate_count": len(candidates),
        "candidates": candidates,
        "approval_state": "review_only",
        "requires_exact_rerun": any(_truthy(row.get("requires_exact_validation")) for row in candidates),
        "requires_fund_rule_review": any(_truthy(row.get("requires_fund_rule_review")) for row in candidates),
    }


def read_qbvs_campaign(campaign_dir: str | Path) -> dict[str, Any]:
    root = Path(campaign_dir)
    plan = _read_json(root / "campaign_plan.json")
    status = _read_csv(root / "campaign_status.csv")
    if plan.get("starts_background_processes") is not False:
        raise ValueError("QBVS campaign must not start background processes.")
    return {
        "kind": "qbvs_campaign",
        "campaign_dir": str(root),
        "plan": plan,
        "status_rows": len(status),
        "status": status,
        "approval_state": "review_only",
    }


def read_qbvs_promotion_candidates(path: str | Path) -> dict[str, Any]:
    rows = _read_csv(Path(path))
    return {
        "kind": "qbvs_promotion_candidates",
        "path": str(path),
        "candidate_count": len(rows),
        "external_candidate_count": sum(1 for row in rows if row.get("promotion_state") == "external_candidate"),
        "requires_exact_rerun": all(_truthy(row.get("requires_quantlab_exact_rerun")) for row in rows) if rows else True,
        "requires_user_approval": all(_truthy(row.get("requires_user_approval_before_strategy_library_write")) for row in rows) if rows else True,
        "candidates": rows,
    }


def build_independent_validation_record(evidence: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_system": "QBVS",
        "status": "ReviewOnly",
        "mode": evidence.get("kind", ""),
        "manifest_path": evidence.get("bundle_dir") or evidence.get("campaign_dir") or evidence.get("path", ""),
        "total_rows": int(evidence.get("candidate_count") or evidence.get("status_rows") or 0),
        "shard_count": 0,
        "payload_json": evidence,
        "approval_boundary": "Do not write approved strategies without exact rerun and user approval.",
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(path)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object.")
    return payload


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(path)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _require_external_only(manifest: dict[str, Any], payload: dict[str, Any]) -> None:
    if manifest.get("writes_quantlab_database") is not False:
        raise ValueError("QBVS bundle must not write QuantLab database.")
    if manifest.get("writes_quantlab_source") is not False:
        raise ValueError("QBVS bundle must not write QuantLab source.")
    if payload.get("ingestion_mode") != "external_evidence_only":
        raise ValueError("QBVS payload must be external_evidence_only.")


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}
'''


def _adapter_test_source() -> str:
    return r'''from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from quantlab_qbvs_readonly_adapter import (
    build_independent_validation_record,
    read_qbvs_bundle,
    read_qbvs_campaign,
    read_qbvs_promotion_candidates,
)


class QBVSReadonlyAdapterTest(unittest.TestCase):
    def test_bundle_campaign_and_promotion_are_review_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            bundle = root / "bundle"
            bundle.mkdir()
            (bundle / "quantlab_bundle_manifest.json").write_text(json.dumps({
                "writes_quantlab_database": False,
                "writes_quantlab_source": False,
            }), encoding="utf-8")
            (bundle / "quantlab_ingestion_payload.json").write_text(json.dumps({
                "ingestion_mode": "external_evidence_only",
            }), encoding="utf-8")
            (bundle / "quantlab_candidate_strategies.csv").write_text(
                "strategy_id,requires_exact_validation,requires_fund_rule_review\ns1,true,false\n",
                encoding="utf-8",
            )
            evidence = read_qbvs_bundle(bundle)
            self.assertEqual(evidence["approval_state"], "review_only")
            self.assertTrue(evidence["requires_exact_rerun"])

            campaign = root / "campaign"
            campaign.mkdir()
            (campaign / "campaign_plan.json").write_text(json.dumps({
                "starts_background_processes": False,
            }), encoding="utf-8")
            (campaign / "campaign_status.csv").write_text("part,status\n1,pending\n", encoding="utf-8")
            campaign_evidence = read_qbvs_campaign(campaign)
            self.assertEqual(campaign_evidence["status_rows"], 1)

            promotion = root / "promotion.csv"
            promotion.write_text(
                "strategy_id,promotion_state,requires_quantlab_exact_rerun,requires_user_approval_before_strategy_library_write\ns1,external_candidate,true,true\n",
                encoding="utf-8",
            )
            promotion_evidence = read_qbvs_promotion_candidates(promotion)
            self.assertTrue(promotion_evidence["requires_user_approval"])

            record = build_independent_validation_record(evidence)
            self.assertEqual(record["status"], "ReviewOnly")


if __name__ == "__main__":
    unittest.main()
'''


def _adapter_readme(config: QuantLabAdapterPackConfig) -> str:
    return f"""# QBVS Readonly Adapter Pack for QuantLab

This pack is generated by QBVS for QuantLab-side reference.

Boundary:

- It does not write QuantLab source.
- It does not write QuantLab database.
- It reads QBVS evidence artifacts and creates review-only records.
- Approved strategy-library writes still require QuantLab exact rerun and user approval.

Detected QuantLab root:

`{config.quantlab_root or "not supplied"}`

Recommended QuantLab alignment:

- `quantlab.integrations.independent_validation`
- Research bus table: `independent_validation_runs`
- Status: `ReviewOnly`

Smoke test:

```bash
cd <this adapter pack>
python3 -m unittest test_quantlab_qbvs_readonly_adapter.py
```

Typical use:

```python
from quantlab_qbvs_readonly_adapter import read_qbvs_bundle, build_independent_validation_record

evidence = read_qbvs_bundle("/path/to/qbvs/handoff/quantlab_bundle_fund_smoke")
record = build_independent_validation_record(evidence)
```
"""
