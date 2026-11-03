#!/usr/bin/env python3
"""Scaffold an agent team into a project (agent-team-kit).

Usage:
  python3 scaffold.py --config team.json --target <project dir> [--dry-run] [--force]

Reads a team config (see team.example.json) and writes:
  CLAUDE.md, docs/ (plans, ADRs, logs, team charters, runbook, spec template),
  .claude/agents/<role>.md, .claude/hooks/ (guard, role state, tests, roles.json),
  .claude/settings.json, .claude/skills/ (workflow skills), .claude/role-tests/.

It never overwrites an existing file unless --force is given. It uses only the
Python standard library.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
TEMPLATES = KIT / "templates"
SKILLS = KIT / "skills"
# Skills copied into the project. setup-team and onboard-project stay in the plugin only.
PROJECT_SKILLS = ["method-guide", "revisit-log", "write-spec", "review-pr", "run-uat", "log-entry", "role-tests", "cost-report"]
# Model tiers. A role's "model" is a tier name (resolved from cfg["models"]) or an explicit model id.
MODEL_TIERS = ("contact", "agentic", "helper")
DEFAULT_MODELS = {"contact": "opus", "agentic": "sonnet", "helper": "haiku"}
# Role test template for each role body type.
TEST_FOR_BODY = {
    "pm": "pm", "scrum-master": "scrum-master", "builder": "builder", "designer": "designer",
    "qa": "qa", "uat": "uat", "release": "release", "growth": "growth",
}
NAME_RE = re.compile(r"^[a-z][a-z0-9-]{1,40}$")
GITIGNORE_LINES = [".claude/state/", ".claude/settings.local.json", "__pycache__/", "*.pyc"]


class Plan:
    """Collects the files to write, then writes them."""

    def __init__(self, target: Path, force: bool, dry_run: bool) -> None:
        self.target, self.force, self.dry_run = target, force, dry_run
        self.written: list[str] = []
        self.skipped: list[str] = []

    def write(self, rel: str, text: str) -> None:
        path = self.target / rel
        if path.exists() and not self.force:
            self.skipped.append(rel)
            return
        self.written.append(rel)
        if not self.dry_run:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)

    def append_lines(self, rel: str, lines: list[str]) -> None:
        path = self.target / rel
        old = path.read_text() if path.exists() else ""
        missing = [line for line in lines if line not in old.splitlines()]
        if not missing:
            return
        self.written.append(f"{rel} (appended {len(missing)} lines)")
        if not self.dry_run:
            text = old + ("" if not old or old.endswith("\n") else "\n") + "\n".join(missing) + "\n"
            path.write_text(text)


def fail(msg: str) -> None:
    sys.stderr.write(f"scaffold: {msg}\n")
    sys.exit(1)


def validate(cfg: dict) -> None:
    for key in ("project", "decider", "roles"):
        if not cfg.get(key):
            fail(f"config needs '{key}'.")
    names = [r.get("name", "") for r in cfg["roles"]]
    for name in names:
        if not NAME_RE.match(name):
            fail(f"role name '{name}' must be kebab-case (a-z, 0-9, -).")
    if len(set(names)) != len(names):
        fail("role names must be unique.")
    contact = cfg.get("contact_role", "pm")
    if contact not in names:
        fail(f"contact_role '{contact}' is not a role.")
    for r in cfg["roles"]:
        body = r.get("body", "builder")
        if not (TEMPLATES / "roles" / f"{body}.md").is_file():
            fail(f"role '{r['name']}' uses body '{body}', but templates/roles/{body}.md does not exist.")
        model = r.get("model")
        if model is not None and (not isinstance(model, str) or not model.strip()):
            fail(f"role '{r['name']}' has an empty model. Use a tier ({', '.join(MODEL_TIERS)}) or a model id.")
    models = cfg.get("models", {})
    if not isinstance(models, dict):
        fail("'models' must be an object, for example {\"contact\": \"opus\", \"agentic\": \"sonnet\", \"helper\": \"haiku\"}.")
    for tier, value in models.items():
        if tier not in MODEL_TIERS:
            fail(f"unknown model tier '{tier}'. Use one of: {', '.join(MODEL_TIERS)}.")
        if not isinstance(value, str) or not value.strip():
            fail(f"model tier '{tier}' needs a model id.")
    cost = cfg.get("cost", {})
    if cost and not isinstance(cost.get("prices_per_million", {}), dict):
        fail("'cost.prices_per_million' must be an object keyed by model id or alias.")


def resolve_model(cfg: dict, role: dict) -> str:
    """Return the model id for a role. A tier name maps through cfg['models']."""
    models = {**DEFAULT_MODELS, **cfg.get("models", {})}
    default_tier = "helper" if role.get("helper") else ("contact" if role["name"] == cfg.get("contact_role", "pm") else "agentic")
    model = role.get("model") or default_tier
    return models.get(model, model)


def fill(text: str, ctx: dict) -> str:
    for key, value in ctx.items():
        text = text.replace("{{" + key + "}}", str(value))
    return text


def role_by_name(cfg: dict, name: str) -> dict | None:
    return next((r for r in cfg["roles"] if r["name"] == name), None)


def reports_to(cfg: dict, role: dict) -> str:
    if role.get("reports_to"):
        return role["reports_to"]
    contact = cfg.get("contact_role", "pm")
    if role["name"] == contact:
        return cfg["decider"]
    if role["name"] == "scrum-master":
        return "the " + role_by_name(cfg, contact)["title"]
    if role_by_name(cfg, "scrum-master") and role.get("body") in ("builder", "designer", "qa", "uat"):
        return "the Scrum master"
    return "the " + role_by_name(cfg, contact)["title"]


def scope_lines(cfg: dict, role: dict) -> str:
    if role.get("no_repo_writes"):
        return "- No writes to the repo or to git. You report through reviews, comments, and messages."
    writes = role.get("write", []) + cfg.get("common_write", [])
    lines = ["- Write: " + ", ".join(f"`{w}`" for w in writes) + "."]
    if role.get("deny"):
        lines.append("- Not: " + ", ".join(f"`{d}`" for d in role["deny"]) + ".")
    if role.get("may_run_workflows"):
        lines.append(f"- You may start workflows. A protected environment still asks {cfg['decider']} to approve.")
    return "\n".join(lines)


def _bullets(items: list, prefix: str = "- ") -> list[str]:
    return [f"{prefix}{item}" for item in items if str(item).strip()]


def stack_section(cfg: dict, role: dict, ctx: dict) -> str:
    """The 'Your stack' section: what the onboarding found about the project and this role's work."""
    project = cfg.get("stack", {}) or {}
    own = role.get("stack", {}) or {}
    lines: list[str] = []
    langs = own.get("languages") or project.get("languages") or []
    frameworks = own.get("frameworks") or project.get("frameworks") or []
    if langs:
        lines.append("- Languages: " + ", ".join(langs) + ".")
    if frameworks:
        lines.append("- Frameworks and libraries: " + ", ".join(frameworks) + ".")
    commands = {**(project.get("commands") or {}), **(own.get("commands") or {})}
    for key in ("install", "build", "test", "lint", "typecheck", "run"):
        if commands.get(key):
            lines.append(f"- {key.capitalize()}: `{commands[key]}`.")
    if project.get("ci"):
        lines.append(f"- CI: {project['ci']}.")
    conventions = list(project.get("conventions") or []) + list(own.get("conventions") or [])
    if conventions:
        lines.append("- Conventions:")
        lines += _bullets([fill(c, ctx) for c in conventions], "  - ")
    refs = list(own.get("references") or [])
    if refs:
        lines.append("- Read first: " + ", ".join(f"`{r}`" for r in refs) + ".")
    if own.get("notes"):
        lines.append("- " + fill(own["notes"], ctx))
    if not lines:
        return ""
    return "\n".join(["## Your stack", "",
                      "The onboarding recorded these facts. Use them. If the code disagrees with them, stop and ask.", ""] + lines)


def cost_json(cfg: dict) -> str:
    cost = cfg.get("cost", {}) or {}
    out = {
        "_comment": "Prices in currency units per 1 million tokens. Keys match a model id by exact match first, then by substring (for example 'sonnet'). Empty prices give a token-only report. Generated by agent-team-kit from team.json.",
        "currency": cost.get("currency", "USD"),
        "log": cost.get("log", "docs/log/COST.md"),
        "prices_per_million": cost.get("prices_per_million", {}),
    }
    return json.dumps(out, indent=2) + "\n"


def agent_file(cfg: dict, role: dict, ctx: dict) -> str:
    fm = ["---", f"name: {role['name']}", "description: " + json.dumps(fill(role["description"], ctx)),
          f"model: {resolve_model(cfg, role)}"]
    if role.get("tools"):
        fm.append("tools: " + ", ".join(role["tools"]))
    if role.get("disallowed_tools"):
        fm.append("disallowedTools: " + ", ".join(role["disallowed_tools"]))
    skills = [s for s in role.get("skills", []) if s in PROJECT_SKILLS]
    if skills:
        fm.append("skills:")
        fm += [f"  - {s}" for s in skills]
    fm += [f"color: {role.get('color', 'blue')}", "---"]
    decider, title = cfg["decider"], role["title"]
    contact_title = role_by_name(cfg, cfg.get("contact_role", "pm"))["title"]
    ask = (f"Ask {decider}. Give each option with context, trade-offs, and a recommendation."
           if role["name"] == cfg.get("contact_role", "pm") else f"Ask the {contact_title} in the issue.")
    parts = [
        "\n".join(fm), "",
        f"# Role: {title}", "",
        f"You are the {title} agent of the {cfg['project']} team. The team design is in `docs/team/README.md`. CLAUDE.md wins over this file.",
        "",
        f"Refer to {decider} by name. Never use a gendered pronoun for a person whose pronouns you do not know.",
        "", "## Mission", "", fill(role["mission"], ctx), "",
        "## Your scope", "", scope_lines(cfg, role), "",
    ]
    stack = stack_section(cfg, role, ctx)
    if stack:
        parts += [stack, ""]
    parts += [fill((TEMPLATES / "roles" / f"{role.get('body', 'builder')}.md").read_text(), ctx).rstrip(), ""]
    if role.get("helper"):
        parts += ["## Start", "", "1. Read the task. It names the question and the output format.", ""]
    else:
        parts += [
            "## Start", "",
            f"1. Only if your task message says so, run `python3 .claude/hooks/role.py set {role['name']}`. A subagent never sets a role: it shares the parent checkout.",
            f"2. Read `CLAUDE.md`, your charter `docs/team/{role['name']}.md`, and the task message.",
            "3. Read each plan and file that the task names.", "",
            "## Rules for every role", "",
            f"1. {ctx['WRITING_RULE_SHORT']}",
            f"2. If anything is unclear, stop and ask. Do not guess. {ask} Stop only the part that needs the answer. Finish the parts that are fully defined, and list the open questions in your report.",
            "3. Read each plan and file that the task names before you ask. Ask only what they do not answer.",
            f"4. Never merge, deploy, push to `{cfg.get('main_branch', 'main')}`, or approve a PR. {decider} does these.",
            "5. Never put a secret or personal data in a file, a commit, a log, an issue, or a message.",
            f"6. If the guard hook blocks an action, do not try another way around it. Report the block to {reports_to(cfg, role)}.",
            f"7. An idea that can change the scope goes to the {contact_title} for the revisit log. Only {decider} decides.",
            f"8. At most {cfg.get('max_sessions', 3)} agent sessions run at the same time. Do not start sessions unless your role says so.",
            "",
        ]
    parts += ["## Never", ""] + [f"- {fill(n, ctx)}" for n in role.get("never", [])] + [""]
    if not role.get("helper"):
        if "log-entry" in role.get("skills", []):
            parts += ["## Logs", "", f"Use the `log-entry` skill. Set `actor` to `llm:{role['name']}`.", ""]
        else:
            parts += ["## Logs", "", f"Put your work-log line at the end of your review or hand-off, with `actor` set to `llm:{role['name']}`. The Scrum master or the {contact_title} appends it.", ""]
    return "\n".join(parts)


def charter(cfg: dict, role: dict, ctx: dict) -> str:
    text = (TEMPLATES / "docs/team/charter.md.tmpl").read_text()
    owns = scope_lines(cfg, role)
    never = "\n".join(f"- {fill(n, ctx)}" for n in role.get("never", []))
    return fill(text, {**ctx, "ROLE_TITLE": role["title"], "ROLE_NAME": role["name"],
                       "MISSION": fill(role["mission"], ctx), "OWNS": owns,
                       "HANDS_OFF": fill(role.get("hands_off", ""), ctx), "NEVER": never,
                       "MODEL": resolve_model(cfg, role)})


def roles_json(cfg: dict) -> str:
    main = cfg.get("main_branch", "main")
    protected = [main] + [b for b in ("main", "master") if b != main]
    out = {
        "_comment": "Write scope and limits for each agent role. Globs are relative to the repo root. 'deny' wins over 'write'. Generated by agent-team-kit; edit through a reviewed PR.",
        "decider": cfg["decider"],
        "contact_role_title": "the " + role_by_name(cfg, cfg.get("contact_role", "pm"))["title"],
        "secret_store": cfg.get("secret_store", "the secret store"),
        "protected_branches": protected,
        "common_write": cfg.get("common_write", ["docs/log/**"]),
        "roles": {},
    }
    for r in cfg["roles"]:
        spec = {"write": r.get("write", [])}
        for key in ("deny", "no_repo_writes", "no_git_writes", "may_run_workflows"):
            if r.get(key):
                spec[key] = r[key]
        out["roles"][r["name"]] = spec
    return json.dumps(out, indent=2) + "\n"


def role_table(cfg: dict) -> str:
    rows = ["| # | Role | Charter | Model |", "|---|---|---|---|"]
    n = 0
    for r in cfg["roles"]:
        if r.get("helper"):
            continue
        n += 1
        rows.append(f"| {n} | {r['title']} | [{r['name']}.md]({r['name']}.md) | {resolve_model(cfg, r)} |")
    return "\n".join(rows)


def stack_summary(cfg: dict) -> str:
    stack = cfg.get("stack", {}) or {}
    bits = []
    if stack.get("languages"):
        bits.append(", ".join(stack["languages"]))
    if stack.get("frameworks"):
        bits.append(", ".join(stack["frameworks"]))
    if not bits:
        return "Stack: add the languages and frameworks here, or run the `onboard-project` skill to find them."
    return "Stack: " + "; ".join(bits) + ". Details: [`docs/team/context.md`](docs/team/context.md)."


def context(cfg: dict) -> dict:
    contact = role_by_name(cfg, cfg.get("contact_role", "pm"))
    ste = bool(cfg.get("ste"))
    team_roles = [r for r in cfg["roles"] if not r.get("helper")]
    helpers = [r for r in cfg["roles"] if r.get("helper")]
    return {
        "PROJECT": cfg["project"],
        "PROJECT_SUMMARY": cfg.get("summary", f"{cfg['project']}: add a one-line summary of what the project does."),
        "DECIDER": cfg["decider"],
        "MAIN_BRANCH": cfg.get("main_branch", "main"),
        "SECRET_STORE": cfg.get("secret_store", "the secret store"),
        "MAX_SESSIONS": cfg.get("max_sessions", 3),
        "CONTACT_TITLE": contact["title"],
        "CONTACT_NAME": contact["name"],
        "ROLE_COUNT": len(team_roles),
        "ROLE_TABLE": role_table(cfg),
        "HELPERS": ", ".join(f"`{h['name']}` ({resolve_model(cfg, h)})" for h in helpers) or "none",
        "STACK_SUMMARY": stack_summary(cfg),
        "COST_LOG": (cfg.get("cost", {}) or {}).get("log", "docs/log/COST.md"),
        "COST_CURRENCY": (cfg.get("cost", {}) or {}).get("currency", "USD"),
        "DATE": dt.date.today().isoformat(),
        "WRITING_RULE": ("Follow the plain-English writing standard in [`docs/standards/writing-ste100.md`](docs/standards/writing-ste100.md) "
                         "(ASD-STE100 at about 80%) in docs, logs, commits, PRs, and chat. Instructions: 20 words max per sentence. Descriptions: 25 words max. Use the active voice."
                         if ste else "Write short, clear sentences in the active voice. Use one term for one meaning."),
        "WRITING_RULE_SHORT": ("Write in the plain-English standard (`docs/standards/writing-ste100.md`): short sentences, active voice, glossary terms."
                               if ste else "Write short, clear sentences in the active voice."),
        "WRITING_MAP_ROW": ("| Writing standard and glossary | [`docs/standards/writing-ste100.md`](docs/standards/writing-ste100.md) |" if ste else ""),
    }


def render_tree(plan: Plan, cfg: dict, ctx: dict) -> None:
    generated_elsewhere = {"docs/team/charter.md.tmpl", ".claude/role-tests/test.md.tmpl"}
    for src in sorted(TEMPLATES.rglob("*")):
        if not src.is_file():
            continue
        rel = src.relative_to(TEMPLATES).as_posix()
        if rel.startswith("roles/") or rel.startswith("role-tests/") or rel in generated_elsewhere or "__pycache__" in rel:
            continue
        if rel == "docs/standards/writing-ste100.md" and not cfg.get("ste"):
            continue
        out = rel[:-5] if rel.endswith(".tmpl") else rel
        if rel in (".claude/hooks/roles.json", ".claude/hooks/cost.json"):
            continue
        plan.write(out, fill(src.read_text(), ctx))


def context_doc(cfg: dict, ctx: dict) -> str:
    """docs/team/context.md: the project facts that the onboarding found. Written only when cfg has a stack."""
    stack = cfg.get("stack", {}) or {}
    lines = [f"# Project context: {cfg['project']}", "",
             "The `onboard-project` skill wrote this file. The role files use it. Update it through a PR when the stack changes.", "",
             "## Summary", "", f"- {ctx['PROJECT_SUMMARY']}", ""]
    if stack.get("stage"):
        lines += [f"- Stage: {stack['stage']}", ""]
    lines += ["## Stack", ""]
    for key, label in (("languages", "Languages"), ("frameworks", "Frameworks and libraries"),
                       ("package_managers", "Package managers"), ("databases", "Data stores"),
                       ("infra", "Infrastructure and hosting")):
        if stack.get(key):
            lines.append(f"- {label}: " + ", ".join(stack[key]) + ".")
    if stack.get("ci"):
        lines.append(f"- CI: {stack['ci']}.")
    lines.append("")
    if stack.get("commands"):
        lines += ["## Commands", "", "| Task | Command |", "|---|---|"]
        lines += [f"| {k} | `{v}` |" for k, v in stack["commands"].items() if v]
        lines.append("")
    if stack.get("layout"):
        lines += ["## Layout", "", "| Folder | Holds | Owner role |", "|---|---|---|"]
        for item in stack["layout"]:
            lines.append(f"| `{item.get('path', '')}` | {item.get('holds', '')} | {item.get('owner', '')} |")
        lines.append("")
    if stack.get("conventions"):
        lines += ["## Conventions", ""] + _bullets([fill(c, ctx) for c in stack["conventions"]]) + [""]
    if stack.get("users"):
        lines += ["## Users and personas", ""] + _bullets(stack["users"]) + [""]
    if stack.get("constraints"):
        lines += ["## Constraints", ""] + _bullets(stack["constraints"]) + [""]
    if stack.get("sources"):
        lines += ["## Sources", ""] + _bullets(stack["sources"]) + [""]
    return fill("\n".join(lines).rstrip() + "\n", ctx)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--target", required=True)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args(argv)

    cfg = json.loads(Path(args.config).read_text())
    validate(cfg)
    ctx = context(cfg)
    target = Path(args.target).resolve()
    if not target.is_dir():
        fail(f"target '{target}' is not a folder.")
    plan = Plan(target, args.force, args.dry_run)

    render_tree(plan, cfg, ctx)
    plan.write(".claude/hooks/roles.json", roles_json(cfg))
    plan.write(".claude/hooks/cost.json", cost_json(cfg))
    if cfg.get("stack"):
        plan.write("docs/team/context.md", context_doc(cfg, ctx))
    for role in cfg["roles"]:
        plan.write(f".claude/agents/{role['name']}.md", agent_file(cfg, role, ctx))
        if not role.get("helper"):
            plan.write(f"docs/team/{role['name']}.md", charter(cfg, role, ctx))
            test = TEST_FOR_BODY.get(role.get("body", "builder"), "builder")
            test_text = fill((TEMPLATES / "role-tests" / f"{test}.md").read_text(), {**ctx, "ROLE_TITLE": role["title"], "ROLE_NAME": role["name"]})
            plan.write(f".claude/role-tests/{role['name']}/test-1.md", test_text)
    for skill in PROJECT_SKILLS:
        for src in sorted((SKILLS / skill).rglob("*")):
            if src.is_file():
                rel = f".claude/skills/{skill}/{src.relative_to(SKILLS / skill).as_posix()}"
                plan.write(rel, fill(src.read_text(), ctx))
    plan.append_lines(".gitignore", GITIGNORE_LINES)

    mode = "Would write" if args.dry_run else "Wrote"
    print(f"{mode} {len(plan.written)} files in {target}.")
    for rel in plan.written:
        print(f"  + {rel}")
    if plan.skipped:
        print(f"Skipped {len(plan.skipped)} files that already exist (use --force to replace them):")
        for rel in plan.skipped:
            print(f"  = {rel}")
    if not args.dry_run:
        print("Next: run `python3 -m unittest discover -s .claude/hooks/tests`, then the role tests (role-tests skill).")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
