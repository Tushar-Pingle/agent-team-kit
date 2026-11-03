---
name: revisit-log
description: Handle a new idea from the decider or an agent without scope creep - explain it back, run the now-or-later analysis, give options with a recommendation, and record the decider's decision in docs/log/REVISIT.md. Use whenever an idea can change the current scope.
---

# Revisit log

Only the decider adopts, parks, or rejects an idea. You never decide it.

## Steps

1. **Explain it back.** Write the idea in your own words, in 2 to 4 lines. Ask the decider to confirm it before you design anything.
2. **Look for history.** Search `docs/log/REVISIT.md` for the same or a close idea. If it is parked, name its id and its trigger, and say if the trigger happened.
3. **Find what it touches.** List the plans, the locked decisions, the ADRs, and the contracts that it changes.
4. **Now-or-later analysis**, in 4 short parts:
   1. **Value now.** What it gives to the current goal and its hypotheses.
   2. **Cost now.** The added work, and the risk to the current time box.
   3. **Risk of delay.** What becomes harder if we do it later.
   4. **Keep open.** What the design must keep possible now, so that later is easy.
5. **Options.** Give 2 or 3 options (for example adopt now, park with a trigger, reject). Give a recommendation and the reason.
6. **Ask the decider to decide.** Do not change a plan, a spec, or the code before the answer.

## Record the decision

1. Add a row to the status table and an item in `docs/log/REVISIT.md`:

```markdown
### RV-NNNN: <title>

- **Idea (<who>):** <the idea, in their words where possible>
- **Analysis:** <value now, cost now, risk of delay>
- **Decision:** <date>. <Adopt | Park | Reject>, and why.
- **Keep open:** <what the design keeps possible>
- **Trigger:** <an event or a date>
- **Links:** <plans, ADRs>
```

2. Never delete an item. To change one, change its status and add a dated `History` line.
3. If the decider adopts it, update the plan or write an ADR. Add a work-log entry for each change.
4. When a trigger happens, run the analysis again. The decider decides again.
