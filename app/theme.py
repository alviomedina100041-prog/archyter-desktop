APP_STYLE = r'''
QWidget {
    background-color: #ffffff;
    color: #172033;
    font-family: "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 11px;
}

QMainWindow,
QDialog {
    background-color: #f4f7fb;
}

QFrame#Sidebar,
QFrame#RightSidebar,
QFrame#CenterFrame,
QFrame#TopBar,
QFrame#StatusBarFrame {
    background-color: #ffffff;
    border: 1px solid #dbe3ec;
    border-radius: 10px;
}

QFrame#TopBar {
    background-color: #fbfdff;
}

QFrame#Sidebar,
QFrame#RightSidebar {
    background-color: #fbfcfe;
}

QFrame#CenterFrame {
    background-color: #ffffff;
}

QFrame#StatusBarFrame {
    background-color: #f8fafc;
}

QFrame#PanelCard {
    background-color: #ffffff;
    border: 1px solid #dce4ee;
    border-radius: 9px;
}

QLabel {
    background-color: transparent;
    color: #172033;
}

QLabel#TitleLabel {
    font-size: 17px;
    font-weight: 700;
    color: #0f172a;
}

QLabel#SectionTitle {
    font-size: 12px;
    font-weight: 700;
    color: #1e293b;
}

QLabel#MutedLabel {
    color: #7b899c;
    font-size: 10px;
}

QLabel#KernelName {
    color: #243248;
    font-size: 11px;
    font-weight: 600;
}

QLabel#ProjectChip {
    background: #eef6ff;
    color: #315f8d;
    border: 1px solid #d4e7fb;
    border-radius: 7px;
    padding: 5px 7px;
    font-size: 10px;
}

QLabel#CountBadge {
    background: #edf2f7;
    color: #52637a;
    border-radius: 7px;
    padding: 2px 6px;
    font-size: 9px;
    font-weight: 700;
}

QLabel#StateBadgeOn {
    background: #e7f7ee;
    color: #187246;
    border: 1px solid #b9e8ce;
    border-radius: 7px;
    padding: 2px 6px;
    font-size: 9px;
    font-weight: 700;
}

QLabel#StateBadgeOff {
    background: #f1f5f9;
    color: #64748b;
    border: 1px solid #dde5ee;
    border-radius: 7px;
    padding: 2px 6px;
    font-size: 9px;
    font-weight: 700;
}

QTreeView {
    background-color: transparent;
    color: #172033;
    border: none;
    border-radius: 7px;
    padding: 2px;
    outline: none;
}

QTreeView::item {
    min-height: 23px;
    padding: 1px 3px;
    color: #263449;
}

QTreeView::item:hover {
    background-color: #f0f5fa;
    border-radius: 5px;
}

QTreeView::item:selected {
    background-color: #dff1ff;
    color: #075985;
    border-radius: 5px;
}

QPushButton {
    background-color: #ffffff;
    border: 1px solid #d1dbe7;
    border-radius: 7px;
    padding: 5px 9px;
    color: #263449;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #f3f8ff;
    border-color: #79b8f7;
    color: #0b65bd;
}

QPushButton:pressed {
    background-color: #e8f2ff;
}

QPushButton:disabled {
    background-color: #f8fafc;
    color: #a2adbc;
    border-color: #e5eaf0;
}

QPushButton#PrimaryButton {
    background-color: #0ea5e9;
    border-color: #0ea5e9;
    color: #ffffff;
    font-weight: 700;
    padding-left: 12px;
    padding-right: 12px;
}

QPushButton#PrimaryButton:hover {
    background-color: #0284c7;
    border-color: #0284c7;
    color: #ffffff;
}

QPushButton#SecondaryButton {
    background: #f8fafc;
    color: #475569;
    border-color: #dce4ee;
    min-height: 18px;
    padding: 4px 7px;
}

QPushButton#CompactButton {
    min-height: 18px;
    padding: 4px 7px;
}

QPushButton#BackButton {
    font-size: 15px;
    padding: 2px 5px;
}

QPushButton#PanelTitleButton {
    background-color: transparent;
    border: none;
    padding: 1px 2px;
    color: #1e293b;
    font-size: 11px;
    font-weight: 700;
    text-align: left;
    min-height: 18px;
}

QPushButton#PanelTitleButton:hover {
    background-color: transparent;
    color: #0b6bd3;
}

QPushButton#PanelActionButton {
    background: transparent;
    color: #5f7188;
    border: none;
    padding: 2px 3px;
    min-height: 18px;
    font-size: 9px;
}

QPushButton#PanelActionButton:hover {
    background: #eef6ff;
    color: #0b6bd3;
}

QPushButton#IconButton {
    background: #f8fafc;
    color: #52637a;
    border-color: #e0e7ef;
    padding: 2px;
    min-height: 20px;
}

QLineEdit,
QComboBox {
    background-color: #ffffff;
    color: #172033;
    border: 1px solid #d4dde8;
    border-radius: 7px;
    padding: 5px 7px;
    selection-background-color: #dbeafe;
    selection-color: #172033;
}

QLineEdit:focus,
QComboBox:focus {
    border-color: #60a5fa;
}

QPlainTextEdit,
QTextEdit,
QTableWidget {
    background-color: #ffffff;
    color: #172033;
    border: 1px solid #dce4ee;
    border-radius: 7px;
    gridline-color: #edf1f5;
    selection-background-color: #dff1ff;
    selection-color: #0f4f9a;
}

QTableWidget {
    font-size: 10px;
    alternate-background-color: #f8fafc;
}

QPlainTextEdit {
    padding: 3px;
}

QPlainTextEdit#TerminalOutput,
QPlainTextEdit#LogPreview,
QPlainTextEdit#LogDialog {
    background-color: #fbfdff;
    color: #334155;
    font-family: "JetBrains Mono", "Noto Sans Mono", "DejaVu Sans Mono", monospace;
    font-size: 9px;
}

QPlainTextEdit#TerminalOutput {
    selection-background-color: #dbeafe;
}

QHeaderView::section {
    background-color: #f6f8fb;
    color: #52637a;
    padding: 5px;
    border: none;
    border-bottom: 1px solid #dfe6ee;
    font-size: 9px;
    font-weight: 700;
}

QTableCornerButton::section {
    background-color: #f6f8fb;
    border: none;
}

QSplitter::handle {
    background-color: #e4eaf1;
    margin: 5px 1px;
    border-radius: 2px;
}

QSplitter::handle:hover {
    background-color: #86bdf2;
}

QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 1px;
}

QScrollBar::handle:vertical {
    background: #cbd5e1;
    min-height: 24px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #aebccc;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background: #cbd5e1;
    min-width: 24px;
    border-radius: 4px;
}

QScrollBar::handle:horizontal:hover {
    background: #aebccc;
}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {
    width: 0px;
}

QToolTip {
    background-color: #172033;
    color: #ffffff;
    border: 1px solid #334155;
    padding: 4px 6px;
}

QMessageBox {
    background: #ffffff;
}
'''
