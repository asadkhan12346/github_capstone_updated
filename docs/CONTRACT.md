# Agentic SDLC Contract

## Purpose

This repository demonstrates a story-agnostic, eight-phase SDLC pipeline for one Confluence user story. Each phase has a narrowly scoped Copilot agent and prompt. A phase must be submitted and explicitly approved by a human before the next phase becomes active. The final phase prepares pull-request materials; opening a pull request is a separate, explicitly authorized action.

The pipeline's controls are demo-grade. The orchestrator validates state and artifact hashes, the PreToolUse hook blocks selected unsafe operations, and the agent instructions define scope. These controls do not replace branch protection, code review, or a trusted human operator.

## Phases

| # | id | agent | prompt | owns |
|---|----|----|----|----|
| 1 | requirements | `.github/agents/requirements.agent.md` | `.github/prompts/run.prompt.md` | `artifacts/requirements.md` |
| 2 | architecture | `.github/agents/architecture.agent.md` | `.github/prompts/run.prompt.md` | `artifacts/architecture.md` |
| 3 | design-review | `.github/agents/design-review.agent.md` | `.github/prompts/run.prompt.md` | `artifacts/design-review.md` |
| 4 | planning | `.github/agents/planning.agent.md` | `.github/prompts/run.prompt.md` | `artifacts/implementation-plan.md` |
| 5 | implementation | `.github/agents/implementation.agent.md` | `.github/prompts/run.prompt.md` | `todo/__init__.py`, `todo/app.py`, `todo/cli.py`, `tests/test_todo.py` |
| 6 | review | `.github/agents/review.agent.md` | `.github/prompts/run.prompt.md` | `artifacts/review.md` |
| 7 | verify | `.github/agents/verify.agent.md` | `.github/prompts/run.prompt.md` | `artifacts/verify.md` |
| 8 | pr | `.github/agents/pr.agent.md` | `.github/prompts/pr.prompt.md` | `artifacts/pr.md`, `CHANGELOG.md` |

`artifacts/requirements.md`, the eight phase outputs, the phase IDs, and their sequence are fixed. The pipeline does not encode the sample story's requirements; only implementation ownership names the sample app files.

## Status model

Each phase is `LOCKED`, `ACTIVE`, `AWAITING_APPROVAL`, or `APPROVED`. Initially requirements is `ACTIVE`; all later phases are `LOCKED`. A successful submit changes the active phase to `AWAITING_APPROVAL`. Only an explicit human approval changes it to `APPROVED` and activates its successor. Rejection returns the phase to `ACTIVE`; reopening an approved phase requires later phase outputs to be removed first.

## Files

The manifest at `sdlc/phases.json` defines phase order, agent and prompt paths, owned files, and protected paths. `sdlc/state.json` records the current state, while `sdlc/audit.log.jsonl` records orchestrator actions. The state and audit files are initialized by the orchestrator, not committed as pre-populated pipeline results.

## Protected files

The following paths are protected from phase writes: `sdlc/state.json`, `sdlc/audit.log.jsonl`, `sdlc/phases.json`, `orchestrator.py`, `hooks/`, and `.github/hooks/`. Agent phases may write only files owned by their active phase. Infrastructure files are created before the live run and are outside phase ownership.

## Orchestrator CLI

Run `python orchestrator.py status [--json]` to inspect state, `python orchestrator.py next` for the next prompt, and `python orchestrator.py submit <phase>` to submit the active phase. A human uses `python orchestrator.py approve <phase> --by <name>` after reviewing the output. `reject <phase> --reason <text>` returns a pending phase to active; `reopen <phase> --reason <text>` reopens an approved phase only when later outputs are absent. `check` verifies state, artifacts, hashes, and protected paths.

Exit code `0` means success, `1` means a rule violation, and `2` means a usage error. Interactive approval, rejection, and reopening require a TTY and an exact phase-ID confirmation. This TTY check is demo-grade and is not an authentication boundary.

## Traceability

Requirements define `FR-###` and `NFR-###` IDs. Architecture, design review, planning, review, verification, and PR materials cite the applicable IDs. Submission checks reject undefined references, missing required references, missing review verdicts, and missing verification evidence. Implementation is checked by tests that name requirement IDs.

## Commands

Run the infrastructure suite with `python -m unittest discover -s tests -v` and syntax compilation with `python -m compileall -q .`. Run `python tools/audit_repo.py` only before the live run; it intentionally fails once phase artifacts or generated implementation outputs exist. To run a phase, use the prompt shown by `python orchestrator.py next`, then submit and wait for human approval.

## Human-approval rule

An agent must stop after a successful submission and print exactly: `Awaiting human approval. Run: python orchestrator.py approve <phase> --by <your-name>`. Agents must never invoke `approve`, `reject`, or `reopen`. The human reviews each artifact and performs the confirmation in a separate interactive terminal. The PR agent's Stage B additionally requires the human to say `go` after the PR phase has been approved.