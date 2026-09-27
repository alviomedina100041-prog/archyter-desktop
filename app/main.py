from __future__ import annotations

import os
import sys

from PySide6.QtWidgets import QApplication

from .window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("Archyter Desktop")
    app.setOrganizationName("EduardoMedinaLabs")

    root_dir = os.getcwd()
    window = MainWindow(root_dir=root_dir)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
