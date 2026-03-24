#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "codex-skills" / "lbyl-conductor" / "scripts" / "dep_partition.py"

spec = importlib.util.spec_from_file_location("dep_partition", SCRIPT_PATH)
assert spec and spec.loader
dep_partition = importlib.util.module_from_spec(spec)
spec.loader.exec_module(dep_partition)


class DepPartitionTests(unittest.TestCase):
    def write_json(self, path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    def test_isolated_targets_are_split_into_parallel_groups(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_json(
                root / ".codex" / "lbyl-deps.json",
                {"dep_maps": {"dir": ".codex/deps", "modules": ["apps/web", "apps/api"]}},
            )
            self.write_json(
                root / ".codex" / "deps" / "deps-apps-web.json",
                {"apps/web/a.ts": ["apps/web/local.ts"]},
            )
            self.write_json(
                root / ".codex" / "deps" / "deps-apps-api.json",
                {"apps/api/b.ts": ["apps/api/lib.ts"]},
            )

            result = dep_partition.build_partition(str(root), ["apps/web/a.ts", "apps/api/b.ts"])

            self.assertEqual(len(result["groups"]), 2)
            self.assertTrue(all(group["safeParallel"] for group in result["groups"]))
            self.assertEqual(result["sharedBoundaries"], [])

    def test_shared_dependency_merges_targets_into_one_group(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_json(
                root / ".codex" / "lbyl-deps.json",
                {"dep_maps": {"dir": ".codex/deps", "modules": ["apps/mobile"]}},
            )
            self.write_json(
                root / ".codex" / "deps" / "deps-apps-mobile.json",
                {
                    "apps/mobile/a.ts": ["packages/shared/colors.ts"],
                    "apps/mobile/b.ts": ["packages/shared/colors.ts"],
                },
            )

            result = dep_partition.build_partition(str(root), ["apps/mobile/a.ts", "apps/mobile/b.ts"])

            self.assertEqual(len(result["groups"]), 1)
            self.assertEqual(
                result["groups"][0]["targets"],
                ["apps/mobile/a.ts", "apps/mobile/b.ts"],
            )
            reasons = {link["reason"] for link in result["directLinks"]}
            self.assertIn("shared_dependency", reasons)

    def test_cross_module_dependents_raise_boundary_group_first(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            self.write_json(
                root / ".codex" / "lbyl-deps.json",
                {
                    "dep_maps": {
                        "dir": ".codex/deps",
                        "modules": ["packages/shared", "apps/web", "apps/mobile"],
                    }
                },
            )
            self.write_json(
                root / ".codex" / "deps" / "deps-packages-shared.json",
                {
                    "packages/shared/theme.ts": [],
                    "apps/web/home.tsx": ["packages/shared/theme.ts"],
                    "apps/mobile/home.tsx": ["packages/shared/theme.ts"],
                },
            )
            self.write_json(root / ".codex" / "deps" / "deps-apps-web.json", {})
            self.write_json(root / ".codex" / "deps" / "deps-apps-mobile.json", {})

            result = dep_partition.build_partition(str(root), ["packages/shared/theme.ts"])

            group = result["groups"][0]
            self.assertEqual(group["parallelHint"], "cross_module_boundary")
            self.assertFalse(group["safeParallel"])
            self.assertEqual(group["suggestedOrder"], 1)
