"""State and Claude subprocess management for the claude-bridge MCP server."""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

CLAUDE_TIMEOUT_SECONDS = int(os.environ.get("CLAUDE_BRIDGE_TIMEOUT", "10800"))
DEFAULT_FINDINGS_DIR = (
    Path.home() / "Projects" / "codex-setup" / "usage-errors" / "claude-findings"
)
VERIFY_CATEGORIES = {
    "INCOMPLETE_WORK",
    "MISSED_CONSUMER",
    "TYPE_SAFETY",
    "SILENT_SCOPE_CUT",
    "WRONG_PATTERN",
    "MISSING_TEST",
    "MISSING_I18N",
    "OTHER",
}
VERIFY_SEVERITIES = {"HIGH", "MEDIUM", "LOW"}


class ClaudeBridgeError(RuntimeError):
    """Raised when the bridge cannot complete a Claude action."""


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def today_string() -> str:
    return datetime.now(UTC).date().isoformat()


def write_json_atomic(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def resolve_first_path(candidates: list[Path]) -> Path | None:
    for candidate in candidates:
        expanded = candidate.expanduser()
        if expanded.exists():
            return expanded.resolve()
    return None


@dataclass
class SessionRecord:
    bridge_session_id: str
    mode: str
    cwd: str
    claude_session_id: str | None = None
    rounds: int = 0
    created_at: str = field(default_factory=utc_now)
    updated_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)


class SessionManager:
    def __init__(self, state_root: Path | None = None) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.state_root = Path(
            state_root
            or os.environ.get("CLAUDE_BRIDGE_HOME")
            or (Path.home() / ".claude-bridge")
        ).expanduser().resolve()
        self.requests_dir = self.state_root / "requests"
        self.live_dir = self.state_root / "live" / "brainstorm"
        self.runs_dir = self.state_root / "runs"
        self.sessions_path = self.state_root / "sessions.json"
        self.heartbeat_path = self.state_root / "extension-heartbeat.json"
        try:
            self.state_root.mkdir(parents=True, exist_ok=True)
            self.requests_dir.mkdir(parents=True, exist_ok=True)
            self.live_dir.mkdir(parents=True, exist_ok=True)
            self.runs_dir.mkdir(parents=True, exist_ok=True)
        except PermissionError as exc:
            raise ClaudeBridgeError(
                f"claude-bridge could not create its state directory at {self.state_root}. "
                "Set CLAUDE_BRIDGE_HOME to a writable path and retry."
            ) from exc
        self._sessions = {
            item["bridge_session_id"]: SessionRecord(**item)
            for item in read_json(self.sessions_path, [])
        }

    def _save_sessions(self) -> None:
        payload = [
            asdict(record)
            for record in sorted(self._sessions.values(), key=lambda item: item.created_at)
        ]
        write_json_atomic(self.sessions_path, payload)

    def resolve_claude_command(self) -> str:
        override = os.environ.get("CLAUDE_BRIDGE_CLAUDE_CMD")
        if override:
            return override

        resolved = shutil.which("claude")
        if not resolved:
            raise ClaudeBridgeError("Claude CLI is not installed or not on PATH.")
        return resolved

    def resolve_plugin_dir(self, override: str | None = None) -> str | None:
        if override:
            path = Path(override).expanduser()
            return str(path.resolve()) if path.exists() else None

        env_override = os.environ.get("CLAUDE_BRIDGE_PLUGIN_DIR")
        if env_override:
            path = Path(env_override).expanduser()
            return str(path.resolve()) if path.exists() else None

        candidate = resolve_first_path(
            [
                Path.home() / "Projects" / "claude-code-setup" / "look-before-you-leap",
                Path.home() / "projects" / "claude-code-setup" / "look-before-you-leap",
            ]
        )
        return str(candidate) if candidate else None

    def require_extension_heartbeat(self, max_age_seconds: int = 30) -> dict[str, Any]:
        heartbeat = read_json(self.heartbeat_path, {})
        if not heartbeat:
            raise ClaudeBridgeError(
                "The Claude brainstorming extension is not running. Install the "
                "claude-bridge VS Code extension and make sure VS Code is open."
            )
        timestamp = heartbeat.get("timestamp")
        if not timestamp:
            raise ClaudeBridgeError("The Claude brainstorming extension heartbeat is invalid.")
        try:
            heartbeat_time = datetime.fromisoformat(timestamp)
        except ValueError as exc:
            raise ClaudeBridgeError("The Claude brainstorming extension heartbeat is unreadable.") from exc
        age = (datetime.now(UTC) - heartbeat_time).total_seconds()
        if age > max_age_seconds:
            raise ClaudeBridgeError(
                "The Claude brainstorming extension heartbeat is stale. Open VS Code "
                "and wait for the claude-bridge extension to activate."
            )
        return heartbeat

    def create_brainstorm_request(self, args: dict[str, Any]) -> dict[str, Any]:
        heartbeat = self.require_extension_heartbeat()
        cwd = Path(args["cwd"]).expanduser().resolve()
        session_id = args.get("sessionId") or str(uuid.uuid4())
        title = args.get("title") or f"Claude Brainstorm {session_id[:8]}"
        prompt = args["prompt"].strip()
        session_dir = self.live_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        prompt_file = session_dir / "prompt.txt"
        prompt_file.write_text(prompt + "\n", encoding="utf-8")
        request_path = self.requests_dir / f"start-brainstorm-{session_id}.json"
        request = {
            "action": "start-brainstorm",
            "sessionId": session_id,
            "title": title,
            "cwd": str(cwd),
            "sessionDir": str(session_dir),
            "promptFile": str(prompt_file),
            "scriptPath": str((self.repo_root / "claude-bridge" / "live_session.py").resolve()),
            "claudeCommand": self.resolve_claude_command(),
            "pluginDir": self.resolve_plugin_dir(args.get("pluginDir")),
            "createdAt": utc_now(),
        }
        write_json_atomic(request_path, request)
        return {
            "sessionId": session_id,
            "status": "queued",
            "requestPath": str(request_path),
            "sessionDir": str(session_dir),
            "extensionHeartbeat": heartbeat,
        }

    def read_brainstorm_status(self, session_id: str, tail_events: int = 40) -> dict[str, Any]:
        self.require_extension_heartbeat()
        session_dir = self.live_dir / session_id
        status = read_json(
            session_dir / "status.json",
            {
                "state": "queued",
                "updatedAt": None,
                "cwd": None,
                "transcriptPath": str(session_dir / "transcript.jsonl"),
            },
        )
        transcript = self._read_transcript_tail(Path(status["transcriptPath"]), tail_events)
        return {
            "sessionId": session_id,
            "state": status.get("state", "queued"),
            "updatedAt": status.get("updatedAt"),
            "startedAt": status.get("startedAt"),
            "endedAt": status.get("endedAt"),
            "exitCode": status.get("exitCode"),
            "cwd": status.get("cwd"),
            "transcript": transcript,
        }

    def _read_transcript_tail(self, transcript_path: Path, limit: int) -> list[dict[str, Any]]:
        if not transcript_path.exists():
            return []
        lines = transcript_path.read_text(encoding="utf-8", errors="replace").splitlines()
        tail = lines[-limit:]
        events: list[dict[str, Any]] = []
        for line in tail:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return events

    def _get_or_create_session(
        self,
        *,
        mode: str,
        cwd: str,
        bridge_session_id: str | None,
        metadata: dict[str, Any] | None = None,
    ) -> SessionRecord:
        if bridge_session_id:
            existing = self._sessions.get(bridge_session_id)
            if not existing:
                raise ClaudeBridgeError(f"Unknown bridge session: {bridge_session_id}")
            if existing.mode != mode:
                raise ClaudeBridgeError(
                    f"Bridge session {bridge_session_id} belongs to {existing.mode}, not {mode}."
                )
            existing.updated_at = utc_now()
            if metadata:
                existing.metadata.update(metadata)
            self._save_sessions()
            return existing

        record = SessionRecord(
            bridge_session_id=str(uuid.uuid4()),
            mode=mode,
            cwd=cwd,
            metadata=metadata or {},
        )
        self._sessions[record.bridge_session_id] = record
        self._save_sessions()
        return record

    def load_schema(self, name: str) -> dict[str, Any]:
        path = self.repo_root / "claude-bridge" / "schemas" / name
        return read_json(path, {})

    def run_frontend_implementation(self, args: dict[str, Any]) -> dict[str, Any]:
        cwd = str(Path(args["cwd"]).expanduser().resolve())
        record = self._get_or_create_session(
            mode="frontend",
            cwd=cwd,
            bridge_session_id=args.get("bridgeSessionId"),
            metadata={
                "stepId": args["stepId"],
                "stepTitle": args["stepTitle"],
                "planName": args.get("planName"),
            },
        )
        prompt = self._build_frontend_prompt(args, round_number=record.rounds + 1)
        result = self._run_structured_claude(
            record=record,
            cwd=Path(cwd),
            prompt=prompt,
            schema=self.load_schema("frontend-implement.json"),
            allow_edits=True,
            plugin_dir=self.resolve_plugin_dir(args.get("pluginDir")),
        )
        result.update(
            {
                "bridgeSessionId": record.bridge_session_id,
                "claudeSessionId": record.claude_session_id,
                "round": record.rounds,
            }
        )
        return result

    def run_verification(self, args: dict[str, Any]) -> dict[str, Any]:
        cwd = str(Path(args["cwd"]).expanduser().resolve())
        record = self._get_or_create_session(
            mode="verify",
            cwd=cwd,
            bridge_session_id=args.get("bridgeSessionId"),
            metadata={
                "stepId": args["stepId"],
                "stepTitle": args["stepTitle"],
                "planName": args["planName"],
            },
        )
        prompt = self._build_verify_prompt(args)
        result = self._run_structured_claude(
            record=record,
            cwd=Path(cwd),
            prompt=prompt,
            schema=self.load_schema("verify-step.json"),
            allow_edits=False,
            plugin_dir=None,
            disable_slash_commands=True,
            allowed_tools=[
                "Read",
                "Grep",
                "Glob",
                "LS",
                "Bash(git status:*)",
                "Bash(git diff:*)",
                "Bash(find:*)",
                "Bash(bash -n:*)",
                "Bash(python3 -m py_compile:*)",
                "Bash(python3 -m unittest:*)",
            ],
        )
        self._validate_findings(result)
        findings_path: str | None = None
        if result["status"] != "PASS":
            findings_path = str(self._write_findings_file(record, args, result))
        result.update(
            {
                "bridgeSessionId": record.bridge_session_id,
                "claudeSessionId": record.claude_session_id,
                "round": record.rounds,
                "findingsPath": findings_path,
            }
        )
        return result

    def _validate_findings(self, result: dict[str, Any]) -> None:
        for finding in result.get("findings", []):
            severity = finding.get("severity")
            category = finding.get("category")
            if severity not in VERIFY_SEVERITIES:
                raise ClaudeBridgeError(f"Claude returned an invalid severity: {severity}")
            if category not in VERIFY_CATEGORIES:
                raise ClaudeBridgeError(f"Claude returned an invalid category: {category}")

    def _write_findings_file(
        self,
        record: SessionRecord,
        args: dict[str, Any],
        result: dict[str, Any],
    ) -> Path:
        findings_dir = Path(args.get("findingsDir") or DEFAULT_FINDINGS_DIR).expanduser().resolve()
        findings_dir.mkdir(parents=True, exist_ok=True)
        suffix = ""
        if record.rounds > 1:
            suffix = f"-reverify-{record.rounds - 1}"
        filename = (
            f"{today_string()}-{args['planName']}-step-{args['stepId']}{suffix}.json"
        )
        output_path = findings_dir / filename
        payload = {
            "plan": args["planName"],
            "project": str(Path(args["cwd"]).expanduser().resolve()),
            "step": args["stepId"],
            "stepTitle": args["stepTitle"],
            "acceptanceCriteria": args["acceptanceCriteria"],
            "date": today_string(),
            "findings": result.get("findings", []),
        }
        write_json_atomic(output_path, payload)
        return output_path

    def _run_structured_claude(
        self,
        *,
        record: SessionRecord,
        cwd: Path,
        prompt: str,
        schema: dict[str, Any],
        allow_edits: bool,
        plugin_dir: str | None,
        bare_mode: bool = False,
        disable_slash_commands: bool = False,
        allowed_tools: list[str] | None = None,
    ) -> dict[str, Any]:
        claude_cmd = self.resolve_claude_command()
        record.rounds += 1
        record.updated_at = utc_now()
        self._save_sessions()

        cmd = [
            claude_cmd,
            "-p",
            prompt,
            "--output-format",
            "stream-json",
            "--verbose",
            "--json-schema",
            json.dumps(schema),
            "--permission-mode",
            "acceptEdits" if allow_edits else "default",
            "--add-dir",
            str(cwd),
        ]
        if bare_mode:
            cmd.append("--bare")
        if disable_slash_commands:
            cmd.append("--disable-slash-commands")
        if allowed_tools:
            cmd.extend(["--allowedTools", ",".join(allowed_tools)])
        if plugin_dir:
            cmd.extend(["--plugin-dir", plugin_dir])
        if record.claude_session_id:
            cmd.extend(["--resume", record.claude_session_id])

        env = {key: value for key, value in os.environ.items() if key != "CLAUDECODE"}
        raw_dir = self.runs_dir / record.mode / record.bridge_session_id
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_path = raw_dir / f"round-{record.rounds}.jsonl"

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(cwd),
            env=env,
            bufsize=1,
        )
        assert process.stdout is not None
        assert process.stderr is not None

        result_event: dict[str, Any] | None = None
        candidate_payloads: list[dict[str, Any]] = []
        with raw_path.open("w", encoding="utf-8") as raw_handle:
            for line in process.stdout:
                raw_handle.write(line)
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if event.get("type") == "system" and event.get("subtype") == "init":
                    session_id = event.get("session_id")
                    if session_id:
                        record.claude_session_id = session_id
                if event.get("type") == "result":
                    session_id = event.get("session_id")
                    if session_id:
                        record.claude_session_id = session_id
                    result_event = event
                candidate = self._extract_candidate_payload(event)
                if candidate is not None:
                    candidate_payloads.append(candidate)

        stderr_text = process.stderr.read()
        try:
            return_code = process.wait(timeout=CLAUDE_TIMEOUT_SECONDS)
        except subprocess.TimeoutExpired as exc:
            process.kill()
            raise ClaudeBridgeError("Claude CLI timed out before returning a result.") from exc
        finally:
            record.updated_at = utc_now()
            self._save_sessions()

        if result_event is None:
            message = stderr_text.strip() or f"Claude exited with code {return_code} without a result."
            raise ClaudeBridgeError(self._normalize_error(message))

        if result_event.get("is_error"):
            errors = result_event.get("errors") or []
            result_text = result_event.get("result", "")
            message = "\n".join(errors) if errors else result_text
            if stderr_text.strip():
                message = f"{message}\n{stderr_text.strip()}".strip()
            raise ClaudeBridgeError(self._normalize_error(message))

        structured_output = result_event.get("structured_output")
        if isinstance(structured_output, dict):
            return structured_output

        payload_text = (result_event.get("result") or "").strip()
        if not payload_text:
            if candidate_payloads:
                return candidate_payloads[-1]
            raise ClaudeBridgeError("Claude returned an empty structured response.")
        try:
            return self._parse_json_payload(payload_text)
        except json.JSONDecodeError as exc:
            if candidate_payloads:
                return candidate_payloads[-1]
            raise ClaudeBridgeError(
                "Claude returned invalid JSON despite the requested schema."
            ) from exc

    def _extract_candidate_payload(self, event: dict[str, Any]) -> dict[str, Any] | None:
        message = event.get("message")
        if not isinstance(message, dict):
            return None

        content = message.get("content")
        if not isinstance(content, list):
            return None

        for item in content:
            if not isinstance(item, dict):
                continue
            if item.get("type") == "tool_use" and item.get("name") == "StructuredOutput":
                payload = item.get("input")
                if isinstance(payload, dict):
                    return payload
            if item.get("type") == "text":
                text = item.get("text")
                if not isinstance(text, str):
                    continue
                try:
                    return self._parse_json_payload(text)
                except json.JSONDecodeError:
                    continue

        return None

    def _normalize_error(self, message: str) -> str:
        if "Not logged in" in message or "/login" in message:
            return (
                "Claude CLI is not authenticated for headless bridge use. "
                "Run `claude /login` and then retry."
            )
        return message.strip() or "Claude bridge request failed."

    def _parse_json_payload(self, payload_text: str) -> dict[str, Any]:
        try:
            parsed = json.loads(payload_text)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            return parsed

        for match in re.finditer(r"```(?:json)?\s*([\s\S]*?)```", payload_text, re.IGNORECASE):
            fenced_payload = match.group(1).strip()
            if not fenced_payload:
                continue
            try:
                parsed = json.loads(fenced_payload)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

        decoder = json.JSONDecoder()
        for index, char in enumerate(payload_text):
            if char not in "{[":
                continue
            try:
                parsed, _ = decoder.raw_decode(payload_text[index:])
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, dict):
                return parsed

        raise json.JSONDecodeError("Unable to find structured JSON payload.", payload_text, 0)

    def _build_frontend_prompt(self, args: dict[str, Any], round_number: int) -> str:
        files = ", ".join(args.get("filesInScope") or []) or "(not specified)"
        plan_name = args.get("planName") or "(not specified)"
        design = args.get("designSummary") or "(not provided)"
        discovery = args.get("discoverySummary") or "(not provided)"
        follow_up = args.get("followUpPrompt") or "(none)"
        return f"""
You are Claude acting as a step-scoped frontend implementation specialist.
Codex remains the orchestrator. Edit the existing working tree directly.

Plan: {plan_name}
Step: {args["stepId"]} - {args["stepTitle"]}
Round: {round_number}

Description:
{args["description"]}

Acceptance criteria:
{args["acceptanceCriteria"]}

Files in scope:
{files}

Discovery context:
{discovery}

Approved design context:
{design}

Explicit implementation request:
{args["prompt"]}

Codex follow-up request for this round:
{follow_up}

Rules:
- Prefer extracting shared components or reusable UI logic when it is justified.
- Stay consistent with the existing app design language and component patterns.
- Do not silently introduce a new visual system.
- If the approved direction requires a deviation from existing patterns, flag it.
- If you notice adjacent visual inconsistencies, mention them without expanding scope.
- Keep changes focused on this step.
- Return only JSON matching the requested schema.
""".strip()

    def _build_verify_prompt(self, args: dict[str, Any]) -> str:
        template = (
            self.repo_root / "claude-bridge" / "prompts" / "verify-template.md"
        ).read_text(encoding="utf-8")
        mapping = {
            "cwd": str(Path(args["cwd"]).expanduser().resolve()),
            "planName": args["planName"],
            "stepId": args["stepId"],
            "stepTitle": args["stepTitle"],
            "description": args["description"],
            "acceptanceCriteria": args["acceptanceCriteria"],
            "filesInScope": ", ".join(args.get("filesInScope") or []) or "(not specified)",
            "discoveryScope": args.get("discoveryScope") or "(not provided)",
            "discoveryConsumers": args.get("discoveryConsumers") or "(not provided)",
            "discoveryBlastRadius": args.get("discoveryBlastRadius") or "(not provided)",
            "verificationCommands": args.get("verificationCommands") or "(not provided)",
        }
        return template.format_map(mapping)
