import json
import os
import re
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTextEdit, QListWidget, QListWidgetItem,
    QSplitter, QFileDialog, QMessageBox, QFrame,
    QScrollArea, QTabWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QTextDocument, QKeyEvent

from core.test_manager import TestManager
from core.parser import QuestionParser
from core.models import Question, Answer
from utils.helpers import image_to_base64, base64_to_pixmap, pixmap_to_base64
from .styles import (
    BUTTON_PRIMARY, BUTTON_PRIMARY_HOVER, BUTTON_SUCCESS,
    BUTTON_SUCCESS_HOVER, BUTTON_DANGER, BUTTON_DANGER_HOVER,
    MAIN_BG, FONT_FAMILY, QUESTION_FONT_SIZE, BORDER_RADIUS,
    CARD_PADDING, TITLE_FONT_SIZE, SUBTITLE_FONT_SIZE,
    SELECTED_BG, HOVER_BG
)


class EditorWidget(QWidget):
    """Виджет редактора тестов с поддержкой добавления и редактирования"""
    
    start_test = pyqtSignal()
    question_added = pyqtSignal(int)
    
    def __init__(self, test_manager: TestManager, parent=None):
        super().__init__(parent)
        self.test_manager = test_manager
        self.editing_index = -1  # -1 = новый, >=0 = редактируем существующий
        
        self.markers = self._load_markers()
        self.strict_mode = self._load_strict_mode()
        
        self._init_ui()
        self._refresh_question_list()
    
    def _load_markers(self) -> list:
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config", "settings.json"
            )
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Если включено автоопределение (по умолчанию True)
                    if data.get("auto_detect_markers", True):
                        return None
                    return data.get("markers", ["a)", "b)", "c)", "d)", "e)"])
        except:
            pass
        return None  # По умолчанию используем автоопределение
    
    def _load_strict_mode(self) -> bool:
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "config", "settings.json"
            )
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("strict_mode", True)
        except:
            pass
        return True
    
    def refresh_settings(self):
        self.markers = self._load_markers()
        self.strict_mode = self._load_strict_mode()
    
    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(2)
        
        # ===== ЛЕВАЯ ПАНЕЛЬ =====
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")
        left_panel.setStyleSheet(f"""
            #leftPanel {{
                background-color: white;
                border-radius: {BORDER_RADIUS}px;
                border: 1px solid #d5d8dc;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(CARD_PADDING, CARD_PADDING, CARD_PADDING, CARD_PADDING)
        left_layout.setSpacing(10)
        
        left_title = QLabel("📝 Список вопросов")
        left_title.setStyleSheet(f"""
            font-size: {SUBTITLE_FONT_SIZE}px;
            font-weight: bold;
            color: #1e3a5f;
        """)
        left_layout.addWidget(left_title)
        
        self.question_count_label = QLabel("Вопросов: 0")
        self.question_count_label.setStyleSheet("font-size: 12px; color: #7f8c8d; margin-bottom: 5px;")
        left_layout.addWidget(self.question_count_label)
        
        self.question_list = QListWidget()
        self.question_list.setStyleSheet(f"""
            QListWidget {{
                border: 1px solid #e5e7ea;
                border-radius: 6px;
                font-size: 12px;
                font-family: {FONT_FAMILY};
                outline: none;
            }}
            QListWidget::item {{
                padding: 10px 12px;
                border-bottom: 1px solid #f0f0f0;
            }}
            QListWidget::item:selected {{
                background-color: {SELECTED_BG};
                color: #1e3a5f;
                border-left: 3px solid #2980b9;
                font-weight: bold;
            }}
            QListWidget::item:hover {{
                background-color: {HOVER_BG};
            }}
        """)
        self.question_list.itemClicked.connect(self._on_question_clicked)
        left_layout.addWidget(self.question_list, stretch=1)
        
        list_buttons = QHBoxLayout()
        list_buttons.setSpacing(8)
        
        self.delete_question_btn = QPushButton("🗑 Удалить")
        self.delete_question_btn.clicked.connect(self._delete_question)
        self.delete_question_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_DANGER};
                color: white;
                font-size: 11px;
                padding: 7px 14px;
                border-radius: 4px;
            }}
            QPushButton:hover {{ background-color: {BUTTON_DANGER_HOVER}; }}
        """)
        
        self.clear_all_btn = QPushButton("Очистить всё")
        self.clear_all_btn.clicked.connect(self._clear_all_questions)
        self.clear_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #95a5a6;
                color: white;
                font-size: 11px;
                padding: 7px 14px;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #7f8c8d; }
        """)
        
        list_buttons.addWidget(self.delete_question_btn)
        list_buttons.addWidget(self.clear_all_btn)
        list_buttons.addStretch()
        left_layout.addLayout(list_buttons)
        
        # ===== ПРАВАЯ ПАНЕЛЬ С ВКЛАДКАМИ =====
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_panel.setStyleSheet(f"""
            #rightPanel {{
                background-color: white;
                border-radius: {BORDER_RADIUS}px;
                border: 1px solid #d5d8dc;
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(CARD_PADDING, CARD_PADDING, CARD_PADDING, CARD_PADDING)
        right_layout.setSpacing(10)
        
        self.right_title = QLabel("✏️ Добавление вопроса")
        self.right_title.setStyleSheet(f"""
            font-size: {SUBTITLE_FONT_SIZE}px;
            font-weight: bold;
            color: #1e3a5f;
        """)
        right_layout.addWidget(self.right_title)
                # Кнопка диагностики
        diag_btn = QPushButton("🩺 Диагностика HTML")
        diag_btn.clicked.connect(self._dump_html)
        diag_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; color: white;
                font-size: 10px; padding: 5px 10px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        right_layout.addWidget(diag_btn, alignment=Qt.AlignRight)
                # Кнопка импорта HTML
        import_btn = QPushButton("📥 Импорт из HTML")
        import_btn.clicked.connect(self._import_from_html)
        import_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a085; color: white;
                font-size: 10px; padding: 5px 10px; border-radius: 4px;
            }
            QPushButton:hover { background-color: #138d75; }
        """)
        right_layout.addWidget(import_btn, alignment=Qt.AlignRight)
        # Кнопка сброса
        new_q_btn = QPushButton("🆕 Новый вопрос")
        new_q_btn.clicked.connect(self._reset_to_new_mode)
        new_q_btn.setStyleSheet("""
            QPushButton { background-color: #8e44ad; color: white; font-size: 11px; padding: 6px 12px; border-radius: 4px; }
            QPushButton:hover { background-color: #7d3c98; }
        """)
        right_layout.addWidget(new_q_btn, alignment=Qt.AlignLeft)
        
        # Вкладки
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet(f"""
            QTabWidget::pane {{
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                background-color: #fafbfc;
            }}
            QTabBar::tab {{
                padding: 8px 16px;
                font-family: {FONT_FAMILY};
                font-size: 12px;
                font-weight: bold;
                border: 1px solid #d5d8dc;
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                background-color: #e5e7ea;
                margin-right: 2px;
            }}
            QTabBar::tab:selected {{
                background-color: #fafbfc;
                border-bottom: 2px solid #2980b9;
            }}
        """)
        
        # === ВКЛАДКА 1: Один вопрос ===
        single_tab = QWidget()
        single_layout = QVBoxLayout(single_tab)
        single_layout.setContentsMargins(10, 10, 10, 10)
        single_layout.setSpacing(8)
        
        self.single_instruction = QLabel(
            "Вставьте ОДИН вопрос с ответами (Ctrl+V).\n"
            "Нажмите Ctrl+Enter или кнопку ниже."
        )
        self.single_instruction.setWordWrap(True)
        self.single_instruction.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        single_layout.addWidget(self.single_instruction)
        
        self.single_text_input = QTextEdit()
        self.single_text_input.setAcceptRichText(True)
        self.single_text_input.setPlaceholderText(
            "Вопрос с ответами...\n\n1. Что такое X?\na) ответ 1\nb) ответ 2\nc) ответ 3"
        )
        self.single_text_input.setMinimumHeight(180)
        self.single_text_input.setStyleSheet(f"""
            QTextEdit {{
                border: 2px dashed #b0b8c1;
                border-radius: 8px;
                padding: 12px;
                font-size: {QUESTION_FONT_SIZE}px;
                font-family: {FONT_FAMILY};
                background-color: #fafbfc;
            }}
            QTextEdit:focus {{
                border-color: #2980b9;
                background-color: white;
            }}
        """)
        self.single_text_input.installEventFilter(self)
        single_layout.addWidget(self.single_text_input, stretch=1)
        
        single_btn_layout = QHBoxLayout()
        single_btn_layout.addStretch()
        
        self.add_single_btn = QPushButton("➕ ДОБАВИТЬ ВОПРОС (Ctrl+Enter)")
        self.add_single_btn.clicked.connect(self._handle_single_action)
        self.add_single_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_SUCCESS};
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: {BUTTON_SUCCESS_HOVER}; }}
        """)
        single_btn_layout.addWidget(self.add_single_btn)
        single_btn_layout.addStretch()
        single_layout.addLayout(single_btn_layout)
        
        self.tab_widget.addTab(single_tab, "📝 Один вопрос")
        
        # === ВКЛАДКА 2: Несколько вопросов ===
        multi_tab = QWidget()
        multi_layout = QVBoxLayout(multi_tab)
        multi_layout.setContentsMargins(10, 10, 10, 10)
        multi_layout.setSpacing(8)
        
        multi_instruction = QLabel(
            "Вставьте НЕСКОЛЬКО вопросов подряд (Ctrl+V).\n"
            "Каждый вопрос должен начинаться с номера: 1. 2. 3. и т.д.\n"
            "Картинки не поддерживаются в этом режиме."
        )
        multi_instruction.setWordWrap(True)
        multi_instruction.setStyleSheet("font-size: 11px; color: #7f8c8d;")
        multi_layout.addWidget(multi_instruction)
        
        self.multi_text_input = QTextEdit()
        self.multi_text_input.setAcceptRichText(False)  # ТОЛЬКО ТЕКСТ
        self.multi_text_input.setPlaceholderText(
            "Несколько вопросов...\n\n"
            "1. Первый вопрос\n"
            "a) ответ 1\n"
            "b) ответ 2\n\n"
            "2. Второй вопрос\n"
            "a) ответ 1\n"
            "b) ответ 2\n\n"
            "3. Третий вопрос..."
        )
        self.multi_text_input.setMinimumHeight(180)
        self.multi_text_input.setStyleSheet(f"""
            QTextEdit {{
                border: 2px dashed #b0b8c1;
                border-radius: 8px;
                padding: 12px;
                font-size: {QUESTION_FONT_SIZE}px;
                font-family: {FONT_FAMILY};
                background-color: #fafbfc;
            }}
            QTextEdit:focus {{
                border-color: #2980b9;
                background-color: white;
            }}
        """)
        multi_layout.addWidget(self.multi_text_input, stretch=1)
        
        multi_btn_layout = QHBoxLayout()
        multi_btn_layout.addStretch()
        
        add_multi_btn = QPushButton("➕ ДОБАВИТЬ ВСЕ ВОПРОСЫ")
        add_multi_btn.clicked.connect(self._add_multi_questions)
        add_multi_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_SUCCESS};
                color: white;
                font-size: 13px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 6px;
            }}
            QPushButton:hover {{ background-color: {BUTTON_SUCCESS_HOVER}; }}
        """)
        multi_btn_layout.addWidget(add_multi_btn)
        multi_btn_layout.addStretch()
        multi_layout.addLayout(multi_btn_layout)
        
        self.tab_widget.addTab(multi_tab, "📚 Несколько вопросов")
        
        right_layout.addWidget(self.tab_widget, stretch=1)
        
        # Предпросмотр
        preview_label = QLabel("Предпросмотр:")
        preview_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: bold;
            color: #1e3a5f;
            margin-top: 5px;
        """)
        right_layout.addWidget(preview_label)
        
        self.preview_area = QScrollArea()
        self.preview_area.setWidgetResizable(True)
        self.preview_area.setMaximumHeight(180)
        self.preview_area.setStyleSheet(f"""
            QScrollArea {{
                border: 1px solid #e5e7ea;
                border-radius: 6px;
                background-color: #fafbfc;
            }}
        """)
        
        self.preview_widget = QLabel()
        self.preview_widget.setWordWrap(True)
        self.preview_widget.setStyleSheet(f"""
            padding: 10px;
            font-size: 11px;
            font-family: {FONT_FAMILY};
        """)
        self.preview_area.setWidget(self.preview_widget)
        right_layout.addWidget(self.preview_area)
        
        # Кнопка старта
        self.start_test_btn = QPushButton("🚀 НАЧАТЬ ТЕСТ")
        self.start_test_btn.clicked.connect(self._on_start_test)
        self.start_test_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_PRIMARY};
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 14px 30px;
                border-radius: 8px;
            }}
            QPushButton:hover {{ background-color: {BUTTON_PRIMARY_HOVER}; }}
            QPushButton:disabled {{
                background-color: #b0b8c1;
                color: #e5e7ea;
            }}
        """)
        right_layout.addWidget(self.start_test_btn)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([320, 700])
        
        main_layout.addWidget(splitter)

    def _import_from_html(self):
        """Импорт вопросов из HTML-файла, сохранённого Word"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите HTML-файл теста", "",
            "HTML файлы (*.htm *.html);;Все файлы (*.*)"
        )
        
        if not file_path:
            return
        
        # Читаем файл
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
        except:
            try:
                with open(file_path, 'r', encoding='windows-1251') as f:
                    html_content = f.read()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось прочитать:\n{e}")
                return
        
        # Папка с файлом
        base_dir = os.path.dirname(os.path.abspath(file_path))
        file_name_no_ext = os.path.splitext(os.path.basename(file_path))[0]
        
        # Возможные имена папки с картинками
        possible_folders = [
            os.path.join(base_dir, file_name_no_ext + "_files"),
            os.path.join(base_dir, file_name_no_ext + ".files"),
            os.path.join(base_dir, "images"),
        ]
        
        images_folder = None
        for folder in possible_folders:
            if os.path.exists(folder) and os.path.isdir(folder):
                images_folder = folder
                break
        
        debug_info = f"Базовая папка: {base_dir}\n"
        debug_info += f"Имя файла: {os.path.basename(file_path)}\n"
        debug_info += f"Папка с картинками: {images_folder}\n"
        
        if images_folder:
            files_in_folder = os.listdir(images_folder)[:10]
            debug_info += f"Файлы в папке (первые 10): {files_in_folder}\n"
        
        # Находим все src в HTML
        all_srcs = re.findall(r'src="([^"]+)"', html_content)
        debug_info += f"\nНайдено src в HTML: {len(all_srcs)}\n"
        for s in all_srcs[:10]:
            debug_info += f"  - {s[:100]}\n"
        
        # Заменяем src на base64
        replaced_count = 0
        
        def replace_src(match):
            nonlocal replaced_count
            src = match.group(1)
            
            if src.startswith('data:image'):
                return match.group(0)
            
            # Ищем файл
            found_path = None
            
            # 1. В папке с картинками
            if images_folder:
                candidate = os.path.join(images_folder, os.path.basename(src))
                if os.path.exists(candidate):
                    found_path = candidate
            
            # 2. Рядом с HTML
            if not found_path:
                candidate = os.path.join(base_dir, os.path.basename(src))
                if os.path.exists(candidate):
                    found_path = candidate
            
            # 3. URL-decode имя файла
            if not found_path:
                from urllib.parse import unquote
                decoded_name = unquote(os.path.basename(src))
                if images_folder:
                    candidate = os.path.join(images_folder, decoded_name)
                    if os.path.exists(candidate):
                        found_path = candidate
            
            if found_path:
                b64 = image_to_base64(found_path)
                if b64:
                    replaced_count += 1
                    return f'src="{b64}"'
            
            return match.group(0)
        
        html_content = re.sub(r'src="([^"]+)"', replace_src, html_content)
        debug_info += f"\nЗаменено картинок: {replaced_count}"
        
        # Извлекаем картинки и заменяем их на плейсхолдеры в HTML
        all_images = []
        def extract_and_replace_img(match):
            tag_text = match.group(0)
            src_match = re.search(r'src="([^"]+)"', tag_text, re.IGNORECASE)
            if src_match:
                src = src_match.group(1)
                # Берем только те, что удалось сконвертировать в base64 (или они уже были)
                if src.startswith('data:image'):
                    idx = len(all_images)
                    all_images.append(src)
                    return f" ___IMG_{idx}___ "
            return " "
            
        html_for_text = re.sub(r'<img[^>]*>', extract_and_replace_img, html_content, flags=re.IGNORECASE)
        html_for_text = re.sub(r'<v:imagedata[^>]*>', extract_and_replace_img, html_for_text, flags=re.IGNORECASE)
        
        # Извлекаем plain_text, сохраняя плейсхолдеры и разрывы строк
        # Преобразуем списки в ответы с маркерами (a), b), c)...)
        li_counter = 0
        def replace_li(match):
            nonlocal li_counter
            marker = chr(97 + (li_counter % 26)) + ")"
            li_counter += 1
            return f"\n{marker} "
            
        def reset_ol(match):
            nonlocal li_counter
            li_counter = 0
            return "\n"
            
        html_for_text = re.sub(r'<ol[^>]*>', reset_ol, html_for_text, flags=re.IGNORECASE)
        html_for_text = re.sub(r'<ul[^>]*>', reset_ol, html_for_text, flags=re.IGNORECASE)
        html_for_text = re.sub(r'<li[^>]*>', replace_li, html_for_text, flags=re.IGNORECASE)
        
        # Преобразуем остальные блочные теги в переносы строк, чтобы слова не слипались в одну строку
        html_for_text = re.sub(r'<(?:p|div|br|tr|h[1-6])[^>]*>', '\n', html_for_text, flags=re.IGNORECASE)
        html_for_text = re.sub(r'</(?:p|div|tr|li|h[1-6]|ol|ul)>', '\n', html_for_text, flags=re.IGNORECASE)
        
        plain_text = re.sub(r'<[^>]+>', '', html_for_text)
        plain_text = re.sub(r'&nbsp;', ' ', plain_text)
        plain_text = re.sub(r'&lt;', '<', plain_text)
        plain_text = re.sub(r'&gt;', '>', plain_text)
        plain_text = re.sub(r'&amp;', '&', plain_text)
        # Убираем множественные пустые строки
        plain_text = re.sub(r'\n{3,}', '\n\n', plain_text)
        plain_text = plain_text.strip()
        
        debug_info += f"\nДлина plain_text: {len(plain_text)} символов"
        debug_info += f"\nПервые 200 символов:\n{plain_text[:200]}"
        debug_info += f"\nИзвлечено картинок (по плейсхолдерам): {len(all_images)}"
        
        # Вставляем оригинальный HTML в поле
        self.multi_text_input.setHtml(html_content)
        
        # Парсим вопросы
        question_texts = self._split_multi_questions(plain_text)
        debug_info += f"\nНайдено вопросов: {len(question_texts)}"
        
        if not question_texts:
            QMessageBox.warning(self, "Диагностика", debug_info)
            return
        
        # Добавляем вопросы
        added_count = 0
        failed_count = 0
        
        parser = QuestionParser(
            custom_markers=self.markers,
            strict_mode=self.strict_mode
        )
        
        for q_text in question_texts:
            try:
                # Парсим текст ВМЕСТЕ с плейсхолдерами (___IMG_x___)
                question = parser.parse(q_text)
                if not question.answers:
                    failed_count += 1
                    continue
                
                # Ищем плейсхолдеры внутри текста ВОПРОСА
                q_images = []
                for match in re.finditer(r'___IMG_(\d+)___', question.question_text):
                    img_idx = int(match.group(1))
                    if img_idx < len(all_images):
                        q_images.append(all_images[img_idx])
                question.question_images = q_images
                # Удаляем метки из текста вопроса
                question.question_text = re.sub(r'\s*___IMG_\d+___\s*', ' ', question.question_text).strip()
                
                # Ищем плейсхолдеры внутри каждого ОТВЕТА (картинка после вопроса)
                for ans in question.answers:
                    a_images = []
                    for match in re.finditer(r'___IMG_(\d+)___', ans.text):
                        img_idx = int(match.group(1))
                        if img_idx < len(all_images):
                            a_images.append(all_images[img_idx])
                    ans.images = a_images
                    # Удаляем метки из текста ответа
                    ans.text = re.sub(r'\s*___IMG_\d+___\s*', ' ', ans.text).strip()
                
                self.test_manager.add_question(question)
                added_count += 1
            except Exception as e:
                failed_count += 1
        
        self._refresh_question_list()
        
        if added_count > 0 and self.test_manager.test and self.test_manager.test.questions:
            self._show_preview(self.test_manager.test.questions[-1])
        
        count = self.test_manager.get_question_count()
        self.question_added.emit(count)
        
        # Показываем диагностику + результат
        debug_info += f"\n\n{'='*30}"
        debug_info += f"\n✅ Добавлено: {added_count}"
        debug_info += f"\n❌ Пропущено: {failed_count}"
        
        QMessageBox.information(self, "Результат импорта", debug_info)
                    
    # ======================== РЕЖИМЫ ========================
    
    def _reset_to_new_mode(self):
        """Сбрасывает в режим добавления нового вопроса"""
        self.editing_index = -1
        self.right_title.setText("✏️ Добавление вопроса")
        self.single_instruction.setText(
            "Вставьте ОДИН вопрос с ответами (Ctrl+V).\n"
            "Нажмите Ctrl+Enter или кнопку ниже."
        )
        self.single_text_input.clear()
        self.single_text_input.setHtml("")  # очищаем HTML тоже
        self.add_single_btn.setText("➕ ДОБАВИТЬ ВОПРОС (Ctrl+Enter)")
        self.question_list.clearSelection()

    def _load_question_for_edit(self, index: int):
        """Загружает вопрос в поле для редактирования (с картинками)"""
        if not self.test_manager.test or index >= len(self.test_manager.test.questions):
            return
        
        question = self.test_manager.test.questions[index]
        self.editing_index = index
        
        self.right_title.setText(f"✏️ Редактирование вопроса #{index + 1}")
        self.single_instruction.setText(
            f"Редактирование вопроса #{index + 1}. Внесите изменения и нажмите Обновить."
        )
        
        # Собираем HTML с текстом и картинками
        html_parts = []
        
        # Картинки вопроса
        for img_b64 in question.question_images:
            html_parts.append(f'<img src="{img_b64}"><br>')
        
        # Текст вопроса
        html_parts.append(f"<p>{question.question_text}</p>")
        
        # Ответы
        for i, answer in enumerate(question.answers):
            marker = self.markers[i] if (self.markers and i < len(self.markers)) else f"{chr(97 + i)})"
            
            # Картинки ответа
            for img_b64 in answer.images:
                html_parts.append(f'<img src="{img_b64}">')
            
            html_parts.append(f"<p>{marker} {answer.text}</p>")
        
        full_html = "".join(html_parts)
        self.single_text_input.setHtml(full_html)
        
        self.add_single_btn.setText("🔄 ОБНОВИТЬ ВОПРОС (Ctrl+Enter)")
        
        # Переключаемся на вкладку "Один вопрос"
        self.tab_widget.setCurrentIndex(0)

    # ======================== ОБРАБОТЧИКИ ========================
    
    def eventFilter(self, obj, event):
        """Ctrl+Enter в поле ввода"""
        if obj == self.single_text_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                self._handle_single_action()
                return True
        return super().eventFilter(obj, event)
    
    def _on_question_clicked(self, item):
        index = item.data(Qt.UserRole)
        if self.test_manager.test and 0 <= index < len(self.test_manager.test.questions):
            self._load_question_for_edit(index)
    
    def _handle_single_action(self):
        """Добавляет или обновляет вопрос в зависимости от режима"""
        if self.editing_index >= 0:
            self._update_question()
        else:
            self._add_single_question()
    
    # ======================== КАРТИНКИ ========================
    
    def _extract_images_from_html(self, html: str) -> list:
        """
        Извлекает ВСЕ картинки и формулы из HTML буфера Word.
        Поддерживает все известные форматы.
        """
        images = []
        seen = set()  # чтобы не было дубликатов
        
        # Способ 1: обычные <img src="...">
        img_pattern = re.compile(r'<img[^>]+src="([^"]+)"[^>]*>', re.IGNORECASE)
        for src in img_pattern.findall(html):
            if src in seen:
                continue
            
            if src.startswith('data:image'):
                images.append(src)
                seen.add(src)
            elif src.startswith('file:///'):
                filepath = src.replace('file:///', '')
                # Пробуем разные варианты пути
                for path in [filepath, '/' + filepath, filepath.replace('/', '\\')]:
                    b64 = image_to_base64(path)
                    if b64:
                        images.append(b64)
                        seen.add(src)
                        break
        
        # Способ 2: VML <v:imagedata src="..."> (старые версии Word)
        vml_pattern = re.compile(r'<v:imagedata[^>]+src="([^"]+)"[^>]*>', re.IGNORECASE)
        for src in vml_pattern.findall(html):
            if src in seen:
                continue
            
            if src.startswith('file:///'):
                filepath = src.replace('file:///', '')
                b64 = image_to_base64(filepath)
                if b64:
                    images.append(b64)
                    seen.add(src)
        
        # Способ 3: OLE объекты <o:OLEObject ...> с img в атрибутах
        ole_pattern = re.compile(r'<o:OLEObject[^>]+DrawAspect="Content"[^>]*>', re.IGNORECASE)
        for ole_match in ole_pattern.finditer(html):
            ole_tag = ole_match.group(0)
            # Ищем картинку внутри OLE объекта
            for img_match in img_pattern.finditer(ole_tag):
                src = img_match.group(1)
                if src in seen:
                    continue
                if src.startswith('data:image'):
                    images.append(src)
                    seen.add(src)
                elif src.startswith('file:///'):
                    filepath = src.replace('file:///', '')
                    b64 = image_to_base64(filepath)
                    if b64:
                        images.append(b64)
                        seen.add(src)
        
        # Способ 4: Ищем base64 в любых атрибутах src (на всякий случай)
        b64_pattern = re.compile(r'src="data:image/[^"]+;base64,([a-zA-Z0-9+/=]+)"', re.IGNORECASE)
        for b64_data in b64_pattern.findall(html):
            full_b64 = f"data:image/png;base64,{b64_data}"
            if full_b64 not in seen:
                images.append(full_b64)
                seen.add(full_b64)
        
        # Способ 5: Ищем временные файлы картинок Word
        # Word часто сохраняет формулы как PNG во временную папку
        tmp_pattern = re.compile(r'src="(file:///[^"]+\.(?:png|jpg|jpeg|gif|wmf|emf))"', re.IGNORECASE)
        for src in tmp_pattern.findall(html):
            if src in seen:
                continue
            filepath = src.replace('file:///', '')
            b64 = image_to_base64(filepath)
            if b64:
                images.append(b64)
                seen.add(src)
        
        return images

    def _distribute_images(self, question: Question, html: str, all_images: list, plain_text: str):
        """Распределяет картинки между вопросом и ответами"""
        answer_starts = []
        for ans_idx, answer in enumerate(question.answers):
            ans_text = answer.text[:30].strip()
            pos = plain_text.find(ans_text)
            if pos >= 0:
                answer_starts.append((pos, ans_idx))
        
        answer_starts.sort(key=lambda x: x[0])
        
        question_images = []
        answer_images = {i: [] for i in range(len(question.answers))}
        
        if answer_starts and all_images:
            img_positions = []
            for match in re.finditer(r'<img[^>]*>', html):
                img_positions.append(match.start())
            
            for img_idx, img_pos in enumerate(img_positions):
                if img_idx >= len(all_images):
                    break
                
                img_b64 = all_images[img_idx]
                html_before_img = html[:img_pos]
                
                last_marker_pos = -1
                last_marker_answer_idx = -1
                
                for ans_pos, ans_idx in answer_starts:
                    ans_text = question.answers[ans_idx].text[:30].strip()
                    if ans_text in html_before_img:
                        text_pos = html_before_img.rfind(ans_text)
                        if text_pos > last_marker_pos:
                            last_marker_pos = text_pos
                            last_marker_answer_idx = ans_idx
                
                if last_marker_answer_idx >= 0:
                    answer_images[last_marker_answer_idx].append(img_b64)
                else:
                    question_images.append(img_b64)
        elif all_images:
            question_images = all_images
        
        question.question_images = question_images
        for ans_idx, images_list in answer_images.items():
            if ans_idx < len(question.answers):
                question.answers[ans_idx].images = images_list
    
    # ======================== ДОБАВЛЕНИЕ ========================
    
    def _add_single_question(self):
        """Добавляет новый вопрос"""
        html = self.single_text_input.toHtml()
        plain_text = self.single_text_input.toPlainText().strip()
        
        if not plain_text:
            QMessageBox.warning(self, "Пустой ввод", "Вставьте текст вопроса с ответами.")
            return
        
        all_images = self._extract_images_from_html(html)
        
        parser = QuestionParser(
            custom_markers=self.markers,
            strict_mode=self.strict_mode
        )
        
        try:
            question = parser.parse(plain_text)
            
            if not question.answers:
                QMessageBox.warning(
                    self, "Не найдены ответы",
                    f"Программа не смогла найти варианты ответов.\n"
                    f"Проверьте, что ответы начинаются с маркеров: {', '.join(self.markers) if self.markers else 'a), b) или 1), 2)'}"
                )
                return
            
            self._distribute_images(question, html, all_images, plain_text)
            
            self.test_manager.add_question(question)
            self.single_text_input.clear()
            self._refresh_question_list()
            self._show_preview(question)
            
            count = self.test_manager.get_question_count()
            self.question_added.emit(count)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка парсинга", f"Не удалось разобрать текст:\n{str(e)}")
    
    def _update_question(self):
        """Обновляет существующий вопрос"""
        html = self.single_text_input.toHtml()
        plain_text = self.single_text_input.toPlainText().strip()
        
        if not plain_text:
            QMessageBox.warning(self, "Пустой ввод", "Введите текст вопроса с ответами.")
            return
        
        all_images = self._extract_images_from_html(html)
        
        parser = QuestionParser(
            custom_markers=self.markers,
            strict_mode=self.strict_mode
        )
        
        try:
            question = parser.parse(plain_text)
            
            if not question.answers:
                QMessageBox.warning(self, "Не найдены ответы", "Проверьте маркеры ответов.")
                return
            
            self._distribute_images(question, html, all_images, plain_text)
            
            # Обновляем вопрос
            self.test_manager.test.questions[self.editing_index] = question
            
            # Сбрасываем режим
            self._reset_to_new_mode()
            self._refresh_question_list()
            self._show_preview(question)
            
            count = self.test_manager.get_question_count()
            self.question_added.emit(count)
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось обновить вопрос:\n{str(e)}")
    
    def _add_multi_questions(self):
        """Добавляет несколько вопросов — ТОЛЬКО ТЕКСТ"""
        plain_text = self.multi_text_input.toPlainText().strip()
        
        if not plain_text:
            QMessageBox.warning(self, "Пустой ввод", "Вставьте текст с вопросами.")
            return
        
        question_texts = self._split_multi_questions(plain_text)
        
        if not question_texts:
            QMessageBox.warning(self, "Не найдены вопросы", "Не удалось разделить текст на вопросы.")
            return
        
        added_count = 0
        failed_count = 0
        
        parser = QuestionParser(
            custom_markers=self.markers,
            strict_mode=self.strict_mode
        )
        
        for q_text in question_texts:
            try:
                question = parser.parse(q_text)
                if not question.answers:
                    failed_count += 1
                    continue
                
                self.test_manager.add_question(question)
                added_count += 1
            except:
                failed_count += 1
        
        self.multi_text_input.clear()
        self._refresh_question_list()
        
        if added_count > 0 and self.test_manager.test and self.test_manager.test.questions:
            self._show_preview(self.test_manager.test.questions[-1])
        
        count = self.test_manager.get_question_count()
        self.question_added.emit(count)
        
        if failed_count == 0:
            QMessageBox.information(self, "Готово", f"✅ Успешно добавлено вопросов: {added_count}")
        else:
            QMessageBox.warning(self, "Готово", f"✅ Добавлено: {added_count}\n❌ Пропущено: {failed_count}")
    
    # ======================== ВСПОМОГАТЕЛЬНЫЕ ========================
    
    def _split_multi_questions(self, plain_text: str) -> list:
        question_pattern = re.compile(r'^\s*(\d+)[.)](?!\d)\s*', re.MULTILINE)
        matches = list(question_pattern.finditer(plain_text))
        
        if not matches:
            return [plain_text]
        
        questions = []
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(plain_text)
            question_text = plain_text[start:end].strip()
            if question_text:
                questions.append(question_text)
        
        return questions if questions else [plain_text]

    def _dump_html(self):
        """Сохраняет HTML из поля ввода в файл для отладки"""
        html = self.single_text_input.toHtml()
        plain = self.single_text_input.toPlainText()
        
        # Сохраняем в папку проекта
        save_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html_path = os.path.join(save_dir, "debug_clipboard.html")
        txt_path = os.path.join(save_dir, "debug_clipboard.txt")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(plain)
        
        images = self._extract_images_from_html(html)
        
        QMessageBox.information(
            self, "Диагностика",
            f"✅ Сохранено:\n{html_path}\n{txt_path}\n\n"
            f"📸 Найдено картинок: {len(images)}\n"
            f"📏 Размер HTML: {len(html)} символов\n"
            f"📝 Размер текста: {len(plain)} символов"
        )

    def _show_preview(self, question: Question):
        preview_text = f"<b>Вопрос:</b><br>{question.question_text}"
        
        if question.question_images:
            preview_text += f"<br><i>🖼️ Картинок: {len(question.question_images)}</i>"
        
        preview_text += "<br><br><b>Ответы:</b><br>"
        
        for i, answer in enumerate(question.answers):
            icon = "⭐" if answer.is_correct else "○"
            preview_text += f"{icon} {answer.text[:100]}"
            if answer.images:
                preview_text += f" <i>({len(answer.images)} карт.)</i>"
            preview_text += "<br>"
        
        self.preview_widget.setText(preview_text)
    
    def _refresh_question_list(self):
        self.question_list.clear()
        
        if not self.test_manager.test:
            self.question_count_label.setText("Вопросов: 0")
            return
        
        for i, question in enumerate(self.test_manager.test.questions):
            text = question.question_text[:60]
            if len(question.question_text) > 60:
                text += "..."
            
            if question.question_images:
                text = "🖼️ " + text
            
            item = QListWidgetItem(f"{i+1}. {text}")
            item.setData(Qt.UserRole, i)
            self.question_list.addItem(item)
        
        count = self.test_manager.get_question_count()
        self.question_count_label.setText(f"Вопросов: {count}")
        self.start_test_btn.setEnabled(count > 0)
        if count > 0:
            self.start_test_btn.setText(f"🚀 НАЧАТЬ ТЕСТ ({count} вопр.)")
        else:
            self.start_test_btn.setText("🚀 НАЧАТЬ ТЕСТ")
    
    def _delete_question(self):
        current_item = self.question_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Не выбрано", "Выберите вопрос для удаления.")
            return
        
        index = current_item.data(Qt.UserRole)
        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить выбранный вопрос?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.test_manager.remove_question(index)
            if self.editing_index == index:
                self._reset_to_new_mode()
            elif self.editing_index > index:
                self.editing_index -= 1
            self._refresh_question_list()
            self.preview_widget.clear()
    
    def _clear_all_questions(self):
        if self.test_manager.get_question_count() == 0:
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение", "Удалить ВСЕ вопросы?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.test_manager.create_new_test()
            self._reset_to_new_mode()
            self._refresh_question_list()
            self.preview_widget.clear()
            self.multi_text_input.clear()
    
    def _on_start_test(self):
        if self.test_manager.get_question_count() == 0:
            QMessageBox.warning(self, "Нет вопросов", "Добавьте хотя бы один вопрос.")
            return
        
        self.start_test.emit()