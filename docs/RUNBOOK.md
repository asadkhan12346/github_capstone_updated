# Runbook

The human performs every approval in a separate interactive terminal. Copilot agents must stop after submitting a phase.

## 1. Clean pre-run check
Run `python orchestrator.py status`, `python -m unittest discover -s tests -v`, `python -m compileall -q .`, and `python tools/audit_repo.py`.
Expected: requirements is ACTIVE, seven phases are LOCKED, tests pass, compilation exits 0, and every audit check is PASS. Point: the audit is intentionally valid only before phase outputs exist.

## 2. Requirements
Run `python orchestrator.py next`, then invoke `/run` in Copilot Chat. When the orchestrator prompts for the Confluence page URL, provide it. Answer the clarification questions before the agent writes the artifact.
Expected: `artifacts/requirements.md` is submitted and the agent prints the awaiting-approval instruction. Point: do not let the agent guess requirement details.

## 3. Approve requirements
Review the artifact. In a human terminal run `python orchestrator.py approve requirements --by <your-name>` and type `requirements` at the prompt.
Expected: requirements becomes APPROVED and architecture becomes ACTIVE. Point: agent submission is not approval.

## 4. Architecture
Run `python orchestrator.py next`, then invoke `/run`. The orchestrator identifies the active phase and executes the architecture specialist.
Expected: a component design, coverage table, and Mermaid diagram are submitted. Point: architecture reads only approved requirements.

## 5. Design review
After approving architecture, run `python orchestrator.py next`, then invoke `/run`. The orchestrator routes to the design-review specialist.
Expected: findings, alternatives, security/usability reviews, and a final verdict. Point: on REVISE, either reject the review or remove later outputs and reopen architecture; do not silently accept a failing verdict.

## 6. Planning
After approving design review, run `python orchestrator.py next`, then invoke `/run`. If any High/Med design-review findings are unresolved, provide decisions when the orchestrator asks.
Expected: ordered tasks with files, requirement IDs, and checkable done-when criteria. Point: unresolved High/Med findings require a human decision.

## 7. Implementation
After approving planning, run `python orchestrator.py next`, then invoke `/run`. The orchestrator routes to the implementation specialist, which follows the approved plan task by task.
Expected: only the four implementation-owned files are changed, with requirement-tagged tests. Point: implementation stops if the approved plan is inconsistent.

## 8. Review
After approving implementation, run `python orchestrator.py next`, then invoke `/run`. The orchestrator routes to the review specialist, which reads the implementation read-only.
Expected: read-only findings, traceability for every requirement, plan adherence, and actual unittest/compileall evidence. Point: the reviewer does not fix its findings.

## 9. Verification
After approving review, run `python orchestrator.py next`, then invoke `/run`. The orchestrator routes to the verify specialist, which runs each requirement check and pastes real command output.
Expected: each requirement has an expected result, a real command/output block, and PASS/FAIL. Point: never approve `Result: FAIL`.

## 10. PR Stage A
After approving verify only when PASS, run `/pr`.
Expected: `artifacts/pr.md` and `CHANGELOG.md` are submitted. Point: this stage prepares materials; it does not push or open a PR.

## 11. PR Stage B
After approving PR, invoke `/pr` again and explicitly say `go` in chat.
Expected: preflight checks, feature branch, exact staged-file review, commit, push, and PR creation, stopping on the first error. Point: a missing remote or authentication is a human setup issue; no bypass is allowed.

## 12. Blocked transition demo
Run `python orchestrator.py submit architecture` while architecture is LOCKED.
Expected: exit code 1 and a `RULE VIOLATION` naming the ACTIVE requirement. Point: skip-ahead is refused.

## 13. Guard demo
Pipe `{"tool_name":"run_in_terminal","tool_input":{"command":"git reset --hard"}}` to `python hooks/guard.py`.
Expected: a denial naming R03 and exit code 2. Point: hooks must be enabled with VS Code `chat.useHooks`.

## 14. Tamper demo
In a disposable copy only, change a submitted artifact and run approve/check.
Expected: hash drift is refused. Restore the copy before continuing. Point: hashes detect changes after submit but are not tamper-proof against a determined local user.
