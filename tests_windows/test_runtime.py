from __future__ import annotations

import inspect
import unittest

import studio.window as studio_window


class WindowsRuntimeTests(unittest.TestCase):
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
