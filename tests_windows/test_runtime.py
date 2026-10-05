from __future__ import annotations

import inspect
import tempfile
import unittest
from pathlib import Path

import studio.window as studio_window
from scripts.build_windows_icon import build_icon
from studio.icons import ASSET_ROOT


class WindowsRuntimeTests(unittest.TestCase):

    def test_archtyer_svg_can_build_windows_ico(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "ArchyterStudio.ico"
            built = build_icon(
                str(ASSET_ROOT / "icon.svg"),
                str(target),
            )
            self.assertEqual(built, target.resolve())
            self.assertTrue(target.is_file())
            self.assertGreater(target.stat().st_size, 500)

    def test_studio_window_has_no_webengine_runtime(self) -> None:
        source = inspect.getsource(studio_window)

        forbidden = (
            "QWebEngineView",
            "QWebEnginePage",
            "QWebEngineProfile",
            "QtWebEngine",
            "runJavaScript",
        )

        for token in forbidden:
            self.assertNotIn(
                token,
                source,
                f"WebEngine dependency returned to Studio window: {token}",
            )


if __name__ == "__main__":
    unittest.main()
