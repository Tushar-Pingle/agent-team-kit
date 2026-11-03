# Role tests

Each role has 1 or more test tasks with a known good result. A role file is used only after it passes its tests. Run the tests again when a role file, its skills, or its charter change. Use the `role-tests` skill.

## How to run a test

1. Use a session that is not the role under test. The grader must not grade its own work.
2. Copy only the **Task** part of the test to a folder outside the repo. The role must not see the known good result or the pass criteria.
3. Start the role with its real agent type (`subagent_type: <role>`), so that the guard and the role scope apply. Tell it: do not set the role, do not read `.claude/role-tests/`, and write only in the output folder.
4. Wait for the result. Do not help the role.
5. Grade the output against the **Pass criteria**. Each `must` item must pass. A test passes when all `must` items pass and at least half of the `should` items pass.
6. Check that `python3 .claude/hooks/role.py show` still prints `none`, and that the repo has no changes.
7. Record the result in [RESULTS.md](RESULTS.md): date, commit, model, pass or fail, and the evidence.

If a test fails, find the cause first. It can be in the role file, a skill, or the test itself. Fix it, record the change openly, and run the test again.

## Tests

Each role folder has `test-1.md`. The kit gives a generic first test for each role type. Write at least one more test that uses this project's own plans, for example a real spec for the {{CONTACT_TITLE}}.
