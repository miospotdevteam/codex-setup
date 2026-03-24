#!/usr/bin/env python3
"""One-shot CLI wrapper around the Claude bridge session manager."""

from __future__ import annotations

import json
import sys
from typing import Any

from session_manager import ClaudeBridgeError, SessionManager


def load_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    return json.loads(raw)


def main() -> int:
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: bridge_cli.py <action>"}))
        return 2

    action = sys.argv[1]
    payload = load_payload()
    manager = SessionManager()

    try:
        if action == "brainstorm_start":
            result = manager.create_brainstorm_request(payload)
        elif action == "brainstorm_status":
            result = manager.read_brainstorm_status(
                payload["sessionId"], payload.get("tailEvents", 40)
            )
        elif action == "attack_plan":
            result = manager.run_plan_attack(payload)
        elif action == "frontend_implement":
            result = manager.run_frontend_implementation(payload)
        elif action == "verify_step":
            result = manager.run_verification(payload)
        else:
            print(json.dumps({"error": f"Unknown action: {action}"}))
            return 2
    except ClaudeBridgeError as exc:
        print(json.dumps({"error": str(exc), "tool": action}))
        return 1
    except Exception as exc:  # pragma: no cover - CLI fallback guardrail
        print(json.dumps({"error": f"Unexpected claude-bridge failure: {exc}", "tool": action}))
        return 1

    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
