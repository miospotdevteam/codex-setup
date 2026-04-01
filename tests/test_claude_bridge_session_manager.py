#!/usr/bin/env python3

from __future__ import annotations

import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_BRIDGE_ROOT = REPO_ROOT / "claude-bridge"

import sys

sys.path.insert(0, str(CLAUDE_BRIDGE_ROOT))
import session_manager  # noqa: E402


class FakeProcess:
    def __init__(
        self,
        payload: dict[str, object],
        *,
        use_structured_output: bool = False,
    ) -> None:
        event = {
            "type": "result",
            "session_id": "claude-session",
            "result": "" if use_structured_output else json.dumps(payload),
        }
        if use_structured_output:
            event["structured_output"] = payload
        self.stdout = io.StringIO(json.dumps(event) + "\n")
        self.stderr = io.StringIO("")

    def wait(self, timeout: int | None = None) -> int:
        return 0


class MultiEventProcess:
    def __init__(self, events: list[dict[str, object]]) -> None:
        self.stdout = io.StringIO("".join(json.dumps(event) + "\n" for event in events))
        self.stderr = io.StringIO("")

    def wait(self, timeout: int | None = None) -> int:
        return 0


class SessionManagerCommandTests(unittest.TestCase):
    def make_manager(self) -> session_manager.SessionManager:
        self.temp_dir = tempfile.TemporaryDirectory()
        return session_manager.SessionManager(state_root=Path(self.temp_dir.name))

    def tearDown(self) -> None:
        if hasattr(self, "temp_dir"):
            self.temp_dir.cleanup()

    def test_bundled_plugin_dir_contains_explorer_skill(self) -> None:
        manager = self.make_manager()

        plugin_dir = manager.resolve_plugin_dir()

        self.assertIsNotNone(plugin_dir)
        plugin_path = Path(plugin_dir)
        explorer_skill = plugin_path / "skills" / "explorer" / "SKILL.md"
        self.assertTrue(explorer_skill.is_file())
        self.assertTrue(explorer_skill.read_text(encoding="utf-8").strip())

    def test_verification_uses_read_only_tools_with_plugin_and_hooks_disabled(self) -> None:
        manager = self.make_manager()
        captured: dict[str, object] = {}

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = cmd
            return FakeProcess(
                {"status": "PASS", "summary": "verified", "findings": []},
                use_structured_output=True,
            )

        args = {
            "cwd": str(REPO_ROOT),
            "planName": "demo-plan",
            "stepId": 1,
            "stepTitle": "Verify",
            "description": "Check the implementation",
            "acceptanceCriteria": "It works",
            "verificationCommands": "python3 -m unittest",
            "pluginDir": "/tmp/should-not-be-used",
        }

        with (
            mock.patch.object(manager, "resolve_claude_command", return_value="/usr/bin/claude"),
            mock.patch.object(manager, "resolve_plugin_dir", return_value="/tmp/plugin"),
            mock.patch.object(session_manager.subprocess, "Popen", side_effect=fake_popen),
        ):
            result = manager.run_verification(args)

        cmd = captured["cmd"]
        assert isinstance(cmd, list)
        self.assertNotIn("--bare", cmd)
        self.assertNotIn("--disable-slash-commands", cmd)
        self.assertIn("--plugin-dir", cmd)
        self.assertEqual(cmd[cmd.index("--plugin-dir") + 1], "/tmp/plugin")
        self.assertIn("--setting-sources", cmd)
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "project,local")
        self.assertIn("--settings", cmd)
        self.assertEqual(
            json.loads(cmd[cmd.index("--settings") + 1]),
            {"disableAllHooks": True},
        )
        self.assertIn("--allowedTools", cmd)
        allowed = cmd[cmd.index("--allowedTools") + 1]
        self.assertIn("Read", allowed)
        self.assertIn("Bash(git status:*)", allowed)
        self.assertNotIn("LS", allowed)
        self.assertEqual(result["status"], "PASS")

    def test_attack_plan_uses_read_only_tools_with_plugin_and_hooks_disabled(self) -> None:
        manager = self.make_manager()
        captured: dict[str, object] = {}

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = cmd
            return FakeProcess(
                {"verdict": "REVISE", "summary": "tighten step order", "findings": []},
                use_structured_output=True,
            )

        args = {
            "cwd": str(REPO_ROOT),
            "planName": "demo-plan",
            "planPath": str(REPO_ROOT / ".temp" / "plan-mode" / "active" / "demo-plan" / "plan.json"),
            "masterPlanPath": str(REPO_ROOT / ".temp" / "plan-mode" / "active" / "demo-plan" / "masterPlan.md"),
            "userGoal": "Ship the feature safely",
            "discoverySummary": "Relevant consumers listed",
            "pluginDir": "/tmp/should-not-be-used",
        }

        with (
            mock.patch.object(manager, "resolve_claude_command", return_value="/usr/bin/claude"),
            mock.patch.object(manager, "resolve_plugin_dir", return_value="/tmp/plugin"),
            mock.patch.object(session_manager.subprocess, "Popen", side_effect=fake_popen),
        ):
            result = manager.run_plan_attack(args)

        cmd = captured["cmd"]
        assert isinstance(cmd, list)
        self.assertNotIn("--bare", cmd)
        self.assertNotIn("--disable-slash-commands", cmd)
        self.assertIn("--plugin-dir", cmd)
        self.assertEqual(cmd[cmd.index("--plugin-dir") + 1], "/tmp/plugin")
        self.assertIn("--setting-sources", cmd)
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "project,local")
        self.assertIn("--settings", cmd)
        self.assertEqual(
            json.loads(cmd[cmd.index("--settings") + 1]),
            {"disableAllHooks": True},
        )
        self.assertIn("--allowedTools", cmd)
        self.assertEqual(result["verdict"], "REVISE")

    def test_draft_plan_uses_read_only_tools_with_plugin_and_hooks_disabled(self) -> None:
        manager = self.make_manager()
        captured: dict[str, object] = {}

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = cmd
            return FakeProcess(
                {
                    "summary": "Drafted a three-step plan",
                    "planJson": {
                        "name": "demo-plan",
                        "title": "Demo Plan",
                        "context": "Context",
                        "review": {"status": "pending"},
                        "discovery": {"scope": "scope"},
                        "steps": [],
                    },
                    "masterPlanMarkdown": "# Demo Plan\n",
                    "notes": ["Used dep partition groups for step sizing"],
                },
                use_structured_output=True,
            )

        args = {
            "cwd": str(REPO_ROOT),
            "planName": "demo-plan",
            "discoveryPath": str(REPO_ROOT / ".temp" / "plan-mode" / "active" / "demo-plan" / "discovery.md"),
            "depPartitionPath": str(REPO_ROOT / ".temp" / "plan-mode" / "active" / "demo-plan" / "dep-partition.json"),
            "planPath": str(REPO_ROOT / ".temp" / "plan-mode" / "active" / "demo-plan" / "plan.json"),
            "masterPlanPath": str(REPO_ROOT / ".temp" / "plan-mode" / "active" / "demo-plan" / "masterPlan.md"),
            "userGoal": "Ship the feature safely",
            "discoverySummary": "Relevant consumers listed",
            "pluginDir": "/tmp/should-not-be-used",
        }

        with (
            mock.patch.object(manager, "resolve_claude_command", return_value="/usr/bin/claude"),
            mock.patch.object(manager, "resolve_plugin_dir", return_value="/tmp/plugin"),
            mock.patch.object(session_manager.subprocess, "Popen", side_effect=fake_popen),
        ):
            result = manager.run_draft_plan(args)

        cmd = captured["cmd"]
        assert isinstance(cmd, list)
        self.assertNotIn("--bare", cmd)
        self.assertIn("--plugin-dir", cmd)
        self.assertEqual(cmd[cmd.index("--plugin-dir") + 1], "/tmp/plugin")
        self.assertIn("--setting-sources", cmd)
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "project,local")
        self.assertIn("--settings", cmd)
        self.assertEqual(
            json.loads(cmd[cmd.index("--settings") + 1]),
            {"disableAllHooks": True},
        )
        self.assertIn("--allowedTools", cmd)
        self.assertEqual(result["summary"], "Drafted a three-step plan")
        self.assertEqual(result["planJson"]["name"], "demo-plan")

    def test_frontend_implementation_keeps_plugin_dir_and_skips_bare_mode(self) -> None:
        manager = self.make_manager()
        captured: dict[str, object] = {}

        def fake_popen(cmd, **kwargs):
            captured["cmd"] = cmd
            return FakeProcess(
                {
                    "summary": "implemented",
                    "changes": ["ui"],
                    "deviations": [],
                    "observations": [],
                    "needsCodexFollowUp": False,
                    "followUpSuggestions": [],
                }
            )

        args = {
            "cwd": str(REPO_ROOT),
            "stepId": 2,
            "stepTitle": "Frontend",
            "description": "Build UI",
            "acceptanceCriteria": "UI matches design",
            "prompt": "Implement the UI",
            "designSummary": "approved",
            "discoverySummary": "context",
            "planName": "demo-plan",
            "pluginDir": "/tmp/plugin",
        }

        with (
            mock.patch.object(manager, "resolve_claude_command", return_value="/usr/bin/claude"),
            mock.patch.object(manager, "resolve_plugin_dir", return_value="/tmp/plugin"),
            mock.patch.object(session_manager.subprocess, "Popen", side_effect=fake_popen),
        ):
            result = manager.run_frontend_implementation(args)

        cmd = captured["cmd"]
        assert isinstance(cmd, list)
        self.assertNotIn("--bare", cmd)
        self.assertIn("--plugin-dir", cmd)
        self.assertEqual(cmd[cmd.index("--plugin-dir") + 1], "/tmp/plugin")
        self.assertIn("--setting-sources", cmd)
        self.assertEqual(cmd[cmd.index("--setting-sources") + 1], "project,local")
        self.assertIn("--settings", cmd)
        self.assertEqual(
            json.loads(cmd[cmd.index("--settings") + 1]),
            {"disableAllHooks": True},
        )
        self.assertEqual(result["summary"], "implemented")

    def test_verification_falls_back_to_candidate_payload_when_final_result_is_polluted(self) -> None:
        manager = self.make_manager()

        events = [
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {
                            "type": "text",
                            "text": (
                                "```json\n"
                                '{"status":"PASS","summary":"verified","findings":[]}\n'
                                "```"
                            ),
                        }
                    ]
                },
            },
            {
                "type": "result",
                "session_id": "claude-session",
                "result": "Stop hook feedback: active plan still has pending work",
            },
        ]

        args = {
            "cwd": str(REPO_ROOT),
            "planName": "demo-plan",
            "stepId": 1,
            "stepTitle": "Verify",
            "description": "Check the implementation",
            "acceptanceCriteria": "It works",
            "verificationCommands": "python3 -m unittest",
        }

        with (
            mock.patch.object(manager, "resolve_claude_command", return_value="/usr/bin/claude"),
            mock.patch.object(
                session_manager.subprocess,
                "Popen",
                return_value=MultiEventProcess(events),
            ),
        ):
            result = manager.run_verification(args)

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["summary"], "verified")


if __name__ == "__main__":
    unittest.main()
