#!/usr/bin/env python3
"""Codex-native filesystem guard for LBYL workflows."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_STEP_FIELDS = {
    "id",
    "title",
    "status",
    "files",
    "acceptanceCriteria",
    "progress",
    "executor",
    "claudeVerify",
    "routingHint",
    "routingReason",
    "routingResolvedAt",
    "routingResolvedBy",
}
VALID_REVIEW_STATES = {"approved", "skipped"}
VALID_EXECUTORS = {"codex", "claude"}
PASS_VERDICT_RE = re.compile(
    r"(?is)(?:claude|claude-bridge).*?\bPASS\b|\bPASS\b.*?(?:claude|claude-bridge)"
)
CODEX_SETUP_ROOT = Path(__file__).resolve().parents[1]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def repo_root_from(start: Path | None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / ".git").exists():
            return candidate
    return current


def state_path(project_root: Path, name: str) -> Path:
    return project_root / name


def audit_log_path(project_root: Path) -> Path:
    return state_path(project_root, ".guard-audit.log")


def validation_path(project_root: Path) -> Path:
    return state_path(project_root, ".guard-validated")


def unlock_state_path(project_root: Path) -> Path:
    return state_path(project_root, ".guard-state")


def load_plan_utils():
    scripts_dir = CODEX_SETUP_ROOT / "codex-skills" / "lbyl-conductor" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    import plan_utils  # type: ignore

    return plan_utils


def load_resolve_executor():
    scripts_dir = CODEX_SETUP_ROOT / "codex-skills" / "lbyl-conductor" / "scripts"
    sys.path.insert(0, str(scripts_dir))
    import resolve_executor  # type: ignore

    return resolve_executor


def active_plan_paths(project_root: Path) -> list[Path]:
    active_dir = project_root / ".temp" / "plan-mode" / "active"
    if not active_dir.is_dir():
        return []
    plans = sorted(
        (
            path
            for path in active_dir.glob("*/plan.json")
            if path.is_file()
        ),
        key=plan_state_mtime,
        reverse=True,
    )
    return plans


def find_active_plan(project_root: Path, explicit_plan: str | None = None) -> Path:
    if explicit_plan:
        plan_path = Path(explicit_plan).resolve()
        if plan_path.is_dir():
            plan_path = plan_path / "plan.json"
        if not plan_path.is_file():
            raise GuardError(f"Plan not found: {plan_path}")
        return plan_path

    plans = active_plan_paths(project_root)
    if not plans:
        raise GuardError("No active plan found in .temp/plan-mode/active/")
    return plans[0]


def git_tracked_files(project_root: Path) -> list[Path]:
    proc = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=project_root,
        check=True,
        capture_output=True,
    )
    entries = [entry for entry in proc.stdout.decode("utf-8").split("\0") if entry]
    return [project_root / entry for entry in entries]


def make_read_only(path: Path) -> None:
    try:
        mode = path.stat().st_mode
    except FileNotFoundError:
        return
    path.chmod(mode & ~(stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH))


def make_user_writable(path: Path) -> None:
    try:
        mode = path.stat().st_mode
    except FileNotFoundError:
        return
    path.chmod(mode | stat.S_IWUSR)


def append_audit(project_root: Path, event: str, **data: Any) -> None:
    payload = {"event": event, "ts": utc_now(), **data}
    with audit_log_path(project_root).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_unlock_state(project_root: Path) -> dict[str, Any] | None:
    path = unlock_state_path(project_root)
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_unlock_state(project_root: Path, payload: dict[str, Any]) -> None:
    with unlock_state_path(project_root).open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def clear_unlock_state(project_root: Path) -> None:
    unlock_state_path(project_root).unlink(missing_ok=True)


def read_validation(project_root: Path) -> dict[str, Any] | None:
    path = validation_path(project_root)
    if not path.is_file():
        return None
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_validation(project_root: Path, plan_path: Path) -> None:
    payload = {"plan_path": str(plan_path), "validated_at": utc_now()}
    with validation_path(project_root).open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def clear_validation(project_root: Path) -> None:
    validation_path(project_root).unlink(missing_ok=True)


def step_files(project_root: Path, step: dict[str, Any]) -> list[Path]:
    return [project_root / relative for relative in step.get("files", [])]


def list_extra_writable_files(project_root: Path, allowed: set[Path]) -> list[str]:
    extras: list[str] = []
    for file_path in git_tracked_files(project_root):
        if not file_path.exists():
            continue
        mode = file_path.stat().st_mode
        if mode & stat.S_IWUSR and file_path.resolve() not in allowed:
            extras.append(str(file_path.relative_to(project_root)))
    return sorted(extras)


def ensure_result_present(step: dict[str, Any]) -> str:
    result = step.get("result")
    if not isinstance(result, str) or not result.strip():
        raise GuardError(
            f"Step {step['id']} is missing a result. Record what was implemented before completion."
        )
    return result


def ensure_pass_verdict(step: dict[str, Any]) -> None:
    result = ensure_result_present(step)
    if step.get("claudeVerify") and not PASS_VERDICT_RE.search(result):
        raise GuardError(
            f"Step {step['id']} has claudeVerify: true but no Claude PASS verdict in result. "
            "Run claude-bridge verification and record a PASS verdict before completing."
        )


def latest_mtime(paths: list[Path]) -> float:
    mtimes = [path.stat().st_mtime for path in paths if path.exists()]
    return max(mtimes) if mtimes else 0.0


def plan_state_mtime(plan_path: Path) -> float:
    plan_utils = load_plan_utils()
    mtimes = [plan_path.stat().st_mtime]
    progress_path = Path(plan_utils.progress_path_for(str(plan_path)))
    if progress_path.exists():
        mtimes.append(progress_path.stat().st_mtime)
    return max(mtimes)


def format_resume(step: dict[str, Any]) -> str:
    return (
        f"Resumed step {step['id']}: {step['title']} — "
        f"{len(step.get('files', []))} file(s) unlocked"
    )


def format_begin(step: dict[str, Any]) -> str:
    return f"Step {step['id']} unlocked: {len(step.get('files', []))} file(s) writable"


def format_claude_route(step: dict[str, Any], *, command: str) -> str:
    return (
        f"Step {step['id']} is routed to Claude and cannot be started with {command}. "
        "Use claude-bridge frontend_implement to continue."
    )


class GuardError(RuntimeError):
    pass


def read_plan(plan_path: Path) -> tuple[Any, dict[str, Any]]:
    plan_utils = load_plan_utils()
    return plan_utils, plan_utils.read_plan(str(plan_path))


def find_step(plan: dict[str, Any], step_id: int) -> dict[str, Any]:
    for step in plan.get("steps", []):
        if step.get("id") == step_id:
            return step
    raise GuardError(f"Step {step_id} not found in {plan.get('name', 'plan')}")


def validate_plan_definition(plan: dict[str, Any]) -> None:
    review = plan.get("review")
    if not isinstance(review, dict):
        raise GuardError("Active plan is missing review metadata.")

    review_status = review.get("status")
    if review_status not in VALID_REVIEW_STATES:
        raise GuardError(
            "Plan review must be approved or explicitly skipped before execution."
        )
    if review_status == "skipped" and not str(review.get("skipReason") or "").strip():
        raise GuardError("review.skipReason is required when review.status is skipped.")

    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        raise GuardError("Active plan has no steps.")

    for index, step in enumerate(steps, start=1):
        missing = sorted(field for field in REQUIRED_STEP_FIELDS if field not in step)
        if missing:
            raise GuardError(f"Step {index} is missing required fields: {', '.join(missing)}")
        executor = step.get("executor")
        if executor not in VALID_EXECUTORS:
            raise GuardError(
                f"Step {index} has invalid executor {executor!r}. "
                f"Expected one of: {', '.join(sorted(VALID_EXECUTORS))}"
            )
        if step.get("routingResolvedBy") != "lbyl-conductor":
            raise GuardError(
                f"Step {index} routingResolvedBy must be 'lbyl-conductor', got "
                f"{step.get('routingResolvedBy')!r}."
            )


def cmd_setup(project_root: Path, args: argparse.Namespace) -> int:
    clear_validation(project_root)
    for file_path in git_tracked_files(project_root):
        make_read_only(file_path)

    clear_unlock_state(project_root)

    try:
        plan_path = find_active_plan(project_root, args.plan)
    except GuardError:
        print("All source files locked. Create a plan to begin.")
        return 0

    plan_utils, plan = read_plan(plan_path)
    current_step = plan_utils.get_next_step(plan)
    if current_step and current_step.get("status") == "in_progress":
        if current_step.get("executor") == "claude":
            append_audit(project_root, "resume_blocked_claude_executor", step=current_step["id"])
            print(format_claude_route(current_step, command="setup"))
            return 0
        files = step_files(project_root, current_step)
        for path in files:
            make_user_writable(path)
        write_unlock_state(
            project_root,
            {
                "plan_path": str(plan_path),
                "step_id": current_step["id"],
                "files": [str(path.relative_to(project_root)) for path in files if path.exists()],
                "unlocked_at": utc_now(),
            },
        )
        append_audit(project_root, "resume_step", step=current_step["id"])
        print(format_resume(current_step))
        return 0

    print("All source files locked. Create a plan to begin.")
    return 0


def cmd_validate_plan(project_root: Path, args: argparse.Namespace) -> int:
    plan_path = find_active_plan(project_root, args.plan)
    resolve_executor = load_resolve_executor()
    routing_result = resolve_executor.resolve_plan(plan_path)
    _, plan = read_plan(plan_path)
    validate_plan_definition(plan)
    write_validation(project_root, plan_path)
    append_audit(
        project_root,
        "validate_plan",
        plan=str(plan_path),
        routing_updates=routing_result.get("updated", 0),
    )
    print(f"Plan validated: {plan_path}")
    return 0


def cmd_begin_step(project_root: Path, args: argparse.Namespace) -> int:
    plan_path = find_active_plan(project_root, args.plan)
    validation = read_validation(project_root)
    if not validation or validation.get("plan_path") != str(plan_path):
        raise GuardError("validate-plan must pass before begin-step.")

    unlock_state = load_unlock_state(project_root)
    if unlock_state and unlock_state.get("step_id") != args.step_id:
        raise GuardError(
            f"Step {unlock_state['step_id']} is already unlocked. Complete it before beginning another step."
        )

    plan_utils, plan = read_plan(plan_path)
    step = find_step(plan, args.step_id)
    if step.get("status") == "done":
        raise GuardError(f"Step {args.step_id} is already done.")
    if step.get("executor") == "claude":
        raise GuardError(format_claude_route(step, command="begin-step"))

    files = step_files(project_root, step)
    for path in files:
        make_user_writable(path)

    write_unlock_state(
        project_root,
        {
            "plan_path": str(plan_path),
            "step_id": args.step_id,
            "files": [str(path.relative_to(project_root)) for path in files if path.exists()],
            "unlocked_at": utc_now(),
        },
    )
    plan_utils.update_step_status(str(plan_path), args.step_id, "in_progress")
    append_audit(project_root, "begin_step", step=args.step_id, files=len(step.get("files", [])))
    print(format_begin(step))
    return 0


def cmd_complete_step(project_root: Path, args: argparse.Namespace) -> int:
    plan_path = find_active_plan(project_root, args.plan)
    unlock_state = load_unlock_state(project_root)
    if unlock_state and unlock_state.get("step_id") != args.step_id:
        raise GuardError(
            f"Step {unlock_state['step_id']} is currently unlocked. Complete that step first."
        )

    plan_utils, plan = read_plan(plan_path)
    step = find_step(plan, args.step_id)
    ensure_pass_verdict(step)

    files = step_files(project_root, step)
    allowed = {path.resolve() for path in files}
    extras = list_extra_writable_files(project_root, allowed)
    if extras:
        append_audit(
            project_root,
            "bypass_detected",
            step=args.step_id,
            extra_writable=extras,
        )

    for path in files:
        make_read_only(path)

    plan_utils.update_step_status(str(plan_path), args.step_id, "done")
    clear_unlock_state(project_root)
    append_audit(project_root, "complete_step", step=args.step_id, extras=extras)
    print(f"Step {args.step_id} completed and locked.")
    return 0


def cmd_checkpoint(project_root: Path, args: argparse.Namespace) -> int:
    unlock_state = load_unlock_state(project_root)
    if not unlock_state:
        raise GuardError("No unlocked step to checkpoint.")

    plan_path = Path(unlock_state["plan_path"])
    _, plan = read_plan(plan_path)
    step = find_step(plan, int(unlock_state["step_id"]))
    files = step_files(project_root, step)
    stale = latest_mtime(files) > plan_state_mtime(plan_path)
    append_audit(
        project_root,
        "checkpoint",
        step=step["id"],
        stale_plan=stale,
    )
    if stale:
        print(f"Checkpoint recorded for step {step['id']} (plan state is older than unlocked files).")
    else:
        print(f"Checkpoint recorded for step {step['id']}.")
    return 0


def cmd_status(project_root: Path, args: argparse.Namespace) -> int:
    payload: dict[str, Any] = {
        "projectRoot": str(project_root),
        "lockedFiles": 0,
        "validatedPlan": None,
        "unlocked": None,
        "lastAuditEvent": None,
    }

    try:
        payload["lockedFiles"] = len(git_tracked_files(project_root))
    except subprocess.CalledProcessError:
        payload["lockedFiles"] = 0

    validation = read_validation(project_root)
    if validation:
        payload["validatedPlan"] = validation

    unlock_state = load_unlock_state(project_root)
    if unlock_state:
        payload["unlocked"] = unlock_state

    audit_path = audit_log_path(project_root)
    if audit_path.is_file():
        lines = audit_path.read_text(encoding="utf-8").splitlines()
        if lines:
            payload["lastAuditEvent"] = json.loads(lines[-1])

    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Codex-native LBYL guard")
    parser.add_argument(
        "--project-root",
        help="Project root containing .git and .temp/plan-mode/",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("setup", "validate-plan", "checkpoint", "status"):
        sub = subparsers.add_parser(name)
        sub.add_argument("--plan", help="Explicit active plan.json path")

    begin = subparsers.add_parser("begin-step")
    begin.add_argument("step_id", type=int)
    begin.add_argument("--plan", help="Explicit active plan.json path")

    complete = subparsers.add_parser("complete-step")
    complete.add_argument("step_id", type=int)
    complete.add_argument("--plan", help="Explicit active plan.json path")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    project_root = repo_root_from(
        Path(args.project_root).resolve() if args.project_root else None
    )

    commands = {
        "setup": cmd_setup,
        "validate-plan": cmd_validate_plan,
        "begin-step": cmd_begin_step,
        "complete-step": cmd_complete_step,
        "checkpoint": cmd_checkpoint,
        "status": cmd_status,
    }

    try:
        return commands[args.command](project_root, args)
    except GuardError as exc:
        eprint(f"Guard error: {exc}")
        return 1
    except subprocess.CalledProcessError as exc:
        eprint(f"Command failed: {' '.join(exc.cmd)}")
        if exc.stderr:
            eprint(exc.stderr.decode('utf-8', errors='ignore'))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
