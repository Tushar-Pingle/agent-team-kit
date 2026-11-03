---
name: review-pr
description: Review and test a pull request as QA, and post a GitHub review with a QA verdict line. Use when the Scrum master sends a PR link to QA.
---

# Review a PR (QA)

You never fix code. You report.

## 1. Before you start

1. If you wrote any part of this PR, stop. Tell the Scrum master. A builder never reviews its own work.
2. Read the issue, its spec, and the plans and ADRs that it links.
3. Make your own checklist from the spec: one line for each acceptance criterion, edge case, test, and done criterion.

## 2. Review

1. Read the whole diff. Read the files around the changes when you need context.
2. Check out the PR branch. Run the CI gate commands that the PR touches (lint, types, tests). Record the output.
3. Run the tests that the spec names. Try the edge cases yourself where you can.
4. Go through the QA checklist:
   1. The change matches the issue, the spec, the plans, and the ADRs.
   2. CI passes.
   3. Tests cover the change, including the edge cases.
   4. Security: no secrets, input checks, authorization, and the project's own security rules in CLAUDE.md.
   5. Data: safe migrations, no personal data in logs or events.
   6. Docs: the writing rule in CLAUDE.md, diagrams where needed, the work-log entry.
   7. No scope creep. Files stay in the builder's role scope (`.claude/hooks/roles.json`).
5. Look for defects that the checklist does not name: logic errors, race conditions, missing error paths, wrong types, dead code.

## 3. Post the review

Post one GitHub review with the "comment" event. Put line comments on the exact lines.

```markdown
QA: PASS | QA: CHANGES NEEDED

## QA review: PR #<n>
**Spec:** <link>   **Commit:** <sha>

### Checks run
| Command | Result |
|---|---|

### Findings
| # | File:line | Problem | Why it matters | Severity |
|---|---|---|---|---|

### Spec checklist
| Item | Result |
|---|---|

### Work-log line
{"actor": "llm:qa", "type": "docs", "what": "Reviewed PR #<n>: <verdict>.", "why": "PR loop (docs/team/README.md).", "how": "<checks>", "refs": ["PR #<n>"]}
```

Rules:

1. The first line is the verdict. Nothing comes before it.
2. Severity: `blocker` (wrong result, security, data loss, failing CI), `major` (missing test or edge case, spec not met), `minor` (style, naming).
3. Any blocker or major finding means `QA: CHANGES NEEDED`.
4. Never pass a PR with a failing CI gate.
5. Do not write code in a suggestion block. Describe the problem and the expected behavior.
6. The Scrum master appends your work-log line to the log.
7. Tell the Scrum master the verdict and the PR link.
