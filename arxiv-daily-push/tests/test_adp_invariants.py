"""V0.3 十条系统不变量的保护测试（业务规则与系统不变量.md）.

每个测试的 docstring 指出它防止的具体事故（验收与测试.md 测试原则）。
依赖 venv（fsrs/yaml/jinja2）；缺依赖时整文件跳过，不污染旧套件。
运行: PYTHONPATH=src var/venv/bin/python -m unittest tests/test_adp_invariants.py
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import fsrs  # noqa: F401
    import yaml  # noqa: F401
    import jinja2  # noqa: F401
    _DEPS = True
except ImportError:
    _DEPS = False

ABSTRACT = (
    "We propose a new framework for efficient learning. "
    "Our method achieves 92% accuracy on three real-world benchmarks. "
    "However, the approach is limited to supervised settings. "
    "These results suggest that transfer to clinical applications may be possible. "
    "Future work should extend the framework to multimodal data."
)


def _item(stable_id: str = "2507.01234", version: int = 1) -> dict:
    return {
        "source_id": f"arxiv:{stable_id}",
        "source_type": "arxiv",
        "stable_id": stable_id,
        "title": "Efficient Learning Framework",
        "retrieved_at": "2026-07-14T00:00:00+00:00",
        "canonical_url": f"https://arxiv.org/abs/{stable_id}v{version}",
        "metadata": {"arxiv": {
            "versioned_id": f"{stable_id}v{version}",
            "primary_category": "cs.LG", "categories": ["cs.LG", "cs.AI"],
            "published": "2026-07-13T18:00:00Z", "updated": "2026-07-13T18:00:00Z",
            "authors": ["A", "B"], "summary": ABSTRACT, "comment": "10 pages",
            "journal_ref": "", "doi": "",
        }},
        "license": {"status": "unknown", "usage": "private_learning_link_only"},
    }


@unittest.skipUnless(_DEPS, "adp venv dependencies not installed")
class InvariantTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["ADP_DATA_DIR"] = self._tmp.name
        from adp import store
        from adp.claims import extract_claims, store_claims
        from adp.lesson import generate_lesson

        self.store = store
        self.conn = store.connect(Path(self._tmp.name) / "test.sqlite3")
        store.upsert_source(self.conn, source_id="SRC-ARXIV", board_id="B1", name="arXiv")
        _, self.version_id, _, _ = store.ingest_document(self.conn, _item())
        store_claims(self.conn, extract_claims(self.version_id, ABSTRACT))
        self.lesson_id = "L-2026-07-14-2507.01234"
        generate_lesson(self.conn, lesson_id=self.lesson_id, candidate_id="arxiv:2507.01234@2026-07-14",
                        doc_version_id=self.version_id, as_of_date="2026-07-14")

    def tearDown(self) -> None:
        self.conn.close()
        os.environ.pop("ADP_DATA_DIR", None)
        self._tmp.cleanup()

    def _thresholds(self):
        from adp.config import load_thresholds

        return load_thresholds()

    def test_inv1_delivery_never_changes_learning_state(self) -> None:
        """防事故：发了邮件被当成学会了（EMAIL_SENT ≠ LEARNED）."""
        from adp.delivery import deliver_lesson
        from adp.review import learning_state

        before = learning_state(self.conn, self.lesson_id)
        receipt = deliver_lesson(self.conn, self.lesson_id)
        after = learning_state(self.conn, self.lesson_id)
        self.assertEqual(before["evidence_state"], after["evidence_state"])
        self.assertEqual(after["recall_count"], 0)
        self.assertIn("发送状态 ≠ 学习状态", receipt["note"])

    def test_inv2_learned_requires_immutable_recall_event(self) -> None:
        """防事故：没有任何回忆证据的条目显示为已学会."""
        from adp.review import grade_recall, learning_state

        self.assertNotEqual(learning_state(self.conn, self.lesson_id)["evidence_state"], "已学会")
        outcome = grade_recall(self.conn, self.lesson_id, 3, self._thresholds())
        self.assertFalse(outcome["duplicate"])
        state = learning_state(self.conn, self.lesson_id)
        self.assertEqual(state["evidence_state"], "已学会")
        self.assertEqual(state["recall_count"], 1)

    def test_inv3_mastery_needs_two_recalls_plus_application_and_manual_is_separate(self) -> None:
        """防事故：手动标记「已掌握」冒充证据、或单次回忆即掌握."""
        from adp.review import grade_recall, learning_state, manual_mark, manual_undo

        manual_mark(self.conn, self.lesson_id, "已掌握")
        state = learning_state(self.conn, self.lesson_id)
        self.assertEqual(state["manual_state"], "已掌握")
        self.assertNotEqual(state["evidence_state"], "已掌握")  # 主观标记不改证据态

        now = datetime.now(timezone.utc)
        grade_recall(self.conn, self.lesson_id, 3, self._thresholds(), at=now)
        grade_recall(self.conn, self.lesson_id, 4, self._thresholds(), at=now + timedelta(days=3))
        self.assertNotEqual(learning_state(self.conn, self.lesson_id)["evidence_state"], "已掌握")
        self.conn.execute(
            "INSERT INTO applications (item_id, kind, payload_json, outcome, at) VALUES (?, 'outcome', '{}', 'ok', ?)",
            (self.lesson_id, self.store.utcnow_iso()),
        )
        self.assertEqual(learning_state(self.conn, self.lesson_id)["evidence_state"], "已掌握")
        # 撤销手动标记：事件不删除，只标 undone
        undone = manual_undo(self.conn, state["manual_event_id"])
        self.assertTrue(undone)
        self.assertIsNone(learning_state(self.conn, self.lesson_id)["manual_state"])

    def test_inv4_correction_reopens_affected_knowledge_and_reminds(self) -> None:
        """防事故：论文出了 v2/撤稿，旧讲义与掌握度仍被当作有效（纠错不传播）."""
        from adp.corrections import detect_and_propagate, resolve, unresolved
        from adp.review import grade_recall, learning_state, manual_mark

        grade_recall(self.conn, self.lesson_id, 3, self._thresholds())
        manual_mark(self.conn, self.lesson_id, "已掌握")  # 手动标记不得豁免纠错提醒
        self.assertEqual(learning_state(self.conn, self.lesson_id)["evidence_state"], "已学会")

        # 注入一次真实形态的版本更新（同 stable_id 的 v2）
        item = _item(version=2)
        item["metadata"]["arxiv"]["summary"] = ABSTRACT + " We add a new ablation study."
        self.store.ingest_document(self.conn, item)

        report = detect_and_propagate(self.conn)
        self.assertEqual(report["corrections_created"], 1)
        detail = report["details"][0]
        self.assertEqual(detail["lesson_id"], self.lesson_id)
        self.assertIn(self.lesson_id, detail["affected"]["lessons"])
        self.assertTrue(detail["affected"]["claims"])  # 受影响声明被找回

        state = learning_state(self.conn, self.lesson_id)
        self.assertEqual(state["evidence_state"], "重开待复习")
        self.assertTrue(state["reopened"])
        row = self.conn.execute("SELECT status FROM lessons WHERE id=?", (self.lesson_id,)).fetchone()
        self.assertEqual(row["status"], "reopened")
        self.assertEqual(len(unresolved(self.conn)), 1)  # 强提醒数据源非空
        debt = self.conn.execute(
            "SELECT COUNT(*) n FROM debts WHERE kind='evidence_stale' AND status='open'"
        ).fetchone()["n"]
        self.assertEqual(debt, 1)

        # 幂等：再次检测不重复开纠错
        self.assertEqual(detect_and_propagate(self.conn)["corrections_created"], 0)
        # 重新复习后关闭
        grade_recall(self.conn, self.lesson_id, 3, self._thresholds(), idempotency_key="after-reopen")
        self.assertTrue(resolve(self.conn, detail["correction_id"]))
        self.assertEqual(len(unresolved(self.conn)), 0)

    def test_inv5_no_side_effect_without_authorization(self) -> None:
        """防事故：未授权时真实发送发生或 manifest 谎报已交付."""
        from adp.delivery import authorization_state, deliver_lesson
        from adp.manifest import ManifestViolation, write_manifest

        auth = authorization_state()
        self.assertFalse(auth["side_effects_authorized"])
        receipt = deliver_lesson(self.conn, self.lesson_id)
        self.assertFalse(receipt["delivered"])
        self.assertEqual(receipt["result"], "BLOCKED_AUTH")
        self.assertTrue(Path(receipt["preview"]).exists())  # 只留预览，不真发
        with self.assertRaises(ManifestViolation):
            write_manifest(None, {
                "run_id": "x", "result": "正常", "side_effects_authorized": False,
                "counts": {"已交付": 1},
            })

    def test_inv6_same_idempotency_key_never_fires_twice(self) -> None:
        """防事故：同一防重号产生第二次发送或第二次学习完成."""
        from adp.delivery import deliver_lesson
        from adp.review import grade_recall

        first = grade_recall(self.conn, self.lesson_id, 3, self._thresholds(), idempotency_key="K1")
        second = grade_recall(self.conn, self.lesson_id, 4, self._thresholds(), idempotency_key="K1")
        self.assertFalse(first["duplicate"])
        self.assertTrue(second["duplicate"])
        events = self.conn.execute(
            "SELECT COUNT(*) AS n FROM learning_events WHERE kind='self_grade'"
        ).fetchone()["n"]
        self.assertEqual(events, 1)

        d1 = deliver_lesson(self.conn, self.lesson_id)
        d2 = deliver_lesson(self.conn, self.lesson_id)
        self.assertFalse(d1["duplicate"])
        self.assertTrue(d2["duplicate"])
        self.assertIn("同日重发被拒", d2["reason"])

    def test_inv7_every_lesson_sentence_traceable(self) -> None:
        """防事故：讲义出现无法跳到出处的句子（不可溯源内容）."""
        from adp.lesson import validate_traceability

        report = validate_traceability(self.conn, self.lesson_id)
        self.assertTrue(report["ok"], report)
        self.assertGreater(report["bindings"], 0)

    def test_inv8_single_version_pointer_per_domain(self) -> None:
        """防事故：多个文件各自宣称不同的当前合同/参数版本（漂移复发）."""
        import yaml

        root = Path(__file__).resolve().parents[1]
        current = yaml.safe_load((root / "docs" / "pursuing_goal" / "CURRENT.yaml").read_text(encoding="utf-8"))
        rebuild = current.get("rebuild_v03") or {}
        self.assertEqual(rebuild.get("status"), "active_development_contract")
        self.assertEqual(rebuild.get("thresholds_registry"), "config/thresholds_v0_3.yaml")
        registry = yaml.safe_load((root / "config" / "thresholds_v0_3.yaml").read_text(encoding="utf-8"))
        self.assertEqual(registry["registry"]["status"], "active")
        status = yaml.safe_load((root / "docs" / "v03" / "STATUS.yaml").read_text(encoding="utf-8"))
        self.assertEqual(status["thresholds"], "config/thresholds_v0_3.yaml")
        self.assertEqual(status["production_side_effects"], "none_enabled")

    def test_inv9_status_badge_reads_only_latest_manifest_line(self) -> None:
        """防事故：首页状态点读旧行/手写状态而不是最近一次运行."""
        from adp.manifest import latest_result, write_manifest

        write_manifest(None, {"run_id": "r1", "result": "正常", "side_effects_authorized": False, "counts": {}})
        write_manifest(None, {"run_id": "r2", "result": "弃权", "弃权原因": "最高分低于弃权线",
                              "side_effects_authorized": False, "counts": {}})
        self.assertEqual(latest_result(), "弃权")

    def test_inv10_selection_fully_replayable(self) -> None:
        """防事故：排序结果无法复现（参数/贡献/硬门未随决策保存）."""
        from adp.arxiv_source import candidates_for_date
        from adp.selection import select_daily

        outcome = select_daily(
            self.conn, run_id="run-1", as_of_date="2026-07-14",
            candidates=candidates_for_date(self.conn, "2026-07-14"),
            thresholds=self._thresholds(),
        )
        row = self.conn.execute("SELECT * FROM selections WHERE run_id='run-1'").fetchone()
        params = json.loads(row["params_json"])
        self.assertIn("weights", params)
        self.assertIn("abstain_threshold", params)
        if not row["abstain"]:
            contributions = json.loads(row["contributions_json"])
            candidate = self.conn.execute(
                "SELECT features_json, gate_results_json FROM candidates WHERE id=?",
                (row["candidate_id"],),
            ).fetchone()
            features = json.loads(candidate["features_json"])
            gates = json.loads(candidate["gate_results_json"])
            self.assertTrue(all(gates.values()))
            for key, weight in params["weights"].items():
                self.assertAlmostEqual(contributions[key], round(weight * features[key], 3), places=2)


@unittest.skipUnless(_DEPS, "adp venv dependencies not installed")
class RemoteGuardTests(unittest.TestCase):
    """防事故：公网入口（Tunnel 直连、无登录）被外人代按 Owner 决策按钮."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        os.environ["ADP_DATA_DIR"] = self._tmp.name

    def tearDown(self) -> None:
        os.environ.pop("ADP_DATA_DIR", None)
        self._tmp.cleanup()

    def _client(self):
        from fastapi.testclient import TestClient

        from adp.webapp import app

        return TestClient(app)

    def test_remote_post_blocked_except_recall(self) -> None:
        """带 CF 头（=经隧道来访）的决策类 POST 一律 403；主动回忆放行."""
        cf = {"cf-connecting-ip": "203.0.113.9"}
        with self._client() as client:
            for path in ("/api/pilot/decision/adopt", "/api/r5/promote",
                         "/api/item/x/state/掌握", "/api/undo/1",
                         "/api/corrections/1/resolve", "/api/transfer/x"):
                self.assertEqual(client.post(path, headers=cf).status_code, 403, path)
            # 主动回忆两端点放行守卫，但编造的讲义 ID 必须 404——
            # 防公网来客往主库注入垃圾 review_state/事件行（复审修复）。
            self.assertEqual(client.post("/api/recall/nope/reveal", headers=cf).status_code, 404)
            self.assertEqual(client.post("/api/recall/nope/grade/3", headers=cf).status_code, 404)
            # 远程 GET 全放行；本机（无 CF 头）POST 不受守卫影响
            self.assertNotEqual(client.get("/system", headers=cf).status_code, 403)
            self.assertNotEqual(client.post("/api/undo/999999").status_code, 403)


if __name__ == "__main__":
    unittest.main()
