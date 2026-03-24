#!/usr/bin/env python3

from __future__ import annotations

import json
import importlib.util
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
GUARD = REPO_ROOT / "codex-guard" / "guard.py"
PLAN_UTILS_PATH = REPO_ROOT / "codex-skills" / "lbyl-conductor" / "scripts" / "plan_utils.py"

spec = importlib.util.spec_from_file_location("codex_guard_plan_utils", PLAN_UTILS_PATH)
assert spec and spec.loader
plan_utils = importlib.util.module_from_spec(spec)
spec.loader.exec_module(plan_utils)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def is_user_writable(path: Path) -> bool:
    return bool(path.stat().st_mode & stat.S_IWUSR)


class GuardCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)
        subprocess.run(["git", "init"], cwd=self.root, check=True, capture_output=True)
        (self.root / "src").mkdir()
        (self.root / "src" / "a.txt").write_text("a\n", encoding="utf-8")
        (self.root / "src" / "b.txt").write_text("b\n", encoding="utf-8")
        subprocess.run(["git", "add", "."], cwd=self.root, check=True, capture_output=True)

    def tearDown(self) -> None:
        for path in self.root.rglob("*"):
            try:
                path.chmod(path.stat().st_mode | stat.S_IWUSR)
            except OSError:
                pass
        self.temp_dir.cleanup()

    def active_plan(self) -> Path:
        return self.root / ".temp" / "plan-mode" / "active" / "demo" / "plan.json"

    def make_plan(
        self,
        *,
        review_status: str = "approved",
        skip_reason: str | None = None,
        step_status: str = "pending",
        result: str | None = None,
        executor: str | None = "codex",
        routing_hint: str | None = None,
        skill: str = "none",
        files: list[str] | None = None,
    ) -> Path:
        step = {
            "id": 1,
            "title": "Edit a.txt",
            "status": step_status,
            "skill": skill,
            "claudeVerify": True,
            "simplify": False,
            "files": files or ["src/a.txt"],
            "description": "Change the first file.",
            "acceptanceCriteria": "Claude verification passes.",
            "progress": [
                {"task": "Update file", "status": "pending", "files": ["src/a.txt"]}
            ],
            "result": result,
        }
        if executor is not None:
            step["executor"] = executor
        if routing_hint is not None:
            step["routingHint"] = routing_hint
        plan = {
            "name": "demo",
            "title": "Demo",
            "context": "Fixture plan",
            "status": "active",
            "requiredSkills": [],
            "disciplines": [],
            "review": {
                "status": review_status,
                "reviewedVia": "orbit",
                "approvedAt": "2026-03-24T00:00:00Z" if review_status != "pending" else None,
                "skipReason": skip_reason,
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
        plan_path = self.active_plan()
        write_json(plan_path, plan)
        return plan_path

    def run_guard(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(GUARD), "--project-root", str(self.root), *args],
            text=True,
            capture_output=True,
            check=False,
        )

    def load_plan(self) -> dict:
        return plan_utils.read_plan(str(self.active_plan()))

    def write_progress(self, payload: dict) -> None:
        write_json(self.active_plan().with_name("progress.json"), payload)

    def test_validate_plan_rejects_pending_review(self) -> None:
        self.make_plan(review_status="pending")
        result = self.run_guard("validate-plan")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("approved or explicitly skipped", result.stderr)

    def test_validate_plan_resolves_executor_metadata(self) -> None:
        self.make_plan(executor=None)
        result = self.run_guard("validate-plan")
        self.assertEqual(result.returncode, 0, result.stderr)
        plan = self.load_plan()
        step = plan["steps"][0]
        self.assertEqual(step["executor"], "codex")
        self.assertEqual(step["routingHint"], "auto")
        self.assertEqual(step["routingResolvedBy"], "lbyl-conductor")
        self.assertIn("Codex", step["routingReason"])

    def test_setup_resumes_in_progress_step(self) -> None:
        self.make_plan(step_status="in_progress")
        result = self.run_guard("setup")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Resumed step 1", result.stdout)
        self.assertTrue(is_user_writable(self.root / "src" / "a.txt"))
        self.assertFalse(is_user_writable(self.root / "src" / "b.txt"))

    def test_setup_resumes_in_progress_step_from_progress_json(self) -> None:
        self.make_plan(step_status="pending")
        self.write_progress({"steps": {"1": {"status": "in_progress"}}})
        result = self.run_guard("setup")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Resumed step 1", result.stdout)
        self.assertTrue(is_user_writable(self.root / "src" / "a.txt"))
        self.assertFalse(is_user_writable(self.root / "src" / "b.txt"))

    def test_begin_step_requires_validation(self) -> None:
        self.make_plan()
        result = self.run_guard("begin-step", "1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("validate-plan must pass", result.stderr)

    def test_complete_step_requires_claude_pass(self) -> None:
        self.make_plan()
        self.assertEqual(self.run_guard("validate-plan").returncode, 0)
        self.assertEqual(self.run_guard("begin-step", "1").returncode, 0)

        self.write_progress(
            {
                "steps": {
                    "1": {
                        "status": "in_progress",
                        "result": "Implemented, but not verified.",
                    }
                }
            }
        )

        result = self.run_guard("complete-step", "1")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no Claude PASS verdict", result.stderr)
        self.assertTrue(is_user_writable(self.root / "src" / "a.txt"))

    def test_complete_step_locks_files_and_marks_done(self) -> None:
        self.make_plan()
        self.assertEqual(self.run_guard("validate-plan").returncode, 0)
        self.assertEqual(self.run_guard("begin-step", "1").returncode, 0)

        self.write_progress(
            {
                "steps": {
                    "1": {
                        "status": "in_progress",
                        "result": "### Verdict\nClaude: PASS",
                    }
                }
            }
        )

        result = self.run_guard("complete-step", "1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("completed and locked", result.stdout)
        self.assertFalse(is_user_writable(self.root / "src" / "a.txt"))
        updated = self.load_plan()
        self.assertEqual(updated["steps"][0]["status"], "done")


if __name__ == "__main__":
    unittest.main()
