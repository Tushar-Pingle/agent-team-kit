---
name: cost-report
description: Show where this session's tokens went, by model, with the cost from the project's price table. Use when the decider asks what a session cost, where the tokens went, or how much the team spends; also to check the cost log or to set the prices.
---

# Cost report

The project logs each session's tokens and cost. This skill shows the numbers on demand.

## Show the current session

Run:

```bash
python3 .claude/hooks/cost_report.py
```

It finds the newest transcript for this project and prints a table: tokens by model (input, output, cache write, cache read), the total, and the cost. Show the table to the decider as it is. Add one line that names the biggest spender and why, if you know (a long file read, a large plan, many tool calls).

For a different session, give the transcript: `--transcript <path>`. Transcripts are in `~/.claude/projects/<project folder>/<session>.jsonl`.

## Read the log

The `SessionEnd` hook appends one line for each session to the cost log (`docs/log/COST.md` by default; `.claude/hooks/cost.json` names it). For a period summary, read the log and sum the `Total` and `Cost` columns for the lines in that period. Report by role too when the decider asks: the `Role` column holds it.

## Set or change the prices

If the report says that prices are not set:

1. Ask the decider for the price page of their provider. Do not guess a price.
2. Put the prices in `team.json` under `cost.prices_per_million`, per 1 million tokens, with `input`, `output`, `cache_write`, and `cache_read`. A key matches a model id exactly or by substring (for example `"sonnet"`).
3. Run `python3 .claude/hooks/../../scripts/scaffold.py` from the kit with `--force` for `.claude/hooks/cost.json` only, or edit `.claude/hooks/cost.json` by hand with the same values.

## Limits

- The report counts this session's transcript. A separate cloud session has its own transcript and its own line.
- A subagent counts only when its messages are in the same transcript.
- The numbers are from the transcript's usage blocks, not from a bill. Use the provider's console for the invoice.
