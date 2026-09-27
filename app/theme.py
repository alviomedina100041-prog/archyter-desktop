APP_STYLE = r'''
QWidget {
    background-color: #ffffff;
    color: #111827;
    font-family: "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 11px;
}

QMainWindow {
    background-color: #ffffff;
}

QFrame#Sidebar,
QFrame#RightSidebar,
QFrame#CenterFrame,
QFrame#TopBar,
QFrame#StatusBarFrame,
QFrame#PanelCard {
    background-color: #ffffff;
    border: 1px solid #d8dee9;
    border-radius: 9px;
}

QFrame#TopBar {
    background-color: #ffffff;
}

QTreeView {
    background-color: #ffffff;
    color: #111827;
    border: none;
    border-radius: 8px;
    padding: 3px;
    outline: none;
}

QTreeView::item {
    min-height: 22px;
    padding: 1px 3px;
    color: #111827;
}

QTreeView::item:hover {
    background-color: #f1f5f9;
    border-radius: 5px;
}

QTreeView::item:selected {
    background-color: #e0f2fe;
    color: #075985;
    border-radius: 5px;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    padding: 5px 9px;
    color: #111827;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #f8fafc;
    border-color: #38bdf8;
}

QPushButton:pressed {
    background-color: #e2e8f0;
}

QPushButton#PrimaryButton {
    background-color: #0ea5e9;
    border-color: #0ea5e9;
    color: #ffffff;
    font-weight: 700;
}

QPushButton#PrimaryButton:hover {
    background-color: #0284c7;
}

QPushButton#BackButton {
    font-size: 15px;
    padding: 2px 5px;
}

QLabel {
    background-color: transparent;
    color: #111827;
}

QLabel#TitleLabel {
    font-size: 17px;
    font-weight: 700;
    color: #0f172a;
}

QLabel#SectionTitle {
    font-size: 12px;
    font-weight: 700;
    color: #0f172a;
}

QLabel#MutedLabel {
    color: #64748b;
    font-size: 10px;
}

QLineEdit,
QComboBox {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #cbd5e1;
    border-radius: 7px;
    padding: 5px 7px;
    selection-background-color: #bae6fd;
    selection-color: #0f172a;
}

QPlainTextEdit,
QTextEdit,
QTableWidget {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #d8dee9;
    border-radius: 7px;
    gridline-color: #e5e7eb;
    selection-background-color: #e0f2fe;
    selection-color: #0f172a;
}

QPlainTextEdit {
    padding: 2px;
}

QPlainTextEdit#TerminalOutput {
    background-color: #ffffff;
    color: #111827;
    font-family: "JetBrains Mono", "Noto Sans Mono", "DejaVu Sans Mono", monospace;
    font-size: 10px;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #334155;
    padding: 4px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
    font-size: 10px;
}

QTableCornerButton::section {
    background-color: #f8fafc;
    border: none;
}

QSplitter::handle {
    background-color: #e2e8f0;
    margin: 5px 1px;
    border-radius: 2px;
}

QSplitter::handle:hover {
    background-color: #7dd3fc;
}

QScrollBar:vertical {
    background: #ffffff;
    width: 8px;
    margin: 1px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #94a3b8;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #ffffff;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    min-width: 24px;
    border-radius: 4px;
}

QToolTip {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #cbd5e1;
}

QTableWidget {
    font-size: 10px;
}

QStatusBar {
    font-size: 10px;
}
'''
