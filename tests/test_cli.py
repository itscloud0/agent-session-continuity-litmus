from __future__ import annotations

import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from agent_session_continuity_litmus.cli import main


class CliTests(unittest.TestCase):
    def test_live_run_requires_explicit_opt_in(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, redirect_stdout(StringIO()) as output:
            code = main(["run", "--adapter", "codex-cli", "--output", str(Path(tmp) / "result")])
        self.assertEqual(code, 2)
        self.assertIn("--allow-live", output.getvalue())

    def test_fixture_command_is_offline(self) -> None:
        with redirect_stdout(StringIO()) as output:
            code = main(["fixture", "--repetition", "2"])
        self.assertEqual(code, 0)
        self.assertIn("VERIFY_OPAQUE_TASK_CONTRACT_R02", output.getvalue())

    def test_fixture_command_selects_profile(self) -> None:
        with redirect_stdout(StringIO()) as output:
            code = main(["fixture", "--profile", "wait-for-user-state"])
        self.assertEqual(code, 0)
        self.assertIn("HOLD_FOR_EXPLICIT_USER_INPUT_R01", output.getvalue())


if __name__ == "__main__":
    unittest.main()
