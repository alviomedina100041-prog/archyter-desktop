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

    def variable_snapshot(
        self,
        kernel_id: str,
        kernel_name: str = "",
        timeout: float = 5.0,
    ) -> list[dict[str, Any]]:
        """Read a lightweight variable snapshot from Python or Julia kernels."""
        session_id = uuid.uuid4().hex
        msg_id = uuid.uuid4().hex
        normalized_name = kernel_name.lower()

        assert self.server_info is not None
        ws_url = (
            f"ws://127.0.0.1:{self.server_info.port}"
            f"/api/kernels/{kernel_id}/channels"
            f"?token={self.token}&session_id={session_id}"
        )

        if "julia" in normalized_name:
            marker = "__ARCHYTER_VAR__"
            mode = "julia"
            code = r"""
for _name in names(Main; all=false, imported=false)
    _label = String(_name)
    if startswith(_label, "#") || _label in ("ans",)
        continue
    end

    try
        _value = getfield(Main, _name)
        _type = string(typeof(_value))

        if _value isa AbstractArray
            _shape = string(size(_value))
        elseif _value isa AbstractDict || _value isa AbstractString
            _shape = "len=" * string(length(_value))
        else
            _shape = "-"
        end

        _preview = sprint(show, _value)
        _preview = replace(_preview, '\n' => ' ', '\t' => ' ')
        if length(_preview) > 80
            _preview = first(_preview, 77) * "..."
        end

        println(
            "__ARCHYTER_VAR__",
            _label, "\t",
            _type, "\t",
            _shape, "\t",
            _preview,
        )
    catch
    end
end
"""
        else:
            marker = "__ARCHYTER_VARS__"
            mode = "python"
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

        ws = websocket.create_connection(
            ws_url,
            timeout=timeout,
            origin=self.base_url,
        )
        ws.send(json.dumps(request_message))

        deadline = time.time() + timeout
        collected: list[dict[str, Any]] = []

        try:
            while time.time() < deadline:
                payload = json.loads(ws.recv())
                parent = payload.get("parent_header", {}) or {}
                if parent.get("msg_id") != msg_id:
                    continue

                msg_type = (
                    payload.get("msg_type")
                    or payload.get("header", {}).get("msg_type")
                )
                content = payload.get("content", {}) or {}

                if msg_type == "stream":
                    output = content.get("text", "")

                    if mode == "python" and marker in output:
                        serialized = output.split(marker, 1)[1].strip()
                        collected = json.loads(serialized)
                        break

                    if mode == "julia":
                        for line in output.splitlines():
                            if not line.startswith(marker):
                                continue
                            fields = line[len(marker):].split("\t", 3)
                            if len(fields) == 4:
                                collected.append(
                                    {
                                        "name": fields[0],
                                        "type": fields[1],
                                        "shape": fields[2],
                                        "value": fields[3],
                                    }
                                )

                if msg_type == "status" and content.get("execution_state") == "idle":
                    if mode == "julia":
                        break

                if msg_type == "error":
                    break
        finally:
            ws.close()

        return collected

    def inject_shortcuts(self, page: Any, compact: bool = False) -> None:
        compact_css = r"""
            :root {
                --jp-ui-font-size0: 10px !important;
                --jp-ui-font-size1: 11px !important;
                --jp-ui-font-size2: 12px !important;
                --jp-code-font-size: 12px !important;
            }

            .jp-Notebook {
                padding: 6px 8px 36px 8px !important;
            }

            .jp-Notebook-cell {
                margin: 4px 0 !important;
                border-radius: 7px !important;
            }

            .jp-NotebookPanel-toolbar {
                min-height: 30px !important;
                height: 30px !important;
                padding: 0 4px !important;
            }

            .jp-Toolbar-item {
                margin: 0 1px !important;
            }

            .jp-ToolbarButtonComponent {
                min-width: 24px !important;
                min-height: 24px !important;
                padding: 2px 4px !important;
            }

            .lm-TabBar-tab {
                min-height: 29px !important;
                height: 29px !important;
                padding: 0 8px !important;
                font-size: 11px !important;
            }

            .jp-Cell-inputWrapper,
            .jp-OutputArea {
                margin: 0 !important;
            }

            .jp-InputPrompt,
            .jp-OutputPrompt {
                min-width: 40px !important;
                width: 40px !important;
                font-size: 10px !important;
            }

            .cm-editor,
            .cm-scroller,
            .jp-OutputArea-output,
            .jp-RenderedText,
            .jp-RenderedHTMLCommon {
                font-size: 12px !important;
            }

            .jp-OutputArea-output table {
                font-size: 10px !important;
            }

            .jp-OutputArea-output table th,
            .jp-OutputArea-output table td {
                padding: 2px 5px !important;
            }

            .jp-OutputArea-output img,
            .jp-OutputArea-output canvas,
            .jp-OutputArea-output svg {
                max-width: 100% !important;
                height: auto !important;
            }
        """ if compact else ""

        page.runJavaScript(
            r""" + f"""
            window.__archyterCompactCSS = {json.dumps(compact_css)};
            """ + r"""
            (() => {
                const old = document.getElementById('archyter-shell-style');
                if (old) old.remove();

                const style = document.createElement('style');
                style.id = 'archyter-shell-style';
                style.textContent = `
                    :root {
                        color-scheme: light !important;

                        --jp-layout-color0: #ffffff !important;
                        --jp-layout-color1: #ffffff !important;
                        --jp-layout-color2: #f8fafc !important;
                        --jp-layout-color3: #eef2f7 !important;
                        --jp-layout-color4: #dbe3ec !important;

                        --jp-content-font-color0: #111827 !important;
                        --jp-content-font-color1: #334155 !important;
                        --jp-content-font-color2: #64748b !important;
                        --jp-content-font-color3: #94a3b8 !important;

                        --jp-ui-font-color0: #111827 !important;
                        --jp-ui-font-color1: #334155 !important;
                        --jp-ui-font-color2: #64748b !important;
                        --jp-ui-font-color3: #94a3b8 !important;

                        --jp-brand-color0: #0369a1 !important;
                        --jp-brand-color1: #0284c7 !important;
                        --jp-brand-color2: #38bdf8 !important;
                        --jp-brand-color3: #bae6fd !important;

                        --jp-border-color0: #cbd5e1 !important;
                        --jp-border-color1: #d8dee9 !important;
                        --jp-border-color2: #e2e8f0 !important;
                        --jp-border-color3: #f1f5f9 !important;

                        --jp-cell-editor-background: #ffffff !important;
                        --jp-cell-editor-border-color: #d8dee9 !important;
                        --jp-notebook-multiselected-color: #e0f2fe !important;

                        --jp-mirror-editor-keyword-color: #7c3aed !important;
                        --jp-mirror-editor-atom-color: #0369a1 !important;
                        --jp-mirror-editor-number-color: #b45309 !important;
                        --jp-mirror-editor-def-color: #1d4ed8 !important;
                        --jp-mirror-editor-variable-color: #111827 !important;
                        --jp-mirror-editor-variable-2-color: #0f766e !important;
                        --jp-mirror-editor-variable-3-color: #047857 !important;
                        --jp-mirror-editor-punctuation-color: #475569 !important;
                        --jp-mirror-editor-property-color: #1d4ed8 !important;
                        --jp-mirror-editor-operator-color: #334155 !important;
                        --jp-mirror-editor-comment-color: #64748b !important;
                        --jp-mirror-editor-string-color: #be123c !important;
                        --jp-mirror-editor-string-2-color: #c2410c !important;
                        --jp-mirror-editor-meta-color: #0369a1 !important;
                        --jp-mirror-editor-qualifier-color: #7c3aed !important;
                        --jp-mirror-editor-builtin-color: #7c3aed !important;
                        --jp-mirror-editor-bracket-color: #334155 !important;
                        --jp-mirror-editor-tag-color: #be123c !important;
                        --jp-mirror-editor-attribute-color: #1d4ed8 !important;
                        --jp-mirror-editor-header-color: #0f172a !important;
                        --jp-mirror-editor-quote-color: #475569 !important;
                        --jp-mirror-editor-link-color: #0369a1 !important;
                        --jp-mirror-editor-error-color: #dc2626 !important;
                    }

                    html,
                    body,
                    #main,
                    .jp-LabShell {
                        width: 100% !important;
                        height: 100% !important;
                        min-width: 0 !important;
                        min-height: 0 !important;
                        margin: 0 !important;
                        padding: 0 !important;
                        overflow: hidden !important;
                        background: #ffffff !important;
                        color: #111827 !important;
                    }

                    #jp-top-panel,
                    #jp-left-stack,
                    #jp-right-stack,
                    .jp-SideBar,
                    .jp-StatusBar {
                        display: none !important;
                        width: 0 !important;
                        height: 0 !important;
                        min-width: 0 !important;
                        min-height: 0 !important;
                    }

                    #jp-main-content-panel,
                    #jp-main-dock-panel {
                        position: absolute !important;
                        inset: 0 !important;
                        left: 0 !important;
                        right: 0 !important;
                        top: 0 !important;
                        bottom: 0 !important;
                        width: 100% !important;
                        height: 100% !important;
                        min-width: 0 !important;
                        min-height: 0 !important;
                        max-width: none !important;
                        max-height: none !important;
                        transform: none !important;
                        background: #ffffff !important;
                    }

                    #jp-main-dock-panel > .lm-DockPanel-widget,
                    .jp-MainAreaWidget,
                    .jp-NotebookPanel,
                    .jp-NotebookPanel-notebook,
                    .jp-Notebook {
                        width: 100% !important;
                        max-width: none !important;
                        min-width: 0 !important;
                        background: #ffffff !important;
                        color: #111827 !important;
                    }

                    .jp-NotebookPanel {
                        height: 100% !important;
                    }

                    .jp-Notebook {
                        padding: 12px 16px 80px 16px !important;
                    }

                    .jp-Notebook-cell {
                        background: #ffffff !important;
                        border: 1px solid #e2e8f0 !important;
                        border-radius: 10px !important;
                        margin: 8px 0 !important;
                        box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
                    }

                    .jp-Notebook-cell.jp-mod-active {
                        border-color: #7dd3fc !important;
                        box-shadow: 0 0 0 1px #bae6fd !important;
                    }

                    .jp-NotebookPanel-toolbar,
                    .lm-TabBar,
                    .lm-TabBar-content {
                        background: #ffffff !important;
                        border-color: #d8dee9 !important;
                        color: #111827 !important;
                    }

                    .lm-TabBar-tab {
                        background: #ffffff !important;
                        color: #475569 !important;
                        border-color: #e2e8f0 !important;
                    }

                    .lm-TabBar-tab.lm-mod-current {
                        background: #f8fafc !important;
                        color: #0f172a !important;
                        border-top: 2px solid #38bdf8 !important;
                    }

                    .jp-InputArea-editor,
                    .jp-OutputArea-output,
                    .cm-editor,
                    .cm-scroller,
                    .cm-gutters {
                        background: #ffffff !important;
                        color: #111827 !important;
                        border-radius: 8px !important;
                    }

                    .cm-gutters {
                        border-right: 1px solid #eef2f7 !important;
                        color: #94a3b8 !important;
                    }

                    .cm-activeLine,
                    .cm-activeLineGutter {
                        background: #f8fafc !important;
                    }

                    .cm-selectionBackground,
                    ::selection {
                        background: #dbeafe !important;
                    }

                    .jp-OutputArea-output pre,
                    .jp-RenderedText pre,
                    .jp-RenderedHTMLCommon,
                    .jp-MarkdownOutput {
                        color: #111827 !important;
                        background: #ffffff !important;
                    }

                    .jp-ToolbarButtonComponent,
                    .jp-ToolbarButtonComponent svg,
                    .jp-icon3,
                    .jp-icon-selectable {
                        color: #334155 !important;
                        fill: #334155 !important;
                    }

                    .jp-ToolbarButtonComponent:hover {
                        background: #f1f5f9 !important;
                    }

                    * {
                        scrollbar-color: #cbd5e1 #ffffff;
                    }

                    ${window.__archyterCompactCSS || ''}
                `;

                document.documentElement.style.colorScheme = 'light';
                document.body.style.colorScheme = 'light';
                document.head.appendChild(style);

                const forceFullLayout = () => {
                    for (const selector of [
                        '#jp-main-content-panel',
                        '#jp-main-dock-panel'
                    ]) {
                        const node = document.querySelector(selector);
                        if (!node) continue;
                        node.style.setProperty('left', '0', 'important');
                        node.style.setProperty('right', '0', 'important');
                        node.style.setProperty('top', '0', 'important');
                        node.style.setProperty('bottom', '0', 'important');
                        node.style.setProperty('width', '100%', 'important');
                        node.style.setProperty('height', '100%', 'important');
                        node.style.setProperty('transform', 'none', 'important');
                        node.style.setProperty('background', '#ffffff', 'important');
                    }
                    window.dispatchEvent(new Event('resize'));
                };

                forceFullLayout();
                requestAnimationFrame(forceFullLayout);
                setTimeout(forceFullLayout, 250);
                setTimeout(forceFullLayout, 1000);

                function sendKey(key, code, extra = {}) {
                    const target =
                        document.activeElement ||
                        document.querySelector('.jp-Notebook') ||
                        document.body;

                    target.dispatchEvent(
                        new KeyboardEvent('keydown', {
                            key,
                            code,
                            bubbles: true,
                            cancelable: true,
                            ...extra
                        })
                    );
                }

                window.__archyter = {
                    save() {
                        sendKey('s', 'KeyS', {ctrlKey: true});
                    },
                    runCell() {
                        const notebook = document.querySelector('.jp-Notebook');
                        if (notebook) notebook.focus();
                        sendKey('Enter', 'Enter', {shiftKey: true});
                    },
                    refit() {
                        forceFullLayout();
                    }
                };
            })();
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
