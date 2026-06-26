from __future__ import annotations

from datetime import time


SESSION_TIMES = {
    "pre_open": {"report": "08:45", "snapshot": "08:40", "order": "14:30-14:55"},
    "midday": {"report": "12:05", "snapshot": "11:30", "order": "14:30-14:55"},
    "post_close": {"report": "16:05", "snapshot": "15:00", "order": "次日14:30-14:55"},
    "kline": {"report": "16:45", "snapshot": "15:00", "order": "次日14:30-14:55"},
    "monday_pre_open": {"report": "周一08:30", "snapshot": "周一08:25", "order": "周一14:30-14:55"},
    "friday_post_close": {"report": "周五16:15", "snapshot": "周五15:00", "order": "下周一14:30-14:55"},
}

REPORT_DUE_TIMES = {
    "monday_pre_open": time(8, 30),
    "pre_open": time(8, 45),
    "midday": time(12, 5),
    "post_close": time(16, 5),
    "kline": time(16, 45),
    "friday_post_close": time(16, 15),
}
