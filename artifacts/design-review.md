# Design Review

## Summary

This review independently assesses the architecture against the approved requirements. The design is minimal, correct, and well-scoped. All 24 FRs and 6 NFRs map cleanly to named components. Two minor findings are raised; neither blocks approval.

## Findings

| ID | Severity | Area | Finding | Related IDs | Suggested change |
|---|---|---|---|---|---|
| F-01 | Low | Error handling | `TodoApp` methods use bare `KeyError` for not-found rather than a named `TodoError` subclass. This leaks a stdlib exception type through the public API boundary. | FR-012, FR-013 | Add `TaskNotFoundError(TodoError)` and raise it instead of `KeyError`; update CLI to catch it. |
| F-02 | Low | Testability | The architecture places `JsonStore` as an internal class inside `app.py` with no documented injection point. Tests relying on `TodoApp(store_path)` cannot substitute a fake store without filesystem I/O. | NFR-006 | Document that `store_path` in a `tempfile.mkdtemp()` is the intended test isolation mechanism; or accept the current design since temp-dir isolation already satisfies NFR-006. |

No High or Medium findings.

## Risks

- **ID monotonicity**: The `next_id` field is stored in the JSON file. If two concurrent writers race on the file, `next_id` may be assigned twice. The requirements explicitly leave concurrent access unspecified (Constraints), so this is an accepted limitation, not a defect.
- **CWD dependency**: `tasks.json` is relative to the current working directory, matching FR-020 but making the tool environment-sensitive. No mitigation is required; this is the specified behaviour.

## Alternatives considered and why rejected

| Alternative | Reason rejected |
|---|---|
| SQLite backend instead of JSON | Adds a heavier dependency pattern; FR-020 specifies a JSON file with an exact schema. Standard library sqlite3 would satisfy NFR-001 but contradicts FR-020's explicit file contract. |
| Separate `next_id` in a sidecar file | Adds a second file to manage atomically; the combined `{next_id, tasks}` root keeps a single atomic write covering both fields, directly satisfying FR-024 and NFR-003. |
| Named `TaskNotFoundError` in the initial architecture | Would have been cleaner but the architecture document describes components at the right level of abstraction; the exact exception type is an implementation detail. F-01 records it as a recommended refinement. |

## Security review

- No network calls anywhere in the design (NFR-005). No credentials, tokens, or secrets are accepted, stored, or transmitted.
- The storage file is a local JSON file. No path traversal is introduced because `store_path` is provided by the caller (the CLI hardcodes `Path("tasks.json")` in the CWD).
- No `eval`, `exec`, or dynamic code execution is used.
- Input validation (FR-016, FR-017) prevents empty or whitespace-only titles from reaching storage.
- No injection risk: task data is serialised with `json.dump`, not string concatenation.

## Usability and accessibility review

- FR-004 through FR-010 define exact, predictable output strings, making the CLI scriptable.
- FR-006 provides a clear empty-state message (`No tasks.`).
- FR-008 and FR-010 provide informative no-op messages so users know their command was received.
- FR-012 sends `Error: task {id} not found.` to stderr, keeping stdout clean for scripting.
- FR-014 requires USAGE prefix on usage errors, consistent with POSIX CLI conventions.
- Exit codes 0/1/2 follow standard POSIX conventions, enabling shell scripting (FR-015).

## Requirement coverage check

All 30 requirement IDs (FR-001 through FR-024, NFR-001 through NFR-006) appear in the architecture's requirement coverage table. No requirement is unaddressed.

| Status | Count |
|---|---|
| Covered | 30 |
| Partially covered | 0 |
| Not covered | 0 |

Verdict: APPROVE
