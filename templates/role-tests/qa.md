# {{ROLE_TITLE}} test 1: find planted defects, and do not fix them

## Task

Review this PR with the `review-pr` skill. You did not write it. Do not post to GitHub. Write the review that you would post as `review.md` in your output folder.

**Issue #60:** "As an org member, I can list the submissions for one assessment."
**Spec (short):** Add `GET /assessments/{assessment_id}/submissions`. Return id, person_id, total, and status. Only the caller's tenant. Tests: one for the list, one for another tenant (must return 404). Add a work-log entry.

**Diff:**

```diff
+++ app/routes/submissions.py
+import logging
+from fastapi import APIRouter, Depends
+from sqlalchemy import text
+from app.db import session_dep
+from app.auth import current_member
+
+log = logging.getLogger(__name__)
+router = APIRouter()
+SCORER_KEY = os.environ.get("SCORER_KEY", "dev-key-123")
+
+@router.get("/assessments/{assessment_id}/submissions")
+def list_submissions(assessment_id: str, db=Depends(session_dep), member=Depends(current_member)):
+    log.info("listing submissions for %s (%s)", member.email, assessment_id)
+    rows = db.execute(text(
+        f"SELECT id, person_id, total, status FROM submission WHERE assessment_id = '{assessment_id}'"
+    )).all()
+    return [dict(r._mapping) for r in rows]

+++ apps/api/tests/test_submissions.py
+def test_list_submissions(client, seed_assessment):
+    r = client.get(f"/assessments/{seed_assessment.id}/submissions")
+    assert r.status_code == 200
```

## Known good result

`QA: CHANGES NEEDED` with these planted defects:

1. SQL injection: the f-string puts `assessment_id` into the SQL (blocker).
2. No tenant check: the query has no `tenant_id` filter and does not check that the assessment belongs to the caller's tenant. With RLS off or a superuser connection, it leaks data. The spec asks for 404 on another tenant (blocker).
3. Personal data in logs: `member.email` (CLAUDE.md: no personal data in logs) (blocker).
4. A hard-coded secret fallback `"dev-key-123"`, and `os` is not imported (blocker or major).
5. The test for another tenant (404) is missing (major).
6. No work-log entry (major).

## Pass criteria

| # | Level | Check |
|---|---|---|
| 1 | must | The first line is `QA: CHANGES NEEDED`. |
| 2 | must | It finds at least 4 of the 6 planted defects, including the SQL injection and the email in the log. |
| 3 | must | Each finding has the file and line, the problem, why it matters, and a severity. |
| 4 | must | It does not write a fix (no code blocks with corrected code, no suggestion blocks). |
| 5 | should | It finds all 6 planted defects. |
| 6 | should | It lists the checks that it would run, and says that it could not run them without the repo. |
| 7 | should | It ends with a work-log line with `actor` `llm:{{ROLE_NAME}}`. |
