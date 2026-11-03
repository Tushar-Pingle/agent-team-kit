---
name: setup-team
description: Set up an AI agent team in the current project - a short tailoring Q&A (preset, team size, models), then a scaffold of CLAUDE.md, docs (plans, ADRs, logs, team charters, runbook, project context), role files that know the stack, workflow skills, guard hooks, the cost hook, and role tests, then a verification run. Use when someone wants to start or adapt a project that one human decider runs with a team of AI agents. Run onboard-project first for a new project, or for a team that knows the stack.
argument-hint: "[path to an existing team.json]"
---

# Set up an agent team

This skill tailors and scaffolds the method in the `method-guide` skill. Read that skill first if the user does not know the method.

Best path: run `onboard-project` first. It writes a `team.json` that already holds the stack, the layout, the models, and the plans. Then this skill asks only about the gaps. Without it, this skill asks the short Q&A below and the team is generic until `docs/team/context.md` is filled.

The kit files are in `${CLAUDE_PLUGIN_ROOT}`:

- `scripts/scaffold.py`: the generator (Python 3, standard library only);
- `scripts/init_team.py` and `scripts/presets.json`: a starter `team.json` from a preset;
- `scripts/team.example.json`: the full example config with 11 roles;
- `templates/`: the files that the generator fills.

## Rules

1. Ask; do not assume. Give each question with options and a recommendation.
2. Never overwrite the user's files. The generator skips existing files. Use `--force` only if the user says so, file by file.
3. Do not set a role state in this session. This is a setup session.
4. Never put a secret in any file.

## Step 1: Explain back

In 3 to 5 lines, explain what you will make, and the 4 things it gives:
1. a decider who talks to one PM;
2. builders that execute specs and know the stack, and reviewers that never fix;
3. guard hooks and role tests;
4. a cost line for each session.

Ask the user to confirm. If there is no `team.json` and no `.claude/onboarding/stack.json`, offer `onboard-project` first (recommended for a new project).

## Step 2: Tailoring questions

If the user gave a `team.json` path, read it and ask only about the gaps. Otherwise ask these, 3 or 4 at a time.

| # | Question | Options | Default |
|---|---|---|---|
| 1 | Project name, and one line about what it does | free text | none |
| 2 | Name of the human decider (approves merges and deploys) | free text | none |
| 3 | Team preset | `solo` (4 roles), `small` (7), `data` (7), `full` (11); show `init_team.py --list` | by the stack: `data` for a warehouse or dbt project, `small` for a web app, `solo` for one language and a small codebase, else `full` |
| 4 | Team size: keep the preset, or fewer, or more | merge roles (QA+UAT into one reviewer), or add a role from a body type | the preset |
| 5 | Model for the contact tier (the PM) | the strongest model available, or an explicit id | `opus` |
| 6 | Model for the agentic tier (builders, reviewers) | a fast agentic model, or an explicit id | `sonnet` |
| 7 | Model for the helper tier (researcher) | a small model, or an explicit id | `haiku` |
| 8 | Session cap | 2, 3, 5 | 3 |
| 9 | Main branch | free text | `main` |
| 10 | Where secrets live | the secret store that they use | free text |
| 11 | Plain-English writing standard (ASD-STE100 at about 80%)? | yes, no | yes for docs-heavy work |
| 12 | The folders that each builder role owns | from the repo layout (read it first, or use `discover.py`) | from the repo |
| 13 | Cost prices: fill the price table now, or later | now (ask for the provider's price page), later (tokens only) | later |
| 14 | The contact role | `pm` | `pm` |

For a new role, pick the nearest body type: `builder`, `designer`, `qa`, `uat`, `release`, `growth`, `pm`, `scrum-master`, or `researcher`. A role with no repo writes sets `no_repo_writes` and `no_git_writes`. Only a release role sets `may_run_workflows`.

A role's `model` is a tier name (`contact`, `agentic`, `helper`) or an explicit model id. The tiers resolve from the `models` block. Keep tiers unless the decider wants one role on a specific model.

## Step 3: Write the config

1. If there is no `team.json`: run `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/init_team.py" --preset <preset> --project "<name>" --decider "<name>" --summary "<one line>" --contact-model <id> --agentic-model <id> --helper-model <id> [--stack .claude/onboarding/stack.json] --out team.json`.
2. Change it to the answers: roles, folders, `never` items, the `stack` blocks, the prices. Keep the `never` lists. Add project-specific items where the user asks.
3. Show the user the role table (name, title, model, write folders, stack line) and ask them to confirm it.

## Step 4: Scaffold

1. Run a dry run first:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" --config team.json --target . --dry-run`
2. Show the list of files, and the files it will skip because they exist.
3. If the user agrees, run it without `--dry-run`.
4. If `.claude/settings.json` already exists, the generator skips it. Then show the user the `hooks` block from `${CLAUDE_PLUGIN_ROOT}/templates/.claude/settings.json` (SessionStart, PreToolUse guard, SessionEnd cost report), and merge it only with the user's approval.

## Step 5: Verify

1. Run `python3 -m unittest discover -s .claude/hooks/tests`. All tests must pass (guard and cost report).
2. Check that `python3 .claude/hooks/role.py show` prints `none`.
3. Run `python3 .claude/hooks/cost_report.py`. It prints this session's tokens, or says that no transcript was found (fine outside Claude Code).
4. Tell the user to start a new Claude Code session, so that the new hooks and agent types load.
5. In that new session, run the role tests with the `role-tests` skill. Every role must pass before real work.

## Step 6: Hand over

Tell the user, in a few lines:

1. what was made;
2. the next steps:
   - if `onboard-project` did not run: fill `CLAUDE.md` section 1 and `docs/team/context.md`, and write Plan 00 (the North Star) by Q&A;
   - if it did: lock the plans after a read;
   - add the project's own security and data rules to CLAUDE.md;
   - fill `cost.prices_per_million` in `team.json` when the price page is at hand (the `cost-report` skill explains it);
   - write one project-specific role test for the PM (a real spec);
3. how to start the PM: `claude --agent pm`, or the runbook in `docs/runbooks/agent-team.md`.

Suggest a first commit on a branch, with a PR for the decider to review. Do not push to the main branch.
