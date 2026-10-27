# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [Unreleased]

### Added

- `todo/app.py`: `Task` dataclass, `TodoError`/`StorageError`/`CorruptStorageError` error hierarchy, `JsonStore` with atomic JSON persistence, `TodoApp` with `add`, `list_tasks`, `done`, `reopen`, and `delete` operations (FR-001 through FR-024, NFR-001 through NFR-006).
- `todo/cli.py`: CLI entry point `main(argv, stdout, stderr, app) -> int` with subcommands `add`, `list`, `done`, `reopen`, `delete`; exit codes 0/1/2 (FR-001, FR-004 through FR-016).
- `todo/__init__.py`: Package initialisation (NFR-001).
- `tests/test_todo.py`: 68 unit tests covering all 24 FRs and 6 NFRs using `unittest` and temporary directories (NFR-006).

### Changed

- Nothing changed; all files are new additions.

### Fixed

- Nothing fixed; this is the initial implementation.
