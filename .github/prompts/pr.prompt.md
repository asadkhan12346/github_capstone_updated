---
name: pr
description: Prepare release materials and create a draft pull request after explicit human authorization.
argument-hint: Use Stage A to prepare release materials, or provide go to authorize Stage B.
agent: pr
---

# /pr — PR Workflow (Stage A and Stage B)

## Stage A — Prepare release materials

Run when the `pr` phase is ACTIVE and the invocation does not explicitly contain `go`.

1. Run `python orchestrator.py status`. Stop if `pr` is not ACTIVE.
2. Read the approved artifacts, especially `artifacts/verify.md`. Stop if `Result: PASS` is absent.
3. Follow `.github/agents/pr.agent.md` and `.github/skills/pr/SKILL.md` to prepare:
   - `artifacts/pr.md`
   - `CHANGELOG.md`
4. Run `python orchestrator.py submit pr`.
5. After successful submission, print exactly:

   `Awaiting human approval. Run: python orchestrator.py approve pr --by <your-name>`

6. Stop. Do not create a branch, push files, or open a pull request during Stage A.

## Stage B — Create the draft pull request

Run only when the human explicitly invokes `/pr go` and all eight phases are APPROVED.

1. Run `python orchestrator.py status` and confirm every phase is APPROVED.
2. Confirm `artifacts/verify.md` contains `Result: PASS`.
3. Confirm explicit `go` was supplied in this invocation. Do not infer authorization from previous messages.
4. Follow the Stage B procedure in `.github/agents/pr.agent.md` and `.github/skills/pr/SKILL.md`.
5. Inspect repository state, the origin URL, current branch, complete diffs, and the exact proposed file list before any remote write.
6. Use only the permitted GitHub MCP operations:
   - `get_me`
   - `create_branch`
   - `push_files`
   - `search_pull_requests`
   - `create_pull_request`
   - `pull_request_read`
7. Create a feature branch from `main` and push only the exact reviewed file contents. Search for an existing PR with this head branch and base `main`. Create a draft PR only if no duplicate exists.
8. Read the created or existing PR and verify its actual head, base, changed files, draft/open state, and URL.
9. Report the observed result or the first error, then stop.

## Rules

- Never approve, reject, or reopen a phase.
- Never merge a pull request.
- Never use local `git push`, force push, `git add -A`, `git add .`, or `--no-verify`.
- Never push directly to `main` or `master`.
- Never use a fallback mutation tool if GitHub MCP fails.
- Never edit `sdlc/`, `orchestrator.py`, `hooks/`, or `.github/hooks/`.
- Do not include unrelated, deleted, untracked, runtime-state, audit, or secret files.
- Report only actual results. Never claim a branch, commit, or PR succeeded without confirmation.
- Stop immediately if any precondition or safety check fails.
