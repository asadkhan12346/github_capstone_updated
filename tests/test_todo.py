"""Tests for the Todo application.

Requirement coverage:
    FR-001  Command-line operations.
    FR-002  Create a task.
    FR-003  Initial task status.
    FR-004  Add output format.
    FR-005  List tasks.
    FR-006  Empty list.
    FR-007  Complete an open task.
    FR-008  Complete an already-done task.
    FR-009  Reopen a done task.
    FR-010  Reopen an already-open task.
    FR-011  Delete a task.
    FR-012  Unknown task ID.
    FR-013  Invalid task ID.
    FR-014  Usage error.
    FR-015  Error stream and exit status.
    FR-016  Empty title rejection.
    FR-017  Title whitespace trimming.
    FR-018  Duplicate titles allowed.
    FR-019  No count or title-length limit.
    FR-020  Persistent storage contract.
    FR-021  Missing or empty storage.
    FR-022  Corrupt storage.
    FR-023  Other storage I/O failures.
    FR-024  Monotonic, non-reused IDs.
    NFR-001 Runtime and dependencies.
    NFR-002 Storage encoding and representation.
    NFR-003 Atomic saves.
    NFR-004 No unintended writes.
    NFR-005 Local privacy.
    NFR-006 Testability.
"""

from __future__ import annotations

import importlib
import inspect
import json
import os
import shutil
import tempfile
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from todo.app import CorruptStorageError, JsonStore, StorageError, Task, TodoApp
from todo.cli import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Base(unittest.TestCase):
    def setUp(self) -> None:
        self._dir = tempfile.mkdtemp()
        self._store = Path(self._dir) / "tasks.json"
        self.app = TodoApp(self._store)

    def tearDown(self) -> None:
        shutil.rmtree(self._dir, ignore_errors=True)

    def _cli(self, *args: str) -> tuple[int, str, str]:
        out, err = StringIO(), StringIO()
        code = main(list(args), stdout=out, stderr=err, app=self.app)
        return code, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# FR-001 Command-line operations
# ---------------------------------------------------------------------------

class TestFR001Commands(_Base):
    """FR-001: Five subcommands exist and are dispatched."""

    def test_add_command_exists(self) -> None:  # FR-001
        code, out, _ = self._cli("add", "Buy milk")
        self.assertEqual(code, 0)

    def test_list_command_exists(self) -> None:  # FR-001
        code, _, _ = self._cli("list")
        self.assertEqual(code, 0)

    def test_done_command_exists(self) -> None:  # FR-001
        t = self.app.add("x")
        code, _, _ = self._cli("done", str(t.id))
        self.assertEqual(code, 0)

    def test_reopen_command_exists(self) -> None:  # FR-001
        t = self.app.add("x")
        self.app.done(t.id)
        code, _, _ = self._cli("reopen", str(t.id))
        self.assertEqual(code, 0)

    def test_delete_command_exists(self) -> None:  # FR-001
        t = self.app.add("x")
        code, _, _ = self._cli("delete", str(t.id))
        self.assertEqual(code, 0)


# ---------------------------------------------------------------------------
# FR-002 Create a task
# ---------------------------------------------------------------------------

class TestFR002CreateTask(_Base):
    """FR-002: add returns a Task with the correct fields."""

    def test_add_returns_task(self) -> None:  # FR-002
        task = self.app.add("Buy milk")
        self.assertIsInstance(task, Task)
        self.assertEqual(task.title, "Buy milk")
        self.assertGreater(task.id, 0)

    def test_add_assigns_sequential_id(self) -> None:  # FR-002
        a = self.app.add("First")
        b = self.app.add("Second")
        self.assertEqual(b.id, a.id + 1)


# ---------------------------------------------------------------------------
# FR-003 Initial task status
# ---------------------------------------------------------------------------

class TestFR003InitialStatus(_Base):
    """FR-003: Newly created tasks have status 'open'."""

    def test_new_task_status_is_open(self) -> None:  # FR-003
        task = self.app.add("Task")
        self.assertEqual(task.status, "open")


# ---------------------------------------------------------------------------
# FR-004 Add output format
# ---------------------------------------------------------------------------

class TestFR004AddOutput(_Base):
    """FR-004: add prints 'Added: {id} [open] {title}' to stdout."""

    def test_add_stdout_format(self) -> None:  # FR-004
        code, out, _ = self._cli("add", "Buy milk")
        self.assertEqual(code, 0)
        self.assertIn("[open]", out)
        self.assertIn("Buy milk", out)
        self.assertIn("Added:", out)

    def test_add_stdout_exact_format(self) -> None:  # FR-004
        task = self.app.add("Pay bills")
        _, out, _ = self._cli("add", "Another")
        lines = out.strip().splitlines()
        self.assertTrue(lines[-1].startswith("Added: "))


# ---------------------------------------------------------------------------
# FR-005 List tasks
# ---------------------------------------------------------------------------

class TestFR005ListTasks(_Base):
    """FR-005: list shows all tasks in creation order."""

    def test_list_returns_all_tasks(self) -> None:  # FR-005
        self.app.add("Alpha")
        self.app.add("Beta")
        code, out, _ = self._cli("list")
        self.assertEqual(code, 0)
        self.assertIn("Alpha", out)
        self.assertIn("Beta", out)

    def test_list_creation_order(self) -> None:  # FR-005
        self.app.add("First")
        self.app.add("Second")
        _, out, _ = self._cli("list")
        self.assertLess(out.index("First"), out.index("Second"))


# ---------------------------------------------------------------------------
# FR-006 Empty list
# ---------------------------------------------------------------------------

class TestFR006EmptyList(_Base):
    """FR-006: list with no tasks prints 'No tasks.'."""

    def test_empty_list_message(self) -> None:  # FR-006
        code, out, _ = self._cli("list")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "No tasks.")


# ---------------------------------------------------------------------------
# FR-007 Complete an open task
# ---------------------------------------------------------------------------

class TestFR007CompleteOpenTask(_Base):
    """FR-007: done changes an open task to done."""

    def test_done_open_task_changes_status(self) -> None:  # FR-007
        task = self.app.add("Task")
        result, changed = self.app.done(task.id)
        self.assertTrue(changed)
        self.assertEqual(result.status, "done")

    def test_done_persists(self) -> None:  # FR-007
        task = self.app.add("Task")
        self.app.done(task.id)
        tasks = self.app.list_tasks()
        self.assertEqual(tasks[0].status, "done")


# ---------------------------------------------------------------------------
# FR-008 Complete an already-done task
# ---------------------------------------------------------------------------

class TestFR008AlreadyDone(_Base):
    """FR-008: done on an already-done task is a no-op."""

    def test_done_already_done_returns_false(self) -> None:  # FR-008
        task = self.app.add("Task")
        self.app.done(task.id)
        _, changed = self.app.done(task.id)
        self.assertFalse(changed)

    def test_done_already_done_prints_message(self) -> None:  # FR-008
        task = self.app.add("Task")
        self.app.done(task.id)
        code, out, _ = self._cli("done", str(task.id))
        self.assertEqual(code, 0)
        self.assertIn(f"Task {task.id} is already done.", out)


# ---------------------------------------------------------------------------
# FR-009 Reopen a done task
# ---------------------------------------------------------------------------

class TestFR009ReopenDoneTask(_Base):
    """FR-009: reopen changes a done task back to open."""

    def test_reopen_done_task(self) -> None:  # FR-009
        task = self.app.add("Task")
        self.app.done(task.id)
        result, changed = self.app.reopen(task.id)
        self.assertTrue(changed)
        self.assertEqual(result.status, "open")


# ---------------------------------------------------------------------------
# FR-010 Reopen an already-open task
# ---------------------------------------------------------------------------

class TestFR010AlreadyOpen(_Base):
    """FR-010: reopen on an already-open task is a no-op."""

    def test_reopen_already_open_returns_false(self) -> None:  # FR-010
        task = self.app.add("Task")
        _, changed = self.app.reopen(task.id)
        self.assertFalse(changed)

    def test_reopen_already_open_prints_message(self) -> None:  # FR-010
        task = self.app.add("Task")
        code, out, _ = self._cli("reopen", str(task.id))
        self.assertEqual(code, 0)
        self.assertIn(f"Task {task.id} is already open.", out)


# ---------------------------------------------------------------------------
# FR-011 Delete a task
# ---------------------------------------------------------------------------

class TestFR011Delete(_Base):
    """FR-011: delete removes the task from storage."""

    def test_delete_removes_task(self) -> None:  # FR-011
        task = self.app.add("Delete me")
        self.app.delete(task.id)
        ids = [t.id for t in self.app.list_tasks()]
        self.assertNotIn(task.id, ids)

    def test_delete_via_cli(self) -> None:  # FR-011
        task = self.app.add("Remove")
        code, _, _ = self._cli("delete", str(task.id))
        self.assertEqual(code, 0)


# ---------------------------------------------------------------------------
# FR-012 Unknown task ID
# ---------------------------------------------------------------------------

class TestFR012UnknownID(_Base):
    """FR-012: not-found errors go to stderr with exit 1."""

    def test_done_unknown_id_stderr_exit1(self) -> None:  # FR-012
        code, _, err = self._cli("done", "9999")
        self.assertEqual(code, 1)
        self.assertIn("9999", err)

    def test_reopen_unknown_id(self) -> None:  # FR-012
        code, _, err = self._cli("reopen", "9999")
        self.assertEqual(code, 1)

    def test_delete_unknown_id(self) -> None:  # FR-012
        code, _, err = self._cli("delete", "9999")
        self.assertEqual(code, 1)

    def test_error_message_format(self) -> None:  # FR-012
        code, _, err = self._cli("done", "42")
        self.assertIn("Error: task 42 not found.", err)


# ---------------------------------------------------------------------------
# FR-013 Invalid task ID
# ---------------------------------------------------------------------------

class TestFR013InvalidID(_Base):
    """FR-013: IDs that are 0, negative, or non-numeric are treated as not-found."""

    def test_zero_id_treated_as_not_found(self) -> None:  # FR-013
        code, _, _ = self._cli("done", "0")
        self.assertEqual(code, 1)

    def test_negative_id_treated_as_not_found(self) -> None:  # FR-013
        code, _, _ = self._cli("done", "-1")
        self.assertEqual(code, 1)

    def test_non_numeric_id_treated_as_not_found(self) -> None:  # FR-013
        code, _, err = self._cli("done", "abc")
        self.assertEqual(code, 1)


# ---------------------------------------------------------------------------
# FR-014 Usage error
# ---------------------------------------------------------------------------

class TestFR014UsageError(_Base):
    """FR-014: bad commands print USAGE and return exit 2."""

    def test_no_subcommand_returns_2(self) -> None:  # FR-014
        code, _, err = self._cli()
        self.assertEqual(code, 2)

    def test_unknown_subcommand_returns_2(self) -> None:  # FR-014
        code, _, err = self._cli("bogus")
        self.assertEqual(code, 2)

    def test_usage_message_starts_with_USAGE(self) -> None:  # FR-014
        _, _, err = self._cli()
        self.assertIn("USAGE", err)


# ---------------------------------------------------------------------------
# FR-015 Error stream and exit status
# ---------------------------------------------------------------------------

class TestFR015ErrorStream(_Base):
    """FR-015: errors go to stderr with non-zero exit."""

    def test_not_found_goes_to_stderr(self) -> None:  # FR-015
        code, out, err = self._cli("done", "999")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("Error", err)


# ---------------------------------------------------------------------------
# FR-016 Empty title rejection
# ---------------------------------------------------------------------------

class TestFR016EmptyTitle(_Base):
    """FR-016: empty or whitespace-only titles are rejected."""

    def test_empty_title_rejected(self) -> None:  # FR-016
        code, _, _ = self._cli("add", "")
        self.assertEqual(code, 2)

    def test_whitespace_only_title_rejected(self) -> None:  # FR-016
        code, _, _ = self._cli("add", "   ")
        self.assertEqual(code, 2)

    def test_empty_title_no_task_created(self) -> None:  # FR-016
        self._cli("add", "")
        tasks = self.app.list_tasks()
        self.assertEqual(tasks, [])


# ---------------------------------------------------------------------------
# FR-017 Title whitespace
# ---------------------------------------------------------------------------

class TestFR017TitleWhitespace(_Base):
    """FR-017: surrounding whitespace is trimmed; internal is preserved."""

    def test_surrounding_whitespace_trimmed(self) -> None:  # FR-017
        code, _, _ = self._cli("add", "  Buy milk  ")
        self.assertEqual(code, 0)
        tasks = self.app.list_tasks()
        self.assertEqual(tasks[0].title, "Buy milk")

    def test_internal_whitespace_preserved(self) -> None:  # FR-017
        code, _, _ = self._cli("add", "  Buy  milk  ")
        self.assertEqual(code, 0)
        tasks = self.app.list_tasks()
        self.assertEqual(tasks[0].title, "Buy  milk")


# ---------------------------------------------------------------------------
# FR-018 Duplicate titles allowed
# ---------------------------------------------------------------------------

class TestFR018DuplicateTitles(_Base):
    """FR-018: identical titles are allowed; each gets a distinct ID."""

    def test_duplicate_titles_allowed(self) -> None:  # FR-018
        a = self.app.add("Same title")
        b = self.app.add("Same title")
        self.assertNotEqual(a.id, b.id)
        self.assertEqual(len(self.app.list_tasks()), 2)


# ---------------------------------------------------------------------------
# FR-019 No count or title-length limit
# ---------------------------------------------------------------------------

class TestFR019NoLimits(_Base):
    """FR-019: no enforced task-count or title-length limit."""

    def test_add_200_tasks(self) -> None:  # FR-019
        for i in range(200):
            self.app.add(f"Task {i}")
        self.assertEqual(len(self.app.list_tasks()), 200)

    def test_long_title_accepted(self) -> None:  # FR-019
        long_title = "A" * 10000
        task = self.app.add(long_title)
        self.assertEqual(len(task.title), 10000)


# ---------------------------------------------------------------------------
# FR-020 Persistent storage contract
# ---------------------------------------------------------------------------

class TestFR020StorageContract(_Base):
    """FR-020: tasks.json has the expected top-level shape."""

    def test_storage_schema(self) -> None:  # FR-020
        self.app.add("Test task")
        data = json.loads(self._store.read_text(encoding="utf-8"))
        self.assertIn("next_id", data)
        self.assertIn("tasks", data)
        self.assertIsInstance(data["next_id"], int)
        self.assertIsInstance(data["tasks"], list)
        task = data["tasks"][0]
        self.assertIn("id", task)
        self.assertIn("title", task)
        self.assertIn("status", task)


# ---------------------------------------------------------------------------
# FR-021 Missing or empty storage
# ---------------------------------------------------------------------------

class TestFR021MissingStorage(_Base):
    """FR-021: missing or empty file is treated as an empty task list."""

    def test_missing_file_gives_empty_list(self) -> None:  # FR-021
        self.assertEqual(self.app.list_tasks(), [])

    def test_empty_file_gives_empty_list(self) -> None:  # FR-021
        self._store.write_text("", encoding="utf-8")
        self.assertEqual(self.app.list_tasks(), [])

    def test_add_to_missing_store(self) -> None:  # FR-021
        task = self.app.add("New task")
        self.assertEqual(task.id, 1)


# ---------------------------------------------------------------------------
# FR-022 Corrupt storage
# ---------------------------------------------------------------------------

class TestFR022CorruptStorage(_Base):
    """FR-022: corrupt JSON raises CorruptStorageError; file bytes unchanged."""

    def test_invalid_json_raises(self) -> None:  # FR-022
        self._store.write_text("{not json}", encoding="utf-8")
        with self.assertRaises(CorruptStorageError):
            self.app.list_tasks()

    def test_duplicate_ids_raises(self) -> None:  # FR-022
        self._store.write_text(
            json.dumps({"next_id": 3, "tasks": [
                {"id": 1, "title": "A", "status": "open"},
                {"id": 1, "title": "B", "status": "open"},
            ]}),
            encoding="utf-8",
        )
        with self.assertRaises(CorruptStorageError):
            self.app.list_tasks()

    def test_corrupt_file_bytes_unchanged(self) -> None:  # FR-022
        bad_content = "{bad json}"
        self._store.write_text(bad_content, encoding="utf-8")
        try:
            self.app.list_tasks()
        except CorruptStorageError:
            pass
        self.assertEqual(self._store.read_text(encoding="utf-8"), bad_content)


# ---------------------------------------------------------------------------
# FR-023 Other storage I/O failures
# ---------------------------------------------------------------------------

class TestFR023StorageIOFailure(_Base):
    """FR-023: I/O errors that are not corruption raise StorageError."""

    def test_read_permission_error_raises_storage_error(self) -> None:  # FR-023
        self.app.add("x")
        import platform
        if platform.system() == "Windows":
            self.skipTest("chmod not reliable on Windows CI")
        os.chmod(self._store, 0o000)
        try:
            with self.assertRaises(StorageError):
                self.app.list_tasks()
        finally:
            os.chmod(self._store, 0o644)


# ---------------------------------------------------------------------------
# FR-024 Monotonic, non-reused IDs
# ---------------------------------------------------------------------------

class TestFR024MonotonicIDs(_Base):
    """FR-024: IDs are monotonic, non-reused, and next_id persists."""

    def test_ids_start_at_1(self) -> None:  # FR-024
        task = self.app.add("First")
        self.assertEqual(task.id, 1)

    def test_ids_increment(self) -> None:  # FR-024
        a = self.app.add("A")
        b = self.app.add("B")
        self.assertEqual(b.id, a.id + 1)

    def test_ids_not_reused_after_delete(self) -> None:  # FR-024
        a = self.app.add("A")
        self.app.delete(a.id)
        b = self.app.add("B")
        self.assertNotEqual(b.id, a.id)
        self.assertGreater(b.id, a.id)

    def test_next_id_persists_across_instances(self) -> None:  # FR-024
        app1 = TodoApp(self._store)
        app1.add("X")
        app2 = TodoApp(self._store)
        task = app2.add("Y")
        self.assertEqual(task.id, 2)


# ---------------------------------------------------------------------------
# NFR-001 Runtime and dependencies
# ---------------------------------------------------------------------------

class TestNFR001Runtime(_Base):
    """NFR-001: Python 3.11+, stdlib only."""

    def test_python_version(self) -> None:  # NFR-001
        import sys
        self.assertGreaterEqual(sys.version_info[:2], (3, 11))

    def test_stdlib_only(self) -> None:  # NFR-001
        import todo.app as app_mod
        import todo.cli as cli_mod
        stdlib_names = {
            "abc", "argparse", "ast", "asyncio", "builtins", "collections",
            "contextlib", "copy", "dataclasses", "datetime", "enum",
            "functools", "io", "itertools", "json", "logging", "math",
            "operator", "os", "pathlib", "re", "shutil", "signal",
            "socket", "stat", "string", "sys", "tempfile", "threading",
            "time", "traceback", "types", "typing", "unittest", "urllib",
            "uuid", "warnings", "__future__",
        }
        for mod in (app_mod, cli_mod):
            src = inspect.getsource(mod)
            # No third-party top-level import
            for line in src.splitlines():
                stripped = line.strip()
                if stripped.startswith("import ") or stripped.startswith("from "):
                    parts = stripped.split()
                    pkg = parts[1].split(".")[0]
                    if pkg not in stdlib_names and not pkg.startswith("todo"):
                        self.fail(f"Non-stdlib import in {mod.__name__}: {stripped}")


# ---------------------------------------------------------------------------
# NFR-002 Storage encoding and representation
# ---------------------------------------------------------------------------

class TestNFR002StorageEncoding(_Base):
    """NFR-002: UTF-8, ensure_ascii=False, indent=2."""

    def test_utf8_encoding(self) -> None:  # NFR-002
        self.app.add("Ünïcödé tïtle")
        raw_bytes = self._store.read_bytes()
        text = raw_bytes.decode("utf-8")
        self.assertIn("Ünïcödé", text)

    def test_ensure_ascii_false(self) -> None:  # NFR-002
        self.app.add("日本語")
        raw_bytes = self._store.read_bytes()
        text = raw_bytes.decode("utf-8")
        self.assertIn("日本語", text)
        self.assertNotIn("\\u", text)

    def test_indent_2(self) -> None:  # NFR-002
        self.app.add("Task")
        text = self._store.read_text(encoding="utf-8")
        self.assertIn("  ", text)


# ---------------------------------------------------------------------------
# NFR-003 Atomic saves
# ---------------------------------------------------------------------------

class TestNFR003AtomicSaves(_Base):
    """NFR-003: write uses temp file + fsync + os.replace; no temp file left behind."""

    def test_no_temp_file_after_write(self) -> None:  # NFR-003
        self.app.add("Task")
        files = list(Path(self._dir).iterdir())
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "tasks.json")

    def test_file_is_valid_json_after_write(self) -> None:  # NFR-003
        self.app.add("Atomicity")
        data = json.loads(self._store.read_text(encoding="utf-8"))
        self.assertIsInstance(data, dict)


# ---------------------------------------------------------------------------
# NFR-004 No unintended writes
# ---------------------------------------------------------------------------

class TestNFR004NoUnintendedWrites(_Base):
    """NFR-004: list, no-ops, and failures do not write the file."""

    def test_list_does_not_write(self) -> None:  # NFR-004
        self.app.list_tasks()
        self.assertFalse(self._store.exists())

    def test_noop_done_does_not_write(self) -> None:  # NFR-004
        task = self.app.add("Task")
        self.app.done(task.id)
        mtime_before = self._store.stat().st_mtime_ns
        self.app.done(task.id)
        self.assertEqual(self._store.stat().st_mtime_ns, mtime_before)

    def test_noop_reopen_does_not_write(self) -> None:  # NFR-004
        task = self.app.add("Task")
        mtime_before = self._store.stat().st_mtime_ns
        self.app.reopen(task.id)
        self.assertEqual(self._store.stat().st_mtime_ns, mtime_before)

    def test_not_found_does_not_write(self) -> None:  # NFR-004
        self.app.add("Task")
        mtime_before = self._store.stat().st_mtime_ns
        try:
            self.app.done(9999)
        except KeyError:
            pass
        self.assertEqual(self._store.stat().st_mtime_ns, mtime_before)


# ---------------------------------------------------------------------------
# NFR-005 Local privacy
# ---------------------------------------------------------------------------

class TestNFR005NoNetwork(_Base):
    """NFR-005: no network calls are made."""

    def test_no_socket_import_in_app(self) -> None:  # NFR-005
        import todo.app as app_mod
        src = inspect.getsource(app_mod)
        self.assertNotIn("import socket", src)
        self.assertNotIn("import urllib", src)
        self.assertNotIn("import http", src)
        self.assertNotIn("requests", src)

    def test_no_socket_import_in_cli(self) -> None:  # NFR-005
        import todo.cli as cli_mod
        src = inspect.getsource(cli_mod)
        self.assertNotIn("import socket", src)
        self.assertNotIn("requests", src)


# ---------------------------------------------------------------------------
# NFR-006 Testability
# ---------------------------------------------------------------------------

class TestNFR006Testability(_Base):
    """NFR-006: tests use unittest and temp directories; main() injectable."""

    def test_main_accepts_injectable_app(self) -> None:  # NFR-006
        # main() receives an app argument — no global state dependency.
        out = StringIO()
        code = main(["list"], stdout=out, stderr=StringIO(), app=self.app)
        self.assertEqual(code, 0)

    def test_main_does_not_call_sys_exit(self) -> None:  # NFR-006
        # main() must return an int, not call sys.exit.
        import todo.cli as cli_mod
        src = inspect.getsource(cli_mod)
        # sys.exit should not appear outside the __main__ guard
        lines = src.splitlines()
        in_main_guard = False
        for line in lines:
            if line.strip().startswith("if __name__"):
                in_main_guard = True
            if not in_main_guard and "sys.exit" in line and "__main__" not in line:
                self.fail(f"sys.exit found outside __main__ guard: {line}")


if __name__ == "__main__":
    unittest.main()
