from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path


DATABASE_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = DATABASE_DIR / "scripts"
PERFORMANCE_SCRIPT = SCRIPTS_DIR / "evaluate_memory_retrieval_performance.py"
CONFIG = DATABASE_DIR / "config/evaluation/memory_retrieval_performance_v1.json"
GOLD_DATASET = DATABASE_DIR / "data/derived/evaluation/memory_gold/benchmark_v1.jsonl"


def load_module(name: str, path: Path):
    if str(SCRIPTS_DIR) not in sys.path:
        sys.path.insert(0, str(SCRIPTS_DIR))
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class MemoryRetrievalPerformanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.evaluator = load_module("memory_retrieval_performance_test", PERFORMANCE_SCRIPT)
        cls.retrieval = sys.modules["memory_retrieval"]
        cls.config = json.loads(CONFIG.read_text(encoding="utf-8"))
        cls.handshake = json.loads(
            (DATABASE_DIR / "data/memory/agent-memory.json").read_text(encoding="utf-8")
        )

    def test_portable_index_routes_existing_bilingual_alias_noise_cases_without_new_samples(self) -> None:
        case = json.loads(GOLD_DATASET.read_text(encoding="utf-8").splitlines()[0])
        state = case["state"]
        shard_map = {str(row["id"]): "in-process://gold" for row in state}
        index = self.retrieval.build_lexical_index(state, shard_map, statuses=None)
        route = self.retrieval.route_lexical_index(
            index,
            f"{case['query']['text']} {case['query']['noise']}",
            aliases=case["query"]["aliases"],
            scope="SyntheticLab-01",
            limit=len(state),
        )

        self.assertTrue(set(case["expected_ids"]).issubset(route["record_ids"]))
        self.assertEqual(route["content_get_count"], 2)
        self.assertEqual(route["recursive_full_tree_scan_count"], 0)
        self.assertEqual(route["shards"], ["in-process://gold"])

    def test_generated_handshake_routes_every_public_active_record_to_one_shard(self) -> None:
        contract = self.handshake["retrieval_contract"]
        index = contract["index"]

        self.assertEqual(index["record_count"], len(self.handshake["active_index"]))
        for row in self.handshake["active_index"]:
            route = self.retrieval.route_lexical_index(index, row["id"], limit=1)
            self.assertEqual(route["record_ids"], [row["id"]])
            self.assertEqual(route["shards"], [row["shard"]])
            self.assertLessEqual(route["content_get_count"], 2)

    def test_local_substring_prefilter_falls_back_when_ngram_completeness_is_not_provable(self) -> None:
        self.assertFalse(self.retrieval.supports_complete_substring_prefilter("a."))
        self.assertFalse(self.retrieval.supports_complete_substring_prefilter("é"))
        self.assertTrue(self.retrieval.supports_complete_substring_prefilter("abc"))
        self.assertTrue(self.retrieval.supports_complete_substring_prefilter("中文"))

    def test_conditional_reader_handles_cold_304_and_commit_invalidation_without_persisting_auth(self) -> None:
        responses = [
            self.retrieval.TransportResponse(200, {"ETag": '"v1"'}, b"one"),
            self.retrieval.TransportResponse(304, {}, b""),
            self.retrieval.TransportResponse(200, {"ETag": '"v2"'}, b"two"),
        ]
        calls: list[dict[str, object]] = []

        def requester(url, headers, max_bytes):
            calls.append({"url": url, "headers": dict(headers), "max_bytes": max_bytes})
            return responses.pop(0)

        reader = self.retrieval.ConditionalGitHubReader(
            lambda: "test",
            requester=requester,
            sleeper=lambda _: None,
        )
        path = "OpenAIDatabase/data/memory/agent-memory.json"
        first = reader.read("LinzeColin", "CodexProject", path, "a" * 40)
        warm = reader.read("LinzeColin", "CodexProject", path, "a" * 40)
        changed = reader.read("LinzeColin", "CodexProject", path, "b" * 40)

        self.assertEqual((first["status"], warm["status"], changed["status"]), (200, 304, 200))
        self.assertEqual(warm["body"], b"one")
        self.assertEqual(warm["transferred_bytes"], 0)
        self.assertEqual(calls[1]["headers"]["If-None-Match"], '"v1"')
        self.assertEqual(reader.cache_commits("LinzeColin", "CodexProject", path), ["b" * 40])
        self.assertNotIn("Authorization", json.dumps(changed, default=str))
        self.assertFalse(responses)

    def test_rate_limit_retry_is_bounded_and_respects_retry_after(self) -> None:
        responses = [
            self.retrieval.TransportResponse(429, {"Retry-After": "2"}, b""),
            self.retrieval.TransportResponse(200, {"ETag": '"ok"'}, b"value"),
        ]
        slept: list[float] = []
        reader = self.retrieval.ConditionalGitHubReader(
            lambda: "test",
            requester=lambda *_: responses.pop(0),
            sleeper=slept.append,
            clock=lambda: 1_700_000_000.0,
        )
        result = reader.read(
            "LinzeColin",
            "CodexProject",
            "OpenAIDatabase/data/memory/agent-memory.json",
            "a" * 40,
        )

        self.assertEqual(result["request_count"], 2)
        self.assertEqual(result["retry_delays_seconds"], [2.0])
        self.assertEqual(slept, [2.0])
        blocked = self.retrieval.ConditionalGitHubReader(
            lambda: "test",
            requester=lambda *_: self.retrieval.TransportResponse(
                429, {"Retry-After": "121"}, b""
            ),
            sleeper=lambda _: self.fail("out-of-bound retry must not sleep"),
        )
        with self.assertRaisesRegex(
            self.retrieval.RetrievalError, "github_retry_delay_exceeds_bound"
        ):
            blocked.read(
                "LinzeColin",
                "CodexProject",
                "OpenAIDatabase/data/memory/agent-memory.json",
                "a" * 40,
            )

        secondary_responses = [
            self.retrieval.TransportResponse(
                403,
                {},
                b'{"message":"You have exceeded a secondary rate limit."}',
            ),
            self.retrieval.TransportResponse(200, {"ETag": '"ok"'}, b"value"),
        ]
        secondary_slept: list[float] = []
        secondary = self.retrieval.ConditionalGitHubReader(
            lambda: "test",
            requester=lambda *_: secondary_responses.pop(0),
            sleeper=secondary_slept.append,
        )
        secondary_result = secondary.read(
            "LinzeColin",
            "CodexProject",
            "OpenAIDatabase/data/memory/agent-memory.json",
            "a" * 40,
        )
        self.assertEqual(secondary_result["request_count"], 2)
        self.assertEqual(secondary_slept, [60.0])

    def test_tracked_performance_report_and_current_runtime_pass_all_gates(self) -> None:
        report, failures = self.evaluator.evaluate(DATABASE_DIR, self.config)
        tracked = self.evaluator.load_json(
            DATABASE_DIR / self.config["files"]["report"]
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(failures, {"hard_failures": [], "runtime_failures": []})
        self.assertEqual(
            self.evaluator.deterministic_projection(report),
            self.evaluator.deterministic_projection(tracked),
        )
        self.assertEqual(report["quality"]["case_count"], 160)
        self.assertEqual(report["quality"]["recall_at_5_degradation"], 0.0)
        self.assertEqual(report["request_profiles"]["warm_304"]["transferred_bytes"], 0)
        self.assertLessEqual(
            report["runtime_observation"]["metrics"]["local_query_p95_ms"], 250
        )
        self.assertLessEqual(
            report["runtime_observation"]["metrics"]["index_rebuild_p95_ms"], 30000
        )


if __name__ == "__main__":
    unittest.main()
