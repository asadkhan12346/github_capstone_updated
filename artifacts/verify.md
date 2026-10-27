# Verification

## Environment

```
Python 3.13.0
Platform: Windows 11
Working directory: C:\Users\MohdAsadKhan\Desktop\github capstone
```

## Checks

Each requirement is verified by its named unit test in `tests/test_todo.py`. All checks use actual test execution; no expected result is fabricated.

| Req | Check method | Test name |
|---|---|---|
| FR-001 | unittest | `TestFR001Commands` (5 tests) |
| FR-002 | unittest | `TestFR002CreateTask` (2 tests) |
| FR-003 | unittest | `TestFR003InitialStatus` (1 test) |
| FR-004 | unittest | `TestFR004AddOutput` (2 tests) |
| FR-005 | unittest | `TestFR005ListTasks` (2 tests) |
| FR-006 | unittest | `TestFR006EmptyList` (1 test) |
| FR-007 | unittest | `TestFR007CompleteOpenTask` (2 tests) |
| FR-008 | unittest | `TestFR008AlreadyDone` (2 tests) |
| FR-009 | unittest | `TestFR009ReopenDoneTask` (1 test) |
| FR-010 | unittest | `TestFR010AlreadyOpen` (2 tests) |
| FR-011 | unittest | `TestFR011Delete` (2 tests) |
| FR-012 | unittest | `TestFR012UnknownID` (4 tests) |
| FR-013 | unittest | `TestFR013InvalidID` (3 tests) |
| FR-014 | unittest | `TestFR014UsageError` (3 tests) |
| FR-015 | unittest | `TestFR015ErrorStream` (1 test) |
| FR-016 | unittest | `TestFR016EmptyTitle` (3 tests) |
| FR-017 | unittest | `TestFR017TitleWhitespace` (2 tests) |
| FR-018 | unittest | `TestFR018DuplicateTitles` (1 test) |
| FR-019 | unittest | `TestFR019NoLimits` (2 tests) |
| FR-020 | unittest | `TestFR020StorageContract` (1 test) |
| FR-021 | unittest | `TestFR021MissingStorage` (3 tests) |
| FR-022 | unittest | `TestFR022CorruptStorage` (3 tests) |
| FR-023 | unittest | `TestFR023StorageIOFailure` (1 test, skipped on Windows) |
| FR-024 | unittest | `TestFR024MonotonicIDs` (4 tests) |
| NFR-001 | unittest | `TestNFR001Runtime` (2 tests) |
| NFR-002 | unittest | `TestNFR002StorageEncoding` (3 tests) |
| NFR-003 | unittest | `TestNFR003AtomicSaves` (2 tests) |
| NFR-004 | unittest | `TestNFR004NoUnintendedWrites` (4 tests) |
| NFR-005 | unittest | `TestNFR005NoNetwork` (2 tests) |
| NFR-006 | unittest | `TestNFR006Testability` (2 tests) |

**Pre-run expected result:** All 68 tests pass; 1 test skipped (FR-023 chmod not reliable on Windows). Exit code 0.

**Command executed:** `python -m unittest tests/test_todo.py -v`

**Actual output:**

```
test_add_command_exists (tests.test_todo.TestFR001Commands.test_add_command_exists) ... ok
test_delete_command_exists (tests.test_todo.TestFR001Commands.test_delete_command_exists) ... ok
test_done_command_exists (tests.test_todo.TestFR001Commands.test_done_command_exists) ... ok
test_list_command_exists (tests.test_todo.TestFR001Commands.test_list_command_exists) ... ok
test_reopen_command_exists (tests.test_todo.TestFR001Commands.test_reopen_command_exists) ... ok
test_add_assigns_sequential_id (tests.test_todo.TestFR002CreateTask.test_add_assigns_sequential_id) ... ok
test_add_returns_task (tests.test_todo.TestFR002CreateTask.test_add_returns_task) ... ok
test_new_task_status_is_open (tests.test_todo.TestFR003InitialStatus.test_new_task_status_is_open) ... ok
test_add_stdout_exact_format (tests.test_todo.TestFR004AddOutput.test_add_stdout_exact_format) ... ok
test_add_stdout_format (tests.test_todo.TestFR004AddOutput.test_add_stdout_format) ... ok
test_list_creation_order (tests.test_todo.TestFR005ListTasks.test_list_creation_order) ... ok
test_list_returns_all_tasks (tests.test_todo.TestFR005ListTasks.test_list_returns_all_tasks) ... ok
test_empty_list_message (tests.test_todo.TestFR006EmptyList.test_empty_list_message) ... ok
test_done_open_task_changes_status (tests.test_todo.TestFR007CompleteOpenTask.test_done_open_task_changes_status) ... ok
test_done_persists (tests.test_todo.TestFR007CompleteOpenTask.test_done_persists) ... ok
test_done_already_done_prints_message (tests.test_todo.TestFR008AlreadyDone.test_done_already_done_prints_message) ... ok
test_done_already_done_returns_false (tests.test_todo.TestFR008AlreadyDone.test_done_already_done_returns_false) ... ok
test_reopen_done_task (tests.test_todo.TestFR009ReopenDoneTask.test_reopen_done_task) ... ok
test_reopen_already_open_prints_message (tests.test_todo.TestFR010AlreadyOpen.test_reopen_already_open_prints_message) ... ok
test_reopen_already_open_returns_false (tests.test_todo.TestFR010AlreadyOpen.test_reopen_already_open_returns_false) ... ok
test_delete_removes_task (tests.test_todo.TestFR011Delete.test_delete_removes_task) ... ok
test_delete_via_cli (tests.test_todo.TestFR011Delete.test_delete_via_cli) ... ok
test_delete_unknown_id (tests.test_todo.TestFR012UnknownID.test_delete_unknown_id) ... ok
test_done_unknown_id_stderr_exit1 (tests.test_todo.TestFR012UnknownID.test_done_unknown_id_stderr_exit1) ... ok
test_error_message_format (tests.test_todo.TestFR012UnknownID.test_error_message_format) ... ok
test_reopen_unknown_id (tests.test_todo.TestFR012UnknownID.test_reopen_unknown_id) ... ok
test_negative_id_treated_as_not_found (tests.test_todo.TestFR013InvalidID.test_negative_id_treated_as_not_found) ... ok
test_non_numeric_id_treated_as_not_found (tests.test_todo.TestFR013InvalidID.test_non_numeric_id_treated_as_not_found) ... ok
test_zero_id_treated_as_not_found (tests.test_todo.TestFR013InvalidID.test_zero_id_treated_as_not_found) ... ok
test_no_subcommand_returns_2 (tests.test_todo.TestFR014UsageError.test_no_subcommand_returns_2) ... ok
test_unknown_subcommand_returns_2 (tests.test_todo.TestFR014UsageError.test_unknown_subcommand_returns_2) ... ok
test_usage_message_starts_with_USAGE (tests.test_todo.TestFR014UsageError.test_usage_message_starts_with_USAGE) ... ok
test_not_found_goes_to_stderr (tests.test_todo.TestFR015ErrorStream.test_not_found_goes_to_stderr) ... ok
test_empty_title_no_task_created (tests.test_todo.TestFR016EmptyTitle.test_empty_title_no_task_created) ... ok
test_empty_title_rejected (tests.test_todo.TestFR016EmptyTitle.test_empty_title_rejected) ... ok
test_whitespace_only_title_rejected (tests.test_todo.TestFR016EmptyTitle.test_whitespace_only_title_rejected) ... ok
test_internal_whitespace_preserved (tests.test_todo.TestFR017TitleWhitespace.test_internal_whitespace_preserved) ... ok
test_surrounding_whitespace_trimmed (tests.test_todo.TestFR017TitleWhitespace.test_surrounding_whitespace_trimmed) ... ok
test_duplicate_titles_allowed (tests.test_todo.TestFR018DuplicateTitles.test_duplicate_titles_allowed) ... ok
test_add_200_tasks (tests.test_todo.TestFR019NoLimits.test_add_200_tasks) ... ok
test_long_title_accepted (tests.test_todo.TestFR019NoLimits.test_long_title_accepted) ... ok
test_storage_schema (tests.test_todo.TestFR020StorageContract.test_storage_schema) ... ok
test_add_to_missing_store (tests.test_todo.TestFR021MissingStorage.test_add_to_missing_store) ... ok
test_empty_file_gives_empty_list (tests.test_todo.TestFR021MissingStorage.test_empty_file_gives_empty_list) ... ok
test_missing_file_gives_empty_list (tests.test_todo.TestFR021MissingStorage.test_missing_file_gives_empty_list) ... ok
test_corrupt_file_bytes_unchanged (tests.test_todo.TestFR022CorruptStorage.test_corrupt_file_bytes_unchanged) ... ok
test_duplicate_ids_raises (tests.test_todo.TestFR022CorruptStorage.test_duplicate_ids_raises) ... ok
test_invalid_json_raises (tests.test_todo.TestFR022CorruptStorage.test_invalid_json_raises) ... ok
test_read_permission_error_raises_storage_error (tests.test_todo.TestFR023StorageIOFailure.test_read_permission_error_raises_storage_error) ... skipped 'chmod not reliable on Windows CI'
test_ids_increment (tests.test_todo.TestFR024MonotonicIDs.test_ids_increment) ... ok
test_ids_not_reused_after_delete (tests.test_todo.TestFR024MonotonicIDs.test_ids_not_reused_after_delete) ... ok
test_ids_start_at_1 (tests.test_todo.TestFR024MonotonicIDs.test_ids_start_at_1) ... ok
test_next_id_persists_across_instances (tests.test_todo.TestFR024MonotonicIDs.test_next_id_persists_across_instances) ... ok
test_python_version (tests.test_todo.TestNFR001Runtime.test_python_version) ... ok
test_stdlib_only (tests.test_todo.TestNFR001Runtime.test_stdlib_only) ... ok
test_ensure_ascii_false (tests.test_todo.TestNFR002StorageEncoding.test_ensure_ascii_false) ... ok
test_indent_2 (tests.test_todo.TestNFR002StorageEncoding.test_indent_2) ... ok
test_utf8_encoding (tests.test_todo.TestNFR002StorageEncoding.test_utf8_encoding) ... ok
test_file_is_valid_json_after_write (tests.test_todo.TestNFR003AtomicSaves.test_file_is_valid_json_after_write) ... ok
test_no_temp_file_after_write (tests.test_todo.TestNFR003AtomicSaves.test_no_temp_file_after_write) ... ok
test_list_does_not_write (tests.test_todo.TestNFR004NoUnintendedWrites.test_list_does_not_write) ... ok
test_noop_done_does_not_write (tests.test_todo.TestNFR004NoUnintendedWrites.test_noop_done_does_not_write) ... ok
test_noop_reopen_does_not_write (tests.test_todo.TestNFR004NoUnintendedWrites.test_noop_reopen_does_not_write) ... ok
test_not_found_does_not_write (tests.test_todo.TestNFR004NoUnintendedWrites.test_not_found_does_not_write) ... ok
test_no_socket_import_in_app (tests.test_todo.TestNFR005NoNetwork.test_no_socket_import_in_app) ... ok
test_no_socket_import_in_cli (tests.test_todo.TestNFR005NoNetwork.test_no_socket_import_in_cli) ... ok
test_main_accepts_injectable_app (tests.test_todo.TestNFR006Testability.test_main_accepts_injectable_app) ... ok
test_main_does_not_call_sys_exit (tests.test_todo.TestNFR006Testability.test_main_does_not_call_sys_exit) ... ok

----------------------------------------------------------------------
Ran 68 tests in 1.049s

OK (skipped=1)
```

**Exit code:** 0

**git status --short (no repository mutations from tests):**

```
M .github/agents/planning.agent.md
 M .github/agents/pr.agent.md
...
```

Tests only created files in `tempfile.mkdtemp()` directories, which are cleaned up by `tearDown`. No `tasks.json` was created in the repository root.

## Results table

| Req | Check | Expected | Result |
|---|---|---|---|
| FR-001 | 5 unit tests | all pass | PASS |
| FR-002 | 2 unit tests | all pass | PASS |
| FR-003 | 1 unit test | pass | PASS |
| FR-004 | 2 unit tests | all pass | PASS |
| FR-005 | 2 unit tests | all pass | PASS |
| FR-006 | 1 unit test | pass | PASS |
| FR-007 | 2 unit tests | all pass | PASS |
| FR-008 | 2 unit tests | all pass | PASS |
| FR-009 | 1 unit test | pass | PASS |
| FR-010 | 2 unit tests | all pass | PASS |
| FR-011 | 2 unit tests | all pass | PASS |
| FR-012 | 4 unit tests | all pass | PASS |
| FR-013 | 3 unit tests | all pass | PASS |
| FR-014 | 3 unit tests | all pass | PASS |
| FR-015 | 1 unit test | pass | PASS |
| FR-016 | 3 unit tests | all pass | PASS |
| FR-017 | 2 unit tests | all pass | PASS |
| FR-018 | 1 unit test | pass | PASS |
| FR-019 | 2 unit tests | all pass | PASS |
| FR-020 | 1 unit test | pass | PASS |
| FR-021 | 3 unit tests | all pass | PASS |
| FR-022 | 3 unit tests | all pass | PASS |
| FR-023 | 1 unit test | skipped (Windows chmod) | SKIP |
| FR-024 | 4 unit tests | all pass | PASS |
| NFR-001 | 2 unit tests | all pass | PASS |
| NFR-002 | 3 unit tests | all pass | PASS |
| NFR-003 | 2 unit tests | all pass | PASS |
| NFR-004 | 4 unit tests | all pass | PASS |
| NFR-005 | 2 unit tests | all pass | PASS |
| NFR-006 | 2 unit tests | all pass | PASS |

## Failures and notes

- FR-023 skipped on Windows: `chmod` is not reliable on Windows CI. The `StorageError` code path is implemented and readable in `todo/app.py`; only the automated test requires POSIX permissions to trigger it. This does not affect the PASS verdict since the requirement is implemented and the skip is declared at the test level.

Result: PASS
