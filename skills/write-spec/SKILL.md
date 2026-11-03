---
name: write-spec
description: Turn an issue or a request from the decider into an implementation-ready spec from the project's spec template. Use when the PM (or the contact role) prepares an issue for a builder, or when a builder asks a spec question.
---

# Write a spec

The template is [`docs/team/spec-template.md`](../../../docs/team/spec-template.md). The team rules are in [`docs/team/README.md`](../../../docs/team/README.md).

## 1. Before you write

1. Read the issue, the plans and ADRs that it links, and the revisit log.
2. Find the milestone or slice in the plans. If the work is not in the current one, stop. Ask the decider.
3. Check for scope creep. If the request adds scope beyond the plans, it goes to the revisit log (`revisit-log` skill). The decider decides. Do not put it in the spec.
4. Check if the work touches a locked decision (a plan decision or an ADR) or a contract (schemas, APIs, events, tables). If it does, the spec needs the decider's approval before the build.

## 2. Write

Fill each section of the template. Do these checks:

| Section | Check |
|---|---|
| Goal and links | One story. Links to each plan, ADR, and prototype that applies. |
| Files | Exact paths. Each file is in the builder role's scope (`.claude/hooks/roles.json`). |
| Interfaces and data | Exact names and types. Example payloads. No "etc.". |
| Steps | Numbered. One action each. A builder can do them in order. |
| Edge cases | At least 3. Include empty input, bad input, and a failure of an external service. |
| Tests | Each acceptance criterion has a test. Each edge case has a test. |
| Out of scope | Name the near things that the builder must not do. |
| Done criteria | Each one passes or fails. Include the CI gate and the work-log entry. |

## 3. The guess test

Read the spec as the builder. For each step, ask: "Can I do this without a guess?" If not, add the missing fact. Typical gaps:

- A name, a type, a default value, or a limit is missing.
- An error case has no expected behavior.
- A UI state (empty, loading, error) has no text or design.
- A test does not say what it checks.

## 4. Size and splits

1. A spec is for 1 PR of less than about 400 changed lines. If it is larger, split the issue.
2. A split must not lose the story's edge cases. List the user-facing edge cases (for example bad input, a duplicate, abuse) in the spec of the part that handles them. If parts share a contract (an API or a table), list the edge cases and their tests at that contract too.
3. Name each new issue and the role that owns it.

## 5. After you write

1. Put the spec in the issue, or in `docs/specs/<issue>.md` if it is long.
2. If it needs the decider's approval, send it to the decider with a 3-line summary and the decision or contract that it touches.
3. When a builder asks a question, answer it in the issue. Update the spec. Tell the builder to continue.
