from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from studio.jupyter_manager import JupyterManager


class JupyterManagerTests(unittest.TestCase):
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
                self.assertIn("/lab/tree/Universidad/notebooks/", manager.open_url(str(created)))

                with self.assertRaises(ValueError):
                    manager.open_url(str(root.parent / "outside.ipynb"))
            finally:
                manager.shutdown()


if __name__ == "__main__":
    unittest.main()
