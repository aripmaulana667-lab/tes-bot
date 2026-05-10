"""Centralised QSS for the controller's dark theme."""


STYLESHEET = """
QWidget {
    background-color: #1c1f24;
    color: #e8eaed;
    font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
}

QFrame#Sidebar {
    background-color: #14171c;
    border: none;
    border-right: 1px solid #2a2e36;
}

QLabel#SidebarTitle {
    color: #ffffff;
    font-size: 16px;
    font-weight: 700;
    padding: 4px 4px 12px 4px;
}

QLabel#SidebarVersion {
    color: #6b7180;
    font-size: 11px;
    padding-top: 6px;
}

QPushButton#SidebarButton {
    text-align: left;
    padding: 8px 14px;
    border-radius: 8px;
    background-color: transparent;
    color: #c8ccd4;
    font-weight: 500;
}

QPushButton#SidebarButton:hover {
    background-color: #1f242c;
    color: #ffffff;
}

QPushButton#SidebarButton:checked {
    background-color: #2c6bff;
    color: #ffffff;
}

QFrame#StatCard {
    background-color: #232830;
    border: 1px solid #2c333d;
    border-radius: 10px;
}

QLabel#StatCardTitle {
    color: #8d96a3;
    font-size: 12px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.4px;
}

QLabel#StatCardValue {
    color: #ffffff;
    font-size: 22px;
    font-weight: 700;
}

QLabel#StatCardSub {
    color: #8d96a3;
    font-size: 11px;
}

QPushButton {
    background-color: #2c6bff;
    color: #ffffff;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #3b78ff;
}

QPushButton:disabled {
    background-color: #3a4250;
    color: #7a8190;
}

QPushButton[secondary="true"] {
    background-color: #2a313b;
    color: #d6dae3;
    border: 1px solid #353c47;
}

QPushButton[secondary="true"]:hover {
    background-color: #313945;
}

QPushButton[danger="true"] {
    background-color: #d04848;
}

QPushButton[danger="true"]:hover {
    background-color: #e25555;
}

QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit, QPlainTextEdit {
    background-color: #161a20;
    border: 1px solid #2b313b;
    border-radius: 6px;
    padding: 6px 8px;
    color: #ffffff;
    selection-background-color: #2c6bff;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
    border-color: #2c6bff;
}

QTableWidget {
    background-color: #1c2027;
    border: 1px solid #2a2e36;
    border-radius: 8px;
    gridline-color: #2a2e36;
    selection-background-color: #2c6bff;
    alternate-background-color: #1f242c;
}

QHeaderView::section {
    background-color: #14171c;
    color: #c4c9d2;
    padding: 8px;
    border: none;
    border-bottom: 1px solid #2a2e36;
    font-weight: 600;
}

QStatusBar {
    background-color: #14171c;
    color: #8d96a3;
}

QProgressBar {
    border: 1px solid #2b313b;
    border-radius: 5px;
    text-align: center;
    background: #161a20;
    color: #ffffff;
}

QProgressBar::chunk {
    background-color: #2c6bff;
    border-radius: 5px;
}

QTabWidget::pane {
    border: 1px solid #2a2e36;
    border-radius: 8px;
    top: -1px;
}

QTabBar::tab {
    background: #1c2027;
    color: #c4c9d2;
    padding: 8px 16px;
    border: 1px solid #2a2e36;
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background: #232a33;
    color: #ffffff;
}

QCheckBox {
    spacing: 8px;
}
"""
