APP_STYLE = r'''
QWidget {
    background-color: #0d1117;
    color: #e6edf3;
    font-family: Inter, Noto Sans, Arial, sans-serif;
    font-size: 13px;
}
QMainWindow { background-color: #0b1220; }

QFrame#Sidebar,
QFrame#RightSidebar,
QFrame#CenterFrame,
QFrame#TopBar,
QFrame#StatusBarFrame,
QFrame#PanelCard {
    background-color: #111827;
    border: 1px solid #1f2937;
    border-radius: 12px;
}

QTreeView {
    background-color: #0f172a;
    border: 1px solid #1f2937;
    border-radius: 10px;
    padding: 6px;
}
QTreeView::item:selected {
    background-color: #1d4ed8;
    color: #ffffff;
    border-radius: 6px;
}
QPushButton {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 8px 12px;
}
QPushButton:hover {
    background-color: #172033;
    border: 1px solid #3b82f6;
}
QPushButton#PrimaryButton {
    background-color: #0ea5e9;
    color: #081018;
    font-weight: 600;
}
QPushButton#PrimaryButton:hover { background-color: #38bdf8; }

QLabel#TitleLabel { font-size: 22px; font-weight: 700; }
QLabel#SectionTitle { font-size: 16px; font-weight: 600; }
QLabel#MutedLabel { color: #93a4b8; }

QLineEdit, QComboBox {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 8px;
}
QPlainTextEdit, QTextEdit, QTableWidget {
    background-color: #0f172a;
    border: 1px solid #1f2937;
    border-radius: 10px;
}
QHeaderView::section {
    background-color: #111827;
    color: #cbd5e1;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #1f2937;
}
QToolButton {
    background-color: transparent;
    border: none;
    padding: 6px;
}
QScrollBar:vertical {
    background: #111827;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #334155;
    min-height: 25px;
    border-radius: 6px;
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical { height: 0px; }
'''
