"""Command-line interface for the Todo application."""

from __future__ import annotations

import argparse
import sys
from io import StringIO
from pathlib import Path
from typing import TextIO

from todo.app import TodoApp, TodoError


DEFAULT_STORE = Path("tasks.json")

_USAGE_PREFIX = "USAGE: python -m todo.cli {add <title> | list | done <id> | reopen <id> | delete <id>}"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="todo",
        description="Manage todo tasks.",
        add_help=True,
    )
    sub = parser.add_subparsers(dest="command")

    add_p = sub.add_parser("add", help="Add a new task.")
    add_p.add_argument("title", help="Title of the new task.")

    sub.add_parser("list", help="List all tasks.")

    done_p = sub.add_parser("done", help="Mark a task as done.")
    done_p.add_argument("id", help="Task ID.")

    reopen_p = sub.add_parser("reopen", help="Reopen a done task.")
    reopen_p.add_argument("id", help="Task ID.")

    delete_p = sub.add_parser("delete", help="Delete a task.")
    delete_p.add_argument("id", help="Task ID.")

    return parser


def _parse_id(raw: str, stderr: TextIO) -> int | None:
    """Parse and validate an ID argument. Writes to stderr and returns None on failure."""
    try:
        value = int(raw)
    except ValueError:
        print(f"Error: task {raw!r} not found.", file=stderr)
        return None
    return value


def main(
    argv: list[str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    app: TodoApp | None = None,
) -> int:
    """Entry point. Returns exit code: 0 success, 1 operation error, 2 usage error."""
    if stdout is None:
        stdout = sys.stdout
    if stderr is None:
        stderr = sys.stderr
    if app is None:
        app = TodoApp(DEFAULT_STORE)

    parser = build_parser()

    class _NonExitingParser(argparse.ArgumentParser):
        def error(self, message: str) -> None:
            print(f"{_USAGE_PREFIX}\nError: {message}", file=stderr)
            raise SystemExit(2)

        def exit(self, status: int = 0, message: str | None = None) -> None:
            raise SystemExit(status)

    # Re-build with non-exiting parser class.
    parser = argparse.ArgumentParser.__new__(_NonExitingParser)
    _NonExitingParser.__init__(
        parser,
        prog="todo",
        description="Manage todo tasks.",
        add_help=True,
    )
    sub = parser.add_subparsers(dest="command")

    add_p = sub.add_parser("add", help="Add a new task.")
    add_p.add_argument("title", help="Title of the new task.")

    sub.add_parser("list", help="List all tasks.")

    done_p = sub.add_parser("done", help="Mark a task as done.")
    done_p.add_argument("id", help="Task ID.")

    reopen_p = sub.add_parser("reopen", help="Reopen a done task.")
    reopen_p.add_argument("id", help="Task ID.")

    delete_p = sub.add_parser("delete", help="Delete a task.")
    delete_p.add_argument("id", help="Task ID.")

    try:
        args = parser.parse_args(argv if argv is not None else sys.argv[1:])
    except SystemExit as exc:
        return int(exc.code) if exc.code is not None else 2

    if args.command is None:
        print(f"{_USAGE_PREFIX}", file=stderr)
        return 2

    try:
        if args.command == "add":
            title = args.title.strip()
            if not title:
                print(f"{_USAGE_PREFIX}\nError: title must not be empty.", file=stderr)
                return 2
            task = app.add(title)
            print(f"Added: {task.id} [open] {task.title}", file=stdout)
            return 0

        elif args.command == "list":
            tasks = app.list_tasks()
            if not tasks:
                print("No tasks.", file=stdout)
            else:
                for task in tasks:
                    print(f"{task.id} [{task.status}] {task.title}", file=stdout)
            return 0

        elif args.command == "done":
            task_id = _parse_id(args.id, stderr)
            if task_id is None:
                return 1
            task, changed = app.done(task_id)
            if not changed:
                print(f"Task {task.id} is already done.", file=stdout)
            return 0

        elif args.command == "reopen":
            task_id = _parse_id(args.id, stderr)
            if task_id is None:
                return 1
            task, changed = app.reopen(task_id)
            if not changed:
                print(f"Task {task.id} is already open.", file=stdout)
            return 0

        elif args.command == "delete":
            task_id = _parse_id(args.id, stderr)
            if task_id is None:
                return 1
            app.delete(task_id)
            return 0

        else:
            print(f"{_USAGE_PREFIX}", file=stderr)
            return 2

    except KeyError as exc:
        bad_id = exc.args[0]
        print(f"Error: task {bad_id} not found.", file=stderr)
        return 1
    except TodoError as exc:
        print(f"Error: {exc}", file=stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
