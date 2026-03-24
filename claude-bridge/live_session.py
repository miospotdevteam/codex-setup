#!/usr/bin/env python3
"""Launch and log a live Claude CLI brainstorming session inside a PTY."""

from __future__ import annotations

import argparse
import json
import os
import pty
import select
import signal
import subprocess
import sys
import termios
import tty
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

HOOKS_DISABLED_SETTINGS = {"disableAllHooks": True}
LIVE_SETTING_SOURCES = "project,local"


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2) + "\n")
    tmp.replace(path)


def append_event(path: Path, kind: str, text: str) -> None:
    if not text:
        return
    event = {
        "timestamp": utc_now(),
        "type": kind,
        "text": text,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=True) + "\n")


def update_status(status_path: Path, **updates: Any) -> None:
    current: dict[str, Any] = {}
    if status_path.exists():
        try:
            current = json.loads(status_path.read_text())
        except json.JSONDecodeError:
            current = {}
    current.update(updates)
    current.setdefault("updatedAt", utc_now())
    write_json_atomic(status_path, current)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-dir", required=True)
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--prompt-file", required=True)
    parser.add_argument("--claude-command", default="claude")
    parser.add_argument("--plugin-dir")
    parser.add_argument("--title", default="Claude Brainstorm")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    session_dir = Path(args.session_dir).expanduser().resolve()
    cwd = Path(args.cwd).expanduser().resolve()
    prompt_file = Path(args.prompt_file).expanduser().resolve()
    transcript_path = session_dir / "transcript.jsonl"
    status_path = session_dir / "status.json"
    prompt = prompt_file.read_text(encoding="utf-8")

    cmd = [args.claude_command, "-n", args.title]
    cmd.extend(["--setting-sources", LIVE_SETTING_SOURCES])
    cmd.extend(["--settings", json.dumps(HOOKS_DISABLED_SETTINGS)])
    if args.plugin_dir:
        cmd.extend(["--plugin-dir", args.plugin_dir])
    cmd.append(prompt)

    env = {key: value for key, value in os.environ.items() if key != "CLAUDECODE"}
    master_fd, slave_fd = pty.openpty()
    proc = subprocess.Popen(
        cmd,
        stdin=slave_fd,
        stdout=slave_fd,
        stderr=slave_fd,
        cwd=str(cwd),
        env=env,
        close_fds=True,
    )
    os.close(slave_fd)

    update_status(
        status_path,
        state="running",
        title=args.title,
        cwd=str(cwd),
        pid=proc.pid,
        startedAt=utc_now(),
        updatedAt=utc_now(),
        transcriptPath=str(transcript_path),
        promptFile=str(prompt_file),
    )
    append_event(transcript_path, "system", f"Started: {' '.join(cmd)}")

    stdin_fd = sys.stdin.fileno()
    old_term = termios.tcgetattr(stdin_fd)
    tty.setraw(stdin_fd)

    def handle_signal(signum: int, _frame: Any) -> None:
        if proc.poll() is None:
            proc.send_signal(signum)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    try:
        while True:
            readers = [master_fd, stdin_fd]
            ready, _, _ = select.select(readers, [], [], 0.25)
            if master_fd in ready:
                data = os.read(master_fd, 4096)
                if not data:
                    break
                os.write(sys.stdout.fileno(), data)
                append_event(transcript_path, "claude", data.decode("utf-8", errors="replace"))
                update_status(status_path, state="running", updatedAt=utc_now())
            if stdin_fd in ready:
                data = os.read(stdin_fd, 1024)
                if not data:
                    break
                os.write(master_fd, data)
                append_event(transcript_path, "user", data.decode("utf-8", errors="replace"))
                update_status(status_path, state="running", updatedAt=utc_now())
            if proc.poll() is not None:
                break
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_term)

    os.close(master_fd)
    return_code = proc.wait()
    append_event(transcript_path, "system", f"Exited with code {return_code}")
    update_status(
        status_path,
        state="exited",
        exitCode=return_code,
        endedAt=utc_now(),
        updatedAt=utc_now(),
    )
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
