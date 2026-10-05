from __future__ import annotations

import os
import unittest

import studio.main  # noqa: F401


class WindowsRuntimeTests(unittest.TestCase):
    def test_chromium_occlusion_throttling_is_disabled(self) -> None:
        if os.name != "nt":
            self.skipTest("Windows-only runtime policy")

        flags = os.environ.get("QTWEBENGINE_CHROMIUM_FLAGS", "")

        for required in (
            "--disable-features=CalculateNativeWinOcclusion",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding",
            "--disable-background-timer-throttling",
        ):
            self.assertIn(required, flags)


if __name__ == "__main__":
    unittest.main()
