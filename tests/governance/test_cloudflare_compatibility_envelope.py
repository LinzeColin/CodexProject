from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"


def governance_load_yaml(path: Path):
    """用仓库自带的 yaml-free 加载器读 yaml。

    CI 的治理测试步骤不安装 pyyaml（`validate_project_governance.load_yaml` 会 ImportError
    回退到纯 Python 的 `fallback_yaml_load`）。测试里直接 `import yaml` 会在 CI 环境
    `ModuleNotFoundError`——必须走这条与 CI 一致的路径。
    """
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location(
        "vpg_cloudflare_test", SCRIPTS / "validate_project_governance.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["vpg_cloudflare_test"] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module.load_yaml(path)
DEPLOYMENTS = ROOT / "governance/cloudflare/deployments.json"
RUN_MANIFEST = ROOT / "governance/run_manifests/CF-L2-20260710.json"
REQUIRED_PROJECTS = {
    "linze-home-hub",
    "nab",
    "eei",
    "openaidatabase",
    "pfi",
    "serenity-alipay",
}
EXPECTED_ONLINE_SURFACES = {
    "linze-home-hub": ("deployed_custom_domain_verified", "https://home.linzezhang.com"),
    "nab": ("deployed_custom_domain_verified", "https://nab.linzezhang.com"),
    "eei": ("deployed_workers_dev_domain_pending", "https://codex-eei.linzezhang35.workers.dev"),
    "openaidatabase": ("deployed_custom_domain_verified", "https://memoryatlas.linzezhang.com"),
    "pfi": ("deployed_workers_dev_domain_pending", "https://codex-pfi.linzezhang35.workers.dev"),
    "serenity-alipay": (
        "deployed_workers_dev_domain_pending",
        "https://serenity-alipay.linzezhang35.workers.dev",
    ),
}
EXPECTED_EVIDENCE_COMMITS = {
    "linze-home-hub": "59347956c03ee2810358887f20cb13bdc2ef9289",
    "nab": "d0721022cfb48ae3edf439fffeb92c36ed00cefc",
    "eei": "ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935",
    "openaidatabase": "00f4187f43960a3b25fc696ae2a15951f4431763",
    "pfi": "ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935",
    "serenity-alipay": "ed0fe3a3e8f2f0f46d0f4f442c23fed5ed093935",
}
# CF-L2-20260710 是一次已完成交付的历史证据。其中 OpenAIDatabase 已迁往 LinzeColin/AgentDatabase、
# PFI 已迁往 LinzeColin/MetaDatabase，两者的 delivery_tasks.yaml 随项目迁走，本仓不再持有。
# 部署事实本身仍由本仓 governance/cloudflare/deployments.json 保存并被本文件其余用例校验。
PROJECT_TASK_FILES = (
    ROOT / "OpenAIDatabase/docs/governance/delivery_tasks.yaml",
    ROOT / "PFI/docs/governance/delivery_tasks.yaml",
)
MIGRATED_TASK_FILE_OWNERS = {
    "OpenAIDatabase": "LinzeColin/AgentDatabase",
    "PFI": "LinzeColin/MetaDatabase",
}


class CloudflareCompatibilityGovernanceTests(unittest.TestCase):
    def test_required_deployments_are_recorded_without_false_live_claims(self) -> None:
        document = json.loads(DEPLOYMENTS.read_text(encoding="utf-8"))
        records = {item["project_id"]: item for item in document["projects"]}
        self.assertEqual(set(records), REQUIRED_PROJECTS)
        for project_id, record in records.items():
            with self.subTest(project_id=project_id):
                if str(record["deploy_result"]).startswith("deployed_"):
                    self.assertTrue(record["actual_url"])
                    self.assertEqual(record["http_verification"], "verified_200")
                else:
                    self.assertFalse(record["actual_url"])

    def test_each_changed_project_has_the_cloudflare_delivery_task(self) -> None:
        """交付任务记录：仍在本仓的项目直接校验；已迁出的改为校验迁移登记。

        原实现无条件读取各项目的 delivery_tasks.yaml。OpenAIDatabase 与 PFI 迁出后该文件
        随项目走，本仓读不到 -> 测试永久 FileNotFoundError，反而掩盖了它该守的东西。
        现改为：文件在则照旧断言；不在则必须能在注册表里证明该项目确已迁出（而非凭空消失）。
        """
        registry = governance_load_yaml(ROOT / "governance" / "projects.yaml")
        migrated = {
            entry["project_id"]: entry
            for entry in (registry.get("migrated_projects") or [])
            if isinstance(entry, dict)
        }
        for path in PROJECT_TASK_FILES:
            project_id = path.relative_to(ROOT).parts[0]
            with self.subTest(path=path):
                if path.exists():
                    self.assertIn('task_id: "CF-L2-20260710"', path.read_text(encoding="utf-8"))
                    continue
                # 文件不在 -> 该项目必须已登记迁出，且目标仓与预期一致
                self.assertIn(
                    project_id, migrated,
                    f"{project_id} 的 delivery_tasks.yaml 不在本仓，且注册表无迁出登记——"
                    f"这不是迁移，是文件凭空消失。",
                )
                self.assertEqual(
                    migrated[project_id]["target_repo"],
                    MIGRATED_TASK_FILE_OWNERS[project_id],
                )

    def test_required_l2_online_surfaces_are_verified(self) -> None:
        document = json.loads(DEPLOYMENTS.read_text(encoding="utf-8"))
        records = {item["project_id"]: item for item in document["projects"]}
        self.assertEqual(set(records), set(EXPECTED_ONLINE_SURFACES))
        for project_id, (expected_result, expected_url) in EXPECTED_ONLINE_SURFACES.items():
            with self.subTest(project_id=project_id):
                record = records[project_id]
                self.assertEqual(record["deploy_result"], expected_result)
                self.assertEqual(record["actual_url"], expected_url)
                self.assertEqual(record["http_verification"], "verified_200")
                self.assertEqual(record["evidence_commit_sha"], EXPECTED_EVIDENCE_COMMITS[project_id])

    def test_root_run_manifest_binds_the_acceptance(self) -> None:
        manifest = json.loads(RUN_MANIFEST.read_text(encoding="utf-8"))
        self.assertGreaterEqual(manifest["schema_version"], 2)
        self.assertEqual(manifest["task_id"], "CF-L2-20260710")
        self.assertIn("ACC-CF-L2-20260710", manifest["acceptance_ids"])
        self.assertIn("governance/cloudflare/deployments.json", manifest["changed_files_actual"])


if __name__ == "__main__":
    unittest.main()
