#!/usr/bin/env python3
"""SessionStart hook: tell the session its role and the first steps."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])


def main() -> None:
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError:
        data = {}
    state = ROOT / ".claude" / "state" / "role"
    role = data.get("agent_type") or (state.read_text().strip() if state.is_file() else "")
    if role:
        print(
            f"Agent role: {role}. Follow .claude/agents/{role}.md and docs/team/{role}.md. "
            "The guard hook limits your writes to your role's scope."
        )
    else:
        print(
            "No agent role is set. If your task message names a role (and you are not a subagent), run "
            "`python3 .claude/hooks/role.py set <role>` first. "
            "Do the start steps in CLAUDE.md, section 3."
        )


if __name__ == "__main__":
    main()
