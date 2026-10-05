from __future__ import annotations

import json
import subprocess
import threading
import uuid
from pathlib import Path

from jupyter_client import KernelManager
from PySide6.QtCore import QObject, Signal


MAX_OUTPUT_CHARS = 180_000


class NativeKernelController(QObject):
    state_changed = Signal(str, str)
    execution_finished = Signal(str, str, bool, int)
    variables_ready = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        root_dir: str,
        kernel_name: str = "python3",
    ):
        super().__init__()
        self.root_dir = str(
            Path(root_dir).resolve()
        )
        self.kernel_name = kernel_name

        self._manager: KernelManager | None = None
        self._client = None

        self._state_lock = threading.RLock()
        self._io_lock = threading.Lock()
        self._ready = threading.Event()
        self._cleanup_done = threading.Event()
        self._cleanup_done.set()

        self._generation = 0
        self._starting_generation: int | None = None
        self._permanent_shutdown = False

    @property
    def is_running(self) -> bool:
        with self._state_lock:
            return bool(
                self._manager
                and self._client
                and self._ready.is_set()
            )

    def _is_current(
        self,
        generation: int,
    ) -> bool:
        with self._state_lock:
            return (
                not self._permanent_shutdown
                and generation == self._generation
            )

    @staticmethod
    def _terminate_resources(
        manager,
        client,
    ) -> None:
        if client is not None:
            try:
                client.stop_channels()
            except Exception:
                pass

        if manager is not None:
            try:
                manager.interrupt_kernel()
            except Exception:
                pass
            try:
                manager.shutdown_kernel(
                    now=True
                )
            except Exception:
                pass

    def start(self) -> None:
        with self._state_lock:
            if self._permanent_shutdown:
                return

            if self.is_running:
                return

            if self._starting_generation is not None:
                return

            self._generation += 1
            generation = self._generation
            self._starting_generation = generation
            self._ready.clear()

        self.state_changed.emit(
            "starting",
            self.kernel_name,
        )

        threading.Thread(
            target=self._start_worker,
            args=(generation,),
            name=f"archyter-kernel-start-{generation}",
            daemon=True,
        ).start()

    def _start_worker(
        self,
        generation: int,
    ) -> None:
        # If an old kernel is still being killed, wait for it. This prevents
        # repeated Stop/Start clicks from leaving multiple Python processes.
        self._cleanup_done.wait(timeout=12)

        if not self._is_current(generation):
            return

        manager = None
        client = None

        try:
            manager = KernelManager(
                kernel_name=self.kernel_name,
                ip="127.0.0.1",
            )
            manager.start_kernel(
                cwd=self.root_dir,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )

            client = manager.blocking_client()
            client.start_channels()
            client.wait_for_ready(timeout=30)

            if not self._is_current(generation):
                self._terminate_resources(
                    manager,
                    client,
                )
                return

            with self._state_lock:
                if not self._is_current(
                    generation
                ):
                    stale = True
                else:
                    stale = False
                    self._manager = manager
                    self._client = client
                    self._starting_generation = None
                    self._ready.set()

            if stale:
                self._terminate_resources(
                    manager,
                    client,
                )
                return

            self.state_changed.emit(
                "idle",
                self.kernel_name,
            )

        except Exception as exc:
            self._terminate_resources(
                manager,
                client,
            )

            if self._is_current(generation):
                with self._state_lock:
                    self._starting_generation = None
                    self._ready.clear()

                self.error.emit(str(exc))
                self.state_changed.emit(
                    "dead",
                    self.kernel_name,
                )

    def _detach_kernel(self) -> tuple[object, object, bool]:
        with self._state_lock:
            manager = self._manager
            client = self._client
            had_start_in_progress = (
                self._starting_generation
                is not None
            )

            self._generation += 1
            self._manager = None
            self._client = None
            self._starting_generation = None
            self._ready.clear()

            # A stale execution may still be unwinding on the previous
            # client. Give the next kernel its own I/O lock immediately so
            # an old get_iopub_msg timeout can never block new executions.
            self._io_lock = threading.Lock()

            has_cleanup = bool(
                manager
                or client
                or had_start_in_progress
            )

            if has_cleanup:
                self._cleanup_done.clear()

            return (
                manager,
                client,
                has_cleanup,
            )

    def stop(self) -> None:
        manager, client, has_cleanup = (
            self._detach_kernel()
        )

        self.state_changed.emit(
            "stopping",
            self.kernel_name,
        )

        if not has_cleanup:
            self._cleanup_done.set()
            self.state_changed.emit(
                "dead",
                self.kernel_name,
            )
            return

        def worker() -> None:
            self._terminate_resources(
                manager,
                client,
            )
            self._cleanup_done.set()

            if not self._permanent_shutdown:
                self.state_changed.emit(
                    "dead",
                    self.kernel_name,
                )

        threading.Thread(
            target=worker,
            name="archyter-kernel-stop",
            daemon=True,
        ).start()

    def restart(self) -> None:
        if self._permanent_shutdown:
            return

        self.stop()

        def worker() -> None:
            self._cleanup_done.wait(
                timeout=12
            )

            if self._permanent_shutdown:
                return

            self.start()

        threading.Thread(
            target=worker,
            name="archyter-kernel-restart",
            daemon=True,
        ).start()

    def interrupt(self) -> None:
        with self._state_lock:
            manager = self._manager

        if manager is None:
            return

        self.state_changed.emit(
            "interrupting",
            self.kernel_name,
        )

        def worker() -> None:
            try:
                manager.interrupt_kernel()
            except Exception as exc:
                self.error.emit(str(exc))

        threading.Thread(
            target=worker,
            name="archyter-kernel-interrupt",
            daemon=True,
        ).start()

    def execute(
        self,
        code: str,
        request_id: str | None = None,
    ) -> str:
        request_id = (
            request_id
            or uuid.uuid4().hex
        )

        if not self.is_running:
            self.start()

        with self._state_lock:
            generation = self._generation
            io_lock = self._io_lock

        def worker() -> None:
            if not self._ready.wait(
                timeout=30
            ):
                self.execution_finished.emit(
                    request_id,
                    "El kernel no quedó listo dentro de 30 segundos.",
                    True,
                    0,
                )
                return

            if not self._is_current(
                generation
            ):
                return

            with io_lock:
                if not self._is_current(
                    generation
                ):
                    return

                with self._state_lock:
                    client = self._client

                if client is None:
                    self.execution_finished.emit(
                        request_id,
                        "Kernel no disponible.",
                        True,
                        0,
                    )
                    return

                self.state_changed.emit(
                    "busy",
                    self.kernel_name,
                )

                output: list[str] = []
                output_chars = 0
                truncated = False
                execution_count = 0
                failed = False

                def append_output(
                    value: object,
                ) -> None:
                    nonlocal output_chars
                    nonlocal truncated

                    if truncated:
                        return

                    text = str(value)
                    remaining = (
                        MAX_OUTPUT_CHARS
                        - output_chars
                    )

                    if remaining <= 0:
                        truncated = True
                        output.append(
                            "\n[Salida truncada por Archyter para proteger la memoria]"
                        )
                        return

                    if len(text) > remaining:
                        output.append(
                            text[:remaining]
                        )
                        output.append(
                            "\n[Salida truncada por Archyter para proteger la memoria]"
                        )
                        output_chars += remaining
                        truncated = True
                        return

                    output.append(text)
                    output_chars += len(text)

                try:
                    msg_id = client.execute(
                        code,
                        store_history=True,
                    )

                    while (
                        self._is_current(
                            generation
                        )
                    ):
                        msg = client.get_iopub_msg(
                            timeout=30
                        )

                        parent = (
                            msg.get(
                                "parent_header"
                            )
                            or {}
                        )

                        if (
                            parent.get("msg_id")
                            != msg_id
                        ):
                            continue

                        msg_type = msg.get(
                            "msg_type"
                        )
                        payload = (
                            msg.get("content")
                            or {}
                        )

                        if msg_type == "stream":
                            append_output(
                                payload.get(
                                    "text",
                                    "",
                                )
                            )

                        elif msg_type in {
                            "execute_result",
                            "display_data",
                        }:
                            data = (
                                payload.get("data")
                                or {}
                            )
                            plain = data.get(
                                "text/plain"
                            )
                            if plain is not None:
                                append_output(
                                    plain
                                )

                        elif msg_type == "error":
                            failed = True
                            traceback = (
                                payload.get(
                                    "traceback"
                                )
                                or []
                            )
                            append_output(
                                "\n".join(
                                    str(line)
                                    for line in traceback
                                )
                            )

                        elif msg_type == "execute_input":
                            execution_count = int(
                                payload.get(
                                    "execution_count"
                                )
                                or 0
                            )

                        elif (
                            msg_type == "status"
                            and payload.get(
                                "execution_state"
                            )
                            == "idle"
                        ):
                            break

                    if not self._is_current(
                        generation
                    ):
                        return

                    self.execution_finished.emit(
                        request_id,
                        "".join(
                            output
                        ).rstrip(),
                        failed,
                        execution_count,
                    )

                except Exception as exc:
                    if self._is_current(
                        generation
                    ):
                        self.execution_finished.emit(
                            request_id,
                            str(exc),
                            True,
                            execution_count,
                        )

                finally:
                    if self._is_current(
                        generation
                    ):
                        self.state_changed.emit(
                            "idle",
                            self.kernel_name,
                        )

        threading.Thread(
            target=worker,
            name=(
                "archyter-exec-"
                + request_id[:8]
            ),
            daemon=True,
        ).start()

        return request_id

    def refresh_variables(self) -> None:
        if not self.is_running:
            return

        marker = "__ARCHYTER_NATIVE_VARS__"

        code = r"""
import json as _arch_json
import types as _arch_types

_arch_skip = {
    "In",
    "Out",
    "exit",
    "quit",
    "get_ipython",
    "open",
}

_arch_items = []

for _arch_name, _arch_value in list(globals().items()):
    if (
        _arch_name.startswith("_")
        or _arch_name in _arch_skip
        or isinstance(_arch_value, _arch_types.ModuleType)
        or callable(_arch_value)
    ):
        continue

    try:
        _arch_type = type(_arch_value).__name__

        if hasattr(_arch_value, "shape"):
            _arch_shape = str(
                getattr(_arch_value, "shape")
            )
        elif isinstance(
            _arch_value,
            (
                dict,
                list,
                tuple,
                set,
                str,
                bytes,
            ),
        ):
            _arch_shape = f"len={len(_arch_value)}"
        else:
            _arch_shape = "-"

        _arch_preview = repr(
            _arch_value
        ).replace("\n", " ")

        if len(_arch_preview) > 90:
            _arch_preview = (
                _arch_preview[:87]
                + "..."
            )

        _arch_items.append(
            {
                "name": _arch_name,
                "type": _arch_type,
                "shape": _arch_shape,
                "value": _arch_preview,
            }
        )
    except Exception:
        pass

print(
    "__ARCHYTER_NATIVE_VARS__"
    + _arch_json.dumps(_arch_items)
)
"""

        with self._state_lock:
            generation = self._generation
            io_lock = self._io_lock

        def worker() -> None:
            if not self._ready.wait(
                timeout=10
            ):
                self.variables_ready.emit(
                    []
                )
                return

            with io_lock:
                if not self._is_current(
                    generation
                ):
                    return

                with self._state_lock:
                    client = self._client

                if client is None:
                    self.variables_ready.emit(
                        []
                    )
                    return

                try:
                    msg_id = client.execute(
                        code,
                        silent=False,
                        store_history=False,
                    )

                    while self._is_current(
                        generation
                    ):
                        msg = client.get_iopub_msg(
                            timeout=15
                        )
                        parent = (
                            msg.get(
                                "parent_header"
                            )
                            or {}
                        )

                        if (
                            parent.get("msg_id")
                            != msg_id
                        ):
                            continue

                        msg_type = msg.get(
                            "msg_type"
                        )
                        payload = (
                            msg.get("content")
                            or {}
                        )

                        if msg_type == "stream":
                            text = str(
                                payload.get(
                                    "text",
                                    "",
                                )
                            )

                            if marker in text:
                                value = text.split(
                                    marker,
                                    1,
                                )[1].strip()

                                self.variables_ready.emit(
                                    json.loads(
                                        value
                                    )
                                )
                                return

                        if (
                            msg_type == "status"
                            and payload.get(
                                "execution_state"
                            )
                            == "idle"
                        ):
                            break

                except Exception:
                    pass

                if self._is_current(
                    generation
                ):
                    self.variables_ready.emit(
                        []
                    )

        threading.Thread(
            target=worker,
            name="archyter-native-vars",
            daemon=True,
        ).start()

    def shutdown(self) -> None:
        self._permanent_shutdown = True
        manager, client, has_cleanup = (
            self._detach_kernel()
        )

        if has_cleanup:
            self._terminate_resources(
                manager,
                client,
            )

        self._cleanup_done.set()
