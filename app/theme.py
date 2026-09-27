APP_STYLE = r'''
QWidget {
    background-color: #0b1220;
    color: #e7edf5;
    font-family: "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 13px;
}
QMainWindow {
    background-color: #07101d;
}

QFrame#Sidebar,
QFrame#RightSidebar,
QFrame#CenterFrame,
QFrame#TopBar,
QFrame#StatusBarFrame,
QFrame#PanelCard {
    background-color: #0f1726;
    border: 1px solid #223049;
    border-radius: 12px;
}

QFrame#TopBar {
    background-color: #0d1625;
}

QTreeView {
    background-color: #0b1422;
    border: none;
    border-radius: 10px;
    padding: 6px;
    outline: none;
}
QTreeView::item {
    min-height: 27px;
    padding: 2px 4px;
}
QTreeView::item:selected {
    background-color: #123b68;
    color: #ffffff;
    border-radius: 6px;
}

QPushButton {
    background-color: #101a2a;
    border: 1px solid #2b3b55;
    border-radius: 9px;
    padding: 8px 13px;
    color: #e7edf5;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #162338;
    border-color: #3b82f6;
}
QPushButton:pressed {
    background-color: #1d4f82;
}
QPushButton#PrimaryButton {
    background-color: #1997f5;
    border-color: #38bdf8;
    color: #ffffff;
    font-weight: 700;
}
QPushButton#PrimaryButton:hover {
    background-color: #2ea8ff;
}

QLabel#TitleLabel {
    font-size: 22px;
    font-weight: 700;
}
QLabel#SectionTitle {
    font-size: 15px;
    font-weight: 700;
}
QLabel#MutedLabel {
    color: #8fa2bb;
}

QLineEdit,
QComboBox {
    background-color: #0b1422;
    border: 1px solid #2a3950;
    border-radius: 8px;
    padding: 7px 9px;
    selection-background-color: #1d4ed8;
}

QPlainTextEdit,
QTextEdit,
QTableWidget {
    background-color: #0a1320;
    border: 1px solid #202f46;
    border-radius: 9px;
    gridline-color: #1d2b40;
}

QPlainTextEdit#TerminalOutput {
    font-family: "JetBrains Mono", "Noto Sans Mono", "DejaVu Sans Mono", monospace;
    font-size: 12px;
}

QHeaderView::section {
    background-color: #101a2a;
    color: #bdcbe0;
    padding: 7px;
    border: none;
    border-bottom: 1px solid #26364e;
}

QSplitter::handle {
    background-color: #152238;
    width: 4px;
    margin: 10px 3px;
    border-radius: 2px;
}
QSplitter::handle:hover {
    background-color: #2596ff;
}

QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 2px;
}
QScrollBar::handle:vertical {
    background: #33445f;
    min-height: 28px;
    border-radius: 5px;
}
QScrollBar::handle:vertical:hover {
    background: #48617f;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 10px;
}
QScrollBar::handle:horizontal {
    background: #33445f;
    min-width: 28px;
    border-radius: 5px;
}
'''
