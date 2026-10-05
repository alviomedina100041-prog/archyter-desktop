from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import requests
import websocket
from PySide6.QtCore import QObject, Signal


class JupyterManager(QObject):
    log_line = Signal(str)
    status_changed = Signal(str)

    def __init__(self, root_dir: str, python_executable: str | None = None):
        super().__init__()
        self.root_dir = str(Path(root_dir).expanduser().resolve())
        self.python_executable = python_executable or sys.executable
        self.process: subprocess.Popen[str] | None = None
        self.port: int | None = None
        self.token = uuid.uuid4().hex
        self._reader: threading.Thread | None = None

    @property
    def base_url(self) -> str:
        if self.port is None:
            raise RuntimeError("Jupyter aún no está iniciado.")
        return f"http://127.0.0.1:{self.port}"

    @property
    def lab_url(self) -> str:
        return f"{self.base_url}/lab?token={self.token}"

    def _free_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            return int(sock.getsockname()[1])

    def start(self, timeout: float = 35.0) -> None:
        if self.process and self.process.poll() is None:
            return

        root = Path(self.root_dir)
        root.mkdir(parents=True, exist_ok=True)
        self.port = self._free_port()
        self.token = uuid.uuid4().hex

        command = [
            self.python_executable,
            "-m",
            "jupyterlab",
            "--no-browser",
            "--ServerApp.ip=127.0.0.1",
            f"--ServerApp.port={self.port}",
            f"--ServerApp.token={self.token}",
            f"--ServerApp.root_dir={self.root_dir}",
            "--ServerApp.open_browser=False",
            "--ServerApp.allow_remote_access=False",
        ]

        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        self.status_changed.emit("iniciando")
        self.process = subprocess.Popen(
            command,
            # The project is passed explicitly to ServerApp.root_dir.
            # Do not make it the Windows process CWD: Windows can otherwise
            # keep the project directory locked briefly during shutdown.
            cwd=None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            creationflags=flags,
        )

        self._reader = threading.Thread(target=self._read_logs, daemon=True)
        self._reader.start()

        deadline = time.time() + timeout
        api_ready = False
        while time.time() < deadline:
            if self.process.poll() is not None:
                raise RuntimeError("JupyterLab se cerró durante el arranque.")

            try:
                if not api_ready:
                    response = self.api_get("/api", timeout=4)
                    api_ready = response.status_code == 200
                if api_ready:
                    response = requests.get(self.lab_url, timeout=4)
                    if response.status_code == 200:
                        self.status_changed.emit("conectado")
                        return
            except requests.RequestException:
                pass

            time.sleep(0.3)

        self.shutdown()
        raise TimeoutError("JupyterLab no quedó listo dentro del tiempo esperado.")

    def _read_logs(self) -> None:
        if not self.process or not self.process.stdout:
            return
        for line in self.process.stdout:
            cleaned = line.rstrip()
            if "token=" in cleaned:
                cleaned = cleaned.split("token=", 1)[0] + "token=••••••••"
            self.log_line.emit(cleaned)

    def api_get(
        self,
        path: str,
        params: dict[str, Any] | None = None,
        timeout: float = 6,
    ) -> requests.Response:
        return requests.get(
            f"{self.base_url}{path}",
            params={**(params or {}), "token": self.token},
            timeout=timeout,
        )

    def api_post(
        self,
        path: str,
        data: dict[str, Any] | None = None,
        timeout: float = 8,
    ) -> requests.Response:
        return requests.post(
            f"{self.base_url}{path}?token={self.token}",
            json=data or {},
            timeout=timeout,
        )

    def _relative(self, path: str | os.PathLike[str]) -> str:
        root = Path(self.root_dir).resolve()
        candidate = Path(path).expanduser().resolve()
        try:
            return candidate.relative_to(root).as_posix()
        except ValueError as exc:
            raise ValueError("La ruta está fuera del proyecto activo.") from exc

    def open_url(self, path: str | None = None) -> str:
        if not path:
            return self.lab_url
        rel = self._relative(path)
        return f"{self.base_url}/lab/tree/{quote(rel)}?token={self.token}"

    def create_notebook(self, directory: str) -> str:
        rel = self._relative(directory)
        endpoint = "/api/contents"
        if rel:
            endpoint += f"/{quote(rel)}"
        response = self.api_post(endpoint, {"type": "notebook", "ext": ".ipynb"})
        response.raise_for_status()
        created = Path(self.root_dir, response.json()["path"]).resolve()
        self._relative(created)
        return str(created)

    def sessions(self) -> list[dict[str, Any]]:
        response = self.api_get("/api/sessions")
        response.raise_for_status()
        return response.json()

    def active_session(self, path: str | None = None) -> dict[str, Any] | None:
        sessions = self.sessions()
        if not sessions:
            return None
        if path:
            wanted = self._relative(path)
            for session in sessions:
                if session.get("path") == wanted:
                    return session
        return sessions[0]

    def restart_kernel(self, kernel_id: str) -> None:
        response = self.api_post(f"/api/kernels/{kernel_id}/restart")
        response.raise_for_status()

    def close_session_for_path(self, path: str) -> None:
        rel = self._relative(path)
        for session in self.sessions():
            if session.get("path") != rel:
                continue
            session_id = session.get("id")
            if not session_id:
                return
            response = requests.delete(
                f"{self.base_url}/api/sessions/{session_id}?token={self.token}",
                timeout=6,
            )
            if response.status_code not in {204, 404}:
                response.raise_for_status()
            return

    def variable_snapshot(
        self,
        kernel_id: str,
        kernel_name: str = "",
        timeout: float = 5.0,
    ) -> list[dict[str, Any]]:
        session_id = uuid.uuid4().hex
        msg_id = uuid.uuid4().hex
        marker = "__ARCHYTER_STUDIO_VARS__"

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
        elif isinstance(_value, (dict, list, tuple, set, str, bytes)):
            _shape = f"len={len(_value)}"
        else:
            _shape = "-"
        _preview = repr(_value).replace("\n", " ")
        if len(_preview) > 90:
            _preview = _preview[:87] + "..."
        _items.append({"name": _name, "type": _type, "shape": _shape, "value": _preview})
    except Exception:
        pass
print("__ARCHYTER_STUDIO_VARS__" + json.dumps(_items))
"""

        if "julia" in kernel_name.lower():
            return []

        ws_url = (
            f"ws://127.0.0.1:{self.port}/api/kernels/{kernel_id}/channels"
            f"?token={self.token}&session_id={session_id}"
        )
        message = {
            "header": {
                "msg_id": msg_id,
                "username": "archyter-studio",
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

        ws = websocket.create_connection(
            ws_url,
            timeout=timeout,
            origin=self.base_url,
        )
        ws.send(json.dumps(message))
        deadline = time.time() + timeout

        try:
            while time.time() < deadline:
                payload = json.loads(ws.recv())
                parent = payload.get("parent_header") or {}
                if parent.get("msg_id") != msg_id:
                    continue
                msg_type = payload.get("msg_type") or payload.get("header", {}).get("msg_type")
                content = payload.get("content") or {}
                if msg_type == "stream":
                    output = content.get("text", "")
                    if marker in output:
                        return json.loads(output.split(marker, 1)[1].strip())
                if msg_type == "error":
                    return []
        finally:
            ws.close()

        return []

    def inject_shell(self, page: Any) -> None:
        page.runJavaScript(r"""
(() => {
  const previous = document.getElementById('archyter-studio-style');
  if (previous) previous.remove();

  const style = document.createElement('style');
  style.id = 'archyter-studio-style';
  style.textContent = `
    :root {
      color-scheme: light !important;
      --jp-layout-color0: #ffffff !important;
      --jp-layout-color1: #ffffff !important;
      --jp-layout-color2: #f8fafc !important;
      --jp-layout-color3: #edf3f8 !important;
      --jp-border-color0: #d5e0ea !important;
      --jp-border-color1: #dce5ed !important;
      --jp-content-font-color0: #172033 !important;
      --jp-content-font-color1: #334155 !important;
      --jp-ui-font-color0: #172033 !important;
      --jp-ui-font-color1: #475569 !important;
      --jp-brand-color1: #168ed2 !important;
      --jp-brand-color2: #38a9e8 !important;
      --jp-cell-editor-background: #ffffff !important;
      --jp-code-font-size: 12px !important;
    }
    html, body, #main, .jp-LabShell {
      width:100% !important; height:100% !important;
      margin:0 !important; padding:0 !important;
      overflow:hidden !important; background:#fff !important;
    }
    #jp-top-panel, #jp-left-stack, #jp-right-stack,
    .jp-SideBar, .jp-StatusBar {
      display:none !important; width:0 !important; height:0 !important;
    }
    #jp-main-content-panel, #jp-main-dock-panel {
      position:absolute !important; inset:0 !important;
      width:100% !important; height:100% !important;
      min-width:0 !important; min-height:0 !important;
      background:#fff !important;
    }
    .jp-MainAreaWidget, .jp-NotebookPanel, .jp-NotebookPanel-notebook,
    .jp-Notebook { width:100% !important; max-width:none !important; min-width:0 !important; }
    .jp-Notebook { padding:10px 16px 80px 16px !important; }
    .jp-NotebookPanel-toolbar {
      min-height:35px !important; height:35px !important;
      background:#fff !important; border-bottom:1px solid #e3eaf1 !important;
      padding:0 6px !important;
    }
    .lm-TabBar, .lm-TabBar-content { background:#fff !important; }
    .lm-TabBar-tab {
      min-height:31px !important; height:31px !important;
      background:#fff !important; color:#64748b !important;
      border-color:#e1e8ef !important;
    }
    .lm-TabBar-tab.lm-mod-current {
      background:#eef7ff !important; color:#075b9b !important;
      border-top:2px solid #129fe2 !important; font-weight:700 !important;
    }
    .jp-Notebook-cell {
      background:#fff !important;
      border:1px solid #dce5ed !important;
      border-left:3px solid transparent !important;
      border-radius:9px !important;
      margin:7px 0 !important;
      box-shadow:0 1px 3px rgba(15,23,42,.04) !important;
      transition:border-color 120ms ease, box-shadow 120ms ease !important;
    }
    .jp-Notebook-cell:hover { border-color:#bfd2e4 !important; }
    .jp-Notebook-cell.jp-mod-active {
      border-color:#8ac9f2 !important; border-left-color:#129fe2 !important;
      box-shadow:0 0 0 1px #c7e7fb !important;
    }
    .jp-InputArea-editor, .cm-editor, .cm-scroller, .cm-gutters,
    .jp-OutputArea-output { background:#fff !important; }
    .cm-gutters { border-right:1px solid #eef2f6 !important; color:#94a3b8 !important; }
    .jp-cell-toolbar, .jp-Cell-toolbar { display:none !important; }
    .jp-ToolbarButtonComponent {
      border-radius:6px !important;
      transition:background 120ms ease !important;
    }
    .jp-ToolbarButtonComponent:hover { background:#eaf5ff !important; }
    * { scrollbar-color:#c5d2df #fff; }
  `;
  document.documentElement.style.colorScheme='light';
  document.head.appendChild(style);

  function sendKey(key, code, extra={}) {
    const target = document.activeElement || document.querySelector('.jp-Notebook') || document.body;
    target.dispatchEvent(new KeyboardEvent('keydown', {key, code, bubbles:true, cancelable:true, ...extra}));
  }

  window.__archyterStudio = {
    save() { sendKey('s', 'KeyS', {ctrlKey:true}); },
    runCell() {
      const notebook=document.querySelector('.jp-Notebook');
      if (notebook) notebook.focus();
      sendKey('Enter','Enter',{shiftKey:true});
    },
    dirty() { return !!document.querySelector('.jp-mod-dirty'); }
  };
  window.dispatchEvent(new Event('resize'));
})();
""")

    def shutdown(self) -> None:
        process = self.process
        self.process = None

        if process:
            if process.poll() is None:
                if os.name == "nt":
                    try:
                        subprocess.run(
                            [
                                "taskkill",
                                "/PID",
                                str(process.pid),
                                "/T",
                                "/F",
                            ],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            check=False,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            timeout=6,
                        )
                        process.wait(timeout=3)
                    except Exception:
                        try:
                            process.kill()
                            process.wait(timeout=3)
                        except Exception:
                            pass
                else:
                    try:
                        process.terminate()
                        process.wait(timeout=5)
                    except Exception:
                        process.kill()
                        try:
                            process.wait(timeout=3)
                        except Exception:
                            pass

            if process.stdout is not None:
                try:
                    process.stdout.close()
                except Exception:
                    pass

        if self._reader and self._reader.is_alive():
            self._reader.join(timeout=2)
        self._reader = None

        self.port = None
        if os.name == "nt":
            time.sleep(0.2)
        self.status_changed.emit("detenido")
