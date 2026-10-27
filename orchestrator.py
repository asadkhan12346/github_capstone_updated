"""Demo-grade SDLC state machine; TTY checks are not an authentication boundary.

Real enforcement also depends on the PreToolUse hook, pull-request review, and
repository branch protection. A determined user can bypass local controls.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

STATUSES = ("LOCKED", "ACTIVE", "AWAITING_APPROVAL", "APPROVED")
_RANK = {"APPROVED": 0, "ACTIVE": 1, "AWAITING_APPROVAL": 1, "LOCKED": 2}
ID_RE = re.compile(r"\b(?:FR|NFR)-\d{3}\b")
FR_RE = re.compile(r"\bFR-\d{3}\b")
DEFAULT_ACTOR = "agent/system"
STATE_FIELDS = {
    "status",
    "hashes",
    "approvedBy",
    "approvedAt",
    "rejectionReason",
}
TRACE_RULES: dict[str, tuple[str, ...]] = {
    "requirements": ("fr", "open"),
    "architecture": ("any",),
    "design-review": ("any", "verdict"),
    "planning": ("any",),
    "review": ("all",),
    "verify": ("all", "fence"),
    "pr": ("all",),
}


class RuleViolation(Exception):
    """A requested operation would violate the pipeline contract."""

    def __init__(self, rule: str, hint: str) -> None:
        self.rule = rule
        self.hint = hint
        super().__init__(f"RULE VIOLATION: {rule}. {hint}")


class UsageError(Exception):
    """The command or phase name is invalid."""


def _manifest_path(root: Path) -> Path:
    return root / "sdlc" / "phases.json"


def load_manifest(root: Path) -> dict[str, Any]:
    """Read and minimally validate the ordered phase manifest."""
    path = _manifest_path(root)
    try:
        manifest = json.loads(path.read_text(encoding="utf-8"))
        phases = manifest["phases"]
        protected = manifest["protected"]
        if not isinstance(phases, list) or not phases or not isinstance(protected, list):
            raise ValueError("phases and protected must be non-empty/list values")
        for phase in phases:
            if not isinstance(phase, dict) or not {
                "id", "order", "agent", "prompt", "owns"
            }.issubset(phase):
                raise ValueError("phase entry is missing required fields")
            if not isinstance(phase["owns"], list):
                raise ValueError("phase owns must be a list")
        phases.sort(key=lambda item: item["order"])
        ids = [phase["id"] for phase in phases]
        orders = [phase["order"] for phase in phases]
        owned = [path for phase in phases for path in phase["owns"]]
        if len(ids) != len(set(ids)) or orders != list(range(1, len(phases) + 1)):
            raise ValueError("phase ids or order are invalid")
        if len(owned) != len(set(owned)):
            raise ValueError("owned paths overlap")
        manifest["phases"] = phases
        return manifest
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RuleViolation(
            "sdlc/phases.json is missing or invalid",
            "Restore a valid manifest before running the pipeline",
        ) from exc


def _get(manifest: dict[str, Any], phase_id: str) -> dict[str, Any]:
    for phase in manifest["phases"]:
        if phase["id"] == phase_id:
            return phase
    valid = ", ".join(phase["id"] for phase in manifest["phases"])
    raise UsageError(f"unknown phase {phase_id!r}. Valid phases: {valid}")


def _state_path(root: Path) -> Path:
    return root / "sdlc" / "state.json"


def _audit_path(root: Path) -> Path:
    return root / "sdlc" / "audit.log.jsonl"


def init_state(root: Path) -> dict[str, Any]:
    """Create initial state and an empty audit log if they do not exist."""
    manifest = load_manifest(root)
    root.joinpath("sdlc").mkdir(parents=True, exist_ok=True)
    entries: dict[str, dict[str, Any]] = {}
    for index, phase in enumerate(manifest["phases"]):
        entries[phase["id"]] = {
            "status": "ACTIVE" if index == 0 else "LOCKED",
            "hashes": {},
            "approvedBy": None,
            "approvedAt": None,
            "rejectionReason": None,
        }
    state = {"phases": entries}
    save_state(root, state)
    _audit_path(root).touch(exist_ok=True)
    return state


def save_state(root: Path, state: dict[str, Any]) -> None:
    """Atomically replace the state file."""
    path = _state_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=path.parent, delete=False, newline="\n"
        ) as temporary:
            temporary_name = temporary.name
            json.dump(state, temporary, indent=2, ensure_ascii=False)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_name, path)
    finally:
        if temporary_name is not None and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def load_state(root: Path, manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    """Load and validate state against the manifest."""
    manifest = manifest or load_manifest(root)
    try:
        state = json.loads(_state_path(root).read_text(encoding="utf-8"))
        phase_state = state["phases"]
        expected_ids = [phase["id"] for phase in manifest["phases"]]
        if not isinstance(phase_state, dict) or list(phase_state) != expected_ids:
            raise ValueError("phase entries do not match manifest order")
        statuses: list[str] = []
        for phase_id in expected_ids:
            entry = phase_state[phase_id]
            if not isinstance(entry, dict) or set(entry) != STATE_FIELDS:
                raise ValueError(f"{phase_id} has invalid fields")
            if entry["status"] not in STATUSES or not isinstance(entry["hashes"], dict):
                raise ValueError(f"{phase_id} has invalid status or hashes")
            statuses.append(entry["status"])
        ranks = [_RANK[status] for status in statuses]
        if ranks != sorted(ranks):
            raise ValueError("phase statuses are out of order")
        active_count = sum(status in {"ACTIVE", "AWAITING_APPROVAL"} for status in statuses)
        if active_count > 1:
            raise ValueError("more than one phase is active or awaiting approval")
        if "LOCKED" in statuses and "ACTIVE" not in statuses and "AWAITING_APPROVAL" not in statuses:
            raise ValueError("locked phases remain without an active phase")
        if set(state) != {"phases"}:
            raise ValueError("state has unexpected top-level fields")
        return state
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise RuleViolation(
            "sdlc/state.json is invalid (phase structure or status invariant failed)",
            "Ask the human to restore it from git or delete it so it is re-initialised",
        ) from exc


def derive(manifest: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    """Derive the current phase and its allowed outputs."""
    phases = manifest["phases"]
    current_index = next(
        (
            index
            for index, phase in enumerate(phases)
            if state["phases"][phase["id"]]["status"]
            in {"ACTIVE", "AWAITING_APPROVAL"}
        ),
        None,
    )
    if current_index is None:
        return {
            "currentPhase": None,
            "previousPhase": phases[-1]["id"] if phases else None,
            "nextPhase": None,
            "phaseStatus": "COMPLETE",
            "approvalStatus": "COMPLETE",
            "requiredArtifacts": [],
            "allowedFiles": [],
        }
    current = phases[current_index]
    status = state["phases"][current["id"]]["status"]
    return {
        "currentPhase": current["id"],
        "previousPhase": phases[current_index - 1]["id"] if current_index else None,
        "nextPhase": phases[current_index + 1]["id"]
        if current_index + 1 < len(phases)
        else None,
        "phaseStatus": status,
        "approvalStatus": "PENDING_HUMAN_APPROVAL"
        if status == "AWAITING_APPROVAL"
        else "NOT_SUBMITTED",
        "requiredArtifacts": list(current["owns"]),
        "allowedFiles": list(current["owns"]) if status == "ACTIVE" else [],
    }


def hash_files(root: Path, owned_files: list[str]) -> dict[str, str]:
    """Return SHA-256 hashes for owned files that currently exist."""
    hashes: dict[str, str] = {}
    for relative_path in owned_files:
        path = root / relative_path
        if path.is_file():
            hashes[relative_path] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def _drift(root: Path, phase: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    current_hashes = hash_files(root, phase["owns"])
    recorded_hashes = entry["hashes"]
    return sorted(
        path
        for path in set(current_hashes) | set(recorded_hashes)
        if current_hashes.get(path) != recorded_hashes.get(path)
    )


def audit(
    root: Path,
    actor: str,
    action: str,
    phase: str | None,
    result: str,
    detail: str,
    hashes: dict[str, str] | None = None,
) -> None:
    """Append one machine-readable audit event."""
    record: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor": actor,
        "action": action,
        "phase": phase,
        "result": result,
        "detail": detail,
    }
    if hashes is not None:
        record["hashes"] = hashes
    path = _audit_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as audit_file:
        audit_file.write(json.dumps(record, ensure_ascii=False) + "\n")


def _guarded(
    root: Path,
    actor: str,
    action: str,
    phase: str | None,
    operation: Any,
) -> Any:
    try:
        result = operation()
        audit(root, actor, action, phase, "ok", "completed")
        return result
    except (RuleViolation, UsageError) as exc:
        audit(root, actor, action, phase, "refused", str(exc))
        raise


def _traceability_error(
    root: Path, phase_id: str, artifact_path: str
) -> str | None:
    if phase_id not in TRACE_RULES:
        return None
    text = (root / artifact_path).read_text(encoding="utf-8")
    rules = TRACE_RULES[phase_id]
    if phase_id == "requirements":
        if not FR_RE.search(text):
            return "requirements must define at least one FR-### id"
        match = re.search(r"(?m)^## Open Questions\s*$", text)
        if match is None:
            return "requirements must include a ## Open Questions section"
        section = text[match.end() :]
        next_heading = re.search(r"(?m)^## ", section)
        if next_heading is not None:
            section = section[: next_heading.start()]
        if re.search(r"(?m)^\s*-\s*\[ \]", section):
            return "requirements contain unanswered open questions"
        return None

    requirements_path = root / "artifacts" / "requirements.md"
    if not requirements_path.is_file():
        return "requirements artifact is missing; submit requirements first"
    defined = set(ID_RE.findall(requirements_path.read_text(encoding="utf-8")))
    mentioned = set(ID_RE.findall(text))
    if not defined:
        return "requirements define no FR/NFR ids"
    undefined = mentioned - defined
    if undefined:
        return f"artifact cites undefined ids: {', '.join(sorted(undefined))}"
    if "any" in rules and not (mentioned & defined):
        return "artifact must cite at least one requirement id"
    if "all" in rules and not defined.issubset(mentioned):
        missing = ", ".join(sorted(defined - mentioned))
        return f"artifact must cite every defined requirement id; missing: {missing}"
    if "verdict" in rules and re.search(r"(?m)^Verdict: (?:APPROVE|REVISE)$", text) is None:
        return "artifact must end with Verdict: APPROVE or Verdict: REVISE"
    if "fence" in rules and "```" not in text:
        return "artifact must contain a fenced code block"
    return None


def _require_status(entry: dict[str, Any], expected: str, action: str) -> None:
    if entry["status"] != expected:
        raise RuleViolation(
            f"{action} needs {expected} but phase is {entry['status']}",
            "Run python orchestrator.py next and work only on the active phase",
        )


def submit(root: Path, phase_id: str, actor: str = DEFAULT_ACTOR) -> dict[str, Any]:
    """Validate and submit the active phase for human approval."""
    def operation() -> dict[str, Any]:
        manifest = load_manifest(root)
        phase = _get(manifest, phase_id)
        state = load_state(root, manifest)
        entry = state["phases"][phase_id]
        _require_status(entry, "ACTIVE", "submit")
        missing = [
            path
            for path in phase["owns"]
            if not (root / path).is_file() or (root / path).stat().st_size == 0
        ]
        if missing:
            raise RuleViolation(
                "owned files are missing or empty",
                f"Create non-empty files for: {', '.join(missing)}",
            )
        trace_error = _traceability_error(root, phase_id, phase["owns"][0])
        if trace_error:
            raise RuleViolation(
                f"traceability checks failed for {phase_id}",
                f"Fix {phase['owns'][0]}: {trace_error}",
            )
        hashes = hash_files(root, phase["owns"])
        entry["hashes"] = hashes
        entry["status"] = "AWAITING_APPROVAL"
        entry["approvedBy"] = None
        entry["approvedAt"] = None
        entry["rejectionReason"] = None
        save_state(root, state)
        audit(root, actor, "submit", phase_id, "ok", "submitted for human approval", hashes)
        return state

    return _guarded(root, actor, "submit", phase_id, operation)


def _confirm(root: Path, phase_id: str, confirmed: bool | None) -> None:
    if confirmed is True:
        return
    if not sys.stdin.isatty():
        raise RuleViolation(
            "approve/reject/reopen must be run by a human in a TTY",
            "Run the command in an interactive terminal and confirm the phase id",
        )
    answer = input("Type the phase id to confirm: ")
    if answer != phase_id:
        raise RuleViolation(
            "human confirmation did not match the phase id",
            f"Type exactly {phase_id!r} to continue",
        )


def approve(
    root: Path,
    phase_id: str,
    by: str,
    confirmed: bool | None = None,
) -> dict[str, Any]:
    """Approve a submitted phase and activate its successor."""
    def operation() -> dict[str, Any]:
        _confirm(root, phase_id, confirmed)
        manifest = load_manifest(root)
        phase = _get(manifest, phase_id)
        state = load_state(root, manifest)
        entry = state["phases"][phase_id]
        _require_status(entry, "AWAITING_APPROVAL", "approve")
        drift = _drift(root, phase, entry)
        if drift:
            raise RuleViolation(
                "files changed since submit (hash drift)",
                f"Reject the phase, restore or resubmit the files: {', '.join(drift)}",
            )
        index = manifest["phases"].index(phase)
        entry["status"] = "APPROVED"
        entry["approvedBy"] = by
        entry["approvedAt"] = datetime.now(timezone.utc).isoformat()
        entry["rejectionReason"] = None
        if index + 1 < len(manifest["phases"]):
            state["phases"][manifest["phases"][index + 1]["id"]]["status"] = "ACTIVE"
        save_state(root, state)
        return state

    return _guarded(root, by or DEFAULT_ACTOR, "approve", phase_id, operation)


def reject(
    root: Path,
    phase_id: str,
    reason: str,
    confirmed: bool | None = None,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    """Return a submitted phase to active after human rejection."""
    def operation() -> dict[str, Any]:
        _confirm(root, phase_id, confirmed)
        manifest = load_manifest(root)
        _get(manifest, phase_id)
        state = load_state(root, manifest)
        entry = state["phases"][phase_id]
        _require_status(entry, "AWAITING_APPROVAL", "reject")
        entry["status"] = "ACTIVE"
        entry["hashes"] = {}
        entry["approvedBy"] = None
        entry["approvedAt"] = None
        entry["rejectionReason"] = reason
        save_state(root, state)
        return state

    return _guarded(root, actor, "reject", phase_id, operation)


def reopen(
    root: Path,
    phase_id: str,
    reason: str,
    confirmed: bool | None = None,
    actor: str = DEFAULT_ACTOR,
) -> dict[str, Any]:
    """Reopen an approved phase only after later outputs are removed."""
    def operation() -> dict[str, Any]:
        _confirm(root, phase_id, confirmed)
        manifest = load_manifest(root)
        phase = _get(manifest, phase_id)
        state = load_state(root, manifest)
        entry = state["phases"][phase_id]
        _require_status(entry, "APPROVED", "reopen")
        index = manifest["phases"].index(phase)
        later_files = [
            path
            for later in manifest["phases"][index + 1 :]
            for path in later["owns"]
            if (root / path).exists()
        ]
        if later_files:
            raise RuleViolation(
                "later phases still have files on disk",
                f"Move or remove later outputs first: {', '.join(later_files)}",
            )
        for later in manifest["phases"][index + 1 :]:
            state["phases"][later["id"]] = {
                "status": "LOCKED",
                "hashes": {},
                "approvedBy": None,
                "approvedAt": None,
                "rejectionReason": None,
            }
        entry["status"] = "ACTIVE"
        entry["hashes"] = {}
        entry["approvedBy"] = None
        entry["approvedAt"] = None
        entry["rejectionReason"] = reason
        save_state(root, state)
        return state

    return _guarded(root, actor, "reopen", phase_id, operation)


def check(root: Path) -> list[str]:
    """Return consistency errors, or an empty list when checks pass."""
    manifest = load_manifest(root)
    state = load_state(root, manifest)
    failures: list[str] = []
    for phase in manifest["phases"]:
        entry = state["phases"][phase["id"]]
        existing = [path for path in phase["owns"] if (root / path).exists()]
        if entry["status"] == "LOCKED" and existing:
            failures.append(f"LOCKED phase {phase['id']} owns existing files: {', '.join(existing)}")
        if entry["status"] == "APPROVED":
            drift = _drift(root, phase, entry)
            if drift:
                failures.append(f"APPROVED phase {phase['id']} has hash drift: {', '.join(drift)}")
    for protected in manifest["protected"]:
        if not (root / protected).exists():
            failures.append(f"protected path missing: {protected}")
    return failures


def status_text(root: Path, as_json: bool = False) -> str:
    """Render state and derived phase information."""
    manifest = load_manifest(root)
    state = load_state(root, manifest)
    derived = derive(manifest, state)
    if as_json:
        return json.dumps({"phases": state["phases"], **derived}, indent=2)
    lines = ["# PHASE STATUS APPROVED BY"]
    for index, phase in enumerate(manifest["phases"], start=1):
        entry = state["phases"][phase["id"]]
        lines.append(
            f"{index} {phase['id']} {entry['status']} {entry['approvedBy'] or '-'}"
        )
    lines.extend(
        [
            f"currentPhase: {derived['currentPhase'] or 'None'}",
            f"previousPhase: {derived['previousPhase'] or 'None'}",
            f"nextPhase: {derived['nextPhase'] or 'None'}",
            f"phaseStatus: {derived['phaseStatus']}",
            f"approvalStatus: {derived['approvalStatus']}",
            f"requiredArtifacts: {', '.join(derived['requiredArtifacts']) or 'None'}",
            f"allowedFiles: {', '.join(derived['allowedFiles']) or 'None'}",
        ]
    )
    return "\n".join(lines)


def next_step(root: Path) -> str:
    """Describe the next action without changing pipeline state."""
    manifest = load_manifest(root)
    state = load_state(root, manifest)
    derived = derive(manifest, state)
    if derived["phaseStatus"] == "COMPLETE":
        return "Pipeline complete: every phase is APPROVED."
    phase_id = derived["currentPhase"]
    phase = _get(manifest, phase_id)
    if derived["phaseStatus"] == "AWAITING_APPROVAL":
        return f"Awaiting human approval. Run: python orchestrator.py approve {phase_id} --by <your-name>"
    artifacts = ", ".join(phase["owns"])
    return "\n".join(
        [
            f"ACTIVE phase: {phase_id}",
            f"Run prompt: /{'pr' if phase_id == 'pr' else 'run'} ({phase['prompt']})",
            f"Must produce: {artifacts}",
            f"Then run: python orchestrator.py submit {phase_id}",
        ]
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Human-gated SDLC pipeline orchestrator")
    subparsers = parser.add_subparsers(dest="command", required=True)
    status_parser = subparsers.add_parser("status")
    status_parser.add_argument("--json", action="store_true", dest="as_json")
    subparsers.add_parser("next")
    for command in ("submit",):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("phase")
    approve_parser = subparsers.add_parser("approve")
    approve_parser.add_argument("phase")
    approve_parser.add_argument("--by", required=True)
    for command in ("reject", "reopen"):
        command_parser = subparsers.add_parser(command)
        command_parser.add_argument("phase")
        command_parser.add_argument("--reason", required=True)
    subparsers.add_parser("check")
    return parser


def main(argv: list[str] | None = None, root: Path | None = None) -> int:
    """Run the CLI, returning a process exit code."""
    root = root or Path(__file__).resolve().parent
    actor = DEFAULT_ACTOR
    try:
        args = _parser().parse_args(argv)
        if not _state_path(root).exists():
            init_state(root)
        if args.command == "status":
            print(status_text(root, args.as_json))
        elif args.command == "next":
            print(next_step(root))
        elif args.command == "submit":
            submit(root, args.phase, actor)
            print(
                f"Awaiting human approval. Run: python orchestrator.py approve {args.phase} --by <your-name>"
            )
        elif args.command == "approve":
            approve(root, args.phase, args.by)
            print(f"Approved phase: {args.phase}")
        elif args.command == "reject":
            reject(root, args.phase, args.reason, actor=actor)
            print(f"Rejected phase: {args.phase}")
        elif args.command == "reopen":
            reopen(root, args.phase, args.reason, actor=actor)
            print(f"Reopened phase: {args.phase}")
        elif args.command == "check":
            failures = check(root)
            if failures:
                raise RuleViolation("pipeline check failed", "; ".join(failures))
            print("all checks passed")
        return 0
    except RuleViolation as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except UsageError as exc:
        print(f"USAGE ERROR: {exc}. Check the command syntax and run --help.", file=sys.stderr)
        return 2
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 2


if __name__ == "__main__":
    raise SystemExit(main())