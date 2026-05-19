# Цветовая схема приложения

# Основные цвета
MAIN_BG = "#f0f2f5"
SIDEBAR_BG = "#1e3a5f"
SIDEBAR_FG = "#ecf0f1"
BUTTON_PRIMARY = "#2980b9"
BUTTON_PRIMARY_HOVER = "#1a5276"
BUTTON_SUCCESS = "#27ae60"
BUTTON_SUCCESS_HOVER = "#1e8449"
BUTTON_DANGER = "#c0392b"
BUTTON_DANGER_HOVER = "#922b21"

# Цвета для ответов
CORRECT_COLOR = "#27ae60"
CORRECT_BG = "#d5f5e3"
WRONG_COLOR = "#c0392b"
WRONG_BG = "#fadbd8"
NEUTRAL_BG = "#ffffff"
SELECTED_BG = "#d4e6f1"
HOVER_BG = "#ebf5fb"

# Шрифты
FONT_FAMILY = "Segoe UI, Arial, sans-serif"
QUESTION_FONT_SIZE = 15
ANSWER_FONT_SIZE = 13
TITLE_FONT_SIZE = 22
SUBTITLE_FONT_SIZE = 16

# Размеры
BORDER_RADIUS = 10
CARD_PADDING = 15

# Стили для PyQt
MAIN_STYLE = f"""
QMainWindow {{
    background-color: {MAIN_BG};
}}

QLabel {{
    font-family: {FONT_FAMILY};
}}

QPushButton {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
    font-weight: bold;
    padding: 10px 20px;
    border-radius: 6px;
    border: none;
    min-height: 20px;
}}

QPushButton:hover {{
    opacity: 0.9;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

QScrollBar:vertical {{
    border: none;
    background: {MAIN_BG};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: #b0b8c1;
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: #8895a7;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}
"""