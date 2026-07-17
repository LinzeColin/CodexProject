from __future__ import annotations

import copy
import json
import unittest

from KMFA.tools import build_v015_s23_p3_stability_usability as builder
from KMFA.tools import v015_s23_p3_stability_usability as model


class StabilityUsabilityTests(unittest.TestCase):
    @staticmethod
    def browser() -> dict:
        return json.loads(builder.BROWSER_ACCEPTANCE_PATH.read_text(encoding="utf-8"))

    def test_taskpack_contract_and_scope_are_exact(self) -> None:
        contract = model.source_contract()
        self.assertEqual(contract["task_ids"], ["S23P3T01", "S23P3T02", "S23P3T03"])
        self.assertEqual(contract["acceptance_zh"], ["结果幂等，无内存或队列泄露。", "关键任务完成率和效率达标。", "关键页面达到约定标准。"])
        self.assertTrue(all(value == 0 for value in model.scope_boundary().values()))

    def test_reduced_real_soak_is_idempotent_and_leak_free(self) -> None:
        value = model.soak_probe(cycle_count=2, restart_count=1, refresh_count=2)
        self.assertEqual(value["status"], "PASS")
        for key in ("operation_error_count", "silent_error_count", "idempotency_failure_count", "queue_leak_count", "temporary_file_leak_count", "thread_leak_count", "restart_error_count", "memory_growth_excess_count"):
            self.assertEqual(value[key], 0, key)

    def test_browser_evidence_has_three_plain_language_roles(self) -> None:
        value = model.validate_browser_evidence(self.browser())
        self.assertEqual([row["role_id"] for row in value["usability"]["tasks"]], ["management", "finance", "tax"])
        self.assertEqual((value["usability"]["completed_task_count"], value["accessibility"]["fail_count"]), (3, 0))

    def test_tampered_accessibility_evidence_fails_closed(self) -> None:
        value = copy.deepcopy(self.browser())
        value["accessibility"]["color_only_critical_info_count"] = 1
        with self.assertRaisesRegex(model.StabilityUsabilityError, "可访问性"):
            model.validate_browser_evidence(value)

    def test_cached_full_workload_passes_sixty_checks(self) -> None:
        soak = json.loads(builder.SOAK_REPORT_PATH.read_text(encoding="utf-8"))
        value = model.public_verification(self.browser(), soak=soak)
        self.assertEqual((value["status"], value["check_count"], value["pass_count"], value["fail_count"]), ("PASS", 60, 60, 0))

    def test_invalid_soak_dimensions_fail_closed(self) -> None:
        with self.assertRaisesRegex(model.StabilityUsabilityError, "正整数"):
            model.soak_probe(cycle_count=0)
        with self.assertRaisesRegex(model.StabilityUsabilityError, "平均分配"):
            model.soak_probe(cycle_count=1, restart_count=2, refresh_count=3)


if __name__ == "__main__":
    unittest.main()
