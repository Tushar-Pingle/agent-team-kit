# {{ROLE_TITLE}} test 1: find the failed criterion, with evidence

## Task

Use the `run-uat` skill. You cannot start the app in this test. Use the session record below as the observed behavior of the running app. Write the review that you would post as `uat.md` in your output folder.

**PR #70:** practice runs in the workspace.
**Acceptance criteria:**

1. A candidate sees "Practice runs left: 5" before the first run.
2. "Run practice tests" runs the visible test cases and shows a pass or fail for each case.
3. After each practice run, the counter goes down by 1.
4. When the counter is 0, the "Run practice tests" button is disabled and a message says "No practice runs left. You can still submit."

**Session record (demo candidate, local stack, commit 4f2a9c1):**

```text
[10:02:11] open /projects/demo/workspace -> header shows "Practice runs left: 5"
[10:02:40] click "Run practice tests" -> status "Running..." -> 3 cases: case-1 pass, case-2 pass, case-3 fail ("total: expected 1234.5, got 1234")
[10:02:41] header shows "Practice runs left: 5"
[10:03:05] click "Run practice tests" -> 3 cases: pass, pass, fail
[10:03:06] header shows "Practice runs left: 5"
[10:03:30] reload page -> header shows "Practice runs left: 3"
[10:04:10] runs 3, 4, 5 done -> header shows "Practice runs left: 0" after reload
[10:04:12] button "Run practice tests" is disabled; message "No practice runs left. You can still submit."
```

## Known good result

`UAT: CHANGES NEEDED`. Criteria 1, 2, and 4 pass. Criterion 3 fails: the counter does not change after a run until the page reloads (10:02:41 and 10:03:06 still show 5). The server count is correct (3 after reload), so the defect is in the UI update. Criterion 4 passes, but only after a reload. A note about that is good.

## Pass criteria

| # | Level | Check |
|---|---|---|
| 1 | must | The first line is `UAT: CHANGES NEEDED`. |
| 2 | must | Criterion 3 is `fail`, with the log lines as evidence. |
| 3 | must | Criteria 1 and 2 are `pass`, with evidence. |
| 4 | must | It does not propose a code fix in code. It reports only. |
| 5 | should | It says that the server count is correct and the UI does not update until a reload. |
| 6 | should | It notes that criterion 4 was checked only after a reload. |
| 7 | should | It ends with a work-log line with `actor` `llm:{{ROLE_NAME}}`. |
