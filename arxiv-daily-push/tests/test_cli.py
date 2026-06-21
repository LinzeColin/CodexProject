import io
import unittest
from contextlib import redirect_stdout

from arxiv_daily_push.cli import main


class CliTests(unittest.TestCase):
    def test_version_command(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["version"])
        self.assertEqual(result, 0)
        self.assertEqual(buffer.getvalue().strip(), "0.1.0")

    def test_doctor_json_command_warns_without_blocking_phase1(self):
        buffer = io.StringIO()
        with redirect_stdout(buffer):
            result = main(["doctor", "--json", "--path", "."])
        self.assertIn(result, (0, 2))
        output = buffer.getvalue()
        self.assertIn('"phase": "1"', output)
        self.assertIn('"future_runtime_commands"', output)


if __name__ == "__main__":
    unittest.main()

