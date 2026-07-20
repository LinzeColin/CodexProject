"""承重：所有 schema_version>=2 的 run manifest 必须满足 Review7 字段与 binding_status 契约。

背景：`lean_governance validate --all`（CI『Validate all registered scopes』步骤）对每个
schema_version>=2 的 run manifest 要求 Review7 必填字段与合法 binding_status。历史迁移清单
`GOV-SPLIT-WAVE6-20260717.json` 声明 schema_version 2 却缺这些字段，慢性拖红夜间 CI。本测试
遍历全部 schema>=2 清单锁死该契约，防新增/遗留清单再次缺字段（把只在夜间可见的红提前到本地单测）。
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
MANIFEST_DIR = ROOT / "governance" / "run_manifests"


def _sync_module():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "vgs_review7_test", SCRIPTS / "validate_governance_sync.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["vgs_review7_test"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class RunManifestReview7ConformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sync = _sync_module()

    def _schema2_manifests(self):
        for path in sorted(MANIFEST_DIR.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                self.fail(f"无法解析 run manifest：{path.name}")
            if isinstance(data, dict) and int(data.get("schema_version") or 0) >= 2:
                yield path, data

    def test_all_schema2_manifests_have_review7_fields(self) -> None:
        """★承重★：任一 schema>=2 清单缺 Review7 必填字段即失败。"""
        offenders = []
        for path, data in self._schema2_manifests():
            missing = sorted(f for f in self.sync.RUN_MANIFEST_REQUIRED_FIELDS if not data.get(f))
            if missing:
                offenders.append(f"{path.name}: 缺 {missing}")
        self.assertEqual(offenders, [], "以下 schema>=2 清单缺 Review7 必填字段：\n" + "\n".join(offenders))

    def test_all_schema2_manifests_have_valid_binding_status(self) -> None:
        """★承重★：binding_status 必须是合法值（含 LEGACY_UNBOUND）。"""
        offenders = []
        for path, data in self._schema2_manifests():
            bs = str(data.get("binding_status") or "")
            if bs not in self.sync.RUN_MANIFEST_BINDING_STATUSES:
                offenders.append(f"{path.name}: binding_status={bs!r}")
        self.assertEqual(offenders, [], "以下清单 binding_status 非法：\n" + "\n".join(offenders))


if __name__ == "__main__":
    unittest.main()
