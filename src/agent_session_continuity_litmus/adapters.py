from __future__ import annotations

import json
import os
import queue
import shutil
import socket
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .core import Fixture, RunResult, create_workspace, score_run, write_result


class JsonRpcProcess:
    def __init__(self, command: list[str]) -> None:
        self.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        self.messages: list[dict[str, Any]] = []
        self.stderr: list[str] = []
        self._queue: queue.Queue[str | None] = queue.Queue()
        self._next_id = 1
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()

    def _read_stdout(self) -> None:
        assert self.process.stdout is not None
        for line in self.process.stdout:
            self._queue.put(line)
        self._queue.put(None)

    def _read_stderr(self) -> None:
        assert self.process.stderr is not None
        self.stderr.extend(self.process.stderr)

    def _send(self, payload: dict[str, Any]) -> None:
        assert self.process.stdin is not None
        self.process.stdin.write(json.dumps(payload, separators=(",", ":")) + "\n")
        self.process.stdin.flush()

    def _read_one(self, timeout: float) -> dict[str, Any]:
        try:
            line = self._queue.get(timeout=max(0.1, timeout))
        except queue.Empty as exc:
            raise TimeoutError("timed out waiting for Codex app-server output") from exc
        if line is None:
            raise RuntimeError(f"Codex app-server exited with {self.process.poll()}")
        message = json.loads(line)
        self.messages.append(message)
        return message

    def request(self, method: str, params: dict[str, Any] | None = None, timeout: int = 300) -> tuple[dict[str, Any], int]:
        request_id = self._next_id
        self._next_id += 1
        start_index = len(self.messages)
        payload: dict[str, Any] = {"method": method, "id": request_id}
        if params is not None:
            payload["params"] = params
        self._send(payload)
        deadline = time.monotonic() + timeout
        while True:
            message = self._read_one(deadline - time.monotonic())
            if message.get("id") == request_id:
                if "error" in message:
                    raise RuntimeError(f"{method} failed: {message['error']}")
                return message.get("result", {}), start_index

    def notify(self, method: str, params: dict[str, Any] | None = None) -> None:
        payload: dict[str, Any] = {"method": method}
        if params is not None:
            payload["params"] = params
        self._send(payload)

    def wait_after(self, start: int, predicate: Callable[[dict[str, Any]], bool], timeout: int = 300) -> dict[str, Any]:
        checked = start
        deadline = time.monotonic() + timeout
        while True:
            while checked < len(self.messages):
                message = self.messages[checked]
                checked += 1
                if predicate(message):
                    return message
            self._read_one(deadline - time.monotonic())

    def close(self) -> None:
        if self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


def resolve_executable(value: str) -> str:
    resolved = value if os.sep in value else shutil.which(value)
    if resolved is None or not Path(resolved).is_file():
        raise FileNotFoundError(f"executable not found: {value}")
    return str(Path(resolved).resolve())


def client_version(executable: str) -> str:
    completed = subprocess.run(
        [executable, "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    value = completed.stdout.strip() or completed.stderr.strip()
    return value.splitlines()[0] if value else "unknown"


def _codex_agent_messages(messages: list[dict[str, Any]], start: int) -> list[str]:
    values = []
    for message in messages[start:]:
        if message.get("method") != "item/completed":
            continue
        item = message.get("params", {}).get("item", {})
        if item.get("type") == "agentMessage" and isinstance(item.get("text"), str):
            values.append(item["text"])
    return values


def _codex_tool_use(messages: list[dict[str, Any]], start: int) -> bool:
    non_tool_items = {"agentMessage", "contextCompaction", "reasoning", "userMessage"}
    return any(
        message.get("method") == "item/completed"
        and message.get("params", {}).get("item", {}).get("type") not in non_tool_items
        for message in messages[start:]
    )


def run_codex(
    fixture: Fixture,
    path: str,
    output: Path,
    *,
    codex_bin: str = "codex",
    timeout_seconds: int = 300,
) -> RunResult:
    if path not in {"baseline", "compact"}:
        raise ValueError(f"unsupported path: {path}")
    executable = resolve_executable(codex_bin)
    workspace = output / "workspace"
    artifacts = output / "artifacts"
    create_workspace(workspace)
    artifacts.mkdir(parents=True)
    rpc = JsonRpcProcess([executable, "app-server", "--stdio"])
    try:
        rpc.request(
            "initialize",
            {
                "clientInfo": {"name": "agent-session-continuity-litmus", "title": "Agent Session Continuity Litmus", "version": "0.1.0"},
                "capabilities": {"experimentalApi": True},
            },
            timeout_seconds,
        )
        rpc.notify("initialized")
        started, _ = rpc.request(
            "thread/start",
            {"cwd": str(workspace.resolve()), "approvalPolicy": "never", "sandbox": "workspace-write", "ephemeral": True},
            timeout_seconds,
        )
        thread_id = started["thread"]["id"]
        first, first_index = rpc.request(
            "turn/start",
            {"threadId": thread_id, "input": [{"type": "text", "text": fixture.phase_one}]},
            timeout_seconds,
        )
        first_turn = first["turn"]["id"]
        rpc.wait_after(
            first_index,
            lambda message: message.get("method") == "turn/completed"
            and message.get("params", {}).get("turn", {}).get("id") == first_turn,
            timeout_seconds,
        )
        if path == "compact":
            _, compact_index = rpc.request("thread/compact/start", {"threadId": thread_id}, timeout_seconds)
            compacted = rpc.wait_after(
                compact_index,
                lambda message: message.get("params", {}).get("threadId") == thread_id
                and (
                    message.get("method") == "thread/compacted"
                    or (
                        message.get("method") == "item/completed"
                        and message.get("params", {}).get("item", {}).get("type") == "contextCompaction"
                    )
                ),
                timeout_seconds,
            )
            boundary = {
                "api": "thread/compact/start",
                "complete": True,
                "completion_event": compacted.get("method"),
                "completion_item_type": compacted.get("params", {}).get("item", {}).get("type"),
                "thread_id": thread_id,
            }
        else:
            boundary = {"api": "none", "complete": True, "proof": "phase-one turn completed", "thread_id": thread_id}
        second, second_index = rpc.request(
            "turn/start",
            {"threadId": thread_id, "input": [{"type": "text", "text": fixture.phase_two}]},
            timeout_seconds,
        )
        second_turn = second["turn"]["id"]
        rpc.wait_after(
            second_index,
            lambda message: message.get("method") == "turn/completed"
            and message.get("params", {}).get("turn", {}).get("id") == second_turn,
            timeout_seconds,
        )
        messages = _codex_agent_messages(rpc.messages, second_index)
        response = messages[-1] if messages else ""
        result = score_run(
            adapter="codex-cli",
            client_version=client_version(executable),
            fixture=fixture,
            path=path,
            boundary=boundary,
            response_text=response,
            workspace=workspace,
            tool_use_after_boundary=_codex_tool_use(rpc.messages, second_index),
        )
        write_result(artifacts, result)
        return result
    finally:
        artifacts.mkdir(parents=True, exist_ok=True)
        (artifacts / "events.json").write_text(json.dumps(rpc.messages, indent=2) + "\n", encoding="utf-8")
        (artifacts / "stderr.txt").write_text("".join(rpc.stderr), encoding="utf-8")
        rpc.close()


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http_json(method: str, url: str, body: dict[str, Any] | None = None, timeout: int = 300) -> tuple[int, Any]:
    data = None if body is None else json.dumps(body).encode("utf-8")
    request = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=timeout) as response:
        raw = response.read()
        return response.status, None if not raw else json.loads(raw)


def _wait_server(url: str, process: subprocess.Popen[str], timeout: int = 30) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"opencode server exited with {process.returncode}")
        try:
            _http_json("GET", f"{url}/global/health", timeout=1)
            return
        except Exception:
            time.sleep(0.1)
    raise TimeoutError("timed out waiting for opencode server")


def _opencode_text(message: dict[str, Any]) -> str:
    return "\n".join(
        part.get("text", "")
        for part in message.get("parts", [])
        if part.get("type") == "text" and isinstance(part.get("text"), str)
    )


def _opencode_tool_use(message: dict[str, Any]) -> bool:
    return any(part.get("type") == "tool" for part in message.get("parts", []))


def run_opencode(
    fixture: Fixture,
    path: str,
    output: Path,
    *,
    opencode_bin: str = "opencode",
    timeout_seconds: int = 300,
) -> RunResult:
    if path not in {"baseline", "compact"}:
        raise ValueError(f"unsupported path: {path}")
    executable = resolve_executable(opencode_bin)
    workspace = output / "workspace"
    artifacts = output / "artifacts"
    create_workspace(workspace)
    artifacts.mkdir(parents=True)
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    process = subprocess.Popen(
        [executable, "serve", "--pure", "--hostname", "127.0.0.1", "--port", str(port), "--print-logs"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        _wait_server(base_url, process)
        query = urlencode({"directory": str(workspace.resolve())})
        model = {"providerID": "opencode", "modelID": "deepseek-v4-flash-free"}
        _, session = _http_json(
            "POST",
            f"{base_url}/session?{query}",
            {
                "title": f"{fixture.fixture_id} continuity litmus",
                "agent": "build",
                "model": {"providerID": model["providerID"], "id": model["modelID"], "variant": "default"},
            },
            timeout_seconds,
        )
        session_id = session["id"]
        _, first = _http_json(
            "POST",
            f"{base_url}/session/{session_id}/message?{query}",
            {"model": model, "agent": "build", "parts": [{"type": "text", "text": fixture.phase_one}]},
            timeout_seconds,
        )
        if path == "compact":
            status, compacted = _http_json(
                "POST",
                f"{base_url}/session/{session_id}/summarize?{query}",
                {"providerID": model["providerID"], "modelID": model["modelID"], "auto": False},
                timeout_seconds,
            )
            boundary = {
                "api": "session.summarize",
                "complete": status == 200 and compacted is True,
                "http_status": status,
                "response": compacted,
                "session_id": session_id,
            }
        else:
            boundary = {"api": "none", "complete": True, "proof": "phase-one response completed", "session_id": session_id}
        _, second = _http_json(
            "POST",
            f"{base_url}/session/{session_id}/message?{query}",
            {"model": model, "agent": "build", "parts": [{"type": "text", "text": fixture.phase_two}]},
            timeout_seconds,
        )
        _, messages = _http_json("GET", f"{base_url}/session/{session_id}/message?{query}", timeout=timeout_seconds)
        (artifacts / "first-response.json").write_text(json.dumps(first, indent=2) + "\n", encoding="utf-8")
        (artifacts / "messages.json").write_text(json.dumps(messages, indent=2) + "\n", encoding="utf-8")
        result = score_run(
            adapter="opencode-cli",
            client_version=client_version(executable),
            fixture=fixture,
            path=path,
            boundary=boundary,
            response_text=_opencode_text(second),
            workspace=workspace,
            tool_use_after_boundary=_opencode_tool_use(second),
        )
        write_result(artifacts, result)
        return result
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        stdout, stderr = process.communicate(timeout=5)
        (artifacts / "server-stdout.txt").write_text(stdout or "", encoding="utf-8")
        (artifacts / "server-stderr.txt").write_text(stderr or "", encoding="utf-8")
