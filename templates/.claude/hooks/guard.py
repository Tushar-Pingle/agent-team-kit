#!/usr/bin/env python3
"""PreToolUse guard for the agent team (agent-team-kit).

Reads the hook input on stdin. Exits 2 with a reason on stderr to block the
tool call. Exits 0 to let it run. Uses only the standard library.

Rules for all sessions:
  - No push to main, no merge, no auto-merge, no direct deploy or apply.
  - No text that looks like a secret in a write, a command, or a GitHub call.
  - No outbound email or chat message (drafts only).
  - No writes to .env files or to the role state.
Rules for a role session (role from agent_type or .claude/state/role):
  - Write only inside the role's folders (roles.json).
  - QA, UAT, and the researcher do not write to the repo or to git.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

HOOK_DIR = Path(__file__).resolve().parent
ROLES_FILE = HOOK_DIR / "roles.json"


def load_roles() -> dict:
    with ROLES_FILE.open() as f:
        return json.load(f)


CONFIG = load_roles()
DECIDER = CONFIG.get("decider", "the decider")
CONTACT = CONFIG.get("contact_role_title", "the PM")
SECRET_STORE = CONFIG.get("secret_store", "the secret store")
PROTECTED = tuple(CONFIG.get("protected_branches", ["main", "master"]))

SECRET_PATTERNS = [
    ("AWS access key", re.compile(r"\b(AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("Anthropic key", re.compile(r"\bsk-ant-[A-Za-z0-9_\-]{20,}")),
    ("OpenAI-style key", re.compile(r"\bsk-(proj-)?[A-Za-z0-9]{32,}")),
    ("GitHub token", re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\b")),
    ("GitHub token", re.compile(r"\bgithub_pat_[A-Za-z0-9_]{40,}\b")),
    ("Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9\-]{10,}")),
    ("Google API key", re.compile(r"\bAIza[0-9A-Za-z_\-]{35}\b")),
    ("Modal token", re.compile(r"\b(ak|as)-[A-Za-z0-9]{20,}\b")),
    ("private key", re.compile(r"-----BEGIN ([A-Z]+ )?PRIVATE KEY-----")),
    (
        "secret assignment",
        re.compile(
            r"(?i)\b[A-Z0-9_]*(SECRET|TOKEN|PASSWORD|API_KEY|PRIVATE_KEY)[A-Z0-9_]*"
            r"\s*[=:]\s*['\"]?(?!\$\{|\$\(|<|\*{3})[A-Za-z0-9/+_\-]{16,}"
        ),
    ),
]

SEND_TOOL = re.compile(
    r"^mcp__([^_]*(gmail|slack|upwork|outlook|linkedin|twitter|x)[^_]*)__"
    r".*(send|reply|forward|post|publish)",
    re.IGNORECASE,
)
PUBLISH_TOOLS = {"mcp__Descript__publish_project"}
MERGE_TOOLS = re.compile(r"^mcp__github__(merge_pull_request|enable_pr_auto_merge)$")
WORKFLOW_TOOL = "mcp__github__actions_run_trigger"
GITHUB_WRITE_TOOLS = re.compile(
    r"^mcp__github__(create_or_update_file|push_files|delete_file|create_branch|update_pull_request_branch)$"
)
WRITE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}


def block(reason: str) -> None:
    sys.stderr.write(f"Blocked by .claude/hooks/guard.py: {reason}\n")
    sys.exit(2)


def project_dir(data: dict) -> Path:
    root = os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or os.getcwd()
    return Path(root).resolve()


def current_role(data: dict, root: Path) -> str | None:
    agent_type = data.get("agent_type")
    roles = load_roles()["roles"]
    if agent_type in roles:
        return agent_type
    state = root / ".claude" / "state" / "role"
    if state.is_file():
        role = state.read_text().strip()
        return role or None
    return None


def glob_to_regex(glob: str) -> re.Pattern[str]:
    out = []
    i = 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def matches(rel: str, globs: list[str]) -> bool:
    return any(glob_to_regex(g).match(rel) for g in globs)


def relative_path(path: str, root: Path, cwd: str | None) -> str | None:
    """Return the path relative to the repo root, or None if it is outside."""
    p = Path(path)
    if not p.is_absolute():
        p = Path(cwd or root) / p
    p = Path(os.path.normpath(p))
    try:
        return p.relative_to(root).as_posix()
    except ValueError:
        return None


def strings(obj: object) -> list[str]:
    """Return every string value inside a tool input."""
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in strings(v)]
    return []


def find_secret(obj: object) -> str | None:
    for text in strings(obj):
        for name, pattern in SECRET_PATTERNS:
            if pattern.search(text):
                return name
    return None


def check_path(rel: str, role: str | None) -> None:
    name = rel.rsplit("/", 1)[-1]
    if name.startswith(".env") and name != ".env.example":
        block(f"do not write .env files ({rel}). Secrets live in {SECRET_STORE}.")
    if rel.startswith(".claude/state/") or rel == ".claude/state":
        block("the role state is set once with .claude/hooks/role.py.")
    if role is None:
        return
    config = load_roles()
    spec = config["roles"].get(role)
    if spec is None:
        block(f"unknown role '{role}'. Check .claude/state/role.")
    if spec.get("no_repo_writes"):
        block(f"the {role} role does not write to the repo. Report findings instead.")
    if matches(rel, spec.get("deny", [])):
        block(f"{rel} is outside the {role} role's scope (denied). Ask {CONTACT}.")
    if not matches(rel, spec.get("write", []) + config.get("common_write", [])):
        block(f"{rel} is outside the {role} role's scope. Ask {CONTACT}.")


def current_branch(cwd: str | None) -> str:
    try:
        out = subprocess.run(
            ["git", "symbolic-ref", "--short", "-q", "HEAD"],
            cwd=cwd or None,
            capture_output=True,
            text=True,
            timeout=5,
        )
        return out.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def check_git_push(segment: str, cwd: str | None) -> None:
    tokens = segment.split()
    try:
        idx = tokens.index("push")
    except ValueError:
        return
    args = tokens[idx + 1 :]
    positional = [a for a in args if not a.startswith("-")]
    refspecs = positional[1:]
    targets = []
    for spec in refspecs:
        spec = spec.lstrip("+")
        dst = spec.split(":", 1)[1] if ":" in spec else spec
        targets.append(dst.removeprefix("refs/heads/"))
    if not refspecs or "HEAD" in targets:
        targets.append(current_branch(cwd))
    if any(t in PROTECTED for t in targets):
        block(f"do not push to {PROTECTED[0]}. Push a branch and open a PR. {DECIDER} merges.")


SEGMENT_SPLIT = re.compile(r"&&|\|\||;|\||\n")
# A command that writes, moves, or removes the role state. Mentions in text are fine.
# A shell segment that runs role.py set. Text that only quotes the command is fine.
ROLE_SET = re.compile(r"^\s*(sudo\s+)?(\S*python3?\s+)?\S*role\.py\s+set\b")
STATE_WRITE = re.compile(
    r"(>>?|\btee\b|\brm\b|\bmv\b|\bcp\b|\btouch\b|\bsed\s+-i|\btruncate\b|\bln\b|\bchmod\b)"
    r"[^\n;&|]*\.claude/state"
)


def check_bash(command: str, role: str | None, cwd: str | None, subagent: bool = False) -> None:
    secret = find_secret(command)
    if secret:
        block(f"the command contains text that looks like a secret ({secret}).")
    if subagent and any(ROLE_SET.match(seg) for seg in SEGMENT_SPLIT.split(command)):
        block("a subagent never sets the role. It shares the parent checkout. agent_type already names the role.")
    if STATE_WRITE.search(command):
        block("the role state is set once with .claude/hooks/role.py.")
    spec = load_roles()["roles"].get(role or "", {})
    for raw in SEGMENT_SPLIT.split(command):
        seg = raw.strip()
        seg = re.sub(r"^(\w+=\S+\s+)+", "", seg)
        if re.match(r"^(sudo\s+)?git\b", seg):
            sub = re.sub(r"^(sudo\s+)?git\s+(-C\s+\S+\s+|-c\s+\S+\s+)*", "", seg)
            verb = sub.split()[0] if sub.split() else ""
            if verb == "push":
                check_git_push("push " + sub[len("push") :], cwd)
            if spec.get("no_git_writes") and verb in (
                "commit", "push", "merge", "rebase", "reset", "tag", "cherry-pick", "revert", "am",
            ):
                block(f"the {role} role does not change git history. Report findings instead.")
        if re.match(r"^(tofu|terraform)\s+(apply|destroy|import|state\s+(rm|mv|push))\b", seg):
            block(f"apply runs only in the deploy pipeline after {DECIDER} approves.")
        if re.match(r"^gh\s+pr\s+merge\b", seg) or re.match(r"^gh\s+pr\s+review\b.*--approve", seg):
            block(f"only {DECIDER} merges or approves PRs.")
        if re.match(r"^gh\s+(workflow\s+run|run\s+rerun)\b", seg) and not spec.get("may_run_workflows"):
            block(f"only a role with may_run_workflows starts workflows, after {DECIDER} approves.")


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        return
    tool = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    cwd = data.get("cwd")
    root = project_dir(data)
    role = current_role(data, root)

    if MERGE_TOOLS.match(tool):
        block(f"only {DECIDER} merges PRs.")
    if SEND_TOOL.match(tool) or tool in PUBLISH_TOOLS:
        block(f"agents make drafts only. {DECIDER} sends or publishes each item.")
    if tool == WORKFLOW_TOOL:
        spec = load_roles()["roles"].get(role or "", {})
        if not spec.get("may_run_workflows"):
            block(f"only a role with may_run_workflows starts workflows, after {DECIDER} approves.")

    if tool == "Bash":
        check_bash(str(tool_input.get("command", "")), role, cwd, subagent=bool(data.get("agent_type")))
        return

    if tool in WRITE_TOOLS:
        path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
        secret = find_secret(tool_input)
        if secret:
            block(f"the content looks like a secret ({secret}). Secrets live in {SECRET_STORE}.")
        rel = relative_path(path, root, cwd)
        if rel is not None:
            check_path(rel, role)
        return

    if tool.startswith("mcp__"):
        secret = find_secret(tool_input)
        if secret:
            block(f"the request contains text that looks like a secret ({secret}).")
        if GITHUB_WRITE_TOOLS.match(tool):
            branch = str(tool_input.get("branch", ""))
            if branch in PROTECTED:
                block(f"do not write to {branch}. Use a branch and a PR.")
            spec = load_roles()["roles"].get(role or "", {})
            if spec.get("no_git_writes"):
                block(f"the {role} role does not change the repo. Report findings instead.")


if __name__ == "__main__":
    main()
