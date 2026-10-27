---
name: pr
description: Reusable methodology for preparing traceable release artifacts and safely executing a human-authorized GitHub pull request workflow.
user-invocable: false
---

# PR Release Skill

## Purpose

Provide reusable quality and safety standards for the PR agent. The agent definition owns tool permissions and execution constraints; the prompt owns invocation routing. This skill defines the release methodology and validation criteria.

## Stage A — Release readiness

Before preparing release materials, verify that:

- The `pr` phase is `ACTIVE`.
- `artifacts/verify.md` contains `Result: PASS`.
- Approved predecessor artifacts and implementation evidence are available.

Prepare only the two release files:

- `artifacts/pr.md`
- `CHANGELOG.md`

### PR artifact requirements

Use these headings in `artifacts/pr.md`:

1. Summary
2. What changed
3. Traceability
4. Test evidence
5. Risks
6. Rollback
7. Reviewer checklist

Map each requirement ID to relevant implementation or verification evidence. Report actual test results and known limitations. Do not invent completed work, test outcomes, approvals, or release scope.

### Changelog requirements

Follow Keep a Changelog format with:

- `## [Unreleased]`
- `### Added`
- `### Changed`
- `### Fixed`

Include only changes supported by observed repository evidence.

### Release validation

Before submission, confirm:

- Every applicable requirement ID has evidence.
- Verification is PASS.
- Release notes match the actual intended changes.
- Risks and rollback guidance are documented.
- Only the two release files are modified by this stage.

## Stage B — Pull request quality standards

Stage B is a separately authorized operation requiring explicit `go` in the invocation. Authorization and phase-state preconditions are enforced by the PR agent and invocation prompt.

### Repository and change review

Before any remote write:

- Identify the repository from its configured `origin`.
- Confirm the intended target base is `main`.
- Review the working-tree status and complete diffs.
- Confirm every proposed file is an intended, reviewed change.
- Exclude unrelated files, secrets, runtime state, audit logs, and protected infrastructure.
- Stop if the exact file list or contents are ambiguous.

### Branch, commit, and PR quality

Use these GitHub MCP operations in order: `create_branch`, `push_files`, `search_pull_requests`, `create_pull_request`, `pull_request_read`.

The intended result is a draft pull request with:

- A descriptive title.
- A conventional commit message.
- A concise, traceable description based on `artifacts/pr.md`.
- The correct feature branch and base `main`.
- `draft: true` set in the `create_pull_request` call.
- No duplicate PR for the same head and base.

The final result must be checked against the actual GitHub response. A requested operation is not evidence that it succeeded.

### Failure handling

If a precondition, repository check, remote operation, or readback fails:

- Stop at the first error.
- Report the observed error and any confirmed partial outcome.
- Do not use an alternative mutation path or bypass a failed check.
- Leave recovery to the human operator.

## Final quality checklist

- Release materials are traceable to approved requirements and actual evidence.
- Verification reports `Result: PASS`.
- Proposed files and contents match the reviewed changes.
- The repository and target base are correct.
- Duplicate-PR checks and final PR readback are complete.
- No secrets, unrelated files, or protected infrastructure are included.
- The final report states only observed outcomes.

## Non-negotiable release principle

A successful submission, a created branch, a pushed commit, and an opened pull request are distinct outcomes. Report each only when supported by actual evidence. Never merge a pull request.
