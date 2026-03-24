#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "look-before-you-leap" / "skills" / "look-before-you-leap" / "scripts"
DEPS_QUERY = SCRIPTS_DIR / "deps-query.py"
DEPS_GENERATE = SCRIPTS_DIR / "deps-generate.py"
DEP_CONFIG = SCRIPTS_DIR / "dep_config.py"


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


dep_config = load_module(DEP_CONFIG, "upstream_dep_config")
deps_generate = load_module(DEPS_GENERATE, "upstream_deps_generate")


class UpstreamDepsScriptsTests(unittest.TestCase):
    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_read_config_prefers_codex_dep_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            self.write_json(
                project_root / ".codex" / "lbyl-deps.json",
                {
                    "dep_maps": {
                        "dir": ".claude/deps",
                        "tool_cmd": "madge --json --extensions ts,tsx",
                        "modules": ["apps/mobile"],
                    }
                },
            )

            config = dep_config.read_config(str(project_root))
            self.assertEqual(config["dep_maps"]["modules"], ["apps/mobile"])

    def test_read_config_falls_back_to_claude_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            claude_config = project_root / ".claude" / "look-before-you-leap.local.md"
            claude_config.parent.mkdir(parents=True, exist_ok=True)
            claude_config.write_text(
                "---\n"
                "dep_maps:\n"
                "  dir: .claude/deps\n"
                "  tool_cmd: \"madge --json --extensions ts,tsx\"\n"
                "  modules:\n"
                "    - apps/mobile\n"
                "---\n",
                encoding="utf-8",
            )

            config = dep_config.read_config(str(project_root))
            self.assertEqual(config["dep_maps"]["modules"], ["apps/mobile"])

    def test_deps_generate_uses_shared_config_reader(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            self.write_json(
                project_root / ".codex" / "lbyl-deps.json",
                {
                    "dep_maps": {
                        "dir": ".claude/deps",
                        "tool_cmd": "madge --json --extensions ts,tsx",
                        "modules": ["apps/mobile"],
                    }
                },
            )

            config = deps_generate.read_config(str(project_root))
            self.assertEqual(config["dep_maps"]["dir"], ".claude/deps")
            self.assertEqual(config["dep_maps"]["modules"], ["apps/mobile"])

    def test_deps_query_cli_works_with_codex_dep_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            self.write_json(
                project_root / ".codex" / "lbyl-deps.json",
                {
                    "dep_maps": {
                        "dir": ".claude/deps",
                        "tool_cmd": "madge --json --extensions ts,tsx",
                        "modules": ["apps/mobile"],
                    }
                },
            )
            self.write_json(
                project_root / ".claude" / "deps" / "deps-apps-mobile.json",
                {
                    "apps/mobile/app/example.tsx": [
                        "apps/mobile/lib/theme.ts"
                    ],
                    "apps/mobile/features/consumer/Screen.tsx": [
                        "apps/mobile/app/example.tsx"
                    ]
                },
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(DEPS_QUERY),
                    str(project_root),
                    "apps/mobile/app/example.tsx",
                ],
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("FILE: apps/mobile/app/example.tsx", result.stdout)
            self.assertIn("DEPENDENCIES (1):", result.stdout)
            self.assertIn("apps/mobile/lib/theme.ts", result.stdout)
            self.assertIn("DEPENDENTS (1):", result.stdout)
            self.assertIn("apps/mobile/features/consumer/Screen.tsx", result.stdout)


if __name__ == "__main__":
    unittest.main()
