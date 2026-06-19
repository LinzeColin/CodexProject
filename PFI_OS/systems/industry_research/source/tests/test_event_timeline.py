from __future__ import annotations

import unittest

from src.reporting.analysis import _full_event_time, catalyst_risk_event_table, event_table_rows


class EventTimelineOrderingTest(unittest.TestCase):
    def test_catalyst_table_sorts_single_digit_times_chronologically(self) -> None:
        content = catalyst_risk_event_table(
            events=[
                self._event("2026-06-04", "10:00 Asia/Shanghai", "十点事件"),
                self._event("2026-06-04", "9:00 Asia/Shanghai", "九点事件"),
                self._event("2026-06-03", "15:30 Asia/Shanghai", "前日事件"),
            ],
            factors=[],
            as_of="2026-06-04",
        )

        self.assertLess(content.index("前日事件"), content.index("九点事件"))
        self.assertLess(content.index("九点事件"), content.index("十点事件"))

    def test_legacy_event_rows_sort_single_digit_times_chronologically(self) -> None:
        rows = event_table_rows(
            [
                self._event("2026-06-04", "10:00 Asia/Shanghai", "十点事件"),
                self._event("2026-06-04", "9:00 Asia/Shanghai", "九点事件"),
            ],
            "2026-06-04",
        )

        self.assertEqual([row["title"] for row in rows], ["九点事件", "十点事件"])

    def test_event_time_without_timezone_gets_source_default_timezone(self) -> None:
        event = self._event("2026-06-03", "08:20", "美股事件")
        event["source_name"] = "Nasdaq Investor Relations"
        event["industry"] = "美股科技"

        self.assertEqual(_full_event_time(event), "2026-06-03 08:20 America/New_York")

    def _event(self, date: str, event_time: str, title: str) -> dict[str, str]:
        return {
            "date": date,
            "event_time": event_time,
            "type": "news",
            "title": title,
            "impact": "neutral",
            "source_name": "UnitTest",
            "source_url": "https://example.org/event",
            "related_symbols": "",
        }


if __name__ == "__main__":
    unittest.main()
