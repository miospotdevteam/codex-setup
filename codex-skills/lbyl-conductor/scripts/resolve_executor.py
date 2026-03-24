#!/usr/bin/env python3
"""Resolve plan step executors using conductor-owned routing rules."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


VALID_HINTS = {"auto", "codex", "claude", "visual"}
VISUAL_EXTENSIONS = {".css", ".scss", ".sass", ".less", ".html"}
PRESENTATION_EXTENSIONS = {".tsx", ".jsx", ".vue", ".svelte"}
VISUAL_KEYWORDS = {
    "layout",
    "style",
    "styling",
    "spacing",
    "typography",
    "color",
    "animation",
    "motion",
    "responsive",
    "theme",
    "token",
    "visual",
    "design",
    "rendered",
    "presentation",
    "ui polish",
}
CONDUCTOR_ID = "lbyl-conductor"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_plan(plan_path: Path) -> dict[str, Any]:
    with plan_path.open(encoding="utf-8") as handle:
        return json.load(handle)


def write_plan(plan_path: Path, plan: dict[str, Any]) -> None:
    with plan_path.open("w", encoding="utf-8") as handle:
        json.dump(plan, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def normalize_hint(step: dict[str, Any]) -> str:
    hint = str(step.get("routingHint") or "auto").strip().lower()
    if hint not in VALID_HINTS:
        raise ValueError(
            f"Step {step.get('id', '?')} has invalid routingHint {hint!r}. "
            f"Expected one of: {', '.join(sorted(VALID_HINTS))}"
        )
    return hint


def is_visual_step(step: dict[str, Any]) -> tuple[bool, str]:
    skill = str(step.get("skill") or "")
    title = str(step.get("title") or "")
    description = str(step.get("description") or "")
    acceptance = str(step.get("acceptanceCriteria") or "")
    text = " ".join((title, description, acceptance)).lower()
    files = [str(path) for path in step.get("files", [])]
    suffixes = {Path(path).suffix.lower() for path in files}

    if "frontend-design" in skill or "immersive-frontend" in skill:
        return True, f"skill {skill!r} is explicitly visual"

    if suffixes & VISUAL_EXTENSIONS:
        return True, "step touches direct presentation assets such as CSS or HTML"

    if suffixes & PRESENTATION_EXTENSIONS:
        for keyword in VISUAL_KEYWORDS:
            if keyword in text:
                return True, f"presentation files plus visual keyword {keyword!r}"

    return False, "default Codex bias for non-visual engineering work"


def route_step(step: dict[str, Any]) -> tuple[str, str]:
    hint = normalize_hint(step)
    if hint == "codex":
        return "codex", "routingHint explicitly requested Codex ownership"
    if hint in {"claude", "visual"}:
        return "claude", f"routingHint {hint!r} explicitly requested Claude ownership"

    visual, reason = is_visual_step(step)
    if visual:
        return "claude", f"auto-routed to Claude because {reason}"
    return "codex", f"auto-routed to Codex because {reason}"


def resolve_step(step: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    step = dict(step)
    step["routingHint"] = normalize_hint(step)
    executor, reason = route_step(step)

    changed = False
    if step.get("executor") != executor:
        step["executor"] = executor
        changed = True
    if step.get("routingReason") != reason:
        step["routingReason"] = reason
        changed = True
    if step.get("routingResolvedBy") != CONDUCTOR_ID:
        step["routingResolvedBy"] = CONDUCTOR_ID
        changed = True
    if not step.get("routingResolvedAt") or changed:
        step["routingResolvedAt"] = utc_now()
        changed = True

    return step, changed


def resolve_plan(plan_path: Path, *, step_id: int | None = None) -> dict[str, Any]:
    plan = read_plan(plan_path)
    updated = 0
    routed: list[dict[str, Any]] = []

    new_steps = []
    for step in plan.get("steps", []):
        if step_id is not None and step.get("id") != step_id:
            new_steps.append(step)
            continue
        resolved_step, changed = resolve_step(step)
        if changed:
            updated += 1
        routed.append(
            {
                "id": resolved_step.get("id"),
                "executor": resolved_step.get("executor"),
                "routingHint": resolved_step.get("routingHint"),
                "routingReason": resolved_step.get("routingReason"),
            }
        )
        new_steps.append(resolved_step)

    plan["steps"] = new_steps
    if updated:
        write_plan(plan_path, plan)

    return {
        "plan": str(plan_path),
        "updated": updated,
        "steps": routed,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Resolve conductor-owned executor routing")
    parser.add_argument("plan", help="Path to plan.json")
    parser.add_argument("--step", type=int, help="Resolve only one step")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = resolve_plan(Path(args.plan).resolve(), step_id=args.step)
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
