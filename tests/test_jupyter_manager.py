from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.jupyter_manager import JupyterServerManager


class JupyterManagerIntegrationTests(unittest.TestCase):
    def test_create_notebook_in_selected_nested_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            nested = root / "notebooks" / "curso"
            nested.mkdir(parents=True)

            manager = JupyterServerManager(root_dir=str(root))
            try:
                manager.start(timeout=35.0)

                created = Path(manager.create_notebook(str(nested)))

                self.assertTrue(created.exists())
                self.assertEqual(created.parent, nested)
                self.assertEqual(created.suffix, ".ipynb")

                url = manager.open_url_for_path(created)
                self.assertIn("/lab/tree/notebooks/curso/", url)
                self.assertIn("token=", url)

                outside = root.parent / "outside.ipynb"
                with self.assertRaises(ValueError):
                    manager.open_url_for_path(outside)
            finally:
                manager.shutdown()


if __name__ == "__main__":
    unittest.main()
