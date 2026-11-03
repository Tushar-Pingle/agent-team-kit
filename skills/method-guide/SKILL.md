---
name: method-guide
description: The playbook behind agent-team-kit - the order to set up a project run by one human decider and a team of AI agents, the reason for each step, and the lessons from the first real setup. Use when you plan a new project with an agent team, explain the method to someone, or decide how to adapt it.
---

# Method guide: one decider, a team of AI agents

This method lets one person (the **decider**) run a project with a team of AI agents, with the checks of a full team. It came from a real project setup. The decider was a solo, part-time founder.

## 1. Core ideas

1. **The human decides. The agents propose and build.** Scope, locked decisions, merges, and deploys are the decider's. Agents ask with options and a recommendation.
2. **Plans first, then code.** Write a plan for each component through questions and answers. Record each important decision as an ADR. Plans and ADRs are the source of truth.
3. **Nothing is lost.** Each work item gets a log entry. Each session gets a summary. Each idea that can change the scope goes to the revisit log, where only the decider decides.
4. **Separation of duties.** A builder never reviews its own work. Reviewers never fix. The decider approves each merge and deploy.
5. **One point of contact.** The decider talks only to the PM. The PM turns input into specs and reports back. A Scrum master under the PM runs the sessions.
6. **Builders execute, they do not guess.** Each issue has an implementation-ready spec. If something is unclear, the builder stops that part and asks.
7. **Trust, but verify the agents.** Hooks block dangerous actions. Each role has a write scope. Role tests check each role file before use.

## 2. The order

Follow this order. Each step needs the one before it.

| # | Step | Output | Why now |
|---|---|---|---|
| 1 | North Star Q&A | Plan 00: the goal, the users, the hypotheses, the locked decisions, the cutlines | Every later choice is checked against it. |
| 2 | Logs and the revisit log | `docs/log/` | Start on day 1, so the decider's reasons are kept from the start. |
| 3 | Writing standard (optional) | `docs/standards/` | Plain, short text is easier for humans and for agents. Decide it before the docs grow. |
| 4 | Component plans, by Q&A | `docs/plans/NN-*.md` + ADRs | Ask, research, give options with a recommendation, then record the decision. One plan at a time. |
| 5 | Team design | The roles, the contact role, the PR loop, the session cap | Decide where agents run (your own sessions, not CI, unless you choose CI) before you build anything for them. |
| 6 | CLAUDE.md | A short root file: rules, start steps, end steps, a map of the docs | Each session reads it first. Keep it short. Link to the details. |
| 7 | Team build | Role files, skills, guard hooks, role tests | Run `setup-team` from this kit. |
| 8 | Role tests | 2 or more runs, with fixes | They find defects that a read does not. |
| 9 | Time boxes | Thin slices with dates and a buffer | Confirm them only after the team works, because the team sets the pace. |
| 10 | Start | The decider starts the PM session | From now on, the decider talks only to the PM. |

## 3. How to run a planning Q&A

1. Read what exists. Research the options (current docs, prices, limits).
2. Ask 3 to 4 questions at a time. Each question has options with context, trade-offs, and a recommendation.
3. When the decider adds a new idea, explain it back first. Then run the now-or-later analysis (`revisit-log` skill).
4. Write the plan with a decision table (`P<NN>-D<n>`). Write ADRs for the decisions that are hard to change.
5. Add the work-log entries and the session summary.

## 4. The team

| Role | Model (by type of work) | Owns |
|---|---|---|
| PM (contact role) | The strongest model | Specs, issues, reports to the decider |
| Scrum master | An agentic model | Sessions, routing, board, logs |
| Builders (platform, backend, frontend, ...) | An agentic model | Their own folders only |
| Designer | An agentic model | Prototypes, tokens, design review |
| QA, UAT | An agentic model | Reviews only, never code |
| Release | An agentic model | Release notes, deploys after approval |
| Growth | An agentic model | Drafts only |
| Researcher (helper) | A small, fast model | Read-only facts with sources |

Keep the session cap low at first (for example 3). Raise it when usage data shows room.

## 5. Guardrails: 3 layers

1. **Instructions:** the role file and the charter (mission, scope, steps, never-list).
2. **Hooks:** `guard.py` blocks, for all sessions: a push to the main branch, merges, `apply` outside the pipeline, workflows outside the release role, secrets in writes and commands, writes to `.env`, outbound sends, and changes to the role state. For a role session, it blocks writes outside the role's folders.
3. **Permissions:** the role file's `disallowedTools` (for example, QA has no edit tools).

The guard finds a session's role from `agent_type` (`claude --agent <role>`, or a subagent), or from `.claude/state/role`, which a separate cloud session sets one time.

## 6. Lessons from the first setup

1. **A subagent must never set the role state.** A subagent shares its parent's checkout. One did set it, and the guard then limited the parent session and blocked the normal undo. Fix: the guard blocks `role.py set` when `agent_type` exists, and role files set a role only if the task message says so.
2. **A guard rule can catch quoted text.** The first fix blocked a heredoc that only quoted the command. Check each shell segment, not the whole text.
3. **Test hooks with the real agent types.** General subagents with a pasted role file do not trigger role rules, so they hide guard defects.
4. **"Stop and ask" can block too much.** One missing token stopped a whole component. The rule now says: stop only the part that needs the answer, finish the defined parts, and list the questions.
5. **Put key rules early and say them plainly.** A pronoun rule at the end of a long list was not followed. In the opening lines, with the exact words to avoid, it was.
6. **Keep edge cases when you split an issue.** One spec split an issue and lost the user-facing edge cases. The spec skill now requires them in the part that owns them.
7. **Role tests find doc conflicts too.** A PM test found that a plan conflicted with an accepted ADR. Write the superseding ADR at once.
8. **Watch the clock.** Use the decider's time zone for dates. A UTC date one day ahead caused wrong dates.
9. **A merge can race a push.** If the decider merges while you push, check that your last commit is in the main branch. If not, open a new PR for it.

## 7. Adapting the method

| Keep fixed | Make local |
|---|---|
| The decider approves merges, deploys, and scope | The stack, the folders, the slices |
| Separation of duties and verdict lines | The roles: keep, rename, merge, or add |
| No secrets in files; drafts only for outbound content | Compliance and data rules |
| The revisit log and the logs | The writing standard (on or off) |
| Role tests before a role file is used | The models and the session cap |
