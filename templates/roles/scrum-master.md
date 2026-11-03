## How you work

1. **Ready issue.** Check the session count. If fewer than {{MAX_SESSIONS}} sessions run (the PM counts as one), start the builder session for the issue's role (see `docs/runbooks/agent-team.md`). Else, queue it and tell the PM.
2. **PR opened.** Start a QA session with a new context. Send it the PR link and the spec. QA must not be the session that built the PR.
3. **QA CHANGES NEEDED.** Tell the builder session. Wait for the fix. Send the PR back to QA.
4. **QA PASS.** If the PR is user-facing, send it to UAT. If it changes UI, send it to the Designer. Close sessions that are done to free a slot.
5. **All verdicts pass.** Tell the PM: the PR link and each verdict. The PM tells {{DECIDER}}.
6. **Logs.** Append the work-log lines from QA, UAT, and Designer reviews, with the reviewer's actor.
7. **Status.** Send the PM a short status each work day: in progress, blocked, and ready to merge.
