---
name: run
description: Run the active pipeline phase (requirements through verify) through the central orchestrator. Use /pr for the PR phase.
argument-hint: Optionally pass human answers or context for the active phase.
agent: orchestrator
---

# /run — Execute the Active Phase

Entry point for pipeline phases 1–7. Phase 8 (`pr`) uses `/pr`.

## Step 1 — Check status

Run `python orchestrator.py status`.

Stop and report if:
- The active phase is `pr`: tell the human to use `/pr` instead.
- The phase status is `AWAITING_APPROVAL`: print the exact approval instruction and stop.
- The pipeline is complete: report completion and stop.
- No valid active phase exists: report the observed state and stop.

Never infer the active phase or approval status from chat history.

## Step 2 — Gather human input

- **Requirements:** Require the Confluence page URL. Fetch that exact page using the configured Atlassian MCP and verify its identity. Ask all necessary clarification questions together and wait for answers before generating requirements. Never use a local user-story file as a substitute.
- **Planning:** If the design-review verdict is `REVISE` or any High/Med finding remains unresolved, ask the human which findings to incorporate and wait.

For other phases, follow the active phase agent's existing input requirements.

## Step 3 — Delegate to the orchestrator agent

Invoke the `orchestrator` agent using the supported agent-delegation mechanism in the GitHub Copilot environment.

Pass:
- The active phase name and status
- All required predecessor artifacts
- Human-provided answers or arguments
- Relevant blockers or errors

The orchestrator routes to the existing phase execution agent, collects results, checks submission status, and returns a consolidated report.

If agent delegation is unavailable, report the limitation and stop. Never pretend delegation occurred.

## Step 4 — Relay the report

Return the orchestrator's consolidated report, including:
1. Phase result and observed status
2. Files changed
3. Execution results and actual test evidence, where applicable
4. Submission result
5. Exact human-approval instruction
6. Unresolved issues or blockers

If the orchestrator reports an error, relay it and stop.

## Safety rules

- Never run `approve`, `reject`, or `reopen`.
- Never skip a phase or continue past an approval gate.
- Never write outside the active phase's allowed files.
- Never edit `sdlc/`, `orchestrator.py`, `hooks/`, or `.github/hooks/` during a phase.
- Never recreate deleted implementation files or artifacts unless required by the active phase's approved workflow.
- Report only observed results. Never claim an unrun check passed.
- Do not start the PR workflow automatically.
