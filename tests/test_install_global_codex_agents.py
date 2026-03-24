#!/usr/bin/env python3

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install-global-codex-agents.sh"
BEGIN_MARKER = "<!-- BEGIN CODEX-SETUP GLOBAL DEFAULTS -->"
END_MARKER = "<!-- END CODEX-SETUP GLOBAL DEFAULTS -->"


class InstallGlobalCodexAgentsTests(unittest.TestCase):
    def run_installer(self, home: Path) -> subprocess.CompletedProcess[str]:
        env = os.environ.copy()
        env["HOME"] = str(home)
        env.pop("CODEX_HOME", None)
        env.pop("CODEX_AGENTS_PATH", None)
        return subprocess.run(
            ["bash", str(INSTALLER)],
            text=True,
            capture_output=True,
            check=False,
            env=env,
        )

    def agents_path(self, home: Path) -> Path:
        return home / ".codex" / "AGENTS.md"

    def test_installer_creates_global_agents_defaults_block(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)

            result = self.run_installer(home)

            self.assertEqual(result.returncode, 0, result.stderr)
            agents_path = self.agents_path(home)
            self.assertTrue(agents_path.is_file())

            text = agents_path.read_text(encoding="utf-8")
            self.assertIn(BEGIN_MARKER, text)
            self.assertIn(END_MARKER, text)
            self.assertIn("default to `lbyl-conductor` and `lbyl-engineering-discipline`", text)
            self.assertIn("nearer project or nested", text)

    def test_installer_updates_managed_block_without_clobbering_other_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            home = Path(temp_dir)
            agents_path = self.agents_path(home)
            agents_path.parent.mkdir(parents=True, exist_ok=True)
            agents_path.write_text(
                "# Personal Defaults\n\nKeep this content.\n\n"
                f"{BEGIN_MARKER}\nold content\n{END_MARKER}\n\n"
                "# Tail Note\n",
                encoding="utf-8",
            )

            result = self.run_installer(home)

            self.assertEqual(result.returncode, 0, result.stderr)
            text = agents_path.read_text(encoding="utf-8")
            self.assertIn("# Personal Defaults", text)
            self.assertIn("Keep this content.", text)
            self.assertIn("# Tail Note", text)
            self.assertNotIn("old content", text)
            self.assertEqual(text.count(BEGIN_MARKER), 1)
            self.assertEqual(text.count(END_MARKER), 1)
            self.assertIn("Use Claude for brainstorming", text)


if __name__ == "__main__":
    unittest.main()
