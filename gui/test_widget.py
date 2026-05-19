from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QSizePolicy,
    QButtonGroup, QRadioButton, QProgressBar, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QPixmap, QFont

from core.test_manager import TestManager
from utils.helpers import base64_to_pixmap
from .styles import (
    CORRECT_COLOR, CORRECT_BG, WRONG_COLOR, WRONG_BG,
    NEUTRAL_BG, SELECTED_BG, HOVER_BG,
    QUESTION_FONT_SIZE, ANSWER_FONT_SIZE, TITLE_FONT_SIZE,
    FONT_FAMILY, BORDER_RADIUS, CARD_PADDING,
    BUTTON_PRIMARY, BUTTON_PRIMARY_HOVER, BUTTON_SUCCESS
)


class TestWidget(QWidget):
    """Виджет для прохождения теста"""
    
    test_finished = pyqtSignal(dict)
    back_to_editor = pyqtSignal()
    
    def __init__(self, test_manager: TestManager, parent=None):
        super().__init__(parent)
        self.test_manager = test_manager
        self.answer_group = QButtonGroup(self)
        self.answer_widgets = []
        self.answered = False
        
        self._init_ui()
    
    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 15, 20, 15)
        main_layout.setSpacing(10)
        
        # === ВЕРХНЯЯ ПАНЕЛЬ ===
        top_panel = QFrame()
        top_panel.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: {BORDER_RADIUS}px;
                border: 1px solid #d5d8dc;
                padding: 10px;
            }}
        """)
        top_layout = QHBoxLayout(top_panel)
        top_layout.setContentsMargins(15, 8, 15, 8)
        
        self.back_btn = QPushButton("← К редактору")
        self.back_btn.clicked.connect(self._on_back)
        self.back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #95a5a6;
                color: white;
                font-size: 12px;
                padding: 7px 14px;
            }}
            QPushButton:hover {{ background-color: #7f8c8d; }}
        """)
        
        self.progress_label = QLabel("Вопрос 0 из 0")
        self.progress_label.setStyleSheet(f"""
            font-size: {ANSWER_FONT_SIZE}px;
            font-weight: bold;
            color: #1e3a5f;
            font-family: {FONT_FAMILY};
        """)
        
        top_layout.addWidget(self.back_btn)
        top_layout.addStretch()
        top_layout.addWidget(self.progress_label)
        main_layout.addWidget(top_panel)
        
        # === ПРОГРЕСС-БАР ===
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setMinimumHeight(22)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                text-align: center;
                font-size: 11px;
                font-weight: bold;
                background-color: white;
                font-family: {FONT_FAMILY};
            }}
            QProgressBar::chunk {{
                background-color: {BUTTON_PRIMARY};
                border-radius: 5px;
            }}
        """)
        main_layout.addWidget(self.progress_bar)
        
        # === КАРТОЧКА ВОПРОСА ===
        question_card = QFrame()
        question_card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border-radius: {BORDER_RADIUS}px;
                border: 1px solid #d5d8dc;
            }}
        """)
        question_card_layout = QVBoxLayout(question_card)
        question_card_layout.setContentsMargins(CARD_PADDING, CARD_PADDING, CARD_PADDING, CARD_PADDING)
        question_card_layout.setSpacing(8)
        
        # Текст вопроса
        self.question_label = QLabel()
        self.question_label.setWordWrap(True)
        self.question_label.setStyleSheet(f"""
            font-size: {QUESTION_FONT_SIZE}px;
            font-weight: bold;
            color: #1e3a5f;
            font-family: {FONT_FAMILY};
            padding: 5px 0;
        """)
        question_card_layout.addWidget(self.question_label)
        
        # Картинки вопроса
        self.question_images_layout = QVBoxLayout()
        self.question_images_layout.setAlignment(Qt.AlignCenter)
        question_card_layout.addLayout(self.question_images_layout)
        
        main_layout.addWidget(question_card)
        
        # === ОБЛАСТЬ ОТВЕТОВ (с прокруткой) ===
        answers_label = QLabel("Выберите ответ:")
        answers_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: #7f8c8d;
            font-family: {FONT_FAMILY};
            margin-top: 5px;
        """)
        main_layout.addWidget(answers_label)
        
        self.answers_scroll = QScrollArea()
        self.answers_scroll.setWidgetResizable(True)
        self.answers_scroll.setFrameShape(QFrame.NoFrame)
        self.answers_scroll.setMaximumHeight(450)  # фиксированная высота с прокруткой
        self.answers_scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
        """)
        
        self.answers_container = QWidget()
        self.answers_layout = QVBoxLayout(self.answers_container)
        self.answers_layout.setSpacing(6)
        self.answers_layout.setContentsMargins(0, 0, 0, 0)
        
        self.answers_scroll.setWidget(self.answers_container)
        main_layout.addWidget(self.answers_scroll, stretch=1)
        
        # === РЕЗУЛЬТАТ ОТВЕТА ===
        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignCenter)
        self.result_label.setWordWrap(True)
        self.result_label.setVisible(False)
        self.result_label.setMinimumHeight(50)
        self.result_label.setStyleSheet(f"""
            font-size: {ANSWER_FONT_SIZE}px;
            font-weight: bold;
            font-family: {FONT_FAMILY};
            padding: 10px;
            border-radius: 8px;
        """)
        main_layout.addWidget(self.result_label)
        
        # === КНОПКИ ===
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(15)
        
        self.submit_btn = QPushButton("✅ ОТВЕТИТЬ")
        self.submit_btn.clicked.connect(self._on_submit)
        self.submit_btn.setEnabled(False)
        self.submit_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_PRIMARY};
                color: white;
                font-size: 15px;
                padding: 12px 35px;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background-color: {BUTTON_PRIMARY_HOVER}; }}
            QPushButton:disabled {{
                background-color: #b0b8c1;
                color: #e5e7ea;
            }}
        """)
        
        self.next_btn = QPushButton("СЛЕДУЮЩИЙ ВОПРОС →")
        self.next_btn.clicked.connect(self._on_next)
        self.next_btn.setVisible(False)
        self.next_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_SUCCESS};
                color: white;
                font-size: 15px;
                padding: 12px 35px;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background-color: #1e8449; }}
        """)
        
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.submit_btn)
        buttons_layout.addWidget(self.next_btn)
        buttons_layout.addStretch()
        main_layout.addLayout(buttons_layout)
    
    def start_test(self):
        """Начинает/перезапускает тест"""
        self.test_manager.start_test_session(shuffle_questions=True)
        self.answered = False
        self._show_current_question()
    
    def _show_current_question(self):
        """Отображает текущий вопрос"""
        self._clear_answers()
        
        question = self.test_manager.get_current_question()
        if not question:
            return
        
        # Прогресс
        current, total = self.test_manager.get_progress()
        self.progress_label.setText(f"Вопрос {current} из {total}")
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        
        # Текст вопроса
        self.question_label.setText(question.question_text)
        
        # Картинки вопроса
        self._clear_layout(self.question_images_layout)
        
        if question.question_images:
            for img_b64 in question.question_images:
                pixmap = base64_to_pixmap(img_b64, max_width=600, max_height=350)
                if pixmap:
                    img_label = QLabel()
                    img_label.setPixmap(pixmap)
                    img_label.setAlignment(Qt.AlignCenter)
                    img_label.setStyleSheet("""
                        border: 1px solid #e5e7ea;
                        border-radius: 6px;
                        padding: 5px;
                        background-color: white;
                        margin: 3px 0;
                    """)
                    self.question_images_layout.addWidget(img_label)
        
        # Перемешанные ответы
        shuffled = self.test_manager.get_shuffled_answers(question)
        
        for btn in self.answer_group.buttons():
            self.answer_group.removeButton(btn)
        
        self.answer_widgets = []
        
        for answer, original_idx in shuffled:
            answer_frame = QFrame()
            answer_frame.setStyleSheet(f"""
                QFrame {{
                    background-color: {NEUTRAL_BG};
                    border: 1px solid #d5d8dc;
                    border-radius: 8px;
                }}
                QFrame:hover {{
                    border-color: {BUTTON_PRIMARY};
                    background-color: {HOVER_BG};
                }}
            """)
            
            frame_layout = QVBoxLayout(answer_frame)
            frame_layout.setContentsMargins(12, 10, 12, 10)
            
            # Радио-кнопка
            radio_btn = QRadioButton(answer.text)
            radio_btn.setStyleSheet(f"""
                font-size: {ANSWER_FONT_SIZE}px;
                font-family: {FONT_FAMILY};
                color: #2c3e50;
                spacing: 10px;
            """)
            radio_btn.toggled.connect(self._on_answer_selected)
            self.answer_group.addButton(radio_btn)
            
            frame_layout.addWidget(radio_btn)
            
            # Картинки ответа
            if answer.images:
                for img_b64 in answer.images:
                    pixmap = base64_to_pixmap(img_b64, max_width=350, max_height=220)
                    if pixmap:
                        img_label = QLabel()
                        img_label.setPixmap(pixmap)
                        img_label.setAlignment(Qt.AlignCenter)
                        img_label.setStyleSheet("""
                            border: 1px solid #eee;
                            border-radius: 4px;
                            padding: 3px;
                            margin-top: 5px;
                        """)
                        frame_layout.addWidget(img_label)
            
            self.answers_layout.addWidget(answer_frame)
            self.answer_widgets.append((radio_btn, answer.id, answer_frame))
        
        # Сбрасываем состояние
        self.submit_btn.setEnabled(False)
        self.submit_btn.setVisible(True)
        self.next_btn.setVisible(False)
        self.result_label.setVisible(False)
        self.answered = False
    
    def _on_answer_selected(self, checked):
        if checked:
            self.submit_btn.setEnabled(True)
    
    def _on_submit(self):
        if self.answered:
            return
        
        selected_btn = self.answer_group.checkedButton()
        if not selected_btn:
            return
        
        selected_answer_id = None
        for radio_btn, answer_id, frame in self.answer_widgets:
            if radio_btn == selected_btn:
                selected_answer_id = answer_id
                break
        
        if not selected_answer_id:
            return
        
        question = self.test_manager.get_current_question()
        if not question:
            return
        
        is_correct = self.test_manager.submit_answer(question.id, selected_answer_id)
        self._highlight_answers(is_correct, selected_answer_id, question)
        
        if is_correct:
            self.result_label.setText("✅ ПРАВИЛЬНО!")
            self.result_label.setStyleSheet(f"""
                font-size: {ANSWER_FONT_SIZE}px;
                font-weight: bold;
                font-family: {FONT_FAMILY};
                padding: 10px;
                border-radius: 8px;
                color: {CORRECT_COLOR};
                background-color: {CORRECT_BG};
            """)
        else:
            correct_answer = question.get_correct_answer()
            correct_text = correct_answer.text if correct_answer else "?"
            self.result_label.setText(f"❌ НЕПРАВИЛЬНО!\nВерный ответ: {correct_text[:120]}")
            self.result_label.setStyleSheet(f"""
                font-size: {ANSWER_FONT_SIZE}px;
                font-weight: bold;
                font-family: {FONT_FAMILY};
                padding: 10px;
                border-radius: 8px;
                color: {WRONG_COLOR};
                background-color: {WRONG_BG};
            """)
        
        self.result_label.setVisible(True)
        self.submit_btn.setVisible(False)
        self.next_btn.setVisible(True)
        self.answered = True
        
        current, total = self.test_manager.get_progress()
        self.progress_bar.setValue(current)
    
    def _highlight_answers(self, is_correct, selected_id, question):
        correct_answer = question.get_correct_answer()
        
        for radio_btn, answer_id, frame in self.answer_widgets:
            radio_btn.setEnabled(False)
            
            if answer_id == correct_answer.id:
                frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {CORRECT_BG};
                        border: 2px solid {CORRECT_COLOR};
                        border-radius: 8px;
                    }}
                """)
            elif answer_id == selected_id and not is_correct:
                frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {WRONG_BG};
                        border: 2px solid {WRONG_COLOR};
                        border-radius: 8px;
                    }}
                """)
    
    def _on_next(self):
        has_more = self.test_manager.next_question()
        
        if has_more:
            self._show_current_question()
        else:
            results = self.test_manager.get_results()
            self.test_finished.emit(results)
    
    def _on_back(self):
        reply = QMessageBox.question(
            self,
            "Вернуться в редактор?",
            "Прогресс теста будет потерян. Продолжить?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.back_to_editor.emit()
    
    def _clear_answers(self):
        for i in reversed(range(self.answers_layout.count())):
            widget = self.answers_layout.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        
        self.answer_widgets = []
    
    def _clear_layout(self, layout):
        if layout is None:
            return
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            elif item.layout():
                self._clear_layout(item.layout())