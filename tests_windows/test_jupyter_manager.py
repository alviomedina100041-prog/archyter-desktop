from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from studio.jupyter_manager import JupyterManager


class JupyterManagerTests(unittest.TestCase):

    def test_prepare_notebook_metadata_is_local_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            notebook = root / "fast.ipynb"
            notebook.write_text(
                '{"cells":[],"metadata":{},"nbformat":4,"nbformat_minor":5}',
                encoding="utf-8",
            )

            manager = JupyterManager(str(root))

            changed = manager.prepare_notebook_metadata(str(notebook))
            self.assertTrue(changed)

            payload = __import__("json").loads(
                notebook.read_text(encoding="utf-8")
            )
            kernelspec = payload["metadata"]["kernelspec"]

            self.assertEqual(kernelspec["name"], "python3")
            self.assertEqual(kernelspec["language"], "python")

            second = manager.prepare_notebook_metadata(str(notebook))
            self.assertFalse(second)

    def test_real_jupyter_creates_nested_notebook(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nested = root / "Universidad" / "notebooks"
            nested.mkdir(parents=True)

            manager = JupyterManager(str(root))
            try:
                manager.start(timeout=45)
                created = Path(manager.create_notebook(str(nested)))

                self.assertTrue(created.exists())
                self.assertTrue(os.path.samefile(str(created.parent), str(nested)))
                self.assertEqual(created.suffix, ".ipynb")
                self.assertIn(
                    "/lab/tree/Universidad/notebooks/",
                    manager.open_url(str(created)),
                )

                session = manager.ensure_notebook_session(str(created))
                self.assertEqual(
                    session.get("path"),
                    "Universidad/notebooks/" + created.name,
                )
                self.assertTrue((session.get("kernel") or {}).get("id"))

                second = manager.ensure_notebook_session(str(created))
                self.assertEqual(second.get("id"), session.get("id"))

                with self.assertRaises(ValueError):
                    manager.open_url(str(root.parent / "outside.ipynb"))
            finally:
                manager.shutdown()


if __name__ == "__main__":
    unittest.main()
