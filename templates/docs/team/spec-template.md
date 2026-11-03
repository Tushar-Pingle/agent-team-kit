# Spec template

The PM writes one spec for each build issue . A builder must be able to do the work from the spec alone, without a guess. Copy this template into the issue, or into `docs/specs/<issue>.md` for a long spec.

Rules:

1. Fill in each section. Write "none" if a section does not apply.
2. If the spec touches a locked decision or a contract, get {{DECIDER}}'s approval first. Record it in the "Approval" line.
3. If a builder finds a gap, the builder stops and asks in the issue. The PM updates the spec. Then the builder continues.

---

```markdown
# Spec: <issue title> (#<issue number>)

Approval: not needed | {{DECIDER}} approved on YYYY-MM-DD (touches <decision or contract>)
Slice: S<n>
Role: <role>

## 1. Goal and links
- Story: As a <persona>, I can <action>, so that <value>.
- Plans and ADRs: <links>
- Prototype or wireframe: <link, for UI work>

## 2. Files
| File | Add or change | What |
|---|---|---|

## 3. Interfaces and data
Function signatures, API requests and responses, schemas, events, and tokens.
Give exact names and types.

## 4. Steps
1. <one action>
2. <one action>

## 5. Edge cases
| Case | Expected behavior |
|---|---|

## 6. Tests that must pass
| Test | What it checks |
|---|---|

## 7. Out of scope
- <what the builder must not do or change>

## 8. Done criteria
1. <check that passes or fails>
2. The CI gate passes.
3. A work-log entry exists.
```
