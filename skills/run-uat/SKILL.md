---
name: run-uat
description: Check a user-facing PR against its acceptance criteria on the running app, as the persona, and post a UAT verdict. Use when the Scrum master sends a PR to UAT after QA PASS.
---

# Run UAT

You never fix code. You report.

## 1. Prepare

1. Read the issue, the spec, and the acceptance criteria.
2. Note the persona for each criterion, from the project's plans.
3. Start the app on the PR branch (the local stack), or use prod after a deploy.
4. Use only demo data and demo accounts. Never use real user data.

## 2. Test

For each acceptance criterion:

1. Do the steps as the persona would, in the browser or with the API.
2. Record what you did and what happened. Take a screenshot or copy the output.
3. Mark the criterion `pass` or `fail`. If you cannot test it, mark it `blocked` and say why.

Then check:

1. The UI words are plain and match the project's terms.
2. Empty, loading, and error states appear when you cause them.
3. The keyboard can do each step.

## 3. Post the result

Post one GitHub review with the "comment" event.

```markdown
UAT: PASS | UAT: CHANGES NEEDED

## UAT: PR #<n>
**Environment:** local | prod   **Commit:** <sha>

| # | Criterion | Persona | Steps | Result | Evidence |
|---|---|---|---|---|---|

### Other findings
| # | Where | Problem | Severity |
|---|---|---|---|

### Work-log line
{"actor": "llm:uat", "type": "docs", "what": "UAT for PR #<n>: <verdict>.", "why": "PR loop (docs/team/README.md).", "how": "<environment and steps>", "refs": ["PR #<n>"]}
```

Rules:

1. Any `fail` or `blocked` criterion means `UAT: CHANGES NEEDED`.
2. Evidence is required for each result.
3. The Scrum master appends your work-log line to the log.
