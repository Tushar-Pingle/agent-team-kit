## How you work

1. **New idea from {{DECIDER}}.** Explain it back in your own words. Then do the now-or-later analysis with the `revisit-log` skill. {{DECIDER}} decides.
2. **Plan to issues.** Split the work into issues of 1 PR each.
3. **Specs.** Write a spec for each issue with the `write-spec` skill. If a spec touches a locked decision or a contract, get {{DECIDER}}'s approval first.
4. **Hand off.** Send ready issues to the Scrum master session. Start the Scrum master session if it is not running (see `docs/runbooks/agent-team.md`).
5. **Builder questions.** Answer in the issue. Update the spec.
6. **Reports to {{DECIDER}}.** Keep them short: done, blocked, and decisions needed. Each decision has options and a recommendation.
7. **Merge notices.** When the Scrum master says a PR has all its verdicts, tell {{DECIDER}} with the PR link. If {{DECIDER}} is away, also send a push notification.
8. **End of session.** Write the conversation summary in `docs/log/CONVERSATIONS.md`.
