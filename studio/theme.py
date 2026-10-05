APP_STYLE = r"""
QWidget {
    font-family: "Segoe UI Variable", "Segoe UI", Arial, sans-serif;
    font-size: 12px;
    color: #172033;
    background: #ffffff;
}
QMainWindow, QDialog { background: #edf4fb; }

QFrame#TopBar, QFrame#Explorer, QFrame#EditorFrame, QFrame#Inspector, QFrame#StatusBar {
    background: #fbfdff;
    border: 1px solid #d8e4ef;
    border-radius: 12px;
}
QFrame#TopBar { background: #ffffff; }
QFrame#EditorFrame { background: #ffffff; }
QFrame#Inspector { background: #f9fbfd; }
QFrame#StatusBar { background: #f8fbff; }

QFrame#NavRail {
    background: #f4f8fc;
    border: none;
    border-right: 1px solid #e1e9f1;
}
QFrame#DocumentBar {
    background: #f8fbff;
    border: 1px solid #d8e6f2;
    border-radius: 8px;
}
QFrame#Card {
    background: #ffffff;
    border: 1px solid #dae4ee;
    border-radius: 9px;
}
QFrame#TerminalCard {
    background: #ffffff;
    border: 1px solid #dae4ee;
    border-radius: 9px;
}
QLabel#AppTitle { font-size: 19px; font-weight: 700; color: #132033; }
QLabel#SectionTitle { font-size: 12px; font-weight: 700; color: #243146; }
QLabel#DocumentTitle { font-size: 12px; font-weight: 700; color: #075b9b; }
QLabel#Muted { color: #8391a4; font-size: 10px; }
QLabel#StatusGood { color: #168552; font-weight: 600; font-size: 10px; }
QLabel#ProjectPath {
    background: #eef7ff;
    color: #17639d;
    border: 1px solid #d0e8fb;
    border-radius: 7px;
    padding: 5px 8px;
    font-weight: 600;
}
QLabel#Badge {
    background: #eef3f8;
    color: #64748b;
    border-radius: 8px;
    padding: 2px 7px;
    font-size: 9px;
    font-weight: 700;
}
QLabel#KernelBadge {
    background: #e8f8ee;
    color: #16794a;
    border: 1px solid #bce7cd;
    border-radius: 8px;
    padding: 2px 8px;
    font-size: 9px;
    font-weight: 700;
}
QPushButton, QToolButton {
    background: #ffffff;
    color: #2b3a50;
    border: 1px solid #d2deea;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 23px;
}
QPushButton:hover, QToolButton:hover {
    background: #f0f7ff;
    color: #0a64b5;
    border-color: #8cc3f3;
}
QPushButton:pressed, QToolButton:pressed { background: #e2f1ff; }
QPushButton:disabled, QToolButton:disabled {
    color: #a2afbd;
    background: #f7f9fb;
    border-color: #e4e9ef;
}
QPushButton#Primary {
    color: #ffffff;
    background: #129fe2;
    border-color: #129fe2;
    font-weight: 700;
}
QPushButton#Primary:hover { background: #0787c7; border-color: #0787c7; }
QToolButton#NavButton {
    border: none;
    background: transparent;
    padding: 8px;
    border-radius: 8px;
}
QToolButton#NavButton:hover { background: #e8f3ff; }
QToolButton#NavButton[active="true"] {
    background: #dceeff;
    border: 1px solid #b8daf8;
}
QToolButton#IconButton {
    min-width: 27px;
    min-height: 27px;
    padding: 3px;
    background: #f7fafc;
}
QToolButton#DeleteButton {
    min-width: 23px;
    min-height: 21px;
    padding: 2px;
    background: #fff;
    border-color: #fecaca;
}
QToolButton#DeleteButton:hover { background: #fff1f2; border-color: #fda4af; }

QTreeView {
    background: transparent;
    border: none;
    outline: none;
    padding: 2px;
}
QTreeView::item { min-height: 25px; padding: 2px 4px; color: #314158; }
QTreeView::item:hover { background: #eff6fd; border-radius: 6px; }
QTreeView::item:selected {
    background: #dceeff;
    color: #075b9b;
    border: 1px solid #a8d2f5;
    border-radius: 6px;
    font-weight: 700;
}

QListWidget {
    background: transparent;
    border: none;
    outline: none;
}
QListWidget::item {
    min-height: 38px;
    padding: 5px 7px;
    border-radius: 7px;
    margin: 1px 0;
}
QListWidget::item:hover { background: #eef6ff; }
QListWidget::item:selected { background: #e1f0ff; color: #075b9b; }

QTableWidget {
    background: #ffffff;
    border: 1px solid #e1e8ef;
    border-radius: 7px;
    gridline-color: #edf1f5;
    selection-background-color: #dceeff;
}
QHeaderView::section {
    background: #f7f9fc;
    color: #52637a;
    border: none;
    border-bottom: 1px solid #e1e8ef;
    padding: 5px;
    font-size: 10px;
    font-weight: 700;
}

QPlainTextEdit#Terminal {
    background: #121a24;
    color: #edf4fb;
    border: none;
    border-radius: 7px;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 10px;
    padding: 7px;
}
QLineEdit {
    background: #ffffff;
    border: 1px solid #d7e1eb;
    border-radius: 7px;
    padding: 6px 8px;
    selection-background-color: #dceeff;
}
QLineEdit:focus { border-color: #69ade9; }

QMenu {
    background: #ffffff;
    border: 1px solid #d7e1eb;
    border-radius: 8px;
    padding: 5px;
}
QMenu::item { padding: 7px 24px 7px 10px; border-radius: 5px; }
QMenu::item:selected { background: #e9f4ff; color: #075b9b; }

QSplitter::handle { background: #e1e8ef; margin: 4px 1px; border-radius: 2px; }
QSplitter::handle:hover { background: #8fc2ef; }

QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #c4d1df; min-height: 28px; border-radius: 4px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal { background: transparent; height: 8px; }
QScrollBar::handle:horizontal { background: #c4d1df; min-width: 28px; border-radius: 4px; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

QToolTip {
    background: #182334;
    color: #ffffff;
    border: 1px solid #334155;
    padding: 5px 7px;
}
"""
