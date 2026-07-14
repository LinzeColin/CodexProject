"""资格硬门与加权纯函数的保护测试（验收与测试.md：各 1 用例 + 边界值）.

每个测试的 docstring 指出它防止的具体事故。缺 venv 依赖时跳过。
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

try:
    import yaml  # noqa: F401
    _DEPS = True
except ImportError:
    _DEPS = False


def _candidate(**overrides):
    base = {
        "doc_id": "arxiv:2507.01234",
        "version_no": 1,
        "title": "Efficient machine learning for semiconductor manufacturing",
        "canonical_url": "https://arxiv.org/abs/2507.01234v1",
        "metadata": {"arxiv": {
            "versioned_id": "2507.01234v1",
            "primary_category": "cs.LG", "categories": ["cs.LG", "eess.SY"],
            "published": "2026-07-13T18:00:00Z",
            "summary": "We propose an efficient machine learning method with 92% accuracy for real-world semiconductor deployment.",
            "doi": "10.1000/x", "journal_ref": "", "comment": "8 pages, 3 figures", "authors": ["A"],
        }},
        "license": {"status": "unknown", "usage": "private_learning_link_only"},
    }
    base.update(overrides)
    return base


_CONTEXT = {"seen_version_ids": set(), "source_health": "active"}


@unittest.skipUnless(_DEPS, "adp venv dependencies not installed")
class GateTests(unittest.TestCase):
    def test_gates_pass_for_clean_candidate(self) -> None:
        """防事故：合规候选被硬门误杀导致永远弃权."""
        from adp.gates import run_gates

        result = run_gates(_candidate(), _CONTEXT)
        self.assertTrue(result.passed, result.results)
        self.assertEqual(result.reject_reason, "")

    def test_gate_evidence_traceable_blocks_missing_abstract(self) -> None:
        """防事故：无摘要（无法定位声明）的条目进入学习流."""
        from adp.gates import run_gates

        candidate = _candidate()
        candidate["metadata"]["arxiv"]["summary"] = "  "
        result = run_gates(candidate, _CONTEXT)
        self.assertFalse(result.passed)
        self.assertFalse(result.results["evidence_traceable"])
        self.assertIn("原文", result.reject_reason)

    def test_gate_https_blocks_non_official_host(self) -> None:
        """防事故：仿冒/镜像站内容被当作官方来源."""
        from adp.gates import run_gates

        result = run_gates(_candidate(canonical_url="http://arxiv.org/abs/x"), _CONTEXT)
        self.assertFalse(result.results["official_https_source"])
        result2 = run_gates(_candidate(canonical_url="https://evil.example/abs/x"), _CONTEXT)
        self.assertFalse(result2.results["official_https_source"])

    def test_gate_dedup_blocks_already_lessoned_version(self) -> None:
        """防事故：同一版本重复入选、重复生成讲义（不变量 6 的选择面）."""
        from adp.gates import run_gates

        context = dict(_CONTEXT, seen_version_ids={"2507.01234v1"})
        result = run_gates(_candidate(), context)
        self.assertFalse(result.results["dedup_version_unique"])
        self.assertIn("重复", result.reject_reason)

    def test_gate_source_health_blocks_auto_disabled(self) -> None:
        """防事故：连续失败已停用的来源仍然供给候选."""
        from adp.gates import run_gates

        result = run_gates(_candidate(), dict(_CONTEXT, source_health="disabled_auto"))
        self.assertFalse(result.results["source_health_ok"])

    def test_gate_license_blocks_unknown_usage(self) -> None:
        """防事故：许可不明内容被纳入并对外镜像."""
        from adp.gates import run_gates

        candidate = _candidate(license={"status": "unknown", "usage": "redistribution"})
        result = run_gates(candidate, _CONTEXT)
        self.assertFalse(result.results["license_policy_ok"])


@unittest.skipUnless(_DEPS, "adp venv dependencies not installed")
class FeatureTests(unittest.TestCase):
    def _context(self):
        return {
            "as_of": datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc),
            "learned_tokens": set(), "seen_docs": [],
            "due_topic_tokens": set(), "recent_selected_primary": [],
        }

    def test_novelty_excludes_candidate_itself(self) -> None:
        """防事故：候选与自己比相似度（新颖度恒为 0，14 分权重失效）."""
        from adp.features import _tokens, score_features

        candidate = _candidate()
        meta = candidate["metadata"]["arxiv"]
        own_tokens = _tokens(f"{candidate['title']} {meta['summary']}")
        context = self._context()
        context["seen_docs"] = [(candidate["doc_id"], own_tokens)]
        features = score_features(candidate, context)
        self.assertGreater(features["novelty_to_user"]["value"], 0.0)
        context["seen_docs"].append(("arxiv:other", own_tokens))  # 他人同词面 → 新颖度应归零
        features2 = score_features(candidate, context)
        self.assertEqual(features2["novelty_to_user"]["value"], 0.0)

    def test_all_feature_values_in_unit_range_and_deterministic(self) -> None:
        """防事故：特征越界（>1）放大权重导致排序不可解释、不可复现."""
        from adp.features import score_features

        first = score_features(_candidate(), self._context())
        second = score_features(_candidate(), self._context())
        for key, entry in first.items():
            self.assertGreaterEqual(entry["value"], 0.0, key)
            self.assertLessEqual(entry["value"], 1.0, key)
            self.assertTrue(entry["reason"])
        self.assertEqual({k: v["value"] for k, v in first.items()},
                         {k: v["value"] for k, v in second.items()})

    def test_registry_weights_sum_104_and_diversity_cap(self) -> None:
        """防事故：注册表漂移（权重和≠104）或单板块期多样性越过上限 10（盲点二）."""
        from adp.config import load_thresholds

        thresholds = load_thresholds()
        self.assertEqual(thresholds.weight_total, 104)
        effective = thresholds.effective_weights(single_board=True)
        self.assertEqual(effective["diversity"], 10)
        self.assertEqual(thresholds.effective_weights(single_board=False)["diversity"], 17)

    def test_total_score_is_weighted_sum_minus_attention_penalty(self) -> None:
        """防事故：打分与公示的公式不一致（贡献表对不上总分）."""
        from adp.config import load_thresholds
        from adp.features import attention_cost, score_features, total_score

        thresholds = load_thresholds()
        features = score_features(_candidate(), self._context())
        cost, _ = attention_cost(_candidate())
        score, contributions = total_score(
            features, thresholds.effective_weights(single_board=True), cost,
            thresholds.attention_cost_penalty,
        )
        self.assertAlmostEqual(score, sum(contributions.values()) - thresholds.attention_cost_penalty * cost, places=3)

    def test_abstain_when_top_below_threshold(self) -> None:
        """防事故：低价值日仍然硬塞一篇（弃权机制失效）."""
        from adp.selection import evaluate_candidates
        from adp.config import load_thresholds

        thresholds = load_thresholds()
        boring = _candidate()
        boring["metadata"]["arxiv"].update({
            "summary": "Miscellaneous notes.", "categories": ["math.GM"],
            "primary_category": "math.GM", "doi": "", "comment": "",
            "published": "2020-01-01T00:00:00Z",
        })
        boring["title"] = "Notes"
        scored, _ = evaluate_candidates([boring], self._context(), thresholds, gate_context=_CONTEXT)
        self.assertTrue(scored)
        self.assertLess(scored[0]["score"], thresholds.abstain_threshold)

    def test_explanations_cover_top_and_runner_up(self) -> None:
        """防事故：双向解释缺失（只说选了什么，不说为什么不是第二名）."""
        from adp.selection import evaluate_candidates, explain_choice
        from adp.config import load_thresholds

        second = _candidate(doc_id="arxiv:2507.09999", title="A note on algebraic tori")
        second["metadata"]["arxiv"].update({
            "versioned_id": "2507.09999v1", "summary": "We study algebraic structures with new bounds.",
            "categories": ["math.AG"], "primary_category": "math.AG", "doi": "",
        })
        scored, _ = evaluate_candidates([_candidate(), second], self._context(),
                                        load_thresholds(), gate_context=_CONTEXT)
        why, why_not = explain_choice(scored[0], scored[1])
        self.assertIn("总分", why)
        self.assertIn("第二名", why_not)


@unittest.skipUnless(_DEPS, "adp venv dependencies not installed")
class ClaimLocatorTests(unittest.TestCase):
    def test_locators_are_reversible(self) -> None:
        """防事故：定位漂移——点击句子跳到错误出处."""
        from adp.claims import extract_claims, split_sentences

        abstract = ("We propose X. Our method achieves 90% accuracy. "
                    "However, limits remain. Results suggest more work.")
        for start, end, sentence in split_sentences(abstract):
            self.assertEqual(abstract[start:end].strip(), sentence)
        claims = extract_claims("v1", abstract)
        types = {c["type"] for c in claims}
        self.assertIn("paper_fact", types)
        self.assertIn("author_claim", types)


@unittest.skipUnless(_DEPS, "adp venv dependencies not installed")
class FsrsMappingTests(unittest.TestCase):
    def test_four_grades_give_monotonic_intervals(self) -> None:
        """防事故：评分档位与间隔倒挂（「轻松」比「忘了」复习得更勤）."""
        try:
            import fsrs  # noqa: F401
        except ImportError:
            self.skipTest("fsrs not installed")
        import os
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            os.environ["ADP_DATA_DIR"] = tmp
            try:
                from adp import store
                from adp.config import load_thresholds
                from adp.review import preview_intervals

                conn = store.connect(Path(tmp) / "t.sqlite3")
                thresholds = load_thresholds()
                at = datetime(2026, 7, 14, 8, 0, tzinfo=timezone.utc)
                from fsrs import Rating, Scheduler
                from fsrs import Card

                scheduler = Scheduler(desired_retention=thresholds.desired_retention)
                dues = {}
                for grade in (1, 2, 3, 4):
                    card, _ = scheduler.review_card(Card(), Rating(grade), at)
                    dues[grade] = card.due
                self.assertLess(dues[1], dues[3])
                self.assertLessEqual(dues[3], dues[4])
                previews = preview_intervals(conn, "any", thresholds, at=at)
                self.assertEqual(set(previews), {1, 2, 3, 4})
                conn.close()
            finally:
                os.environ.pop("ADP_DATA_DIR", None)


if __name__ == "__main__":
    unittest.main()
