#!/usr/bin/env python3
"""Set or show the agent role of this session (agent-team-kit).

Usage:
  python3 .claude/hooks/role.py set <role>   # once, at the start of a role session
  python3 .claude/hooks/role.py show

The role is stored in .claude/state/role (git ignores it). It can be set
only one time per checkout. guard.py reads it to apply the role's scope.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / ".claude" / "state" / "role"
ROLES = json.loads((ROOT / ".claude" / "hooks" / "roles.json").read_text())["roles"]


def main(argv: list[str]) -> int:
    if len(argv) == 2 and argv[1] == "show":
        print(STATE.read_text().strip() if STATE.is_file() else "none")
        return 0
    if len(argv) != 3 or argv[1] != "set":
        print(__doc__, file=sys.stderr)
        return 1
    role = argv[2]
    if role not in ROLES:
        print(f"Unknown role '{role}'. Roles: {', '.join(sorted(ROLES))}", file=sys.stderr)
        return 1
    if STATE.is_file():
        current = STATE.read_text().strip()
        if current == role:
            print(f"Role is already {role}.")
            return 0
        print(f"Role is already set to {current}. Start a new session for a new role.", file=sys.stderr)
        return 1
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(role + "\n")
    print(f"Role set to {role}. Read .claude/agents/{role}.md and follow it.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
