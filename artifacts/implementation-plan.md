# Implementation Plan

## Ordered tasks

### T-01 — Package initialisation
- **Goal**: Create `todo/__init__.py` with a package docstring.
- **Files**: `todo/__init__.py`
- **IDs**: NFR-001 (stdlib only, Python 3.11+)
- **Done when**: `python -m compileall -q todo/` exits 0; `import todo` succeeds.

### T-02 — Error hierarchy and `Task` dataclass
- **Goal**: Define `TodoError`, `StorageError`, `CorruptStorageError`, and the `Task` dataclass in `todo/app.py`.
- **Files**: `todo/app.py`
- **IDs**: FR-003, FR-012, FR-013, FR-022, FR-023, NFR-001
- **Done when**: `from todo.app import Task, TodoError, StorageError, CorruptStorageError` succeeds; `Task(id=1, title='x', status='open')` constructs correctly.

### T-03 — `JsonStore`: atomic read/write
- **Goal**: Implement `JsonStore` in `todo/app.py` with `read()` → `(next_id, tasks)` and `write(next_id, tasks)` using atomic temp-file + fsync + `os.replace`.
- **Files**: `todo/app.py`
- **IDs**: FR-020, FR-021, FR-022, FR-023, FR-024, NFR-002, NFR-003, NFR-004
- **Done when**: `JsonStore` reads missing file as empty state; writes produce valid UTF-8 JSON; corrupt file raises `CorruptStorageError`; failed write leaves original file unchanged.

### T-04 — `TodoApp`: CRUD operations
- **Goal**: Implement `TodoApp(store_path)` with `add(title)→Task`, `list_tasks()→list[Task]`, `done(id)→tuple[Task,bool]`, `reopen(id)→tuple[Task,bool]`, `delete(id)→None`.
- **Files**: `todo/app.py`
- **IDs**: FR-002 through FR-011, FR-016 through FR-019, FR-024, NFR-004
- **Done when**: unit tests for add/list/done/reopen/delete pass in a temp directory.

### T-05 — CLI layer
- **Goal**: Implement `todo/cli.py` with `build_parser()` and `main(argv, stdout, stderr, app)→int`. No `sys.exit` calls. Commands: `add`, `list`, `done`, `reopen`, `delete`.
- **Files**: `todo/cli.py`
- **IDs**: FR-001, FR-004 through FR-015, FR-016, FR-017
- **Done when**: `main(["add", "Buy milk"], ..., app)` returns 0 and prints `Added: 1 [open] Buy milk`; `main(["list"], ...)` returns 0; bad ID returns 1; bad command returns 2.

### T-06 — Test suite
- **Goal**: Write `tests/test_todo.py` covering every FR and NFR with at least one named test each.
- **Files**: `tests/test_todo.py`
- **IDs**: FR-001 through FR-024, NFR-001 through NFR-006
- **Done when**: `python -m unittest tests/test_todo.py -v` exits 0 with all tests passing.

## File-level change list

| File | Change type | Owned by |
|---|---|---|
| `todo/__init__.py` | Create | implementation |
| `todo/app.py` | Create | implementation |
| `todo/cli.py` | Create | implementation |
| `tests/test_todo.py` | Create | implementation |

No existing files are modified. No files outside the four owned paths are touched.

## Test plan

| Requirement | Test name | Method |
|---|---|---|
| FR-001 | `test_cli_add_command_exists` | `unittest` — call `main(["add","x"], ...)` |
| FR-002 | `test_add_returns_task_with_correct_fields` | `unittest` — check returned `Task` |
| FR-003 | `test_new_task_status_is_open` | `unittest` |
| FR-004 | `test_add_stdout_format` | `unittest` — check stdout string |
| FR-005 | `test_list_all_tasks` | `unittest` |
| FR-006 | `test_list_empty` | `unittest` — stdout == "No tasks.\n" |
| FR-007 | `test_done_open_task` | `unittest` — check status after done() |
| FR-008 | `test_done_already_done_noop` | `unittest` — returns (task, False) |
| FR-009 | `test_reopen_done_task` | `unittest` |
| FR-010 | `test_reopen_already_open_noop` | `unittest` |
| FR-011 | `test_delete_task` | `unittest` |
| FR-012 | `test_not_found_stderr_exit1` | `unittest` — stderr + return 1 |
| FR-013 | `test_invalid_id_treated_as_not_found` | `unittest` — id=0, negative |
| FR-014 | `test_usage_error_exit2` | `unittest` — bad subcommand |
| FR-015 | `test_error_to_stderr` | `unittest` |
| FR-016 | `test_empty_title_rejected` | `unittest` |
| FR-017 | `test_title_whitespace_trimmed` | `unittest` |
| FR-018 | `test_duplicate_titles_allowed` | `unittest` |
| FR-019 | `test_no_count_limit` | `unittest` — add 200 tasks |
| FR-020 | `test_storage_schema` | `unittest` — inspect JSON on disk |
| FR-021 | `test_missing_file_is_empty_list` | `unittest` |
| FR-022 | `test_corrupt_storage_raises` | `unittest` |
| FR-023 | `test_storage_io_error_raises` | `unittest` |
| FR-024 | `test_ids_monotonic_never_reused` | `unittest` |
| NFR-001 | `test_stdlib_only` | `unittest` — check no third-party imports |
| NFR-002 | `test_storage_encoding` | `unittest` — check UTF-8, indent=2 |
| NFR-003 | `test_atomic_write` | `unittest` — verify temp file gone after write |
| NFR-004 | `test_no_write_on_noop` | `unittest` — mtime unchanged after list/no-op |
| NFR-005 | `test_no_network_calls` | `unittest` — import check (no socket/requests) |
| NFR-006 | Entire test file | `unittest` in temp dirs |

## Rollback notes

All four implementation files are new creations. Rollback is:
```
git revert HEAD
```
or, if uncommitted:
```
git checkout -- todo/ tests/test_todo.py
```
No database migrations, schema changes, or external resources are involved.
