#!/usr/bin/env python3

from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
INSTALLER = REPO_ROOT / "scripts" / "install-claude-bridge-codex-integration.sh"


class InstallClaudeBridgeCodexIntegrationTests(unittest.TestCase):
    def test_installer_persists_long_running_mcp_timeout_defaults(self) -> None:
        text = INSTALLER.read_text(encoding="utf-8")

        self.assertIn('CONFIG_PATH="${CODEX_CONFIG_PATH:-$HOME/.codex/config.toml}"', text)
        self.assertIn(
            'MCP_STARTUP_TIMEOUT_SEC="${CLAUDE_BRIDGE_MCP_STARTUP_TIMEOUT_SEC:-300}"',
            text,
        )
        self.assertIn(
            'MCP_TOOL_TIMEOUT_SEC="${CLAUDE_BRIDGE_MCP_TOOL_TIMEOUT_SEC:-10800}"',
            text,
        )
        self.assertIn('startup_timeout_sec', text)
        self.assertIn('tool_timeout_sec', text)
        self.assertIn('Configured claude-bridge MCP timeouts', text)

    def test_embedded_python_writes_timeouts_inside_target_mcp_section(self) -> None:
        text = INSTALLER.read_text(encoding="utf-8")
        match = re.search(r"<<'PYEOF'\n(?P<script>.*?)\nPYEOF", text, re.DOTALL)
        self.assertIsNotNone(match)
        script = match.group("script")

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "config.toml"
            config_path.write_text(
                '[mcp_servers.claude-bridge]\n'
                'command = "/opt/homebrew/bin/node"\n'
                'args = ["/tmp/server.mjs"]\n'
                '\n'
                '[plugins."github@openai-curated"]\n'
                'enabled = true\n',
                encoding="utf-8",
            )

            result = subprocess.run(
                [
                    "python3",
                    "-c",
                    script,
                    str(config_path),
                    "claude-bridge",
                    "300",
                    "10800",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            updated = config_path.read_text(encoding="utf-8")
            self.assertIn("[mcp_servers.claude-bridge]", updated)
            self.assertRegex(
                updated,
                r"\[mcp_servers\.claude-bridge\]\n"
                r'command = "/opt/homebrew/bin/node"\n'
                r'args = \["/tmp/server\.mjs"\]\n'
                r"\n?"
                r"startup_timeout_sec = 300\n"
                r"tool_timeout_sec = 10800\n"
                r"\[plugins\.\"github@openai-curated\"\]\n"
                r"enabled = true\n",
            )
            self.assertNotRegex(
                updated,
                r"\[plugins\.\"github@openai-curated\"\]\n"
                r"enabled = true\n"
                r"startup_timeout_sec = 300\n"
                r"tool_timeout_sec = 10800\n",
            )


if __name__ == "__main__":
    unittest.main()
