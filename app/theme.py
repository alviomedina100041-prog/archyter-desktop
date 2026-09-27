APP_STYLE = r'''
QWidget {
    background-color: #ffffff;
    color: #111827;
    font-family: "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 13px;
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
    border-radius: 12px;
}

QFrame#TopBar {
    background-color: #ffffff;
}

QTreeView {
    background-color: #ffffff;
    color: #111827;
    border: none;
    border-radius: 10px;
    padding: 6px;
    outline: none;
}

QTreeView::item {
    min-height: 27px;
    padding: 2px 4px;
    color: #111827;
}

QTreeView::item:hover {
    background-color: #f1f5f9;
    border-radius: 6px;
}

QTreeView::item:selected {
    background-color: #e0f2fe;
    color: #075985;
    border-radius: 6px;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 9px;
    padding: 8px 13px;
    color: #111827;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #f8fafc;
    border-color: #3b82f6;
}

QPushButton:pressed {
    background-color: #e2e8f0;
}

QPushButton#PrimaryButton {
    background-color: #e0f2fe;
    border-color: #38bdf8;
    color: #0369a1;
    font-weight: 700;
}

QPushButton#PrimaryButton:hover {
    background-color: #bae6fd;
}

QLabel {
    background-color: transparent;
    color: #111827;
}

QLabel#TitleLabel {
    font-size: 22px;
    font-weight: 700;
    color: #0f172a;
}

QLabel#SectionTitle {
    font-size: 15px;
    font-weight: 700;
    color: #0f172a;
}

QLabel#MutedLabel {
    color: #64748b;
}

QLineEdit,
QComboBox {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #cbd5e1;
    border-radius: 8px;
    padding: 7px 9px;
    selection-background-color: #bae6fd;
    selection-color: #0f172a;
}

QPlainTextEdit,
QTextEdit,
QTableWidget {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #d8dee9;
    border-radius: 9px;
    gridline-color: #e5e7eb;
    selection-background-color: #e0f2fe;
    selection-color: #0f172a;
}

QPlainTextEdit#TerminalOutput {
    background-color: #ffffff;
    color: #111827;
    font-family: "JetBrains Mono", "Noto Sans Mono", "DejaVu Sans Mono", monospace;
    font-size: 12px;
}

QHeaderView::section {
    background-color: #f8fafc;
    color: #334155;
    padding: 7px;
    border: none;
    border-bottom: 1px solid #e2e8f0;
}

QTableCornerButton::section {
    background-color: #f8fafc;
    border: none;
}

QSplitter::handle {
    background-color: #e2e8f0;
    width: 4px;
    margin: 10px 3px;
    border-radius: 2px;
}

QSplitter::handle:hover {
    background-color: #7dd3fc;
}

QScrollBar:vertical {
    background: #ffffff;
    width: 10px;
    margin: 2px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 28px;
    border-radius: 5px;
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
    height: 10px;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    min-width: 28px;
    border-radius: 5px;
}

QToolTip {
    background-color: #ffffff;
    color: #111827;
    border: 1px solid #cbd5e1;
}
'''
