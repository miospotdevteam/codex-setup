#!/usr/bin/env python3
"""Shared dep-map config loading for vendored Codex skill scripts."""

from __future__ import annotations

import json
import os
import re
from typing import Any

CODEX_CONFIG_PATH = os.path.join(".codex", "lbyl-deps.json")
CLAUDE_CONFIG_PATH = os.path.join(".claude", "look-before-you-leap.local.md")


def codex_config_path(project_root: str) -> str:
    return os.path.join(project_root, CODEX_CONFIG_PATH)


def claude_config_path(project_root: str) -> str:
    return os.path.join(project_root, CLAUDE_CONFIG_PATH)


def describe_config_sources() -> str:
    return f"{CODEX_CONFIG_PATH} or {CLAUDE_CONFIG_PATH}"


def read_config(project_root: str) -> dict[str, Any]:
    codex_config = _read_codex_config(project_root)
    if codex_config:
        return codex_config

    claude_config = _read_claude_frontmatter(project_root)
    if claude_config:
        return claude_config

    return {}


def _read_codex_config(project_root: str) -> dict[str, Any]:
    config_file = codex_config_path(project_root)
    try:
        with open(config_file, encoding="utf-8") as handle:
            return json.load(handle)
    except (FileNotFoundError, PermissionError, json.JSONDecodeError):
        return {}


def _read_claude_frontmatter(project_root: str) -> dict[str, Any]:
    config_file = claude_config_path(project_root)
    try:
        with open(config_file, encoding="utf-8") as handle:
            content = handle.read()
    except (FileNotFoundError, PermissionError, OSError):
        return {}

    frontmatter = _extract_frontmatter(content)
    if not frontmatter:
        return {}

    dep_maps = _parse_dep_maps(frontmatter)
    return {"dep_maps": dep_maps} if dep_maps else {}


def _extract_frontmatter(markdown: str) -> str:
    match = re.match(r"^---\s*\n(.*?)\n---", markdown, re.DOTALL)
    return match.group(1) if match else ""


def _parse_dep_maps(frontmatter: str) -> dict[str, Any]:
    lines = frontmatter.splitlines()
    dep_maps: dict[str, Any] = {"modules": []}
    in_dep_maps = False
    current_list: str | None = None

    for line in lines:
        if not in_dep_maps:
            if line.strip() == "dep_maps:":
                in_dep_maps = True
            continue

        if re.match(r"^[A-Za-z0-9_]+:\s*", line) and not line.startswith(" "):
            break

        key_match = re.match(r"^ {2}([a-z_]+):\s*(.*)$", line)
        if key_match:
            key, raw_value = key_match.groups()
            value = raw_value.strip()
            if value:
                dep_maps[key] = _strip_quotes(value)
                current_list = None
            elif key == "modules":
                dep_maps["modules"] = []
                current_list = "modules"
            else:
                current_list = None
            continue

        if current_list == "modules":
            item_match = re.match(r"^ {4}- (.+)$", line)
            if item_match:
                dep_maps["modules"].append(item_match.group(1).strip())

    if dep_maps.get("dir") and dep_maps.get("tool_cmd") and dep_maps["modules"]:
        return dep_maps
    return {}


def _strip_quotes(value: str) -> str:
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    return value
