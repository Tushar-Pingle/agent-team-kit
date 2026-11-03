# Agent Team Kit

**One human decider. A team of AI agents that know your stack.**

A Claude Code plugin that plans a project by Q&A before any agent writes code, then scaffolds a tailored agent team: a PM as your single point of contact, builders that execute specs in their own folders, reviewers that never fix, guard hooks, role tests, and a cost line for every session.

Version 0.2.0. MIT. Author: Tushar Pingle. The method came from a real project run by a solo, part-time founder. Every part was tested before it went in.

```text
/agent-team-kit:onboard-project   ->   /agent-team-kit:setup-team   ->   claude --agent pm
   discover + plan by Q&A              scaffold + verify                  the team runs
```

## Why

Generic agent teams guess. They do not know your framework's conventions, your folder ownership, your users, or what "done" means. So the decider answers the same questions in every session, and the agents drift.

This kit front-loads the thinking. The onboarding scans the repo, asks what a scan cannot see, checks the current conventions of your stack on the web, and writes the plans with you until no question is open. The PM then runs on plans that already hold the answers.

## What you get

| Part | What it does |
|---|---|
| `onboard-project` skill | The front door. Repo scan + context Q&A + web check of the stack. `plan` mode writes Plan 00 (North Star), component plans, ADRs, and slices by Q&A. `team-only` mode goes straight to the team design. Ends with a `team.json`. |
| `setup-team` skill | Preset, team size, and one model choice for each tier. Then the scaffold, the hook tests, and a hand-over. Reads a `team.json` and asks only about the gaps. |
| `method-guide` skill | The playbook: the order of the setup, the reason for each step, and the lessons from the first real setup. |
| `revisit-log` skill | Handles new ideas without scope creep. Only the decider decides. |
| `write-spec` skill | Implementation-ready specs, so builders execute and never guess. |
| `review-pr`, `run-uat` skills | QA and UAT reviews with verdict lines. Reviewers never fix. |
| `log-entry` skill | One work-log entry for each work item. |
| `role-tests` skill | Test each role file before use, with planted traps and pass criteria. |
| `cost-report` skill | Where the tokens went, by model, with the cost from your price table. |
| `scripts/discover.py` | Read-only repo scan: languages, frameworks, package managers, commands, CI, data stores, layout. Prints JSON. |
| `scripts/init_team.py` | A starter `team.json` from a preset and the stack. |
| `scripts/scaffold.py` | Fills the templates from `team.json`. Standard-library Python. Never overwrites a file unless you say so. |

The scaffold writes these into your project:

- `CLAUDE.md`: short rules, the stack line, start and end steps, a docs map.
- `docs/plans/`: the North Star template, the component plan template, the plan index. `docs/adr/`: ADR 0000.
- `docs/log/`: the work log (JSONL and a table), the conversation log, the revisit log, the cost log.
- `docs/team/`: the team README with diagrams, `context.md` (your stack, layout, users, constraints), one charter for each role, the spec template.
- `docs/runbooks/agent-team.md`: how to start the PM and the role sessions, the task message, the limits of the guard, the cost hook.
- `.claude/agents/<role>.md`: one role file for each role, with model, scope, **your stack**, steps, rules, and a never-list.
- `.claude/hooks/`: `guard.py`, `role.py`, `session_start.py`, `cost_report.py`, `roles.json`, `cost.json`, and the unit tests.
- `.claude/settings.json`: the hook wiring (SessionStart, PreToolUse guard, SessionEnd cost report).
- `.claude/skills/`: the workflow skills, so the project works without the plugin too.
- `.claude/role-tests/`: one generic test for each role, a README, and a results table.

## Presets

| Preset | Roles | For |
|---|---|---|
| `solo` | PM, Developer, QA, Researcher | One language, a small codebase, one person |
| `small` | PM, Scrum master, Backend, Frontend, QA, UAT, Researcher | A web app |
| `data` | PM, Scrum master, Pipeline, Modeling, Activation, Data QA, Researcher | A warehouse, dbt, reverse ETL |
| `full` | + Platform, Designer, Release, Growth | A product with design, releases, and outreach |

You can keep, rename, merge, or add roles in the setup Q&A. New roles pick a body type: `builder`, `designer`, `qa`, `uat`, `release`, `growth`, `pm`, `scrum-master`, `researcher`.

## Models

Three tiers, chosen once at setup:

| Tier | Roles | Recommendation |
|---|---|---|
| `contact` | The PM | The strongest model you have |
| `agentic` | Builders, reviewers, Scrum master | A fast agentic model |
| `helper` | The researcher | A small model |

A role's `model` in `team.json` is a tier name or an explicit model id. Change a tier in one place and every role on it follows.

## Cost

A `SessionEnd` hook reads the session transcript, sums the tokens by model (input, output, cache write, cache read), prices them from `team.json` (`cost.prices_per_million`, per 1 million tokens), and appends one line to `docs/log/COST.md`. The next session's start message repeats the last total. Run `python3 .claude/hooks/cost_report.py` or the `cost-report` skill at any time for the current session.

Prices are yours to fill from your provider's price page. The kit ships none, so nothing goes stale. An empty table gives a token-only report.

## Install

### From GitHub (Claude Code)

```text
/plugin marketplace add <github-user>/agent-team-kit
/plugin install agent-team-kit@agent-team-kit
```

Start a new session in your project.

### From a folder

```bash
git clone https://github.com/<github-user>/agent-team-kit.git
claude --plugin-dir /path/to/agent-team-kit
```

### Check it

```bash
claude plugin validate /path/to/agent-team-kit
python3 tests/test_scaffold.py          # scaffolds every preset into a temp repo and runs the hook suite there
python3 templates/.claude/hooks/tests/test_cost_report.py
```

## Quick start

1. Open your project (new or existing) in Claude Code.
2. Run `/agent-team-kit:onboard-project`. Pick `plan` for a new project, `team-only` for a planned one. Answer the questions, 3 or 4 at a time.
3. Run `/agent-team-kit:setup-team team.json`. Review the dry run. Let it write the files.
4. Start a new session. Run the role tests with `/agent-team-kit:role-tests`.
5. Lock the plans after a read. Then start the PM: `claude --agent pm`.

From now on, you talk only to the PM.

## Requirements

- Claude Code with plugin support.
- Python 3.10 or later on the path (standard library only).
- Git.

## Fixed and local

| Keep fixed | Make local |
|---|---|
| A human decider approves merges, deploys, and scope | The stack, the folders, the milestones |
| Separation of duties and verdict lines | The roles and their names |
| No secrets in files; outbound content is drafts only | Compliance and data rules |
| The revisit log and the logs | The writing standard (on or off) |
| Role tests before a role file is used | The models, the session cap, the prices |

## Limits

- The guard is one layer of three (instructions, hooks, permissions). It checks the paths of `Write` and `Edit`, not every file that a shell command writes. Add a secret scan to CI as a second check.
- The guard finds common secret formats only.
- A user can turn hooks off in their own settings.
- The plugin installs no global hooks. The guard and the cost hook run only in projects that you scaffold.
- The cost hook counts one session's transcript. A separate cloud session has its own line. A subagent counts only when its messages are in the same transcript. The numbers come from the transcript's usage blocks, not from a bill.
- The web check in the onboarding gives facts with sources. It never copies a page into a plan.

## Contributing

Open an issue with the project type and what the team got wrong. PRs welcome: keep the standard library only, add a test, and update the changelog.
