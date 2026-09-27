from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .window import MainWindow


def resolve_root_dir() -> str:
    if len(sys.argv) > 1:
        return os.path.abspath(os.path.expanduser(sys.argv[1]))

    env_root = os.environ.get("ARCHYTER_PROJECT")
    if env_root:
        return os.path.abspath(os.path.expanduser(env_root))

    return str(Path.home())


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Archyter Desktop")
    app.setOrganizationName("EduardoMedinaLabs")

    window = MainWindow(root_dir=resolve_root_dir())
    window.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
