APP_STYLE = r"""
* {
    font-family: "Segoe UI Variable", "Segoe UI", Arial, sans-serif;
}

QWidget {
    font-size: 12px;
    color: #172033;
    background: transparent;
}

QMainWindow, QDialog {
    background: #edf4fa;
}

QFrame#TopBar,
QFrame#Explorer,
QFrame#EditorFrame,
QFrame#Inspector,
QFrame#StatusBar {
    background: #fbfdff;
    border: 1px solid #d8e4ef;
    border-radius: 11px;
}

QFrame#TopBar {
    background: #ffffff;
}

QFrame#Explorer {
    background: #fbfdff;
}

QFrame#EditorFrame {
    background: #ffffff;
}

QFrame#Inspector {
    background: #fafdff;
}

QFrame#StatusBar {
    background: #f8fbff;
}

QFrame#NavRail {
    background: #f6f9fc;
    border: none;
    border-right: 1px solid #e2eaf2;
}

QFrame#DocumentBar {
    background: #f8fbff;
    border: 1px solid #d9e6f1;
    border-radius: 8px;
}

QFrame#DocumentTab {
    background: #ffffff;
    border: 1px solid #cfe1f0;
    border-bottom: 2px solid #179fe6;
    border-radius: 7px;
}

QFrame#Card,
QFrame#TerminalCard {
    background: #ffffff;
    border: 1px solid #dce6ef;
    border-radius: 9px;
}

QLabel#AppTitle {
    font-size: 20px;
    font-weight: 700;
    color: #122033;
}

QLabel#SectionTitle {
    font-size: 12px;
    font-weight: 700;
    color: #213047;
}

QLabel#DocumentTitle {
    font-size: 12px;
    font-weight: 700;
    color: #0b5e9e;
}

QLabel#Muted {
    color: #7f8da0;
    font-size: 10px;
}

QLabel#StatusGood {
    color: #158653;
    font-weight: 600;
    font-size: 10px;
}

QLabel#ProjectPath {
    background: #eef7ff;
    color: #17639d;
    border: 1px solid #cfe7fb;
    border-radius: 7px;
    padding: 5px 8px;
    font-weight: 600;
}

QLabel#Badge {
    background: #eef3f8;
    color: #607086;
    border-radius: 8px;
    padding: 2px 7px;
    font-size: 9px;
    font-weight: 700;
}

QLabel#KernelBadge {
    background: #e9f8ef;
    color: #16794a;
    border: 1px solid #bee8cf;
    border-radius: 8px;
    padding: 2px 8px;
    font-size: 9px;
    font-weight: 700;
}

QPushButton,
QToolButton {
    background: #ffffff;
    color: #2b3a50;
    border: 1px solid #d2deea;
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 23px;
}

QPushButton:hover,
QToolButton:hover {
    background: #f0f7ff;
    color: #0a64b5;
    border-color: #87c2f3;
}

QPushButton:pressed,
QToolButton:pressed {
    background: #e2f1ff;
    border-color: #65adea;
}

QPushButton:disabled,
QToolButton:disabled {
    color: #a5b0bd;
    background: #f8fafc;
    border-color: #e5eaf0;
}

QPushButton#Primary {
    color: #ffffff;
    background: #149fe2;
    border-color: #149fe2;
    font-weight: 700;
    padding-left: 14px;
    padding-right: 14px;
}

QPushButton#Primary:hover {
    background: #0789cb;
    border-color: #0789cb;
}

QPushButton#FlatAction,
QToolButton#FlatAction {
    background: transparent;
    border: none;
    padding: 4px;
}

QPushButton#FlatAction:hover,
QToolButton#FlatAction:hover {
    background: #eef6ff;
    border: none;
}

QToolButton#NavButton {
    border: none;
    background: transparent;
    padding: 8px;
    border-radius: 8px;
    min-width: 31px;
    min-height: 31px;
}

QToolButton#NavButton:hover {
    background: #e9f4ff;
}

QToolButton#NavButton[active="true"] {
    background: #dceeff;
    border: 1px solid #b8dbf8;
}

QToolButton#IconButton {
    min-width: 27px;
    min-height: 27px;
    padding: 3px;
    background: #f8fbfd;
}

QToolButton#DeleteButton {
    min-width: 27px;
    min-height: 27px;
    padding: 3px;
    background: #fffafa;
    border-color: #f3d4d7;
}

QToolButton#DeleteButton:hover {
    background: #fff0f2;
    border-color: #f3aab0;
}

QToolButton#TabButton {
    min-width: 22px;
    min-height: 22px;
    padding: 2px;
    background: transparent;
    border: none;
}

QToolButton#TabButton:hover {
    background: #eaf4ff;
}

QTreeView {
    background: transparent;
    border: none;
    outline: none;
    padding: 2px;
}

QTreeView::branch,
QTreeView::branch:selected,
QTreeView::branch:hover {
    background: transparent;
}

QTreeView::item {
    min-height: 26px;
    padding: 2px 5px;
    color: #314158;
}

QTreeView::item:hover {
    background: #eff6fd;
    border-radius: 6px;
}

QTreeView::item:selected {
    background: #dceeff;
    color: #075b9b;
    border: 1px solid #a7d2f5;
    border-radius: 6px;
    font-weight: 700;
}

QListWidget {
    background: transparent;
    border: none;
    outline: none;
}

QListWidget::item {
    min-height: 42px;
    padding: 6px 8px;
    border-radius: 7px;
    margin: 1px 0;
    color: #334155;
}

QListWidget::item:hover {
    background: #eef6ff;
}

QListWidget::item:selected {
    background: #e1f0ff;
    color: #075b9b;
}

QTableWidget {
    background: #ffffff;
    border: 1px solid #e1e8ef;
    border-radius: 7px;
    gridline-color: #edf1f5;
    selection-background-color: #dceeff;
    alternate-background-color: #fbfdff;
}

QTableWidget::item {
    padding: 3px 5px;
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
    background: #111923;
    color: #eef4fb;
    border: none;
    border-radius: 7px;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 10px;
    padding: 8px;
    selection-background-color: #275d86;
}

QLineEdit {
    background: #ffffff;
    border: 1px solid #d7e1eb;
    border-radius: 7px;
    padding: 6px 8px;
    selection-background-color: #dceeff;
}

QLineEdit:focus {
    border-color: #69ade9;
}

QMenu {
    background: #ffffff;
    border: 1px solid #d7e1eb;
    border-radius: 8px;
    padding: 5px;
}

QMenu::item {
    padding: 7px 24px 7px 10px;
    border-radius: 5px;
}

QMenu::item:selected {
    background: #e9f4ff;
    color: #075b9b;
}

QSplitter::handle {
    background: #e2e9f0;
    margin: 5px 1px;
    border-radius: 2px;
}

QSplitter::handle:hover {
    background: #8fc3ee;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 1px;
}

QScrollBar::handle:vertical {
    background: #c3d0de;
    min-height: 28px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #9fb5c9;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background: #c3d0de;
    min-width: 28px;
    border-radius: 4px;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0;
}

QToolTip {
    background: #182334;
    color: #ffffff;
    border: 1px solid #334155;
    padding: 5px 7px;
}

QLabel#StudioWelcome {
    background: #ffffff;
    border: 1px solid #e1e8ef;
    border-radius: 12px;
    color: #172033;
}

QFrame#NativeNotebook {
    background: #ffffff;
    border: none;
}

QFrame#NativeNotebookToolbar {
    background: #ffffff;
    border: 1px solid #e2e9f0;
    border-radius: 8px;
}

QPushButton#NotebookToolButton {
    background: #ffffff;
    border: 1px solid #d7e2ec;
    border-radius: 7px;
    padding: 5px 9px;
    min-height: 22px;
}

QPushButton#NotebookToolButton:hover {
    background: #eef7ff;
    border-color: #96c9f2;
}

QScrollArea#NotebookScroll {
    background: #ffffff;
    border: none;
}

QScrollArea#NotebookScroll > QWidget > QWidget {
    background: #ffffff;
}

QFrame#NativeCell {
    background: #ffffff;
    border: 1px solid #dce5ed;
    border-left: 3px solid transparent;
    border-radius: 10px;
}

QFrame#NativeCell:hover {
    border-color: #bfd2e4;
}

QFrame#NativeCell[active="true"] {
    border-color: #8ac9f2;
    border-left-color: #149fe2;
    background: #ffffff;
}

QLabel#CellPrompt {
    color: #7b8ba0;
    font-family: "Cascadia Mono", "Consolas", monospace;
    font-size: 10px;
}

QPushButton#CellRunButton {
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 3px;
}

QPushButton#CellRunButton:hover {
    background: #eaf5ff;
}

QPlainTextEdit#CellEditor {
    background: #ffffff;
    color: #172033;
    border: 1px solid #e1e8ef;
    border-radius: 7px;
    padding: 7px 8px;
    selection-background-color: #dceeff;
    font-family: "Cascadia Mono", "Consolas", monospace;
}

QPlainTextEdit#CellEditor:focus {
    border: 1px solid #6ab7eb;
}

QPlainTextEdit#CellOutput {
    background: #fbfdff;
    color: #26384d;
    border: 1px solid #edf1f5;
    border-radius: 7px;
    padding: 7px 8px;
    font-family: "Cascadia Mono", "Consolas", monospace;
}

QPlainTextEdit#CellOutput[error="true"] {
    background: #fff6f6;
    color: #a12b2b;
    border-color: #f3c3c3;
}

"""
