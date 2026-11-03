# Agent Team Kit

Run a project with **one human decider and a team of AI agents**, with the checks of a full team. This kit gives you the method, the reasons behind it, and a scaffold that you tailor to any project.

Version 0.1.0. Author: Tushar Pingle. The method came from a real project setup, and every part was tested before it went into this kit.

## What you get

| Part | What it does |
|---|---|
| `method-guide` skill | The playbook: the order of the setup, the reason for each step, and the lessons from the first real setup. |
| `setup-team` skill | A tailoring Q&A, then a scaffold of your project, then a check that it works. |
| `revisit-log` skill | Handles new ideas without scope creep. Only the decider decides. |
| `write-spec` skill | Implementation-ready specs, so builders execute and never guess. |
| `review-pr`, `run-uat` skills | QA and UAT reviews with verdict lines. Reviewers never fix. |
| `log-entry` skill | One work-log entry for each work item. |
| `role-tests` skill | Test each role file before use, with planted traps and pass criteria. |
| `scripts/scaffold.py` | Fills the templates from your `team.json`. Standard-library Python. Never overwrites a file unless you say so. |

The scaffold writes these into your project:

- `CLAUDE.md`: short rules, start and end steps, and a docs map.
- `docs/plans/`, `docs/adr/`: a plan template, a plan index, and ADR 0000.
- `docs/log/`: the work log (JSONL and a table), the conversation log, and the revisit log.
- `docs/team/`: the team README with diagrams, one charter for each role, and the spec template.
- `docs/runbooks/agent-team.md`: how to start the contact role and role sessions, the task message, and the limits of the guard.
- `.claude/agents/<role>.md`: one role file for each role, with model, scope, steps, rules, and never-list.
- `.claude/hooks/`: `guard.py`, `role.py`, `session_start.py`, `roles.json`, and the guard unit tests.
- `.claude/settings.json`: the hook wiring.
- `.claude/skills/`: the workflow skills, so the project works without the plugin too.
- `.claude/role-tests/`: one generic test for each role, a README, and a results table.

## Default team

| Role | Job |
|---|---|
| PM | The decider's single point of contact. Writes specs. Reports back. |
| Scrum master | Starts sessions, routes PRs, keeps the logs. Under the PM. |
| Platform, Backend, Frontend | Builders. Execute specs in their own folders only. |
| Designer | Prototypes, tokens, and DESIGN verdicts on UI PRs. |
| QA, UAT | Review with verdict lines. Never fix code. |
| Release | Deploys only after the decider approves. |
| Growth | Drafts only. Never sends or posts. |
| Researcher (helper) | Read-only facts with sources, on a small model. |

You can keep, rename, merge, or add roles in the setup Q&A.

## Install

### Upload (claude.ai or an app that takes a plugin zip)

Upload `agent-team-kit-0.1.0-plugin.zip`. Its top-level folder `agent-team-kit/` holds `.claude-plugin/plugin.json`.

### Claude Code, from a folder

1. Unzip the plugin zip. You get the folder `agent-team-kit/`.
2. Run `claude --plugin-dir /path/to/agent-team-kit` to load it for a session.

### Claude Code, as a local marketplace (from the marketplace zip)

1. Unzip `agent-team-kit-0.1.0.zip` (the marketplace zip). You get the folder `agent-team-kit-marketplace/`.
2. In Claude Code, run:

```text
/plugin marketplace add /path/to/agent-team-kit-marketplace
/plugin install agent-team-kit@agent-team-kit-marketplace
```

3. Start a new session in your project.

### Check the plugin

```bash
claude plugin validate /path/to/agent-team-kit
python3 /path/to/agent-team-kit/tests/test_scaffold.py
```

## Quick start

1. Open your project (new or existing) in Claude Code.
2. Run `/agent-team-kit:setup-team`. Answer the questions.
3. Review the dry run. Then let it write the files.
4. Run `python3 -m unittest discover -s .claude/hooks/tests`.
5. Start a new session. Run the role tests with `/agent-team-kit:role-tests`.
6. Write Plan 00 (your North Star) by Q&A. Then start the PM: `claude --agent pm`.

## Fixed and local

| Keep fixed | Make local |
|---|---|
| A human decider approves merges, deploys, and scope | The stack, the folders, the milestones |
| Separation of duties and verdict lines | The roles and their names |
| No secrets in files; outbound content is drafts only | Compliance and data rules |
| The revisit log and the logs | The writing standard (on or off) |
| Role tests before a role file is used | The models and the session cap |

## Limits

- The guard is one layer of three (instructions, hooks, permissions). It checks the paths of `Write` and `Edit`, not every file that a shell command writes. Add a secret scan to CI as a second check.
- The guard finds common secret formats only.
- A user can turn hooks off in their own settings.
- The plugin installs no global hooks. The guard runs only in projects that you scaffold.
