#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PLAN_UTILS_PATH = REPO_ROOT / "codex-skills" / "lbyl-conductor" / "scripts" / "plan_utils.py"

spec = importlib.util.spec_from_file_location("codex_plan_utils", PLAN_UTILS_PATH)
assert spec and spec.loader
plan_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_utils)


def make_plan(
    *,
    progress: list[dict] | None = None,
    result: str | None = None,
) -> dict:
    return {
        "name": "demo",
        "title": "Demo",
        "context": "Fixture plan",
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
        "steps": [
            {
                "id": 1,
                "title": "Regression target",
                "status": "pending",
                "skill": "none",
                "routingHint": "auto",
                "executor": "codex",
                "routingReason": "fixture",
                "routingResolvedAt": "2026-03-24T00:00:00Z",
                "routingResolvedBy": "lbyl-conductor",
                "claudeVerify": True,
                "simplify": False,
                "files": ["src/a.ts"],
                "description": "Do the work",
                "acceptanceCriteria": "It works",
                "progress": progress
                or [{"task": "Do the work", "status": "pending", "files": ["src/a.ts"]}],
                "subPlan": None,
                "result": result,
            }
        ],
        "blocked": [],
        "completedSummary": [],
        "deviations": [],
    }


class CodexPlanUtilsTests(unittest.TestCase):
    def write_plan(self, temp_dir: str, plan: dict) -> Path:
        plan_path = Path(temp_dir) / "plan.json"
        plan_path.write_text(json.dumps(plan, indent=2) + "\n", encoding="utf-8")
        return plan_path

    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(PLAN_UTILS_PATH), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_mutations_write_to_progress_json_not_plan_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = self.write_plan(temp_dir, make_plan())
            plan_before = plan_path.read_text(encoding="utf-8")

            result = self.run_cli("set-result", str(plan_path), "1", "test result")

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(plan_path.read_text(encoding="utf-8"), plan_before)

            progress_path = Path(temp_dir) / "progress.json"
            self.assertTrue(progress_path.exists())
            progress = json.loads(progress_path.read_text(encoding="utf-8"))
            self.assertEqual(progress["steps"]["1"]["result"], "test result")

    def test_read_plan_merges_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_path = self.write_plan(temp_dir, make_plan())
            self.run_cli("set-result", str(plan_path), "1", "implemented")
            self.run_cli("update-step", str(plan_path), "1", "done")

            merged = plan_utils.read_plan(str(plan_path))
            self.assertEqual(merged["steps"][0]["status"], "done")
            self.assertEqual(merged["steps"][0]["result"], "implemented")
            self.assertEqual(merged["steps"][0]["title"], "Regression target")

    def test_legacy_fallback_reads_from_plan_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = make_plan(result="legacy result")
            plan["steps"][0]["status"] = "done"
            plan_path = self.write_plan(temp_dir, plan)

            merged = plan_utils.read_plan(str(plan_path))
            self.assertEqual(merged["steps"][0]["status"], "done")
            self.assertEqual(merged["steps"][0]["result"], "legacy result")

    def test_first_write_migration_preserves_existing_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan = make_plan(result="partial result")
            plan["steps"][0]["status"] = "in_progress"
            plan["completedSummary"] = ["step 0 done"]
            plan["deviations"] = ["went off-script"]
            plan_path = self.write_plan(temp_dir, plan)

            result = self.run_cli("add-deviation", str(plan_path), "another deviation")

            self.assertEqual(result.returncode, 0, result.stderr)
            progress = json.loads((Path(temp_dir) / "progress.json").read_text(encoding="utf-8"))
            self.assertEqual(progress["steps"]["1"]["status"], "in_progress")
            self.assertEqual(progress["steps"]["1"]["result"], "partial result")
            self.assertEqual(progress["completedSummary"], ["step 0 done"])
            self.assertIn("went off-script", progress["deviations"])
            self.assertIn("another deviation", progress["deviations"])

    def test_find_active_uses_progress_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            active_dir = Path(temp_dir) / ".temp" / "plan-mode" / "active"
            plan_a_dir = active_dir / "plan-a"
            plan_b_dir = active_dir / "plan-b"
            plan_a_dir.mkdir(parents=True)
            plan_b_dir.mkdir(parents=True)

            plan_json = json.dumps(make_plan(), indent=2)
            (plan_a_dir / "plan.json").write_text(plan_json, encoding="utf-8")
            time.sleep(0.05)
            (plan_b_dir / "plan.json").write_text(plan_json, encoding="utf-8")
            time.sleep(0.05)
            (plan_a_dir / "plan.json").write_text(plan_json, encoding="utf-8")
            time.sleep(0.05)
            (plan_b_dir / "progress.json").write_text(
                json.dumps({"steps": {"1": {"status": "in_progress"}}}, indent=2) + "\n",
                encoding="utf-8",
            )

            result = plan_utils.find_active_plan(temp_dir)
            self.assertIsNotNone(result)
            self.assertIn("plan-b", result)


if __name__ == "__main__":
    unittest.main()
