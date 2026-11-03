# Changelog

All notable changes to this kit. The format follows Keep a Changelog. Versions follow SemVer.

## 0.2.0 - 2026-11-02

### Added

- `onboard-project` skill: the front door. A read-only repo scan (`scripts/discover.py`), a context Q&A, and a web check of the stack. In `plan` mode it writes the North Star (Plan 00), the component plans, the ADRs, and the slices by Q&A, and closes every open question, so the PM can run on its own. In `team-only` mode it goes straight to the team design.
- Team presets (`scripts/presets.json`, `scripts/init_team.py`): `solo` (4 roles), `small` (7), `data` (7, for warehouse and dbt work), `full` (11). The setup Q&A asks for the preset and the team size.
- Model tiers in `team.json` (`models.contact`, `models.agentic`, `models.helper`). A role's `model` is a tier or an explicit id. The setup Q&A asks for each tier with options.
- Stack in the role files: a `stack` block for the project and for each role (languages, frameworks, commands, conventions with sources, references). The scaffold writes a "Your stack" section into each role file and `docs/team/context.md` for the project.
- Cost report: a `SessionEnd` hook (`cost_report.py`) sums the session transcript's tokens by model, prices them from `team.json` (`cost.prices_per_million`), and appends one line to `docs/log/COST.md`. The next `SessionStart` repeats the last total. The `cost-report` skill shows the current session on demand. Empty prices give a token-only report. 4 unit tests.
- `docs/plans/00-north-star.md` template with personas, hypotheses, locked decisions, scope, components, slices, and an open-questions table.
- Publish files: MIT license, this changelog, a GitHub Actions workflow that runs both test suites, and `.claude-plugin/marketplace.json` so the repo is a one-line marketplace.

### Changed

- `setup-team` asks 14 short questions in batches, reads an existing `team.json` and asks only about the gaps, and runs `init_team.py` instead of hand-copying the example.
- `method-guide` has a step 0 (discovery) and names the model tiers and the cost log.
- The runbook lists the project context and the cost hook.
- `team.example.json` uses tiers, a `models` block, a `cost` block, and a `stack` block with two role-level examples.
- 5 new scaffold tests: tiers resolve, stack sections and context doc, cost files, every preset scaffolds, and a bad tier is rejected.

### Removed

- The stray `.in_use/` folder.

## 0.1.0 - 2026-10

First release: method guide, setup Q&A and scaffold, workflow skills (revisit-log, write-spec, review-pr, run-uat, log-entry, role-tests), guard hooks, role tests.
