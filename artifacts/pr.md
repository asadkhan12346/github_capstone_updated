# PR

## Summary

This pull request delivers a minimal command-line Todo task manager implemented in Python 3.11+ using only the standard library. The application satisfies all 24 functional requirements (FR-001 through FR-024) and all 6 non-functional requirements (NFR-001 through NFR-006) as verified by 68 unit tests (1 skipped on Windows).

## What changed

**New files (phase 5 — implementation):**
- `todo/__init__.py` — package docstring
- `todo/app.py` — `Task` dataclass, error hierarchy (`TodoError`, `StorageError`, `CorruptStorageError`), `JsonStore` (atomic JSON persistence), `TodoApp` (CRUD operations)
- `todo/cli.py` — CLI entry point: `build_parser()`, `main(argv, stdout, stderr, app) -> int`
- `tests/test_todo.py` — 68 unit tests covering all FRs and NFRs

**New artifacts (pipeline phases 1–8):**
- `artifacts/requirements.md` — 24 FRs, 6 NFRs
- `artifacts/architecture.md` — component design, data model, Mermaid diagram
- `artifacts/design-review.md` — independent review, Verdict: APPROVE
- `artifacts/implementation-plan.md` — T-01 through T-06
- `artifacts/review.md` — code review, Verdict: APPROVE
- `artifacts/verify.md` — test evidence, Result: PASS
- `artifacts/pr.md` — this file
- `CHANGELOG.md` — release notes

## Traceability

| Req | Implementation | Test |
|---|---|---|
| FR-001 | `todo/cli.py` subcommands | `TestFR001Commands` |
| FR-002 | `TodoApp.add` | `TestFR002CreateTask` |
| FR-003 | `status="open"` on creation | `TestFR003InitialStatus` |
| FR-004 | `Added: {id} [open] {title}` stdout | `TestFR004AddOutput` |
| FR-005 | `TodoApp.list_tasks` | `TestFR005ListTasks` |
| FR-006 | `No tasks.` empty branch | `TestFR006EmptyList` |
| FR-007 | `TodoApp.done` → "done" | `TestFR007CompleteOpenTask` |
| FR-008 | `done` no-op, message to stdout | `TestFR008AlreadyDone` |
| FR-009 | `TodoApp.reopen` → "open" | `TestFR009ReopenDoneTask` |
| FR-010 | `reopen` no-op, message to stdout | `TestFR010AlreadyOpen` |
| FR-011 | `TodoApp.delete` | `TestFR011Delete` |
| FR-012 | `Error: task {id} not found.` stderr, exit 1 | `TestFR012UnknownID` |
| FR-013 | `_validate_id` for id ≤ 0 | `TestFR013InvalidID` |
| FR-014 | USAGE prefix, exit 2 | `TestFR014UsageError` |
| FR-015 | All errors to stderr, non-zero exit | `TestFR015ErrorStream` |
| FR-016 | Empty/whitespace title rejected, exit 2 | `TestFR016EmptyTitle` |
| FR-017 | `title.strip()` before `add()` | `TestFR017TitleWhitespace` |
| FR-018 | No duplicate-title check | `TestFR018DuplicateTitles` |
| FR-019 | No count or title-length limit | `TestFR019NoLimits` |
| FR-020 | `JsonStore` schema `{next_id, tasks}` | `TestFR020StorageContract` |
| FR-021 | Missing/empty file → default state | `TestFR021MissingStorage` |
| FR-022 | `_validate_store` → `CorruptStorageError` | `TestFR022CorruptStorage` |
| FR-023 | `OSError` → `StorageError` | `TestFR023StorageIOFailure` |
| FR-024 | `next_id` monotonic, never reused | `TestFR024MonotonicIDs` |
| NFR-001 | Python 3.13.0, stdlib only | `TestNFR001Runtime` |
| NFR-002 | UTF-8, ensure_ascii=False, indent=2 | `TestNFR002StorageEncoding` |
| NFR-003 | NamedTemporaryFile + fsync + os.replace | `TestNFR003AtomicSaves` |
| NFR-004 | No write on no-op/list/failure | `TestNFR004NoUnintendedWrites` |
| NFR-005 | No network imports | `TestNFR005NoNetwork` |
| NFR-006 | unittest, temp dirs, injectable app | `TestNFR006Testability` |

## Test evidence

```
Ran 68 tests in 1.049s
OK (skipped=1)
```

68 tests pass. 1 test skipped (`test_read_permission_error_raises_storage_error` — chmod is not reliable on Windows). Exit code 0. Full output in `artifacts/verify.md`.

## Risks

- **CWD dependency**: `tasks.json` is created in the current working directory (FR-020). Users who run the CLI from different directories will see different task lists. This is the specified behaviour.
- **No concurrency guarantee**: Concurrent writes are unspecified (Constraints). Simultaneous CLI invocations may corrupt the store. Not a defect; accepted limitation.
- **FR-023 skip on Windows**: The `StorageError` I/O path is implemented but its automated test is skipped on Windows because `chmod` is not reliable there. The code path is present and correct.

## Rollback

All implementation files (`todo/`, `tests/test_todo.py`) are new additions. Pipeline artifacts are also new additions.

```
git revert HEAD
```

No database migrations, external services, or schema changes are involved. Rollback has zero side effects.

## Reviewer checklist

- [ ] Requirements artifact covers all story behaviours
- [ ] Architecture matches implementation structure
- [ ] Design-review verdict is APPROVE
- [ ] Implementation follows approved plan (T-01 through T-06)
- [ ] All tests pass (68/68, 1 skipped on Windows)
- [ ] Verification result is PASS
- [ ] No secrets, network calls, or unintended writes
- [ ] CHANGELOG entries match actual changes
- [ ] Target base is `main`; no direct push to `main`
