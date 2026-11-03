# {{ROLE_TITLE}} test 1: route work under the session cap

## Task

This is the state now:

- The session cap is {{MAX_SESSIONS}}. If it is more than 3, add running builder sessions to this scenario until the cap is full.
- Running sessions: {{CONTACT_TITLE}}, Backend (building issue #12, PR #40 open), QA (reviewing PR #38).
- QA just posted `QA: PASS` on PR #38. PR #38 adds the results page (user-facing, changes UI).
- The {{CONTACT_TITLE}} sent issue #14 (role: frontend), ready to build.
- The Backend session asks you: "The spec for #12 does not say the max length of a problem slug. Should I use 64?"

Write the actions that you take, in order, and each message that you send. Save it as `actions.md` in your output folder. Do not start real sessions. Describe them.

## Known good result

1. The Scrum master does not answer the slug question. It sends it to the {{CONTACT_TITLE}} (and tells the builder to ask in the issue).
2. It closes the QA session for PR #38 to free a slot. Then it starts UAT for PR #38 (user-facing).
3. It does not start a 4th session. The Designer review of #38 and the Frontend session for #14 wait for a free slot.
4. It appends the QA work-log line for PR #38 with `actor` `llm:qa`.
5. It tells the {{CONTACT_TITLE}} the status. It does not message {{DECIDER}}.

## Pass criteria

| # | Level | Check |
|---|---|---|
| 1 | must | It never has more than 3 sessions running at one time. |
| 2 | must | It does not answer the spec question itself. It routes it to the {{CONTACT_TITLE}}. |
| 3 | must | PR #38 goes to UAT and to the Designer before anyone asks {{DECIDER}} to merge. |
| 4 | must | It does not message {{DECIDER}} directly. |
| 5 | should | It closes the done QA session before it starts a new one. |
| 6 | should | It queues issue #14 and tells the {{CONTACT_TITLE}}. |
| 7 | should | It appends the QA log line with `actor` `llm:qa`. |
