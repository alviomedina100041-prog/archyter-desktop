from __future__ import annotations

import tempfile
import threading
import time
import unittest
from pathlib import Path

from PySide6.QtCore import QCoreApplication

from studio.native_kernel import NativeKernelController


class NativeKernelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = QCoreApplication.instance() or QCoreApplication([])

    def _wait_until(self, predicate, timeout: float = 35.0) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            self.app.processEvents()
            if predicate():
                return True
            time.sleep(0.03)
        return False


    def test_variable_inspector_hides_runtime_modules_and_functions(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            controller = NativeKernelController(temp)
            results: list[tuple] = []
            snapshots: list[list[dict]] = []

            controller.execution_finished.connect(
                lambda *args: results.append(args)
            )
            controller.variables_ready.connect(
                lambda values: snapshots.append(list(values))
            )

            try:
                controller.start()
                self.assertTrue(
                    self._wait_until(lambda: controller.is_running),
                    "Native Python kernel did not become ready",
                )

                controller.execute(
                    "import math\n"
                    "def helper():\n"
                    "    return 1\n"
                    "user_value = 123",
                    request_id="vars-setup",
                )
                self.assertTrue(
                    self._wait_until(lambda: bool(results)),
                    "Variable setup did not finish",
                )

                controller.refresh_variables()
                self.assertTrue(
                    self._wait_until(lambda: bool(snapshots)),
                    "Variable snapshot did not arrive",
                )

                names = {
                    item.get("name")
                    for item in snapshots[-1]
                }
                self.assertIn("user_value", names)
                self.assertNotIn("math", names)
                self.assertNotIn("helper", names)
                self.assertNotIn("open", names)
            finally:
                controller.shutdown()


    def test_kernel_stop_start_and_execute_again(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            controller = NativeKernelController(temp)
            states: list[str] = []
            results: list[tuple] = []

            controller.state_changed.connect(
                lambda state, _name: states.append(state)
            )
            controller.execution_finished.connect(
                lambda *args: results.append(args)
            )

            try:
                controller.start()
                self.assertTrue(
                    self._wait_until(lambda: controller.is_running),
                    "Kernel did not start",
                )

                controller.stop()
                self.assertTrue(
                    self._wait_until(
                        lambda: (
                            not controller.is_running
                            and "dead" in states
                        ),
                        timeout=12,
                    ),
                    "Kernel did not stop cleanly",
                )

                controller.start()
                self.assertTrue(
                    self._wait_until(lambda: controller.is_running),
                    "Kernel did not start again after Stop",
                )

                controller.execute(
                    "print(6 * 7)",
                    request_id="after-stop",
                )
                self.assertTrue(
                    self._wait_until(
                        lambda: any(
                            row[0] == "after-stop"
                            for row in results
                        )
                    ),
                    "Kernel could not execute after Stop/Start",
                )

                row = next(
                    item
                    for item in results
                    if item[0] == "after-stop"
                )
                self.assertFalse(row[2])
                self.assertIn("42", row[1])
            finally:
                controller.shutdown()

    def test_interrupt_heavy_process_then_execute_again(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            controller = NativeKernelController(temp)
            results: list[tuple] = []

            controller.execution_finished.connect(
                lambda *args: results.append(args)
            )

            try:
                controller.start()
                self.assertTrue(
                    self._wait_until(lambda: controller.is_running),
                    "Kernel did not start",
                )

                controller.execute(
                    "import time\ntime.sleep(5)\nprint('late')",
                    request_id="long-job",
                )
                time.sleep(0.35)
                controller.interrupt()

                self.assertTrue(
                    self._wait_until(
                        lambda: any(
                            row[0] == "long-job"
                            for row in results
                        ),
                        timeout=10,
                    ),
                    "Interrupted process did not return control",
                )

                controller.execute(
                    "print(20 + 22)",
                    request_id="after-interrupt",
                )
                self.assertTrue(
                    self._wait_until(
                        lambda: any(
                            row[0] == "after-interrupt"
                            for row in results
                        ),
                        timeout=10,
                    ),
                    "Kernel stayed blocked after interrupt",
                )

                row = next(
                    item
                    for item in results
                    if item[0] == "after-interrupt"
                )
                self.assertFalse(row[2])
                self.assertIn("42", row[1])
            finally:
                controller.shutdown()

    def test_real_python_kernel_executes_without_jupyterlab_server(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            controller = NativeKernelController(temp)
            states: list[str] = []
            results: list[tuple] = []

            controller.state_changed.connect(
                lambda state, _name: states.append(state)
            )
            controller.execution_finished.connect(
                lambda *args: results.append(args)
            )

            try:
                controller.start()
                self.assertTrue(
                    self._wait_until(lambda: controller.is_running),
                    "Native Python kernel did not become ready",
                )

                controller.execute("x = 40 + 2\nprint(x)", request_id="cell-1")
                self.assertTrue(
                    self._wait_until(lambda: bool(results)),
                    "Native cell execution did not finish",
                )

                request_id, output, failed, execution_count = results[-1]
                self.assertEqual(request_id, "cell-1")
                self.assertFalse(failed)
                self.assertIn("42", output)
                self.assertGreaterEqual(execution_count, 1)
                self.assertIn("idle", states)
            finally:
                controller.shutdown()


if __name__ == "__main__":
    unittest.main()
