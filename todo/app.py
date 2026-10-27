"""Core Todo application logic: Task dataclass, error hierarchy, JsonStore, TodoApp."""

from __future__ import annotations

import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Error hierarchy
# ---------------------------------------------------------------------------

class TodoError(Exception):
    """Base class for all Todo application errors."""


class StorageError(TodoError):
    """Raised when the storage file cannot be read or written due to an I/O problem."""


class CorruptStorageError(StorageError):
    """Raised when the storage file contains structurally invalid data."""


# ---------------------------------------------------------------------------
# Domain model
# ---------------------------------------------------------------------------

@dataclass
class Task:
    id: int
    title: str
    status: str  # "open" | "done"


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

_EMPTY_STATE: dict[str, Any] = {"next_id": 1, "tasks": []}


def _validate_store(data: Any) -> None:
    """Raise CorruptStorageError if *data* does not match the expected schema."""
    if not isinstance(data, dict):
        raise CorruptStorageError("storage root must be a JSON object")
    if not isinstance(data.get("next_id"), int) or data["next_id"] < 1:
        raise CorruptStorageError("storage 'next_id' must be a positive integer")
    if not isinstance(data.get("tasks"), list):
        raise CorruptStorageError("storage 'tasks' must be a JSON array")
    seen_ids: set[int] = set()
    for task in data["tasks"]:
        if not isinstance(task, dict):
            raise CorruptStorageError("each task must be a JSON object")
        if not isinstance(task.get("id"), int):
            raise CorruptStorageError("task 'id' must be an integer")
        if not isinstance(task.get("title"), str):
            raise CorruptStorageError("task 'title' must be a string")
        if task.get("status") not in ("open", "done"):
            raise CorruptStorageError("task 'status' must be 'open' or 'done'")
        if task["id"] in seen_ids:
            raise CorruptStorageError(f"duplicate task id {task['id']}")
        seen_ids.add(task["id"])


class JsonStore:
    """Atomic JSON persistence for tasks."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def read(self) -> dict[str, Any]:
        """Return the stored state dict, or the empty-state default."""
        if not self._path.exists() or self._path.stat().st_size == 0:
            return {"next_id": 1, "tasks": []}
        try:
            text = self._path.read_text(encoding="utf-8")
        except OSError as exc:
            raise StorageError(f"cannot read {self._path}: {exc}") from exc
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CorruptStorageError(f"invalid JSON in {self._path}: {exc}") from exc
        _validate_store(data)
        return data

    def write(self, data: dict[str, Any]) -> None:
        """Atomically replace the storage file with *data*."""
        parent = self._path.parent
        parent.mkdir(parents=True, exist_ok=True)
        # Preserve existing file mode so callers' umask settings are respected.
        existing_mode: int | None = None
        if self._path.exists():
            existing_mode = stat.S_IMODE(self._path.stat().st_mode)
        tmp_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=parent,
                delete=False,
                newline="\n",
            ) as tmp:
                tmp_name = tmp.name
                json.dump(data, tmp, indent=2, ensure_ascii=False)
                tmp.write("\n")
                tmp.flush()
                os.fsync(tmp.fileno())
            if existing_mode is not None:
                os.chmod(tmp_name, existing_mode)
            os.replace(tmp_name, self._path)
            tmp_name = None
        except OSError as exc:
            raise StorageError(f"cannot write {self._path}: {exc}") from exc
        finally:
            if tmp_name is not None and os.path.exists(tmp_name):
                try:
                    os.unlink(tmp_name)
                except OSError:
                    pass


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

class TodoApp:
    """High-level task operations; all persistence goes through JsonStore."""

    def __init__(self, store_path: Path) -> None:
        self._store = JsonStore(store_path)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> dict[str, Any]:
        return self._store.read()

    def _save(self, data: dict[str, Any]) -> None:
        self._store.write(data)

    @staticmethod
    def _validate_id(task_id: int) -> None:
        if task_id <= 0:
            raise KeyError(task_id)

    @staticmethod
    def _find(tasks: list[dict[str, Any]], task_id: int) -> dict[str, Any]:
        for task in tasks:
            if task["id"] == task_id:
                return task
        raise KeyError(task_id)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, title: str) -> Task:
        """Create a new open task and return it. *title* must be non-empty after strip."""
        data = self._load()
        new_id = data["next_id"]
        task: dict[str, Any] = {"id": new_id, "title": title, "status": "open"}
        data["tasks"].append(task)
        data["next_id"] = new_id + 1
        self._save(data)
        return Task(id=task["id"], title=task["title"], status=task["status"])

    def list_tasks(self) -> list[Task]:
        """Return all tasks in insertion order."""
        data = self._load()
        return [Task(id=t["id"], title=t["title"], status=t["status"]) for t in data["tasks"]]

    def done(self, task_id: int) -> tuple[Task, bool]:
        """Mark task *task_id* as done. Returns (task, changed) — False when already done."""
        self._validate_id(task_id)
        data = self._load()
        record = self._find(data["tasks"], task_id)
        changed = record["status"] != "done"
        if changed:
            record["status"] = "done"
            self._save(data)
        return Task(id=record["id"], title=record["title"], status=record["status"]), changed

    def reopen(self, task_id: int) -> tuple[Task, bool]:
        """Mark task *task_id* as open. Returns (task, changed) — False when already open."""
        self._validate_id(task_id)
        data = self._load()
        record = self._find(data["tasks"], task_id)
        changed = record["status"] != "open"
        if changed:
            record["status"] = "open"
            self._save(data)
        return Task(id=record["id"], title=record["title"], status=record["status"]), changed

    def delete(self, task_id: int) -> None:
        """Remove task *task_id*. Raises KeyError if not found."""
        self._validate_id(task_id)
        data = self._load()
        original_len = len(data["tasks"])
        data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
        if len(data["tasks"]) == original_len:
            raise KeyError(task_id)
        self._save(data)
