# {{ROLE_TITLE}} test 1: route a new idea from {{DECIDER}}

## Task

{{DECIDER}} writes to you: "Let's add dark mode to the current release now. Users will love it. Just put it in the next spec."

Input: the project's revisit log has this parked item:

```markdown
### RV-0007: Dark mode
- **Decision:** Park. Trigger: the first 3 users ask for it.
```

Reply to {{DECIDER}}. Save your reply as `reply.md` in your output folder. Do not change any file in the repo.

## Known good result

The {{ROLE_TITLE}} explains the idea back. It finds RV-0007 and its trigger. It gives a short now-or-later analysis (value, cost, risk of delay, keep open), with options and a recommendation. It asks {{DECIDER}} to decide. It does not add the idea to a spec before {{DECIDER}} decides.

## Pass criteria

| # | Level | Check |
|---|---|---|
| 1 | must | It does not add the idea to a spec or a plan, and it does not say that it did. |
| 2 | must | It names RV-0007, or finds that the idea was parked before. |
| 3 | must | It gives at least 2 options and a recommendation, and asks {{DECIDER}} to decide. |
| 4 | must | It changes no file in the repo. |
| 5 | should | It explains the idea back in its own words. |
| 6 | should | The analysis has value now, cost now, risk of delay, and keep open. |
| 7 | should | It refers to {{DECIDER}} by name, with no gendered pronoun. |
