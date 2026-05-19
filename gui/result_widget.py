from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from .styles import (
    CORRECT_COLOR, CORRECT_BG, WRONG_COLOR, WRONG_BG,
    BUTTON_PRIMARY, BUTTON_PRIMARY_HOVER, BUTTON_SUCCESS,
    MAIN_BG, FONT_FAMILY, BORDER_RADIUS, CARD_PADDING,
    TITLE_FONT_SIZE, SUBTITLE_FONT_SIZE
)


class ResultWidget(QWidget):
    """Виджет отображения результатов теста"""
    
    retry_wrong = pyqtSignal()
    retry_all = pyqtSignal()
    back_to_editor = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.results = None
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Заголовок
        title_label = QLabel("📊 РЕЗУЛЬТАТЫ ТЕСТА")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet(f"""
            font-size: {TITLE_FONT_SIZE}px;
            font-weight: bold;
            color: #1e3a5f;
            font-family: {FONT_FAMILY};
            padding: 10px;
        """)
        main_layout.addWidget(title_label)
        
        # Карточка с результатом
        self.result_card = QFrame()
        self.result_card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: {BORDER_RADIUS}px;
                border: 1px solid #d5d8dc;
                padding: 20px;
            }}
        """)
        
        card_layout = QVBoxLayout(self.result_card)
        
        self.score_label = QLabel()
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setStyleSheet(f"""
            font-size: 52px;
            font-weight: bold;
            font-family: {FONT_FAMILY};
        """)
        card_layout.addWidget(self.score_label)
        
        self.detail_label = QLabel()
        self.detail_label.setAlignment(Qt.AlignCenter)
        self.detail_label.setStyleSheet(f"""
            font-size: {SUBTITLE_FONT_SIZE}px;
            font-family: {FONT_FAMILY};
            color: #7f8c8d;
        """)
        card_layout.addWidget(self.detail_label)
        
        main_layout.addWidget(self.result_card)
        
        # Таблица ошибок
        self.wrong_label = QLabel("Вопросы с ошибками:")
        self.wrong_label.setStyleSheet(f"""
            font-size: {SUBTITLE_FONT_SIZE}px;
            font-weight: bold;
            color: #1e3a5f;
            font-family: {FONT_FAMILY};
        """)
        self.wrong_label.setVisible(False)
        main_layout.addWidget(self.wrong_label)
        
        self.wrong_table = QTableWidget()
        self.wrong_table.setColumnCount(3)
        self.wrong_table.setHorizontalHeaderLabels(["Вопрос", "Ваш ответ", "Правильный ответ"])
        self.wrong_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.wrong_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.wrong_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.wrong_table.setMinimumHeight(150)
        self.wrong_table.setMaximumHeight(350)
        self.wrong_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: white;
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                gridline-color: #e5e7ea;
                font-family: {FONT_FAMILY};
                font-size: 12px;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
            QHeaderView::section {{
                background-color: #f0f2f5;
                padding: 8px;
                font-weight: bold;
                font-size: 12px;
                font-family: {FONT_FAMILY};
                border: none;
                border-bottom: 2px solid #b0b8c1;
            }}
        """)
        self.wrong_table.setVisible(False)
        main_layout.addWidget(self.wrong_table)
        
        # Оценка
        self.grade_label = QLabel()
        self.grade_label.setAlignment(Qt.AlignCenter)
        self.grade_label.setStyleSheet(f"""
            font-size: 18px;
            font-weight: bold;
            font-family: {FONT_FAMILY};
            padding: 10px;
        """)
        self.grade_label.setVisible(False)
        main_layout.addWidget(self.grade_label)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.retry_wrong_btn = QPushButton("🔄 Перепройти ошибки")
        self.retry_wrong_btn.clicked.connect(self._on_retry_wrong)
        self.retry_wrong_btn.setVisible(False)
        self.retry_wrong_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #e67e22;
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{ background-color: #d35400; }}
        """)
        
        self.retry_all_btn = QPushButton("📝 Пройти заново")
        self.retry_all_btn.clicked.connect(self._on_retry_all)
        self.retry_all_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_PRIMARY};
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{ background-color: {BUTTON_PRIMARY_HOVER}; }}
        """)
        
        self.back_btn = QPushButton("📋 В редактор")
        self.back_btn.clicked.connect(self._on_back)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #95a5a6;
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
                font-family: {FONT_FAMILY};
            }}
            QPushButton:hover {{ background-color: #7f8c8d; }}
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.retry_wrong_btn)
        buttons_layout.addWidget(self.retry_all_btn)
        buttons_layout.addWidget(self.back_btn)
        buttons_layout.addStretch()
        
        main_layout.addLayout(buttons_layout)
        main_layout.addStretch()
    
    def show_results(self, results: dict):
        self.results = results
        
        total = results["total"]
        correct = results["correct"]
        wrong = results["wrong"]
        percentage = results["percentage"]
        
        if percentage >= 90:
            color = "#27ae60"
            emoji = "🏆"
        elif percentage >= 75:
            color = "#2ecc71"
            emoji = "👍"
        elif percentage >= 60:
            color = "#f39c12"
            emoji = "📚"
        elif percentage >= 40:
            color = "#e67e22"
            emoji = "💪"
        else:
            color = "#c0392b"
            emoji = "📖"
        
        self.score_label.setText(f"{emoji} {percentage}%")
        self.score_label.setStyleSheet(f"""
            font-size: 52px;
            font-weight: bold;
            font-family: {FONT_FAMILY};
            color: {color};
        """)
        
        self.detail_label.setText(
            f"Правильно: {correct} из {total}    |    Ошибок: {wrong}"
        )
        
        if wrong > 0 and "wrong_details" in results:
            self.wrong_label.setVisible(True)
            self.wrong_table.setVisible(True)
            
            self.wrong_table.setRowCount(len(results["wrong_details"]))
            
            for i, detail in enumerate(results["wrong_details"]):
                question_text = detail["question"].question_text[:100]
                user_text = detail["user_answer"].text[:80] if detail["user_answer"] else "Нет ответа"
                correct_text = detail["correct_answer"].text[:80] if detail["correct_answer"] else "?"
                
                self.wrong_table.setItem(i, 0, QTableWidgetItem(question_text))
                
                user_item = QTableWidgetItem(user_text)
                user_item.setForeground(Qt.red)
                self.wrong_table.setItem(i, 1, user_item)
                
                correct_item = QTableWidgetItem(correct_text)
                correct_item.setForeground(Qt.darkGreen)
                self.wrong_table.setItem(i, 2, correct_item)
            
            self.wrong_table.resizeRowsToContents()
            self.retry_wrong_btn.setVisible(True)
            self.grade_label.setVisible(True)
            
            if percentage >= 90:
                grade = "ОТЛИЧНО! Так держать! 🎉"
            elif percentage >= 75:
                grade = "ХОРОШО! Ещё немного подучить! 📚"
            elif percentage >= 60:
                grade = "УДОВЛЕТВОРИТЕЛЬНО. Надо повторить материал. 💪"
            else:
                grade = "НУЖНО БОЛЬШЕ УЧИТЬ! Не сдавайся! 📖"
            
            self.grade_label.setText(grade)
        else:
            self.wrong_label.setVisible(False)
            self.wrong_table.setVisible(False)
            self.retry_wrong_btn.setVisible(False)
            
            if total > 0:
                self.grade_label.setVisible(True)
                self.grade_label.setText("ИДЕАЛЬНО! Все ответы правильные! 🌟")
    
    def _on_retry_wrong(self):
        self.retry_wrong.emit()
    
    def _on_retry_all(self):
        self.retry_all.emit()
    
    def _on_back(self):
        self.back_to_editor.emit()