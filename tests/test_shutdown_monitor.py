import time
import unittest

from quantlab.system.shutdown_monitor import HeartbeatState, stable_timeout


class ShutdownMonitorTests(unittest.TestCase):
    def test_shutdown_requires_seen_heartbeat_and_timeout(self):
        state = HeartbeatState(streamlit_pid=999999, terminal_tty="", timeout=1)

        self.assertFalse(state.should_shutdown())
        state.heartbeat()
        self.assertFalse(state.should_shutdown())
        state.last_heartbeat = time.time() - 2
        self.assertTrue(state.should_shutdown())
        self.assertTrue(state.mark_shutdown())
        self.assertFalse(state.mark_shutdown())

    def test_stable_timeout_raises_short_legacy_values(self):
        self.assertEqual(stable_timeout(15), 60)
        self.assertEqual(stable_timeout(120), 120)


if __name__ == "__main__":
    unittest.main()
