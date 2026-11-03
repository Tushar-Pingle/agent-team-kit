# Writing standard: ASD-STE100 (about 80%)

## 1. Scope

Use this standard for all of these:

- Plans, ADRs, standards, and all other Markdown in `docs/`.
- `CLAUDE.md` and other instructions for LLMs.
- The work log and the conversation log.
- LLM replies and questions in chat.
- Code comments, commit messages, and pull request text.

This standard does not apply to UI text at this time. A later decision can add it.

## 2. What "about 80%" means

ASD-STE100 is Simplified Technical English. It was made for aircraft maintenance manuals. We use its main rules, but not its full dictionary.

Target: at least 80% of sentences obey the rules in section 3.

These items are exempt:

- Technical names (for example: `user_id`, Postgres, JSON Schema).
- Code, commands, file paths, and data.
- Direct quotes from a person or a source document.
- Tables, when a short phrase is clearer than a full sentence.

## 3. Rules

| # | Rule | Limit or example |
|---|---|---|
| R1 | Keep instructions short. | 20 words max per sentence. |
| R2 | Keep descriptions short. | 25 words max per sentence. |
| R3 | Write one instruction per sentence. | "Run the tests. Then push." Not: "Run the tests and push if they pass and nothing else changed." |
| R4 | Use the active voice. | "The worker writes the score card." Not: "The score card is written by the worker." |
| R5 | Use the imperative for instructions. | "Add a log entry." Not: "A log entry should be added." |
| R6 | Write one topic per paragraph. | Paragraphs have 6 sentences max. |
| R7 | Use one word for one meaning. | Use one term every time. Do not change it to a synonym. See the glossary in section 5. |
| R8 | Use simple verbs. | "use", not "utilize". "start", not "initiate". "help", not "facilitate". |
| R9 | Do not use slang, idioms, or filler. | Not: "out of the box", "under the hood", "basically", "simply". |
| R10 | Put a warning or condition first. | "If the test fails, stop." Not: "Stop if the test fails." |
| R11 | Use lists for steps and for more than 3 items. | Number the steps. Use one action per step. |
| R12 | Do not use noun clusters of more than 3 words. | Not: "user account settings page header". Write: "the header of the settings page". |

## 4. Examples

| Before | After |
|---|---|
| "It should be noted that jobs are processed asynchronously by the worker, which facilitates scalability." | "The worker processes jobs asynchronously. This lets the system scale." |
| "Make sure you basically just run the migrations and then, assuming nothing breaks, deploy." | "Run the migrations. If they pass, deploy." |
| "The cache is utilized to reduce latency." | "The cache reduces latency." |

## 5. Glossary (one word, one meaning)

| Term | Meaning |
|---|---|
| decider | The human who decides scope, locked decisions, revisit items, merges, and deploys. |
| agent role | One AI agent job, for example QA or frontend. |
| role session | A Claude Code session that runs one agent role. |
| charter | The human description of a role, in `docs/team/<role>.md`. |
| role file | The machine definition of a role, in `.claude/agents/<role>.md`. |
| spec | The implementation-ready description of one build issue. |
| implementation-ready | So complete that a builder can do the work without a guess. |
| PR loop | Builder opens a PR, QA reviews, builder fixes, until QA PASS; then UAT and Designer; then the decider merges. |
| verdict line | The first line of a review: PASS or CHANGES NEEDED. |
| hook | A Claude Code setting that runs a check before or after an agent action, and can block it. |
| role test | A test task with a known good result. A role file must pass it before use. |
| revisit log | The list of ideas that can change the scope, with the decider's decision for each. |
| ADR | Architecture decision record: one decision, its context, and its consequences. |

Add new terms here when a plan defines them.

## 6. Diagrams (D14)

Use a diagram when a human must understand one of these:

- A flow or a sequence (for example: sign up, verify, sign in).
- A structure (for example: services, data entities).
- A dependency (for example: which plan depends on which plan).
- A state machine (for example: order status).

Rules for diagrams:

1. Use Mermaid in a fenced code block. GitHub shows it as a diagram. Git shows changes as text. LLMs can read and write it.
2. Put 15 nodes max in one diagram. If you need more, make two diagrams.
3. Use the glossary terms for the labels.
4. Write one sentence before the diagram. The sentence tells what the diagram shows.
5. Do not use a diagram in place of text that a rule or a decision needs. The text is the source of truth.

## 7. How to check

Before a commit, do these steps:

1. Read each new sentence. Find the sentences with more than 20 words (instructions) or 25 words (descriptions).
2. Make long sentences shorter, or split them.
3. Find passive verbs. Change them to the active voice where possible.
4. Make sure that each term agrees with the glossary.
