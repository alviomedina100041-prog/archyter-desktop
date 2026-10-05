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
