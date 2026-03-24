#!/usr/bin/env python3

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "codex-skills" / "lbyl-conductor" / "scripts"

import sys

sys.path.insert(0, str(SCRIPTS_DIR))
import resolve_executor  # noqa: E402


class ResolveExecutorTests(unittest.TestCase):
    def write_plan(self, payload: dict) -> Path:
        self.temp_dir = tempfile.TemporaryDirectory()
        plan_path = Path(self.temp_dir.name) / "plan.json"
        plan_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return plan_path

    def tearDown(self) -> None:
        if hasattr(self, "temp_dir"):
            self.temp_dir.cleanup()

    def base_plan(self, step: dict) -> dict:
        return {
            "name": "demo",
            "title": "Demo",
            "context": "fixture",
            "status": "active",
            "requiredSkills": [],
            "disciplines": [],
            "review": {
                "status": "approved",
                "reviewedVia": "orbit",
                "approvedAt": "2026-03-24T00:00:00Z",
                "skipReason": None,
            },
            "discovery": {
                "scope": "fixture",
                "entryPoints": "fixture",
                "consumers": "fixture",
                "existingPatterns": "fixture",
                "testInfrastructure": "fixture",
                "conventions": "fixture",
                "blastRadius": "fixture",
                "confidence": "high",
            },
            "steps": [step],
            "blocked": [],
            "completedSummary": [],
            "deviations": [],
        }

    def test_defaults_to_codex_for_non_visual_work(self) -> None:
        plan_path = self.write_plan(
            self.base_plan(
                {
                    "id": 1,
                    "title": "Update guard behavior",
                    "status": "pending",
                    "skill": "none",
                    "claudeVerify": True,
                    "simplify": False,
                    "files": ["codex-guard/guard.py"],
                    "description": "Tighten guard validation.",
                    "acceptanceCriteria": "Tests pass.",
                    "progress": [],
                    "result": None,
                }
            )
        )
        result = resolve_executor.resolve_plan(plan_path)
        self.assertEqual(result["updated"], 1)
        step = json.loads(plan_path.read_text())["steps"][0]
        self.assertEqual(step["executor"], "codex")
        self.assertEqual(step["routingHint"], "auto")

    def test_routes_visual_frontend_steps_to_claude(self) -> None:
        plan_path = self.write_plan(
            self.base_plan(
                {
                    "id": 1,
                    "title": "Refresh dashboard layout",
                    "status": "pending",
                    "skill": "lbyl-frontend-design",
                    "claudeVerify": True,
                    "simplify": False,
                    "files": ["src/dashboard/page.tsx", "src/dashboard/styles.css"],
                    "description": "Adjust layout, spacing, and color for the dashboard.",
                    "acceptanceCriteria": "Rendered dashboard matches the new design.",
                    "progress": [],
                    "result": None,
                }
            )
        )
        resolve_executor.resolve_plan(plan_path)
        step = json.loads(plan_path.read_text())["steps"][0]
        self.assertEqual(step["executor"], "claude")
        self.assertIn("visual", step["routingReason"])

    def test_explicit_routing_hint_overrides_heuristics(self) -> None:
        plan_path = self.write_plan(
            self.base_plan(
                {
                    "id": 1,
                    "title": "Adjust copy",
                    "status": "pending",
                    "skill": "none",
                    "routingHint": "codex",
                    "claudeVerify": True,
                    "simplify": False,
                    "files": ["src/app/page.tsx"],
                    "description": "Update copy on the page.",
                    "acceptanceCriteria": "New copy is present.",
                    "progress": [],
                    "result": None,
                }
            )
        )
        resolve_executor.resolve_plan(plan_path)
        step = json.loads(plan_path.read_text())["steps"][0]
        self.assertEqual(step["executor"], "codex")
        self.assertIn("routingHint", step["routingReason"])


if __name__ == "__main__":
    unittest.main()
