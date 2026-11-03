---
name: setup-team
description: Set up an AI agent team in the current project - a tailoring Q&A, then a scaffold of CLAUDE.md, docs (plans, ADRs, logs, team charters, runbook), role files, workflow skills, guard hooks, and role tests, then a verification run. Use when someone wants to start or adapt a project that one human decider runs with a team of AI agents.
argument-hint: "[path to an existing team.json]"
---

# Set up an agent team

This skill tailors and scaffolds the method in the `method-guide` skill. Read that skill first if the user does not know the method.

The kit files are in `${CLAUDE_PLUGIN_ROOT}`:

- `${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py`: the generator (Python 3, standard library only);
- `${CLAUDE_PLUGIN_ROOT}/scripts/team.example.json`: the example config with 10 roles and a helper;
- `${CLAUDE_PLUGIN_ROOT}/templates/`: the files that the generator fills.

## Rules

1. Ask; do not assume. Give each question with options and a recommendation.
2. Never overwrite the user's files. The generator skips existing files. Use `--force` only if the user says so, file by file.
3. Do not set a role state in this session. This is a setup session.
4. Never put a secret in any file.

## Step 1: Explain back

In 3 to 5 lines, explain what you will make, and the 3 things it gives:
1. a decider who talks to one PM;
2. builders that execute specs, and reviewers that never fix;
3. guard hooks and role tests.

Ask the user to confirm.

## Step 2: Tailoring questions

Ask these, a few at a time. If the user gave a `team.json` path, read it and ask only about the gaps.

| # | Question | Default |
|---|---|---|
| 1 | Project name, and one line about what it does | none |
| 2 | Name of the human decider (the person who approves merges and deploys) | none |
| 3 | Main branch | `main` |
| 4 | Where secrets live | the secret store that they use |
| 5 | Plain-English writing standard (ASD-STE100 at about 80%)? | ask; recommend yes for docs-heavy work |
| 6 | Which roles to keep, rename, merge, or add (show the 10 defaults) | all 10 + researcher |
| 7 | The folders that each builder role owns (show the defaults; read the repo layout first) | from the repo |
| 8 | Models for each role type | strongest model for the PM; an agentic model for the others; a small model for the helper |
| 9 | Session cap | 3 |
| 10 | The contact role | `pm` |

For a new role, pick the nearest body type: `builder`, `designer`, `qa`, `uat`, `release`, `growth`, `pm`, `scrum-master`, or `researcher`. A role with no repo writes sets `no_repo_writes` and `no_git_writes`. Only a release role sets `may_run_workflows`.

## Step 3: Write the config

1. Copy `${CLAUDE_PLUGIN_ROOT}/scripts/team.example.json` to `team.json` in the project root.
2. Change it to the answers. Keep the `never` lists. Add project-specific items where the user asks.
3. Show the user the role table (name, title, model, write folders) and ask them to confirm it.

## Step 4: Scaffold

1. Run a dry run first:
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/scaffold.py" --config team.json --target . --dry-run`
2. Show the list of files, and the files it will skip because they exist.
3. If the user agrees, run it without `--dry-run`.
4. If `.claude/settings.json` already exists, the generator skips it. Then show the user the `hooks` block from `${CLAUDE_PLUGIN_ROOT}/templates/.claude/settings.json`, and merge it only with the user's approval.

## Step 5: Verify

1. Run `python3 -m unittest discover -s .claude/hooks/tests`. All tests must pass.
2. Check that `python3 .claude/hooks/role.py show` prints `none`.
3. Tell the user to start a new Claude Code session, so that the new hooks and agent types load.
4. In that new session, run the role tests with the `role-tests` skill. Every role must pass before real work.

## Step 6: Hand over

Tell the user, in a few lines:

1. what was made;
2. the next steps:
   - fill in `CLAUDE.md` section 1;
   - write Plan 00 (the North Star) by Q&A;
   - add the project's own security and data rules to CLAUDE.md;
   - write one project-specific role test for the PM (a real spec);
3. how to start the PM: `claude --agent pm`, or the runbook in `docs/runbooks/agent-team.md`.

Suggest a first commit on a branch, with a PR for the decider to review. Do not push to the main branch.
