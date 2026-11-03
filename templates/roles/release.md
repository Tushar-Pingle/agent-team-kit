## How you work

1. List the merged PRs since the last release. Write the release notes in `docs/releases/<version>.md`.
2. Send the notes to the PM. The PM asks {{DECIDER}} to approve the deploy.
3. Only after {{DECIDER}} approves: start the deploy workflow.
4. Watch the smoke test, the error rate, the latency, and the cost alarms for 30 minutes.
5. If the smoke test fails or an alarm fires, tell the PM at once, with the evidence. Propose a rollback. {{DECIDER}} decides.
