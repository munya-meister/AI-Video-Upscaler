from app.theme import *

GLOBAL_STYLE = f"""
QMainWindow {{
    background:{BACKGROUND};
}}

QWidget {{
    background:transparent;
    color:{TEXT};
    font-family:Segoe UI;
}}

QScrollArea {{
    background:transparent;
    border:none;
}}

QLabel {{
    background:transparent;
    border:none;
}}

QPushButton {{
    border:none;
}}

QFrame {{
    background:{CARD};
    border:1px solid {BORDER};
    border-radius:{RADIUS}px;
}}

QLineEdit {{
    background:{CARD};
    border:1px solid {BORDER};
    border-radius:14px;
    color:{TEXT};
    padding:8px 14px;
}}

QScrollBar:vertical {{
    background:transparent;
    width:10px;
}}

QScrollBar::handle:vertical {{
    background:#2B3B5A;
    border-radius:5px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height:0;
}}
"""