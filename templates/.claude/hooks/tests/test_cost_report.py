"""Tests for the cost report hook (agent-team-kit).

Run: python3 -m unittest discover -s .claude/hooks/tests
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]

PRICES = {
    "currency": "USD",
    "log": "docs/log/COST.md",
    "prices_per_million": {
        "_comment": "ignored",
        "test-strong-1": {"input": 10, "output": 50, "cache_write": 12.5, "cache_read": 1},
        "small": {"input": 1, "output": 5},
    },
}


def assistant(msg_id: str, model: str, usage: dict) -> str:
    return json.dumps({"type": "assistant", "uuid": msg_id + "-u", "message": {"id": msg_id, "model": model, "usage": usage}})


TRANSCRIPT = "\n".join([
    json.dumps({"type": "user", "message": {"role": "user", "content": "hi"}}),
    # one streamed message, two chunks with the same id: counted once, last usage wins
    assistant("m1", "test-strong-1", {"input_tokens": 100, "output_tokens": 1, "cache_creation_input_tokens": 0, "cache_read_input_tokens": 0}),
    assistant("m1", "test-strong-1", {"input_tokens": 100, "output_tokens": 40, "cache_creation_input_tokens": 200, "cache_read_input_tokens": 1000}),
    assistant("m2", "test-small-9", {"input_tokens": 1000, "output_tokens": 100}),
    "not json at all",
    json.dumps({"type": "assistant", "message": {"model": "test-small-9"}}),  # no usage: ignored
]) + "\n"


class CostReportTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        hooks = self.root / ".claude" / "hooks"
        hooks.mkdir(parents=True)
        shutil.copy(HOOKS / "cost_report.py", hooks / "cost_report.py")
        (hooks / "cost.json").write_text(json.dumps(PRICES))
        self.transcript = self.root / "session.jsonl"
        self.transcript.write_text(TRANSCRIPT)
        self.script = hooks / "cost_report.py"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def run_report(self, *args: str, stdin: str = "") -> subprocess.CompletedProcess:
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.root)}
        return subprocess.run([sys.executable, str(self.script), *args], input=stdin, capture_output=True, text=True, env=env, cwd=self.root)

    def test_counts_each_message_once_and_prices_by_match(self) -> None:
        result = self.run_report("--transcript", str(self.transcript), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        summary = json.loads(result.stdout)
        self.assertEqual(summary["messages"], 2)
        by_model = {r["model"]: r for r in summary["rows"]}
        strong = by_model["test-strong-1"]
        self.assertEqual((strong["input"], strong["output"], strong["cache_write"], strong["cache_read"]), (100, 40, 200, 1000))
        # 100*10 + 40*50 + 200*12.5 + 1000*1, per million
        self.assertAlmostEqual(strong["cost"], (1000 + 2000 + 2500 + 1000) / 1e6)
        small = by_model["test-small-9"]
        self.assertAlmostEqual(small["cost"], (1000 * 1 + 100 * 5) / 1e6)  # substring match on 'small'
        self.assertTrue(summary["priced"])
        self.assertEqual(summary["total"]["total"], 100 + 40 + 200 + 1000 + 1000 + 100)

    def test_hook_input_names_transcript_and_appends_log(self) -> None:
        hook_input = json.dumps({"session_id": "abcdef1234567890", "transcript_path": str(self.transcript), "cwd": str(self.root), "hook_event_name": "SessionEnd"})
        result = self.run_report("--append", stdin=hook_input)
        self.assertEqual(result.returncode, 0, result.stderr)
        log = (self.root / "docs" / "log" / "COST.md").read_text()
        self.assertIn("| abcdef12 |", log)
        self.assertIn("test-strong-1", log)
        self.assertIn("| all |", log)
        last = (self.root / ".claude" / "state" / "last-cost.txt").read_text()
        self.assertIn("tokens", last)
        self.assertIn("USD", last)
        # a second run appends, it does not rewrite
        self.run_report("--append", stdin=hook_input)
        self.assertEqual((self.root / "docs" / "log" / "COST.md").read_text().count("| abcdef12 |"), 6)

    def test_no_prices_gives_tokens_only(self) -> None:
        (self.root / ".claude" / "hooks" / "cost.json").write_text(json.dumps({"prices_per_million": {}}))
        result = self.run_report("--transcript", str(self.transcript))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Prices are not set", result.stdout)
        self.assertIn("2,440", result.stdout)

    def test_missing_transcript_never_fails(self) -> None:
        result = self.run_report("--transcript", str(self.root / "nope.jsonl"), "--append")
        self.assertEqual(result.returncode, 0)
        self.assertIn("no transcript", result.stdout)


if __name__ == "__main__":
    unittest.main()
