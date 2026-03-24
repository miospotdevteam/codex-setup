#!/usr/bin/env python3
"""
Plan utilities for Codex persistent plans.

Provides read/update operations on plan.json (immutable definition) and
progress.json (mutable execution state). After Orbit approval, plan.json
is treated as the plan definition; runtime mutations go to progress.json.

read_plan() returns a merged view (plan + progress) for backwards
compatibility. Legacy plans without progress.json still work — mutable
fields are read from plan.json as a fallback.

CLI usage:
    python3 plan-utils.py status <plan.json>
    python3 plan-utils.py next-step <plan.json>
    python3 plan-utils.py update-step <plan.json> <step_id> <new_status>
    python3 plan-utils.py update-progress <plan.json> <step_id> <progress_index> <new_status>
    python3 plan-utils.py set-result <plan.json> <step_id> <result_text>
    python3 plan-utils.py add-summary <plan.json> <summary_text>
    python3 plan-utils.py add-deviation <plan.json> <deviation_text>
    python3 plan-utils.py init-progress <plan.json>
    python3 plan-utils.py complete-plan <plan.json>
    python3 plan-utils.py is-fresh <plan.json>
    python3 plan-utils.py is-complete <plan.json>
    python3 plan-utils.py find-active <project_root>
"""

from __future__ import annotations

import copy
import json
import os
import shutil
import sys


def progress_path_for(plan_path: str) -> str:
    """Derive the progress.json path from a plan.json path."""
    return os.path.join(os.path.dirname(os.path.abspath(plan_path)), "progress.json")


def read_progress(plan_path: str) -> dict:
    """Read progress.json sibling. Returns empty dict if missing."""
    path = progress_path_for(plan_path)
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def write_progress(plan_path: str, progress: dict) -> None:
    """Write progress dict to progress.json sibling."""
    path = progress_path_for(plan_path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(progress, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def extract_progress(plan: dict) -> dict:
    """Extract mutable fields from a plan dict into progress format."""
    progress: dict[str, object] = {"steps": {}}

    for step in plan.get("steps", []):
        step_id = str(step["id"])
        step_prog: dict[str, object] = {
            "status": step.get("status", "pending"),
        }
        if "result" in step:
            step_prog["result"] = step["result"]
        if step.get("progress"):
            step_prog["progress"] = [
                {"status": item.get("status", "pending")}
                for item in step["progress"]
            ]
        sub_plan = step.get("subPlan")
        if sub_plan and sub_plan.get("groups"):
            groups: dict[str, dict[str, object]] = {}
            for index, group in enumerate(sub_plan["groups"]):
                group_prog: dict[str, object] = {}
                if "status" in group:
                    group_prog["status"] = group["status"]
                if "notes" in group:
                    group_prog["notes"] = group["notes"]
                if group_prog:
                    groups[str(index)] = group_prog
            if groups:
                step_prog["groups"] = groups
        progress["steps"][step_id] = step_prog

    if plan.get("completedSummary"):
        progress["completedSummary"] = list(plan["completedSummary"])
    if plan.get("deviations"):
        progress["deviations"] = list(plan["deviations"])

    return progress


def init_progress(plan: dict) -> dict:
    """Create a fresh progress.json for a new plan (all steps pending)."""
    progress: dict[str, object] = {"steps": {}}
    for step in plan.get("steps", []):
        step_id = str(step["id"])
        step_prog: dict[str, object] = {"status": "pending"}
        if step.get("progress"):
            step_prog["progress"] = [{"status": "pending"} for _ in step["progress"]]
        sub_plan = step.get("subPlan")
        if sub_plan and sub_plan.get("groups"):
            groups: dict[str, dict[str, str]] = {}
            for index, _group in enumerate(sub_plan["groups"]):
                groups[str(index)] = {"status": "pending"}
            step_prog["groups"] = groups
        progress["steps"][step_id] = step_prog
    return progress


def _ensure_progress(plan_path: str) -> dict:
    """Return progress dict, migrating from plan.json on first call."""
    progress_path = progress_path_for(plan_path)
    if os.path.isfile(progress_path):
        with open(progress_path, encoding="utf-8") as handle:
            return json.load(handle)

    with open(plan_path, encoding="utf-8") as handle:
        plan = json.load(handle)
    return extract_progress(plan)


def merge_plan_progress(plan: dict, progress: dict) -> dict:
    """Merge progress into a copy of plan, returning the merged view."""
    merged = copy.deepcopy(plan)

    steps_progress = progress.get("steps", {})
    for step in merged.get("steps", []):
        step_id = str(step["id"])
        step_progress = steps_progress.get(step_id, {})
        if "status" in step_progress:
            step["status"] = step_progress["status"]
        if "result" in step_progress:
            step["result"] = step_progress["result"]
        if "progress" in step_progress and step.get("progress"):
            for index, progress_item in enumerate(step_progress["progress"]):
                if index < len(step["progress"]):
                    step["progress"][index]["status"] = progress_item.get(
                        "status",
                        step["progress"][index].get("status", "pending"),
                    )
        if "groups" in step_progress:
            sub_plan = step.get("subPlan")
            if sub_plan and sub_plan.get("groups"):
                for index_str, group_progress in step_progress["groups"].items():
                    index = int(index_str)
                    if 0 <= index < len(sub_plan["groups"]):
                        if "status" in group_progress:
                            sub_plan["groups"][index]["status"] = group_progress["status"]
                        if "notes" in group_progress:
                            sub_plan["groups"][index]["notes"] = group_progress["notes"]

    if "completedSummary" in progress:
        merged["completedSummary"] = list(progress["completedSummary"])
    if "deviations" in progress:
        merged["deviations"] = list(progress["deviations"])

    return merged


def _plan_dir_mtime(plan_dir: str) -> float:
    """Get the most recent mtime across plan.json and progress.json."""
    plan_path = os.path.join(plan_dir, "plan.json")
    progress_path = os.path.join(plan_dir, "progress.json")
    mtime = 0.0
    if os.path.isfile(plan_path):
        mtime = os.path.getmtime(plan_path)
    if os.path.isfile(progress_path):
        mtime = max(mtime, os.path.getmtime(progress_path))
    return mtime


def read_plan(plan_path: str) -> dict:
    """Read plan.json and merge with progress.json if it exists."""
    with open(plan_path, encoding="utf-8") as handle:
        plan = json.load(handle)
    progress = read_progress(plan_path)
    if progress:
        return merge_plan_progress(plan, progress)
    return plan


def read_plan_definition(plan_path: str) -> dict:
    """Read only the immutable plan definition (plan.json)."""
    with open(plan_path, encoding="utf-8") as handle:
        return json.load(handle)


def write_plan(plan_path: str, plan: dict) -> None:
    """Write a plan dict back to plan.json with consistent formatting."""
    with open(plan_path, "w", encoding="utf-8") as handle:
        json.dump(plan, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def get_step(plan: dict, step_id: int):
    """Get a specific step by ID. Returns None if not found."""
    for step in plan.get("steps", []):
        if step["id"] == step_id:
            return step
    return None


def count_by_status(plan: dict) -> dict:
    """Count steps by status. Returns dict of status -> count."""
    counts = {"pending": 0, "in_progress": 0, "done": 0, "blocked": 0}
    for step in plan.get("steps", []):
        status = step.get("status", "pending")
        counts[status] = counts.get(status, 0) + 1
    return counts


def get_next_step(plan: dict):
    """Find the next step to work on (in_progress first, then pending)."""
    for step in plan.get("steps", []):
        if step["status"] == "in_progress":
            return step
    for step in plan.get("steps", []):
        if step["status"] == "pending":
            return step
    return None


def is_fresh(plan: dict) -> bool:
    """Check if plan is fresh (all steps pending, none done/in_progress)."""
    for step in plan.get("steps", []):
        if step["status"] != "pending":
            return False
    return len(plan.get("steps", [])) > 0


def is_complete(plan: dict) -> bool:
    """Check if all steps are done."""
    steps = plan.get("steps", [])
    if not steps:
        return False
    return all(step["status"] == "done" for step in steps)


def get_plan_dirs(plan_path: str) -> tuple[str, str, str]:
    """Resolve the plan directory plus active/completed siblings."""
    plan_dir = os.path.dirname(os.path.abspath(plan_path))
    active_dir = os.path.dirname(plan_dir)
    completed_dir = os.path.join(os.path.dirname(active_dir), "completed")
    return plan_dir, active_dir, completed_dir


def _update_step_in_progress(plan_path: str, step_id: int, updater) -> dict:
    """Read progress, apply updater to a step's entry, write back."""
    progress = _ensure_progress(plan_path)
    step_key = str(step_id)
    if step_key not in progress.get("steps", {}):
        progress.setdefault("steps", {})[step_key] = {"status": "pending"}
    updater(progress["steps"][step_key])
    write_progress(plan_path, progress)
    return progress


def complete_plan(plan_path: str) -> bool:
    """Mark a fully done active plan completed and move it to completed/."""
    plan_dir, active_dir, completed_dir = get_plan_dirs(plan_path)
    if os.path.basename(active_dir) != "active":
        print(
            f"Error: complete-plan only works on plans inside active/. Got: {plan_path}",
            file=sys.stderr,
        )
        return False

    merged_plan = read_plan(plan_path)
    if not is_complete(merged_plan):
        print("Error: cannot complete a plan with unfinished steps", file=sys.stderr)
        return False

    if any(step.get("status") == "blocked" for step in merged_plan.get("steps", [])):
        print("Error: cannot complete a plan with blocked steps", file=sys.stderr)
        return False

    if merged_plan.get("blocked"):
        print("Error: cannot complete a plan with blocked items listed", file=sys.stderr)
        return False

    destination = os.path.join(completed_dir, os.path.basename(plan_dir))
    if os.path.exists(destination):
        print(
            f"Error: destination already exists in completed/: {destination}",
            file=sys.stderr,
        )
        return False

    plan_definition = read_plan_definition(plan_path)
    plan_definition["status"] = "completed"
    write_plan(plan_path, plan_definition)

    os.makedirs(completed_dir, exist_ok=True)
    shutil.move(plan_dir, destination)
    print(destination)
    return True


def update_step_status(plan_path: str, step_id: int, new_status: str) -> bool:
    """Update a step's status and write to progress.json."""
    plan = read_plan(plan_path)
    if get_step(plan, step_id) is None:
        print(f"Error: step {step_id} not found", file=sys.stderr)
        return False
    _update_step_in_progress(
        plan_path,
        step_id,
        lambda step_progress: step_progress.__setitem__("status", new_status),
    )
    return True


def update_progress_item(plan_path: str, step_id: int, progress_index: int, new_status: str) -> bool:
    """Update a progress item's status within a step. Writes to progress.json."""
    plan = read_plan(plan_path)
    step = get_step(plan, step_id)
    if step is None:
        print(f"Error: step {step_id} not found", file=sys.stderr)
        return False
    progress_items = step.get("progress", [])
    if progress_index < 0 or progress_index >= len(progress_items):
        print(f"Error: progress index {progress_index} out of range", file=sys.stderr)
        return False

    def _update(step_progress: dict) -> None:
        step_progress.setdefault("progress", [])
        while len(step_progress["progress"]) <= progress_index:
            step_progress["progress"].append({"status": "pending"})
        step_progress["progress"][progress_index]["status"] = new_status

    _update_step_in_progress(plan_path, step_id, _update)
    return True


def set_result(plan_path: str, step_id: int, result_text: str) -> bool:
    """Set the result field on a step. Writes to progress.json."""
    plan = read_plan(plan_path)
    if get_step(plan, step_id) is None:
        print(f"Error: step {step_id} not found", file=sys.stderr)
        return False
    _update_step_in_progress(
        plan_path,
        step_id,
        lambda step_progress: step_progress.__setitem__("result", result_text),
    )
    return True


def add_summary(plan_path: str, text: str) -> bool:
    """Append to the completedSummary array in progress.json."""
    progress = _ensure_progress(plan_path)
    progress.setdefault("completedSummary", []).append(text)
    write_progress(plan_path, progress)
    return True


def add_deviation(plan_path: str, text: str) -> bool:
    """Append to the deviations array in progress.json."""
    progress = _ensure_progress(plan_path)
    progress.setdefault("deviations", []).append(text)
    write_progress(plan_path, progress)
    return True


def find_active_plan(project_root: str):
    """Find the most recently modified active plan, considering progress.json."""
    active_dir = os.path.join(project_root, ".temp", "plan-mode", "active")
    if not os.path.isdir(active_dir):
        return None

    latest_path = None
    latest_mtime = 0.0
    for entry in os.listdir(active_dir):
        plan_dir = os.path.join(active_dir, entry)
        plan_path = os.path.join(plan_dir, "plan.json")
        if os.path.isfile(plan_path):
            mtime = _plan_dir_mtime(plan_dir)
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_path = plan_path
    return latest_path


def format_status(plan: dict) -> str:
    """Format a human-readable status summary."""
    counts = count_by_status(plan)
    parts = []
    if counts["done"]:
        parts.append(f"{counts['done']} done")
    if counts["in_progress"]:
        parts.append(f"{counts['in_progress']} active")
    if counts["pending"]:
        parts.append(f"{counts['pending']} pending")
    if counts["blocked"]:
        parts.append(f"{counts['blocked']} blocked")
    return " | ".join(parts) if parts else "empty"


def cli_status(plan_path: str) -> None:
    """Print plan status summary."""
    plan = read_plan(plan_path)
    counts = count_by_status(plan)
    print(json.dumps({
        "name": plan.get("name", "unknown"),
        "title": plan.get("title", "unknown"),
        "status": plan.get("status", "unknown"),
        "counts": counts,
        "summary": format_status(plan),
        "total_steps": len(plan.get("steps", [])),
    }))


def cli_next_step(plan_path: str) -> None:
    """Print the next step to work on."""
    plan = read_plan(plan_path)
    step = get_next_step(plan)
    if step:
        print(json.dumps({
            "id": step["id"],
            "title": step["title"],
            "status": step["status"],
            "description": step.get("description", ""),
        }))
    else:
        print(json.dumps({"id": None, "title": None, "message": "No pending steps"}))


def main() -> None:
    if len(sys.argv) < 3:
        print("Usage: plan-utils.py <command> <plan.json|project_root> [args...]", file=sys.stderr)
        sys.exit(1)

    command = sys.argv[1]

    if command == "find-active":
        project_root = sys.argv[2]
        result = find_active_plan(project_root)
        print(result or "")
        return

    plan_path = sys.argv[2]

    if command == "status":
        cli_status(plan_path)
    elif command == "next-step":
        cli_next_step(plan_path)
    elif command == "update-step":
        if len(sys.argv) < 5:
            print("Usage: plan-utils.py update-step <plan.json> <step_id> <status>", file=sys.stderr)
            sys.exit(1)
        if not update_step_status(plan_path, int(sys.argv[3]), sys.argv[4]):
            sys.exit(1)
    elif command == "update-progress":
        if len(sys.argv) < 6:
            print("Usage: plan-utils.py update-progress <plan.json> <step_id> <index> <status>", file=sys.stderr)
            sys.exit(1)
        if not update_progress_item(plan_path, int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]):
            sys.exit(1)
    elif command == "set-result":
        if len(sys.argv) < 5:
            print("Usage: plan-utils.py set-result <plan.json> <step_id> <result_text>", file=sys.stderr)
            sys.exit(1)
        if not set_result(plan_path, int(sys.argv[3]), sys.argv[4]):
            sys.exit(1)
    elif command == "add-summary":
        if len(sys.argv) < 4:
            print("Usage: plan-utils.py add-summary <plan.json> <text>", file=sys.stderr)
            sys.exit(1)
        add_summary(plan_path, sys.argv[3])
    elif command == "add-deviation":
        if len(sys.argv) < 4:
            print("Usage: plan-utils.py add-deviation <plan.json> <text>", file=sys.stderr)
            sys.exit(1)
        add_deviation(plan_path, sys.argv[3])
    elif command == "init-progress":
        plan = read_plan_definition(plan_path)
        write_progress(plan_path, init_progress(plan))
    elif command == "complete-plan":
        if not complete_plan(plan_path):
            sys.exit(1)
    elif command == "is-fresh":
        print("true" if is_fresh(read_plan(plan_path)) else "false")
    elif command == "is-complete":
        print("true" if is_complete(read_plan(plan_path)) else "false")
    else:
        print(f"Unknown command: {command}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
