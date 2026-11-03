---
name: log-entry
description: Add a work-log entry (worklog.jsonl and WORKLOG.md) in the correct format, in the same commit as the work. Use at the end of each work item.
---

# Write a work-log entry

The full rules are in [`docs/log/README.md`](../../../docs/log/README.md).

## Steps

1. Get the time: `date -Iseconds` (with `TZ` set to the decider's time zone).
2. Find the last id: `tail -1 docs/log/worklog.jsonl`. Add 1.
3. Append one JSON line to `docs/log/worklog.jsonl`:

```json
{"id": "WL-NNNN", "ts": "<time>", "session": "S-NNN", "actor": "llm:<role>", "type": "<plan|feat|fix|refactor|docs|ops|ship|correction>", "what": "...", "why": "...", "how": "...", "files": ["..."], "commit": null, "refs": ["..."]}
```

4. Append the same entry as one table row to `docs/log/WORKLOG.md`: `| id | ts | session | type | what | why | how | refs |`.
5. Check the JSON: `python3 -c "import json; [json.loads(l) for l in open('docs/log/worklog.jsonl')]"`.
6. Commit the entry with the work.

## Rules

1. Never edit or delete an old entry. To correct one, add a new entry with type `correction` and the old id in `refs`.
2. `what`, `why`, and `how` are 1 or 2 sentences each, in the writing rule of CLAUDE.md.
3. `why` links the decision, plan, issue, or request.
4. No personal data and no secrets.
5. QA, UAT, and Designer reviews put their log line in the review. The Scrum master appends it with the reviewer's actor.
6. If two sessions add the same id, the later PR changes its ids before merge.
