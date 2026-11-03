"""Tests for the agent guard hooks (agent-team-kit).

Run: python3 -m unittest discover -s .claude/hooks/tests

GuardLogicTest runs a copy of guard.py with a fixed test config, so it does not
depend on this project's roles. ProjectConfigTest checks this project's roles.json.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[1]

# Fake secrets, built in parts so that this file does not hold a full pattern.
AWS_KEY = "AKIA" + "ABCDEFGHIJKLMNOP"
ANTHROPIC_KEY = "sk-" + "ant-api03-" + "x" * 30
GITHUB_TOKEN = "ghp_" + "a" * 36
PRIVATE_KEY = "-----BEGIN " + "RSA PRIVATE KEY-----"
MODAL_SECRET = "as-" + "Z" * 24
KEY_ASSIGNMENT = "API_" + 'KEY = "' + "abcdefghijklmnopqrstuv" + '"'

TEST_CONFIG = {
    "decider": "the decider",
    "contact_role_title": "the lead",
    "secret_store": "the secret store",
    "protected_branches": ["main", "master"],
    "common_write": ["docs/log/**"],
    "roles": {
        "lead": {"write": ["docs/**", "CLAUDE.md"], "deny": ["docs/source/**"]},
        "builder": {"write": ["src/**"], "deny": ["src/styles/tokens.css"]},
        "designer": {"write": ["docs/design/**", "src/styles/tokens.css"]},
        "reviewer": {"write": [], "no_repo_writes": True, "no_git_writes": True},
        "release": {"write": ["docs/releases/**"], "may_run_workflows": True},
    },
}


def run_guard(hooks: Path, root: Path, tool: str, tool_input: dict, agent_type: str | None = None):
    data = {"tool_name": tool, "tool_input": tool_input, "cwd": str(root)}
    if agent_type:
        data["agent_type"] = agent_type
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
    return subprocess.run(
        [sys.executable, str(hooks / "guard.py")], input=json.dumps(data), capture_output=True, text=True, env=env
    )


class GuardLogicTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", "-b", "feature", str(self.root)], check=True)
        self.hooks = self.root / ".claude" / "hooks"
        self.hooks.mkdir(parents=True)
        shutil.copy(HOOKS / "guard.py", self.hooks / "guard.py")
        (self.hooks / "roles.json").write_text(json.dumps(TEST_CONFIG))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def guard(self, tool: str, tool_input: dict, agent_type: str | None = None):
        return run_guard(self.hooks, self.root, tool, tool_input, agent_type)

    def set_role(self, role: str) -> None:
        state = self.root / ".claude" / "state"
        state.mkdir(parents=True, exist_ok=True)
        (state / "role").write_text(role + "\n")

    def assertBlocked(self, result, text: str = "") -> None:
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn(text, result.stderr)

    def assertAllowed(self, result) -> None:
        self.assertEqual(result.returncode, 0, result.stderr)

    def write(self, rel: str, content: str = "x", agent_type: str | None = None):
        return self.guard("Write", {"file_path": str(self.root / rel), "content": content}, agent_type)

    # Git and GitHub
    def test_push_to_main_blocked(self) -> None:
        for cmd in [
            "git push origin main",
            "git push -u origin HEAD:main",
            "git push origin +feature:refs/heads/main",
            "git push --force origin main",
            "cd x && git push origin master",
        ]:
            self.assertBlocked(self.guard("Bash", {"command": cmd}), "main")

    def test_push_branch_allowed(self) -> None:
        self.assertAllowed(self.guard("Bash", {"command": "git push -u origin feature"}))
        self.assertAllowed(self.guard("Bash", {"command": "git push --force-with-lease origin feature"}))

    def test_bare_push_on_main_blocked(self) -> None:
        subprocess.run(["git", "-C", str(self.root), "checkout", "-q", "-b", "main"], check=True)
        self.assertBlocked(self.guard("Bash", {"command": "git push"}), "main")

    def test_merge_blocked(self) -> None:
        self.assertBlocked(self.guard("mcp__github__merge_pull_request", {"pullNumber": 1}), "the decider")
        self.assertBlocked(self.guard("mcp__github__enable_pr_auto_merge", {"pullNumber": 1}))
        self.assertBlocked(self.guard("Bash", {"command": "gh pr merge 3 --squash"}))

    def test_github_write_to_main_blocked(self) -> None:
        self.assertBlocked(self.guard("mcp__github__push_files", {"branch": "main", "files": []}))
        self.assertAllowed(self.guard("mcp__github__push_files", {"branch": "feat/x", "files": []}))

    def test_apply_and_workflows(self) -> None:
        self.assertBlocked(self.guard("Bash", {"command": "tofu apply -auto-approve"}), "approves")
        self.assertBlocked(self.guard("Bash", {"command": "terraform destroy"}))
        self.assertBlocked(self.guard("mcp__github__actions_run_trigger", {"workflow_id": "deploy.yml"}))
        self.assertAllowed(
            self.guard("mcp__github__actions_run_trigger", {"workflow_id": "deploy.yml"}, agent_type="release")
        )
        self.assertAllowed(self.guard("Bash", {"command": "tofu plan"}))

    # Secrets
    def test_secrets_blocked(self) -> None:
        for secret in [AWS_KEY, ANTHROPIC_KEY, GITHUB_TOKEN, PRIVATE_KEY, MODAL_SECRET]:
            self.assertBlocked(self.write("src/x.py", f"value = '{secret}'"), "secret")
            self.assertBlocked(self.guard("Bash", {"command": f"echo {secret}"}), "secret")
        self.assertBlocked(self.write("x.py", KEY_ASSIGNMENT), "secret")
        self.assertBlocked(self.guard("mcp__github__add_issue_comment", {"body": f"token {GITHUB_TOKEN}"}))

    def test_secret_references_allowed(self) -> None:
        self.assertAllowed(self.write("a.yml", "token: ${{ secrets.GITHUB_TOKEN }}"))
        self.assertAllowed(self.write("a.md", "Add API_TOKEN_SECRET to the environment secrets."))
        self.assertAllowed(self.write("a.py", 'api_key = os.environ["ANTHROPIC_API_KEY"]'))

    def test_env_file_blocked(self) -> None:
        self.assertBlocked(self.write(".env", "A=1"), ".env")
        self.assertBlocked(self.write("src/.env.local", "A=1"), ".env")
        self.assertAllowed(self.write(".env.example", "A="))

    # Outbound messages
    def test_send_blocked(self) -> None:
        for tool in [
            "mcp__Gmail__send_message",
            "mcp__Gmail__reply",
            "mcp__Gmail__forward",
            "mcp__Slack__post_message",
            "mcp__Descript__publish_project",
        ]:
            self.assertBlocked(self.guard(tool, {}), "drafts")
        self.assertAllowed(self.guard("mcp__Gmail__create_draft", {}))
        self.assertAllowed(self.guard("mcp__claude-code-remote__send_message", {"message": "hi"}))

    # Role scope
    def test_no_role_is_unrestricted(self) -> None:
        self.assertAllowed(self.write("src/page.tsx"))
        self.assertAllowed(self.write("CLAUDE.md"))

    def test_role_from_state_file(self) -> None:
        self.set_role("builder")
        self.assertAllowed(self.write("src/page.tsx"))
        self.assertAllowed(self.write("docs/log/worklog.jsonl"))
        self.assertBlocked(self.write("CLAUDE.md"), "the lead")
        self.assertBlocked(self.write("src/styles/tokens.css"), "scope")

    def test_agent_type_wins(self) -> None:
        self.set_role("builder")
        self.assertAllowed(self.write("docs/design/a.html", agent_type="designer"))

    def test_role_scopes(self) -> None:
        cases = {
            "lead": (["docs/specs/12.md", "CLAUDE.md"], ["src/page.tsx", "docs/source/original.md"]),
            "designer": (["docs/design/landing.html", "src/styles/tokens.css"], ["src/page.tsx"]),
            "release": (["docs/releases/v0.1.md"], ["src/main.py"]),
            "reviewer": ([], ["docs/log/worklog.jsonl", "src/main.py"]),
        }
        for role, (allowed, blocked) in cases.items():
            for rel in allowed:
                self.assertAllowed(self.write(rel, agent_type=role))
            for rel in blocked:
                self.assertBlocked(self.write(rel, agent_type=role))

    def test_outside_repo_allowed(self) -> None:
        result = self.guard("Write", {"file_path": "/tmp/scratch-note.md", "content": "x"}, agent_type="reviewer")
        self.assertAllowed(result)

    def test_reviewer_no_git_writes(self) -> None:
        self.assertBlocked(self.guard("Bash", {"command": "git commit -m fix"}, agent_type="reviewer"), "reviewer")
        self.assertBlocked(self.guard("mcp__github__create_or_update_file", {"branch": "x"}, agent_type="reviewer"))
        self.assertAllowed(self.guard("Bash", {"command": "git diff main...HEAD"}, agent_type="reviewer"))
        self.assertAllowed(self.guard("mcp__github__pull_request_review_write", {"body": "QA: PASS"}, agent_type="reviewer"))

    def test_unknown_role_blocked(self) -> None:
        self.set_role("nobody")
        self.assertBlocked(self.write("src/a.py"), "unknown role")

    def test_state_tamper_blocked(self) -> None:
        self.assertBlocked(self.write(".claude/state/role", "lead"), "role")
        self.assertBlocked(self.guard("Bash", {"command": "echo lead > .claude/state/role"}), "role")
        self.assertBlocked(self.guard("Bash", {"command": "rm -f .claude/state/role"}), "role")
        self.assertAllowed(self.guard("Bash", {"command": "grep -rn 'not .claude/state/' docs"}))
        self.assertAllowed(self.guard("Bash", {"command": "python3 .claude/hooks/role.py set reviewer"}))

    def test_subagent_never_sets_role(self) -> None:
        cmd = "python3 .claude/hooks/role.py set builder"
        self.assertBlocked(self.guard("Bash", {"command": cmd}, agent_type="builder"), "subagent")
        self.assertBlocked(self.guard("Bash", {"command": "cd x && python3 role.py set lead"}, agent_type="lead"))
        self.assertAllowed(self.guard("Bash", {"command": "python3 .claude/hooks/role.py show"}, agent_type="lead"))
        self.assertAllowed(self.guard("Bash", {"command": cmd}))
        quoted = "cat > /tmp/out.md <<'X'\n1. Run `python3 .claude/hooks/role.py set builder`.\nX"
        self.assertAllowed(self.guard("Bash", {"command": quoted}, agent_type="lead"))


def sample_path(glob: str) -> str:
    """Make one concrete path that matches a write glob."""
    path = glob.replace("**/", "").replace("**", "sample.md").replace("*", "sample")
    return path or "sample.md"


class ProjectConfigTest(unittest.TestCase):
    """Checks this project's own roles.json."""

    def setUp(self) -> None:
        self.config = json.loads((HOOKS / "roles.json").read_text())

    def test_required_keys(self) -> None:
        for key in ("decider", "contact_role_title", "protected_branches", "common_write", "roles"):
            self.assertIn(key, self.config)
        self.assertTrue(self.config["roles"])

    def test_each_role_can_write_its_own_folders(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git", "init", "-q", "-b", "feature", str(root)], check=True)
            hooks = root / ".claude" / "hooks"
            hooks.mkdir(parents=True)
            shutil.copy(HOOKS / "guard.py", hooks / "guard.py")
            shutil.copy(HOOKS / "roles.json", hooks / "roles.json")
            for role, spec in self.config["roles"].items():
                deny = [re.compile("^" + re.escape(d).replace(r"\*\*", ".*").replace(r"\*", "[^/]*") + "$") for d in spec.get("deny", [])]
                for glob in spec.get("write", []):
                    rel = sample_path(glob)
                    if rel.startswith(".claude/state") or any(d.match(rel) for d in deny):
                        continue
                    result = run_guard(hooks, root, "Write", {"file_path": str(root / rel), "content": "x"}, role)
                    self.assertEqual(result.returncode, 0, f"{role} cannot write {rel}: {result.stderr}")


class RoleScriptTest(unittest.TestCase):
    def test_set_once(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            hooks = Path(tmp) / ".claude" / "hooks"
            hooks.mkdir(parents=True)
            shutil.copy(HOOKS / "role.py", hooks / "role.py")
            (hooks / "roles.json").write_text(json.dumps(TEST_CONFIG))
            script = str(hooks / "role.py")

            def run(*args: str) -> subprocess.CompletedProcess:
                return subprocess.run([sys.executable, script, *args], capture_output=True, text=True)

            self.assertEqual(run("show").stdout.strip(), "none")
            self.assertEqual(run("set", "nobody").returncode, 1)
            self.assertEqual(run("set", "reviewer").returncode, 0)
            self.assertEqual(run("set", "reviewer").returncode, 0)
            self.assertEqual(run("set", "lead").returncode, 1)
            self.assertEqual(run("show").stdout.strip(), "reviewer")


if __name__ == "__main__":
    unittest.main()
