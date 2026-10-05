from __future__ import annotations

import json
import threading
import uuid
from pathlib import Path

from jupyter_client import KernelManager
from PySide6.QtCore import QObject, Signal


class NativeKernelController(QObject):
    state_changed = Signal(str, str)
    execution_finished = Signal(str, str, bool, int)
    variables_ready = Signal(object)
    error = Signal(str)

    def __init__(self, root_dir: str, kernel_name: str = "python3"):
        super().__init__()
        self.root_dir = str(Path(root_dir).resolve())
        self.kernel_name = kernel_name
        self._manager: KernelManager | None = None
        self._client = None
        self._lock = threading.RLock()
        self._ready = threading.Event()
        self._starting = False
        self._closing = False

    @property
    def is_running(self) -> bool:
        return bool(self._manager and self._client)

    def start(self) -> None:
        if self.is_running or self._starting:
            return

        self._starting = True
        self._ready.clear()
        self.state_changed.emit("starting", self.kernel_name)

        def worker() -> None:
            try:
                manager = KernelManager(kernel_name=self.kernel_name)
                manager.start_kernel(cwd=self.root_dir)
                client = manager.blocking_client()
                client.start_channels()
                client.wait_for_ready(timeout=30)

                if self._closing:
                    try:
                        client.stop_channels()
                    finally:
                        manager.shutdown_kernel(now=True)
                    return

                with self._lock:
                    self._manager = manager
                    self._client = client
                    self._ready.set()

                self.state_changed.emit("idle", self.kernel_name)
            except Exception as exc:
                self.error.emit(str(exc))
                self.state_changed.emit("dead", self.kernel_name)
            finally:
                self._starting = False

        threading.Thread(
            target=worker,
            name="archyter-native-kernel-start",
            daemon=True,
        ).start()

    def execute(self, code: str, request_id: str | None = None) -> str:
        request_id = request_id or uuid.uuid4().hex

        if not self.is_running:
            self.start()

        def worker() -> None:
            if not self._ready.wait(timeout=30):
                self.execution_finished.emit(
                    request_id,
                    "El kernel no quedó listo dentro de 30 segundos.",
                    True,
                    0,
                )
                return

            with self._lock:
                client = self._client
                if client is None:
                    self.execution_finished.emit(
                        request_id,
                        "Kernel no disponible.",
                        True,
                        0,
                    )
                    return

                try:
                    self.state_changed.emit("busy", self.kernel_name)
                    msg_id = client.execute(code, store_history=True)
                    output: list[str] = []
                    execution_count = 0
                    failed = False

                    while not self._closing:
                        msg = client.get_iopub_msg(timeout=30)
                        parent = msg.get("parent_header") or {}
                        if parent.get("msg_id") != msg_id:
                            continue

                        msg_type = msg.get("msg_type")
                        content = msg.get("content") or {}

                        if msg_type == "stream":
                            output.append(str(content.get("text", "")))
                        elif msg_type in {"execute_result", "display_data"}:
                            data = content.get("data") or {}
                            plain = data.get("text/plain")
                            if plain is not None:
                                output.append(str(plain))
                        elif msg_type == "error":
                            failed = True
                            traceback = content.get("traceback") or []
                            output.append("\n".join(str(line) for line in traceback))
                        elif msg_type == "execute_input":
                            execution_count = int(content.get("execution_count") or 0)
                        elif (
                            msg_type == "status"
                            and content.get("execution_state") == "idle"
                        ):
                            break

                    self.execution_finished.emit(
                        request_id,
                        "".join(output).rstrip(),
                        failed,
                        execution_count,
                    )
                except Exception as exc:
                    self.execution_finished.emit(
                        request_id,
                        str(exc),
                        True,
                        0,
                    )
                finally:
                    self.state_changed.emit("idle", self.kernel_name)

        threading.Thread(
            target=worker,
            name=f"archyter-exec-{request_id[:8]}",
            daemon=True,
        ).start()
        return request_id

    def refresh_variables(self) -> None:
        if not self.is_running:
            self.start()

        marker = "__ARCHYTER_NATIVE_VARS__"
        code = r'''
import json
_arch_skip = {"In", "Out", "exit", "quit", "get_ipython"}
_arch_items = []
for _arch_name, _arch_value in list(globals().items()):
    if _arch_name.startswith("_") or _arch_name in _arch_skip:
        continue
    try:
        _arch_type = type(_arch_value).__name__
        if hasattr(_arch_value, "shape"):
            _arch_shape = str(getattr(_arch_value, "shape"))
        elif isinstance(_arch_value, (dict, list, tuple, set, str, bytes)):
            _arch_shape = f"len={len(_arch_value)}"
        else:
            _arch_shape = "-"
        _arch_preview = repr(_arch_value).replace("\n", " ")
        if len(_arch_preview) > 90:
            _arch_preview = _arch_preview[:87] + "..."
        _arch_items.append({
            "name": _arch_name,
            "type": _arch_type,
            "shape": _arch_shape,
            "value": _arch_preview,
        })
    except Exception:
        pass
print("__ARCHYTER_NATIVE_VARS__" + json.dumps(_arch_items))
'''

        def worker() -> None:
            if not self._ready.wait(timeout=30):
                self.variables_ready.emit([])
                return

            with self._lock:
                client = self._client
                if client is None:
                    self.variables_ready.emit([])
                    return

                try:
                    msg_id = client.execute(
                        code,
                        silent=False,
                        store_history=False,
                    )

                    while not self._closing:
                        msg = client.get_iopub_msg(timeout=15)
                        parent = msg.get("parent_header") or {}
                        if parent.get("msg_id") != msg_id:
                            continue

                        msg_type = msg.get("msg_type")
                        content = msg.get("content") or {}

                        if msg_type == "stream":
                            text = str(content.get("text", ""))
                            if marker in text:
                                payload = text.split(marker, 1)[1].strip()
                                self.variables_ready.emit(json.loads(payload))
                                return

                        if (
                            msg_type == "status"
                            and content.get("execution_state") == "idle"
                        ):
                            break
                except Exception as exc:
                    self.error.emit(str(exc))

                self.variables_ready.emit([])

        threading.Thread(
            target=worker,
            name="archyter-native-vars",
            daemon=True,
        ).start()

    def restart(self) -> None:
        if not self._manager:
            self.start()
            return

        def worker() -> None:
            with self._lock:
                try:
                    self.state_changed.emit("starting", self.kernel_name)
                    self._manager.restart_kernel(now=True)
                    if self._client:
                        self._client.stop_channels()
                    self._client = self._manager.blocking_client()
                    self._client.start_channels()
                    self._client.wait_for_ready(timeout=30)
                    self._ready.set()
                    self.state_changed.emit("idle", self.kernel_name)
                except Exception as exc:
                    self.error.emit(str(exc))
                    self.state_changed.emit("dead", self.kernel_name)

        threading.Thread(
            target=worker,
            name="archyter-native-kernel-restart",
            daemon=True,
        ).start()

    def shutdown(self) -> None:
        self._closing = True
        self._ready.clear()
        with self._lock:
            try:
                if self._client:
                    self._client.stop_channels()
            except Exception:
                pass
            try:
                if self._manager:
                    self._manager.shutdown_kernel(now=True)
            except Exception:
                pass
            self._client = None
            self._manager = None
