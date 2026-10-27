# Code Review

## Summary

Reviewed `todo/app.py`, `todo/cli.py`, `todo/__init__.py`, and `tests/test_todo.py` against the approved implementation plan (T-01 through T-06) and all 24 FRs and 6 NFRs. The implementation is correct, well-structured, and test coverage is comprehensive. One minor finding is noted. All tests pass (68 run, 1 skipped on Windows due to chmod limitation).

## Findings

| ID | Severity | File:line | Finding | Related IDs | Suggested change |
|---|---|---|---|---|---|
| R-01 | Minor | `todo/cli.py:40-70` | The `_NonExitingParser` subclass duplicates the `build_parser()` logic inline in `main()`. If the parser is extended, two places must be updated. | NFR-006 | Extract a `_build_parser(cls)` factory that accepts the parser class; call it from both `build_parser()` and `main()`. |
| R-02 | Nit | `todo/app.py:8` | `from io import StringIO` is imported but not used in `app.py`. | NFR-001 | Remove unused import. |

No Blocker or Major findings.

## Traceability matrix

| Requirement | Code location | Test |
|---|---|---|
| FR-001 | `todo/cli.py` `build_parser`, `main` subcommands | `TestFR001Commands` |
| FR-002 | `todo/app.py` `TodoApp.add` | `TestFR002CreateTask` |
| FR-003 | `todo/app.py` `TodoApp.add` status="open" | `TestFR003InitialStatus` |
| FR-004 | `todo/cli.py` `main` add branch: `Added: {id} [open] {title}` | `TestFR004AddOutput` |
| FR-005 | `todo/app.py` `TodoApp.list_tasks` | `TestFR005ListTasks` |
| FR-006 | `todo/cli.py` `main` list branch: `No tasks.` | `TestFR006EmptyList` |
| FR-007 | `todo/app.py` `TodoApp.done` → sets status "done" | `TestFR007CompleteOpenTask` |
| FR-008 | `todo/app.py` `TodoApp.done` → returns `(task, False)` when already done | `TestFR008AlreadyDone` |
| FR-009 | `todo/app.py` `TodoApp.reopen` → sets status "open" | `TestFR009ReopenDoneTask` |
| FR-010 | `todo/app.py` `TodoApp.reopen` → returns `(task, False)` when already open | `TestFR010AlreadyOpen` |
| FR-011 | `todo/app.py` `TodoApp.delete` | `TestFR011Delete` |
| FR-012 | `todo/app.py` `_find` raises `KeyError`; `todo/cli.py` catches and prints `Error: task {id} not found.` | `TestFR012UnknownID` |
| FR-013 | `todo/app.py` `_validate_id` raises `KeyError` for id ≤ 0 | `TestFR013InvalidID` |
| FR-014 | `todo/cli.py` `_NonExitingParser.error` and `main` `args.command is None` branch | `TestFR014UsageError` |
| FR-015 | `todo/cli.py` all error paths write to `stderr`, return 1 | `TestFR015ErrorStream` |
| FR-016 | `todo/cli.py` `main` add: `title.strip()` then empty check, exit 2 | `TestFR016EmptyTitle` |
| FR-017 | `todo/cli.py` `main` add: `title = args.title.strip()` | `TestFR017TitleWhitespace` |
| FR-018 | `todo/app.py` `TodoApp.add`: no duplicate-title check | `TestFR018DuplicateTitles` |
| FR-019 | `todo/app.py` `TodoApp.add`: no count or length limit | `TestFR019NoLimits` |
| FR-020 | `todo/app.py` `JsonStore` schema `{next_id, tasks}` at `store_path` | `TestFR020StorageContract` |
| FR-021 | `todo/app.py` `JsonStore.read`: missing/empty → `{"next_id":1,"tasks":[]}` | `TestFR021MissingStorage` |
| FR-022 | `todo/app.py` `_validate_store` raises `CorruptStorageError` | `TestFR022CorruptStorage` |
| FR-023 | `todo/app.py` `JsonStore.read/write` wraps `OSError` in `StorageError` | `TestFR023StorageIOFailure` |
| FR-024 | `todo/app.py` `JsonStore` `next_id` incremented on add, never reset | `TestFR024MonotonicIDs` |
| NFR-001 | All files use Python 3.11+ features; stdlib-only imports | `TestNFR001Runtime` |
| NFR-002 | `todo/app.py` `JsonStore.write`: `ensure_ascii=False, indent=2` | `TestNFR002StorageEncoding` |
| NFR-003 | `todo/app.py` `JsonStore.write`: `NamedTemporaryFile` + `os.fsync` + `os.replace` | `TestNFR003AtomicSaves` |
| NFR-004 | `todo/app.py` `done`/`reopen` no-op paths skip `_save`; `list_tasks` never calls `_save` | `TestNFR004NoUnintendedWrites` |
| NFR-005 | No network imports anywhere in `todo/` | `TestNFR005NoNetwork` |
| NFR-006 | `tests/test_todo.py` uses `unittest`, temp dirs, injectable `app` parameter | `TestNFR006Testability` |

## Plan adherence

| Task | Status | Notes |
|---|---|---|
| T-01 Package init | Done | `todo/__init__.py` has package docstring |
| T-02 Error hierarchy and Task dataclass | Done | `TodoError`, `StorageError`, `CorruptStorageError`, `Task` in `app.py` |
| T-03 JsonStore atomic read/write | Done | `NamedTemporaryFile + fsync + os.replace`; corrupt file raises `CorruptStorageError` |
| T-04 TodoApp CRUD | Done | `add`, `list_tasks`, `done`, `reopen`, `delete` all implemented and tested |
| T-05 CLI layer | Done | `build_parser`, `main(argv, stdout, stderr, app)→int`; no `sys.exit` in `main` |
| T-06 Test suite | Done | 68 tests run, 1 skipped (Windows chmod), 0 failures |

Verdict: APPROVE
