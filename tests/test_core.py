from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agent_session_continuity_litmus.core import PROFILE_NAMES, compare_paths, extract_json, make_fixture, score_run
from agent_session_continuity_litmus.adapters import _codex_tool_use


class CoreTests(unittest.TestCase):
    def test_fixture_values_change_between_repetitions(self) -> None:
        first = make_fixture(1)
        second = make_fixture(2)
        self.assertNotEqual(first.expected["intent"], second.expected["intent"])
        self.assertNotEqual(first.expected["artifact_sha256"], second.expected["artifact_sha256"])

    def test_profiles_have_distinct_contracts(self) -> None:
        fixtures = [make_fixture(1, profile) for profile in PROFILE_NAMES]
        self.assertEqual(len({fixture.fixture_id for fixture in fixtures}), 3)
        self.assertEqual(len({fixture.expected["intent"] for fixture in fixtures}), 3)
        self.assertEqual(len({fixture.expected["decision_status"] for fixture in fixtures}), 3)
        self.assertIn("blocked on user input", fixtures[2].phase_one)

    def test_unknown_profile_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "unsupported profile"):
            make_fixture(1, "unknown")

    def test_extract_json_accepts_fenced_object(self) -> None:
        self.assertEqual(extract_json('```json\n{"intent":"A"}\n```'), {"intent": "A"})

    def test_exact_score_and_boundary_comparison(self) -> None:
        fixture = make_fixture(1)
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "phase-one.txt").write_bytes(fixture.artifact_bytes)
            exact = json.dumps(fixture.expected)
            baseline = score_run(
                adapter="fake",
                client_version="1",
                fixture=fixture,
                path="baseline",
                boundary={"complete": True},
                response_text=exact,
                workspace=workspace,
                tool_use_after_boundary=False,
            )
            drifted = dict(fixture.expected)
            drifted["intent"] = "paraphrased"
            compact = score_run(
                adapter="fake",
                client_version="1",
                fixture=fixture,
                path="compact",
                boundary={"complete": True},
                response_text=json.dumps(drifted),
                workspace=workspace,
                tool_use_after_boundary=False,
            )
            self.assertEqual(baseline.status, "PASS")
            self.assertEqual(compact.status, "FAIL")
            self.assertEqual(compare_paths(baseline, compact)["boundary_attributable_exact_drift"], ["intent"])

    def test_missing_boundary_is_inconclusive(self) -> None:
        fixture = make_fixture(1)
        with tempfile.TemporaryDirectory() as tmp:
            workspace = Path(tmp)
            (workspace / "phase-one.txt").write_bytes(fixture.artifact_bytes)
            result = score_run(
                adapter="fake",
                client_version="1",
                fixture=fixture,
                path="compact",
                boundary={"complete": False},
                response_text=json.dumps(fixture.expected),
                workspace=workspace,
                tool_use_after_boundary=False,
            )
            self.assertEqual(result.status, "INCONCLUSIVE")

    def test_codex_user_and_compaction_items_are_not_tools(self) -> None:
        messages = [
            {"method": "item/completed", "params": {"item": {"type": "userMessage"}}},
            {"method": "item/completed", "params": {"item": {"type": "contextCompaction"}}},
            {"method": "item/completed", "params": {"item": {"type": "agentMessage"}}},
        ]
        self.assertFalse(_codex_tool_use(messages, 0))
        messages.append({"method": "item/completed", "params": {"item": {"type": "commandExecution"}}})
        self.assertTrue(_codex_tool_use(messages, 0))


if __name__ == "__main__":
    unittest.main()
