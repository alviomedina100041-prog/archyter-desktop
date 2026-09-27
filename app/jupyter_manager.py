from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
import websocket
from PySide6.QtCore import QObject, Signal


@dataclass
class ServerInfo:
    port: int
    token: str
    root_dir: str


class JupyterServerManager(QObject):
    log_line = Signal(str)
    status_changed = Signal(str)

    def __init__(self, root_dir: str | None = None, python_executable: str | None = None):
        super().__init__()
        self.root_dir = os.path.abspath(root_dir or os.getcwd())
        self.python_executable = python_executable or sys.executable
        self.process: subprocess.Popen[str] | None = None
        self.server_info: ServerInfo | None = None
        self._reader_thread: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        if not self.server_info:
            raise RuntimeError("Jupyter server is not running.")
        return f"http://127.0.0.1:{self.server_info.port}"

    @property
    def token(self) -> str:
        if not self.server_info:
            raise RuntimeError("Jupyter server is not running.")
        return self.server_info.token

    def _free_port(self) -> int:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        sock.close()
        return port

    def start(self, timeout: float = 30.0) -> None:
        if self.process and self.process.poll() is None:
            return

        Path(self.root_dir).mkdir(parents=True, exist_ok=True)
        port = self._free_port()
        token = uuid.uuid4().hex
        self.server_info = ServerInfo(port=port, token=token, root_dir=self.root_dir)

        command = [
            self.python_executable,
            "-m",
            "jupyterlab",
            "--no-browser",
            "--ServerApp.ip=127.0.0.1",
            f"--ServerApp.port={port}",
            f"--ServerApp.token={token}",
            f"--ServerApp.root_dir={self.root_dir}",
            "--ServerApp.allow_origin=*",
        ]

        self.status_changed.emit("iniciando")
        self.process = subprocess.Popen(
            command,
            cwd=self.root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )

        self._reader_thread = threading.Thread(target=self._read_logs, daemon=True)
        self._reader_thread.start()

        deadline = time.time() + timeout
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError("JupyterLab se cerró antes de iniciar.")
            try:
                response = self.api_get("/api")
                if response.status_code == 200:
                    self.status_changed.emit("conectado")
                    return
            except Exception:
                time.sleep(0.35)

        raise TimeoutError("No se pudo iniciar JupyterLab a tiempo.")

    def _read_logs(self) -> None:
        if not self.process or not self.process.stdout:
            return
        for line in self.process.stdout:
            self.log_line.emit(line.rstrip())

    def api_get(self, path: str, params: dict[str, Any] | None = None) -> requests.Response:
        return requests.get(
            f"{self.base_url}{path}",
            params={**(params or {}), "token": self.token},
            timeout=5,
        )

    def api_post(self, path: str, json_data: dict[str, Any] | None = None) -> requests.Response:
        return requests.post(
            f"{self.base_url}{path}?token={self.token}",
            json=json_data or {},
            timeout=8,
        )

    def list_sessions(self) -> list[dict[str, Any]]:
        response = self.api_get("/api/sessions")
        response.raise_for_status()
        return response.json()

    def list_kernels(self) -> list[dict[str, Any]]:
        response = self.api_get("/api/kernels")
        response.raise_for_status()
        return response.json()

    def active_session(self) -> dict[str, Any] | None:
        sessions = self.list_sessions()
        return sessions[0] if sessions else None

    def current_kernel_id(self) -> str | None:
        session = self.active_session()
        if session and "kernel" in session:
            return session["kernel"]["id"]

        kernels = self.list_kernels()
        return kernels[0]["id"] if kernels else None

    def restart_kernel(self, kernel_id: str) -> None:
        response = self.api_post(f"/api/kernels/{kernel_id}/restart")
        response.raise_for_status()

    def open_url_for_path(self, path: str | os.PathLike[str] | None = None) -> str:
        if path:
            relative = os.path.relpath(os.fspath(path), self.root_dir).replace("\\", "/")
            return f"{self.base_url}/lab/tree/{quote(relative)}?token={self.token}"
        return f"{self.base_url}/lab?token={self.token}"

    def create_notebook(self, directory: str | None = None) -> str:
        rel_dir = ""
        if directory:
            rel_dir = os.path.relpath(directory, self.root_dir).replace("\\", "/")
            if rel_dir == ".":
                rel_dir = ""

        endpoint = "/api/contents"
        if rel_dir:
            endpoint += f"/{quote(rel_dir)}"

        response = self.api_post(endpoint, {"type": "notebook", "ext": ".ipynb"})
        response.raise_for_status()
        data = response.json()
        return os.path.join(self.root_dir, data["path"])

    def variable_snapshot(self, kernel_id: str, timeout: float = 5.0) -> list[dict[str, Any]]:
        marker = "__ARCHYTER_VARS__"
        session_id = uuid.uuid4().hex
        msg_id = uuid.uuid4().hex

        assert self.server_info is not None
        ws_url = (
            f"ws://127.0.0.1:{self.server_info.port}"
            f"/api/kernels/{kernel_id}/channels"
            f"?token={self.token}&session_id={session_id}"
        )

        code = r"""
import json
_skip = {"In", "Out", "exit", "quit", "get_ipython"}
_items = []
for _name, _value in list(globals().items()):
    if _name.startswith("_") or _name in _skip:
        continue
    try:
        _type = type(_value).__name__
        if hasattr(_value, "shape"):
            _shape = str(getattr(_value, "shape"))
        elif isinstance(_value, dict):
            _shape = f"len={len(_value)}"
        elif isinstance(_value, (list, tuple, set, str, bytes)):
            _shape = f"len={len(_value)}"
        else:
            _shape = "-"
        _preview = repr(_value)
        if len(_preview) > 80:
            _preview = _preview[:77] + "..."
        _items.append({
            "name": _name,
            "type": _type,
            "shape": _shape,
            "value": _preview,
        })
    except Exception:
        pass
print("__ARCHYTER_VARS__" + json.dumps(_items))
"""

        request_message = {
            "header": {
                "msg_id": msg_id,
                "username": "archyter",
                "session": session_id,
                "date": datetime.now(timezone.utc).isoformat(),
                "msg_type": "execute_request",
                "version": "5.3",
            },
            "parent_header": {},
            "metadata": {},
            "content": {
                "code": code,
                "silent": False,
                "store_history": False,
                "user_expressions": {},
                "allow_stdin": False,
                "stop_on_error": True,
            },
            "channel": "shell",
            "buffers": [],
        }

        ws = websocket.create_connection(ws_url, timeout=timeout, origin=self.base_url)
        ws.send(json.dumps(request_message))

        deadline = time.time() + timeout
        collected: list[dict[str, Any]] = []

        try:
            while time.time() < deadline:
                payload = json.loads(ws.recv())
                parent = payload.get("parent_header", {}) or {}
                if parent.get("msg_id") != msg_id:
                    continue

                msg_type = payload.get("msg_type") or payload.get("header", {}).get("msg_type")
                content = payload.get("content", {}) or {}

                if msg_type == "stream":
                    output = content.get("text", "")
                    if marker in output:
                        serialized = output.split(marker, 1)[1].strip()
                        collected = json.loads(serialized)
                        break

                if msg_type == "error":
                    break
        finally:
            ws.close()

        return collected

    def inject_shortcuts(self, page: Any) -> None:
        page.runJavaScript(
            """
            window.__archyter = {
                save() {
                    document.dispatchEvent(new KeyboardEvent(
                        'keydown',
                        {key:'s', code:'KeyS', ctrlKey:true, bubbles:true}
                    ));
                },
                runCell() {
                    document.dispatchEvent(new KeyboardEvent(
                        'keydown',
                        {key:'Enter', code:'Enter', shiftKey:true, bubbles:true}
                    ));
                }
            };
            """
        )

    def shutdown(self) -> None:
        if self.process and self.process.poll() is None:
            try:
                self.process.terminate()
                self.process.wait(timeout=4)
            except Exception:
                self.process.kill()

        self.status_changed.emit("detenido")
