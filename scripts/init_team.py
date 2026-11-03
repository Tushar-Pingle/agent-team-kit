#!/usr/bin/env python3
"""Make a starter team.json from a preset (agent-team-kit).

Usage:
  python3 init_team.py --preset small --project "My App" --decider Alex [--out team.json]
      [--summary "..."] [--contact-model opus] [--agentic-model sonnet] [--helper-model haiku]
      [--stack stack.json] [--main-branch main] [--secret-store "..."] [--no-ste]
  python3 init_team.py --list

The setup-team skill runs this after the Q&A, then adjusts the result. The output
never has secrets. Standard library only.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXAMPLE = HERE / "team.example.json"
PRESETS = HERE / "presets.json"


def load_presets() -> dict:
    return json.loads(PRESETS.read_text())["presets"]


def build(preset_name: str, args: argparse.Namespace) -> dict:
    presets = load_presets()
    if preset_name not in presets:
        sys.stderr.write(f"init_team: unknown preset '{preset_name}'. Known: {', '.join(presets)}.\n")
        sys.exit(1)
    preset = presets[preset_name]
    example = json.loads(EXAMPLE.read_text())
    by_name = {r["name"]: r for r in example["roles"]}
    roles = []
    for name in preset["roles"]:
        if name not in by_name:
            sys.stderr.write(f"init_team: preset role '{name}' is not in team.example.json.\n")
            sys.exit(1)
        role = copy.deepcopy(by_name[name])
        role.pop("stack", None)  # the example's stack is an example; the onboarding fills the real one
        role.update(copy.deepcopy(preset.get("overrides", {}).get(name, {})))
        role["model"] = "helper" if role.get("helper") else ("contact" if role["name"] == "pm" else "agentic")
        roles.append(role)

    cfg = {
        "_comment": f"Made by init_team.py from the '{preset_name}' preset. Tailor it with the setup-team skill, then run scaffold.py.",
        "project": args.project,
        "summary": args.summary or f"{args.project}: add a one-line summary of what the project does.",
        "decider": args.decider,
        "main_branch": args.main_branch,
        "secret_store": args.secret_store,
        "ste": not args.no_ste,
        "contact_role": "pm",
        "max_sessions": args.max_sessions,
        "preset": preset_name,
        "models": {"contact": args.contact_model, "agentic": args.agentic_model, "helper": args.helper_model},
        "cost": {"currency": "USD", "log": "docs/log/COST.md", "prices_per_million": {}},
        "common_write": ["docs/log/**"],
        "roles": roles,
    }
    if args.stack:
        cfg["stack"] = json.loads(Path(args.stack).read_text())
    return cfg


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--list", action="store_true", help="list the presets and exit")
    ap.add_argument("--preset", default="small")
    ap.add_argument("--project")
    ap.add_argument("--decider")
    ap.add_argument("--summary", default="")
    ap.add_argument("--out", default="team.json")
    ap.add_argument("--contact-model", default="opus")
    ap.add_argument("--agentic-model", default="sonnet")
    ap.add_argument("--helper-model", default="haiku")
    ap.add_argument("--stack", help="path to a stack.json from discover.py or the onboarding Q&A")
    ap.add_argument("--main-branch", default="main")
    ap.add_argument("--secret-store", default="the secret store")
    ap.add_argument("--max-sessions", type=int, default=3)
    ap.add_argument("--no-ste", action="store_true", help="turn the plain-English writing standard off")
    ap.add_argument("--force", action="store_true", help="replace an existing --out file")
    args = ap.parse_args(argv)

    if args.list:
        for name, preset in load_presets().items():
            print(f"{name:6} {preset['summary']}")
            print(f"       roles: {', '.join(preset['roles'])}")
        return 0
    if not args.project or not args.decider:
        ap.error("--project and --decider are required (or use --list).")
    out = Path(args.out)
    if out.exists() and not args.force:
        sys.stderr.write(f"init_team: {out} exists. Use --force to replace it.\n")
        return 1
    cfg = build(args.preset, args)
    out.write_text(json.dumps(cfg, indent=2) + "\n")
    print(f"Wrote {out} ({args.preset} preset, {len(cfg['roles'])} roles). Next: tailor it, then run scaffold.py.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
