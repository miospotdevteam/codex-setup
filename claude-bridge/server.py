#!/usr/bin/env python3
"""Minimal stdio MCP server for Claude specialist workflows."""

from __future__ import annotations

import json
import os
import sys
import traceback
from typing import Any

from __init__ import BRIDGE_NAME, BRIDGE_VERSION
from session_manager import ClaudeBridgeError, SessionManager

DEFAULT_PROTOCOL_VERSION = "2024-11-05"
DEBUG_LOG_PATH = os.environ.get("CLAUDE_BRIDGE_DEBUG_LOG")


def debug_log(message: str) -> None:
    if not DEBUG_LOG_PATH:
        return
    with open(DEBUG_LOG_PATH, "a", encoding="utf-8") as handle:
        handle.write(message + "\n")


def brainstorm_start_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["cwd", "title", "prompt"],
        "properties": {
            "cwd": {"type": "string"},
            "title": {"type": "string"},
            "prompt": {"type": "string"},
            "sessionId": {"type": "string"},
            "pluginDir": {"type": "string"},
        },
    }


def brainstorm_status_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["sessionId"],
        "properties": {
            "sessionId": {"type": "string"},
            "tailEvents": {"type": "integer", "minimum": 1, "maximum": 200},
        },
    }


def frontend_tool_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "cwd",
            "stepId",
            "stepTitle",
            "description",
            "acceptanceCriteria",
            "prompt",
        ],
        "properties": {
            "cwd": {"type": "string"},
            "planName": {"type": "string"},
            "stepId": {"type": "integer"},
            "stepTitle": {"type": "string"},
            "description": {"type": "string"},
            "acceptanceCriteria": {"type": "string"},
            "filesInScope": {"type": "array", "items": {"type": "string"}},
            "discoverySummary": {"type": "string"},
            "designSummary": {"type": "string"},
            "prompt": {"type": "string"},
            "followUpPrompt": {"type": "string"},
            "bridgeSessionId": {"type": "string"},
            "pluginDir": {"type": "string"},
        },
    }


def attack_plan_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": ["cwd", "planName", "planPath", "masterPlanPath"],
        "properties": {
            "cwd": {"type": "string"},
            "planName": {"type": "string"},
            "planPath": {"type": "string"},
            "masterPlanPath": {"type": "string"},
            "userGoal": {"type": "string"},
            "discoverySummary": {"type": "string"},
            "bridgeSessionId": {"type": "string"},
            "pluginDir": {"type": "string"},
        },
    }


def draft_plan_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "cwd",
            "planName",
            "discoveryPath",
            "planPath",
            "masterPlanPath",
        ],
        "properties": {
            "cwd": {"type": "string"},
            "planName": {"type": "string"},
            "discoveryPath": {"type": "string"},
            "depPartitionPath": {"type": "string"},
            "planPath": {"type": "string"},
            "masterPlanPath": {"type": "string"},
            "userGoal": {"type": "string"},
            "discoverySummary": {"type": "string"},
            "bridgeSessionId": {"type": "string"},
            "pluginDir": {"type": "string"}
        },
    }


def verify_tool_schema() -> dict[str, Any]:
    return {
        "type": "object",
        "additionalProperties": False,
        "required": [
            "cwd",
            "planName",
            "stepId",
            "stepTitle",
            "description",
            "acceptanceCriteria",
        ],
        "properties": {
            "cwd": {"type": "string"},
            "planName": {"type": "string"},
            "stepId": {"type": "integer"},
            "stepTitle": {"type": "string"},
            "description": {"type": "string"},
            "acceptanceCriteria": {"type": "string"},
            "filesInScope": {"type": "array", "items": {"type": "string"}},
            "discoveryScope": {"type": "string"},
            "discoveryConsumers": {"type": "string"},
            "discoveryBlastRadius": {"type": "string"},
            "verificationCommands": {"type": "string"},
            "bridgeSessionId": {"type": "string"},
            "pluginDir": {"type": "string"},
            "findingsDir": {"type": "string"},
        },
    }


TOOLS = [
    {
        "name": "brainstorm_start",
        "description": (
            "Queue a live Claude brainstorming session in VS Code. "
            "Use this for interactive brainstorming where the user will talk "
            "to Claude directly and Codex will read the transcript via "
            "brainstorm_status."
        ),
        "inputSchema": brainstorm_start_schema(),
    },
    {
        "name": "brainstorm_status",
        "description": (
            "Read machine-visible status and recent transcript events from a "
            "live Claude brainstorming session launched by brainstorm_start."
        ),
        "inputSchema": brainstorm_status_schema(),
    },
    {
        "name": "draft_plan",
        "description": (
            "Run a headless Claude planning pass that drafts plan.json and "
            "masterPlan.md content from discovery and dep-partition context. "
            "Claude authors the draft; Codex stays the orchestrator and reviewer."
        ),
        "inputSchema": draft_plan_schema(),
    },
    {
        "name": "attack_plan",
        "description": (
            "Run a headless Claude adversarial review of a draft plan written by Codex. "
            "Claude reads plan.json and masterPlan.md, returns structured findings, "
            "and does not become the plan authority."
        ),
        "inputSchema": attack_plan_schema(),
    },
    {
        "name": "frontend_implement",
        "description": (
            "Run a headless Claude frontend implementation pass for a visually "
            "material step. Claude edits the same working tree directly. Reuse "
            "bridgeSessionId to send Codex follow-up on the same thread."
        ),
        "inputSchema": frontend_tool_schema(),
    },
    {
        "name": "verify_step",
        "description": (
            "Run a headless Claude verification pass for a plan step. This is "
            "a hard reviewer gate. Reuse bridgeSessionId for re-verification on "
            "the same Claude thread. Non-PASS rounds write JSON findings files."
        ),
        "inputSchema": verify_tool_schema(),
    },
]


def read_message() -> dict[str, Any] | None:
    headers: dict[str, str] = {}
    while True:
        line = sys.stdin.buffer.readline()
        if not line:
            debug_log("stdin-eof")
            return None
        if line in (b"\r\n", b"\n"):
            break
        name, _, value = line.decode("utf-8").partition(":")
        headers[name.lower()] = value.strip()
    length = int(headers.get("content-length", "0"))
    if length <= 0:
        return None
    body = sys.stdin.buffer.read(length)
    if not body:
        debug_log("stdin-empty-body")
        return None
    message = json.loads(body.decode("utf-8"))
    debug_log(f"recv method={message.get('method')} id={message.get('id')}")
    return message


def write_message(payload: dict[str, Any]) -> None:
    body = json.dumps(payload).encode("utf-8")
    header = f"Content-Length: {len(body)}\r\n\r\n".encode("utf-8")
    sys.stdout.buffer.write(header)
    sys.stdout.buffer.write(body)
    sys.stdout.buffer.flush()
    debug_log(
        "send "
        + ("result" if "result" in payload else "error")
        + f" id={payload.get('id')}"
    )


def ok_response(message_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def error_response(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def tool_result(payload: dict[str, Any], *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(payload, indent=2)}],
        "structuredContent": payload,
        "isError": is_error,
    }


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    message_id = request.get("id")
    params = request.get("params") or {}

    if method == "initialize":
        protocol_version = params.get("protocolVersion") or DEFAULT_PROTOCOL_VERSION
        return ok_response(
            message_id,
            {
                "protocolVersion": protocol_version,
                "capabilities": {
                    "tools": {"listChanged": False},
                    "resources": {"subscribe": False, "listChanged": False},
                },
                "serverInfo": {"name": BRIDGE_NAME, "version": BRIDGE_VERSION},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "notifications/cancelled":
        return None
    if method == "ping":
        return ok_response(message_id, {})
    if method == "tools/list":
        return ok_response(message_id, {"tools": TOOLS, "nextCursor": None})
    if method == "resources/list":
        return ok_response(message_id, {"resources": [], "nextCursor": None})
    if method == "resources/templates/list":
        return ok_response(message_id, {"resourceTemplates": [], "nextCursor": None})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        try:
            manager = SessionManager()
            if name == "brainstorm_start":
                result = manager.create_brainstorm_request(arguments)
            elif name == "brainstorm_status":
                result = manager.read_brainstorm_status(
                    arguments["sessionId"], arguments.get("tailEvents", 40)
                )
            elif name == "draft_plan":
                result = manager.run_draft_plan(arguments)
            elif name == "attack_plan":
                result = manager.run_plan_attack(arguments)
            elif name == "frontend_implement":
                result = manager.run_frontend_implementation(arguments)
            elif name == "verify_step":
                result = manager.run_verification(arguments)
            else:
                return error_response(message_id, -32601, f"Unknown tool: {name}")
            return ok_response(message_id, tool_result(result))
        except ClaudeBridgeError as exc:
            return ok_response(
                message_id,
                tool_result({"error": str(exc), "tool": name}, is_error=True),
            )
        except Exception as exc:  # pragma: no cover - fallback guardrail
            traceback.print_exc(file=sys.stderr)
            return ok_response(
                message_id,
                tool_result(
                    {"error": f"Unexpected claude-bridge failure: {exc}", "tool": name},
                    is_error=True,
                ),
            )
    return error_response(message_id, -32601, f"Unsupported method: {method}")


def main() -> int:
    debug_log("server-start")
    print("claude-bridge MCP server running on stdio", file=sys.stderr, flush=True)
    while True:
        request = read_message()
        if request is None:
            debug_log("server-stop")
            return 0
        response = handle_request(request)
        if response is not None:
            write_message(response)


if __name__ == "__main__":
    raise SystemExit(main())
