#!/usr/bin/env python3
"""Generate normalized dependency maps via madge.

Usage:
    python3 deps-generate.py <project_root> --module apps/api
    python3 deps-generate.py <project_root> --all
    python3 deps-generate.py <project_root> --stale-only

Configuration lives in .codex/lbyl-deps.json:
{
  "dep_maps": {
    "dir": ".codex/deps",
    "tool_cmd": "madge --json --extensions ts,tsx",
    "modules": ["apps/api", "packages/shared"]
  }
}
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from typing import Any

CONFIG_PATH = os.path.join(".codex", "lbyl-deps.json")


def read_config(project_root: str) -> dict[str, Any]:
    config_file = os.path.join(project_root, CONFIG_PATH)
    try:
        with open(config_file, encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, PermissionError, json.JSONDecodeError):
        return {}


def module_slug(module_path: str) -> str:
    return module_path.replace("/", "-")


def get_deps_dir(project_root: str, config: dict[str, Any]) -> str:
    dep_maps = config.get("dep_maps", {})
    rel_dir = dep_maps.get("dir", ".codex/deps")
    return os.path.join(project_root, rel_dir)


def get_stale_modules(deps_dir: str) -> set[str]:
    stale_file = os.path.join(deps_dir, ".stale")
    if not os.path.exists(stale_file):
        return set()
    try:
        with open(stale_file, encoding="utf-8") as handle:
            return {line.strip() for line in handle if line.strip()}
    except (FileNotFoundError, PermissionError):
        return set()


def clear_stale(deps_dir: str, slug: str) -> None:
    stale_file = os.path.join(deps_dir, ".stale")
    if not os.path.exists(stale_file):
        return
    try:
        with open(stale_file, encoding="utf-8") as handle:
            lines = [line.strip() for line in handle if line.strip()]
        remaining = [line for line in lines if line != slug]
        with open(stale_file, "w", encoding="utf-8") as handle:
            handle.write("\n".join(remaining) + ("\n" if remaining else ""))
    except (FileNotFoundError, PermissionError):
        pass


def is_stale_by_mtime(project_root: str, deps_dir: str, module_path: str) -> bool:
    slug = module_slug(module_path)
    dep_file = os.path.join(deps_dir, f"deps-{slug}.json")
    if not os.path.exists(dep_file):
        return True

    dep_mtime = os.path.getmtime(dep_file)
    src_dir = os.path.join(project_root, module_path, "src")
    if not os.path.isdir(src_dir):
        src_dir = os.path.join(project_root, module_path)

    for root, _dirs, files in os.walk(src_dir):
        if "node_modules" in root:
            continue
        for filename in files:
            if filename.endswith((".ts", ".tsx")) and not filename.endswith(
                (".test.ts", ".test.tsx", ".spec.ts", ".spec.tsx")
            ):
                file_path = os.path.join(root, filename)
                if os.path.getmtime(file_path) > dep_mtime:
                    return True
    return False


def run_madge(project_root: str, module_path: str, tool_cmd: str) -> dict[str, list[str]] | None:
    module_abs = os.path.join(project_root, module_path)
    src_dir = os.path.join(module_abs, "src")
    if not os.path.isdir(src_dir):
        src_dir = module_abs

    tsconfig = os.path.join(module_abs, "tsconfig.json")

    cmd = tool_cmd.split()
    if os.path.exists(tsconfig):
        cmd.extend(["--ts-config", tsconfig])
    cmd.append(src_dir)

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=120,
            check=False,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass

    npx_cmd = ["npx", "--yes"] + cmd
    try:
        result = subprocess.run(
            npx_cmd,
            capture_output=True,
            text=True,
            cwd=project_root,
            timeout=180,
            check=False,
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        print(f"  madge stderr: {result.stderr[:500]}", file=sys.stderr)
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError) as exc:
        print(f"  madge failed: {exc}", file=sys.stderr)
        return None


def normalize_paths(
    raw_deps: dict[str, list[str]],
    project_root: str,
    module_path: str,
) -> dict[str, list[str]]:
    module_abs = os.path.join(project_root, module_path)
    src_dir = os.path.join(module_abs, "src")
    if not os.path.isdir(src_dir):
        src_dir = module_abs

    normalized: dict[str, list[str]] = {}
    for file_key, deps in raw_deps.items():
        abs_key = os.path.normpath(os.path.join(src_dir, file_key))
        repo_key = os.path.relpath(abs_key, project_root)

        repo_deps = []
        for dep in deps:
            abs_dep = os.path.normpath(os.path.join(src_dir, dep))
            repo_dep = os.path.relpath(abs_dep, project_root)
            if not repo_dep.startswith(".."):
                repo_deps.append(repo_dep)

        normalized[repo_key] = repo_deps

    return normalized


def generate_module(project_root: str, module_path: str, config: dict[str, Any]) -> bool:
    dep_maps = config.get("dep_maps", {})
    tool_cmd = dep_maps.get("tool_cmd", "madge --json --extensions ts,tsx")
    deps_dir = get_deps_dir(project_root, config)
    slug = module_slug(module_path)

    os.makedirs(deps_dir, exist_ok=True)

    print(f"Generating deps for {module_path}...", file=sys.stderr)
    raw = run_madge(project_root, module_path, tool_cmd)
    if raw is None:
        print(f"  FAILED: could not run madge for {module_path}", file=sys.stderr)
        return False

    normalized = normalize_paths(raw, project_root, module_path)
    out_path = os.path.join(deps_dir, f"deps-{slug}.json")
    with open(out_path, "w", encoding="utf-8") as handle:
        json.dump(normalized, handle, indent=2, sort_keys=True)

    clear_stale(deps_dir, slug)
    print(f"  OK: {len(normalized)} files -> {out_path}", file=sys.stderr)
    return True


def main() -> None:
    if len(sys.argv) < 3:
        print(
            "Usage: deps-generate.py <project_root> (--module <path> | --all | --stale-only)",
            file=sys.stderr,
        )
        sys.exit(1)

    project_root = os.path.abspath(sys.argv[1])
    config = read_config(project_root)
    dep_maps = config.get("dep_maps", {})
    modules = dep_maps.get("modules", [])

    if not modules:
        print(f"No dep_maps.modules configured in {CONFIG_PATH}", file=sys.stderr)
        sys.exit(1)

    mode = sys.argv[2]

    if mode == "--module":
        if len(sys.argv) < 4:
            print("--module requires a module path", file=sys.stderr)
            sys.exit(1)
        target = sys.argv[3]
        if target not in modules:
            print(f"Module '{target}' not in configured modules: {modules}", file=sys.stderr)
            sys.exit(1)
        success = generate_module(project_root, target, config)
        sys.exit(0 if success else 1)

    if mode == "--all":
        failed = [module for module in modules if not generate_module(project_root, module, config)]
        if failed:
            print(f"\nFailed modules: {failed}", file=sys.stderr)
            sys.exit(1)
        print(f"\nAll {len(modules)} modules generated successfully.", file=sys.stderr)
        return

    if mode == "--stale-only":
        deps_dir = get_deps_dir(project_root, config)
        stale_slugs = get_stale_modules(deps_dir)
        generated = 0
        for module in modules:
            slug = module_slug(module)
            if slug in stale_slugs or is_stale_by_mtime(project_root, deps_dir, module):
                generate_module(project_root, module, config)
                generated += 1
        if generated == 0:
            print("All dep maps are up to date.", file=sys.stderr)
        else:
            print(f"Regenerated {generated} stale module(s).", file=sys.stderr)
        return

    print(f"Unknown mode: {mode}", file=sys.stderr)
    sys.exit(1)


if __name__ == "__main__":
    main()
