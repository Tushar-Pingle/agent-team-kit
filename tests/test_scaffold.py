"""Self-test for agent-team-kit. Run: python3 tests/test_scaffold.py

It scaffolds the example config into a temp git repo and checks the result.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
SCAFFOLD = KIT / "scripts" / "scaffold.py"
EXAMPLE = KIT / "scripts" / "team.example.json"
PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}")


def frontmatter(text: str) -> dict:
    """Parse the simple YAML frontmatter that the scaffold writes."""
    assert text.startswith("---\n"), "no frontmatter"
    body = text.split("---\n", 2)[1]
    try:
        import yaml  # type: ignore

        return yaml.safe_load(body)
    except ImportError:
        out, key = {}, None
        for line in body.splitlines():
            if line.startswith("  - ") and key:
                out.setdefault(key, []).append(line[4:])
            elif ":" in line:
                key, _, value = line.partition(":")
                value = value.strip()
                out[key] = json.loads(value) if value.startswith('"') else value
        return out


class ScaffoldTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.tmp = tempfile.TemporaryDirectory()
        cls.root = Path(cls.tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "main", str(cls.root)], check=True)
        cls.config = json.loads(EXAMPLE.read_text())
        cls.first = subprocess.run(
            [sys.executable, str(SCAFFOLD), "--config", str(EXAMPLE), "--target", str(cls.root)],
            capture_output=True, text=True,
        )

    @classmethod
    def tearDownClass(cls) -> None:
        cls.tmp.cleanup()

    def test_scaffold_runs(self) -> None:
        self.assertEqual(self.first.returncode, 0, self.first.stderr)

    def test_core_files_exist(self) -> None:
        for rel in [
            "CLAUDE.md", "docs/plans/README.md", "docs/plans/_template.md",
            "docs/adr/0000-record-architecture-decisions.md", "docs/log/worklog.jsonl",
            "docs/log/REVISIT.md", "docs/team/README.md", "docs/team/spec-template.md",
            "docs/runbooks/agent-team.md", ".claude/settings.json", ".claude/hooks/guard.py",
            ".claude/hooks/roles.json", ".claude/skills/write-spec/SKILL.md", ".claude/role-tests/README.md",
        ]:
            self.assertTrue((self.root / rel).is_file(), rel)

    def test_each_role_has_files(self) -> None:
        for role in self.config["roles"]:
            agent = self.root / ".claude" / "agents" / f"{role['name']}.md"
            self.assertTrue(agent.is_file(), agent)
            fm = frontmatter(agent.read_text())
            self.assertEqual(fm["name"], role["name"])
            self.assertTrue(fm["description"])
            if not role.get("helper"):
                self.assertTrue((self.root / "docs" / "team" / f"{role['name']}.md").is_file())
                self.assertTrue((self.root / ".claude" / "role-tests" / role["name"] / "test-1.md").is_file())

    def test_no_placeholders_left(self) -> None:
        for path in self.root.rglob("*"):
            if path.is_file() and ".git" not in path.parts:
                found = PLACEHOLDER.findall(path.read_text(errors="ignore"))
                self.assertFalse(found, f"{path}: {found}")

    def test_generated_guard_tests_pass(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "unittest", "discover", "-s", ".claude/hooks/tests"],
            cwd=self.root, capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr[-2000:])

    def test_role_state_is_none(self) -> None:
        result = subprocess.run(
            [sys.executable, ".claude/hooks/role.py", "show"], cwd=self.root, capture_output=True, text=True
        )
        self.assertEqual(result.stdout.strip(), "none")

    def test_second_run_changes_nothing(self) -> None:
        before = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}
        second = subprocess.run(
            [sys.executable, str(SCAFFOLD), "--config", str(EXAMPLE), "--target", str(self.root)],
            capture_output=True, text=True,
        )
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("Wrote 0 files", second.stdout)
        after = {p: p.read_bytes() for p in self.root.rglob("*") if p.is_file() and ".git" not in p.parts}
        self.assertEqual(before, after)

    def test_bad_config_is_rejected(self) -> None:
        bad = dict(self.config, contact_role="nobody")
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(bad, f)
        result = subprocess.run(
            [sys.executable, str(SCAFFOLD), "--config", f.name, "--target", str(self.root), "--dry-run"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 1)
        self.assertIn("contact_role", result.stderr)


if __name__ == "__main__":
    unittest.main()
