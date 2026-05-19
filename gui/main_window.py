import os
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QStackedWidget, QMenuBar, QMenu, QAction,
    QFileDialog, QMessageBox, QToolBar, QStatusBar,
    QLabel
)
from PyQt5.QtCore import Qt

from core.test_manager import TestManager
from .editor_widget import EditorWidget
from .test_widget import TestWidget
from .result_widget import ResultWidget
from .config_dialog import ConfigDialog
from .styles import MAIN_STYLE, MAIN_BG, SIDEBAR_BG, FONT_FAMILY


class MainWindow(QMainWindow):
    """Главное окно приложения TestMaster3000"""
    
    def __init__(self):
        super().__init__()
        
        self.test_manager = TestManager()
        self.test_manager.create_new_test()
        
        self.setWindowTitle("TestMaster3000 — Конструктор тестов")
        self.setMinimumSize(950, 650)
        self.resize(1150, 750)
        self.setStyleSheet(MAIN_STYLE)
        
        # Центральный стек
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)
        
        # Виджеты
        self.editor_widget = EditorWidget(self.test_manager)
        self.test_widget = TestWidget(self.test_manager)
        self.result_widget = ResultWidget()
        
        self.stacked_widget.addWidget(self.editor_widget)   # 0
        self.stacked_widget.addWidget(self.test_widget)     # 1
        self.stacked_widget.addWidget(self.result_widget)   # 2
        
        self.stacked_widget.setCurrentIndex(0)
        
        # Сигналы
        self.editor_widget.start_test.connect(self._start_test)
        self.test_widget.test_finished.connect(self._show_results)
        self.test_widget.back_to_editor.connect(self._back_to_editor)
        self.result_widget.retry_wrong.connect(self._retry_wrong)
        self.result_widget.retry_all.connect(self._retry_all)
        self.result_widget.back_to_editor.connect(self._back_to_editor)
        
        self._create_menu()
        self._create_toolbar()
        self._create_statusbar()
    
    def _create_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet(f"""
            QMenuBar {{
                background-color: white;
                border-bottom: 1px solid #d5d8dc;
                font-family: {FONT_FAMILY};
                font-size: 13px;
            }}
            QMenuBar::item {{
                padding: 6px 12px;
            }}
            QMenuBar::item:selected {{
                background-color: #e5e7ea;
                border-radius: 4px;
            }}
            QMenu {{
                background-color: white;
                border: 1px solid #d5d8dc;
                border-radius: 6px;
                padding: 5px;
                font-family: {FONT_FAMILY};
            }}
            QMenu::item {{
                padding: 8px 25px;
                border-radius: 4px;
            }}
            QMenu::item:selected {{
                background-color: #e5e7ea;
            }}
        """)
        
        # Файл
        file_menu = menubar.addMenu("📁 Файл")
        
        new_action = QAction("🆕 Новый тест", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_test)
        file_menu.addAction(new_action)
        
        open_action = QAction("📂 Открыть тест...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_test)
        file_menu.addAction(open_action)
        
        save_action = QAction("💾 Сохранить тест", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_test)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("💾 Сохранить как...", self)
        save_as_action.setShortcut("Ctrl+Shift+S")
        save_as_action.triggered.connect(self._save_test_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("🚪 Выход", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Настройки
        settings_menu = menubar.addMenu("⚙️ Настройки")
        
        config_action = QAction("🔧 Настройки парсера...", self)
        config_action.triggered.connect(self._open_config)
        settings_menu.addAction(config_action)
        
        # Помощь
        help_menu = menubar.addMenu("❓ Помощь")
        
        about_action = QAction("ℹ️ О программе", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_toolbar(self):
        toolbar = QToolBar("Основная")
        toolbar.setMovable(False)
        toolbar.setStyleSheet(f"""
            QToolBar {{
                background-color: {SIDEBAR_BG};
                border: none;
                padding: 6px;
                spacing: 12px;
            }}
            QToolButton {{
                color: white;
                font-size: 12px;
                font-family: {FONT_FAMILY};
                padding: 6px 14px;
                border-radius: 4px;
            }}
            QToolButton:hover {{
                background-color: #2c4a6e;
            }}
        """)
        
        self.addToolBar(toolbar)
        
        new_btn = toolbar.addAction("🆕 Новый")
        new_btn.triggered.connect(self._new_test)
        
        open_btn = toolbar.addAction("📂 Открыть")
        open_btn.triggered.connect(self._open_test)
        
        save_btn = toolbar.addAction("💾 Сохранить")
        save_btn.triggered.connect(self._save_test)
        
        toolbar.addSeparator()
        
        self.toolbar_count_label = QLabel("Вопросов: 0")
        self.toolbar_count_label.setStyleSheet("color: white; font-size: 12px; font-weight: bold;")
        toolbar.addWidget(self.toolbar_count_label)
        
        self.editor_widget.question_added.connect(self._update_toolbar_count)
    
    def _create_statusbar(self):
        self.statusbar = QStatusBar()
        self.statusbar.setStyleSheet(f"""
            QStatusBar {{
                background-color: white;
                border-top: 1px solid #d5d8dc;
                font-family: {FONT_FAMILY};
                font-size: 11px;
                color: #7f8c8d;
            }}
        """)
        self.statusbar.showMessage("Готов к работе. Ctrl+V чтобы вставить вопрос, Ctrl+Enter чтобы добавить.")
        self.setStatusBar(self.statusbar)
    
    def _update_toolbar_count(self, count: int):
        self.toolbar_count_label.setText(f"Вопросов: {count}")
    
    def _start_test(self):
        if self.test_manager.current_path:
            self.test_manager.save_test()
        
        self.test_widget.start_test()
        self.stacked_widget.setCurrentWidget(self.test_widget)
        self.statusbar.showMessage("Тест запущен. Выберите ответ и нажмите ОТВЕТИТЬ.")
    
    def _show_results(self, results: dict):
        self.result_widget.show_results(results)
        self.stacked_widget.setCurrentWidget(self.result_widget)
        self.statusbar.showMessage("Тест завершён.")
    
    def _retry_wrong(self):
        self.test_manager.retry_wrong_questions()
        self.test_widget.start_test()
        self.stacked_widget.setCurrentWidget(self.test_widget)
        self.statusbar.showMessage("Повторное прохождение неправильных вопросов.")
    
    def _retry_all(self):
        self.test_widget.start_test()
        self.stacked_widget.setCurrentWidget(self.test_widget)
        self.statusbar.showMessage("Тест перезапущен.")
    
    def _back_to_editor(self):
        self.stacked_widget.setCurrentWidget(self.editor_widget)
        self._update_toolbar_count(self.test_manager.get_question_count())
        self.statusbar.showMessage("Готов к работе. Ctrl+V чтобы вставить вопрос, Ctrl+Enter чтобы добавить.")
    
    def _new_test(self):
        reply = QMessageBox.question(
            self, "Новый тест",
            "Создать новый тест? Несохранённые изменения будут потеряны.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.test_manager.create_new_test()
            self.editor_widget._refresh_question_list()
            self._update_toolbar_count(0)
            self.statusbar.showMessage("Создан новый тест.")
    
    def _open_test(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Открыть тест", "",
            "JSON файлы (*.json);;Все файлы (*.*)"
        )
        
        if file_path:
            if self.test_manager.load_test(file_path):
                self.editor_widget._refresh_question_list()
                count = self.test_manager.get_question_count()
                self._update_toolbar_count(count)
                self.statusbar.showMessage(f"Загружен тест: {file_path} ({count} вопросов)")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось загрузить тест.")
    
    def _save_test(self):
        if self.test_manager.current_path:
            if self.test_manager.save_test():
                self.statusbar.showMessage(f"Сохранено: {self.test_manager.current_path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить тест.")
        else:
            self._save_test_as()
    
    def _save_test_as(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить тест как", "test.json",
            "JSON файлы (*.json);;Все файлы (*.*)"
        )
        
        if file_path:
            if self.test_manager.save_test(file_path):
                self.statusbar.showMessage(f"Сохранено: {file_path}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить тест.")
    
    def _open_config(self):
        dialog = ConfigDialog(self)
        if dialog.exec_():
            self.editor_widget.refresh_settings()
            self.statusbar.showMessage("Настройки сохранены.")
    
    def _show_about(self):
        QMessageBox.about(
            self, "О программе",
            "TestMaster3000\n\n"
            "Лёгкий конструктор тестов для подготовки к сессии.\n\n"
            "Версия: 1.0\n"
            "Python + PyQt5\n\n"
            "Возможности:\n"
            "• Вставка вопросов из Word (Ctrl+V)\n"
            "• Автоматический парсинг ответов\n"
            "• Поддержка картинок в вопросах и ответах\n"
            "• Перемешивание вопросов и ответов\n"
            "• Результаты и работа над ошибками\n"
            "• Сохранение/загрузка тестов"
        )