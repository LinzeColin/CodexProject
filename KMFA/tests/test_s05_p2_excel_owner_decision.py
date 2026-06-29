import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / "KMFA" / "tools" / "check_s05_p2_excel_owner_decision.py"
PACKET = ROOT / "KMFA" / "stage_artifacts" / "S05_P2_a0_golden_fixture" / "machine" / "excel_owner_decision_packet.json"


class S05P2ExcelOwnerDecisionTests(unittest.TestCase):
    def run_checker(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CHECKER), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

    def test_current_owner_decision_packet_matches_fixture_and_events(self) -> None:
        result = self.run_checker()
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("PASS: KMFA S05-P2 Excel owner decision check passed", result.stdout)
        self.assertIn("allowed_decisions=3", result.stdout)
        self.assertIn("pending_fields=5", result.stdout)

    def test_rejects_placeholder_hashes_for_owner_decision_packet(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            packet_path = Path(tmp) / "excel_owner_decision_packet.json"
            packet = json.loads(PACKET.read_text(encoding="utf-8"))
            packet["placeholder_hashes_allowed"] = True
            packet_path.write_text(json.dumps(packet, ensure_ascii=False, sort_keys=True), encoding="utf-8")

            result = self.run_checker("--packet", str(packet_path))

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("placeholder_hashes_allowed must be false", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
