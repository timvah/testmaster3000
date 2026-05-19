import json
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QLineEdit, QCheckBox, QPushButton, QMessageBox,
    QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt

from .styles import MAIN_STYLE


class ConfigDialog(QDialog):
    """Диалог настроек приложения"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self.setMinimumWidth(450)
        self.setStyleSheet(MAIN_STYLE)
        
        # Загружаем текущие настройки
        self.settings = self._load_settings()
        
        self._init_ui()
    
    def _load_settings(self) -> dict:
        """Загружает настройки из JSON"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "settings.json"
        )
        
        defaults = {
            "auto_detect_markers": True,
            "markers": ["a)", "b)", "c)", "d)", "e)"],
            "strict_mode": True
        }
        
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    defaults.update(data)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
        
        return defaults
    
    def _save_settings(self):
        """Сохраняет настройки в JSON"""
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "config", "settings.json"
        )
        
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить настройки:\n{e}")
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Группа настроек парсера
        parser_group = QGroupBox("Настройки парсера")
        parser_layout = QFormLayout()
        
        # Автоопределение маркеров
        self.auto_detect_check = QCheckBox("Определять маркеры автоматически")
        self.auto_detect_check.setChecked(self.settings.get("auto_detect_markers", True))
        self.auto_detect_check.setToolTip(
            "Если включено, программа попытается сама определить формат маркеров (a), 1), а. и т.д.).\n"
            "При отключении будут использоваться только маркеры, указанные ниже."
        )
        self.auto_detect_check.stateChanged.connect(self._toggle_markers_input)
        parser_layout.addRow(self.auto_detect_check)
        
        # Маркеры
        markers_label = QLabel("Свои маркеры (через запятую):")
        markers_label.setToolTip(
            "Например: a), b), c), d), e)\n"
            "Используются только если автоопределение выключено."
        )
        
        self.markers_input = QLineEdit()
        self.markers_input.setText(", ".join(self.settings.get("markers", [])))
        self.markers_input.setPlaceholderText("a), b), c), d), e)")
        self.markers_input.setEnabled(not self.auto_detect_check.isChecked())
        
        parser_layout.addRow(markers_label)
        parser_layout.addRow(self.markers_input)
        
        # Strict mode
        self.strict_mode_check = QCheckBox("Строгий режим (маркеры только в начале строки)")
        self.strict_mode_check.setChecked(self.settings.get("strict_mode", True))
        self.strict_mode_check.setToolTip(
            "Если включено — маркер должен быть в начале строки.\n"
            "Если выключено — маркер может быть в любом месте строки."
        )
        parser_layout.addRow(self.strict_mode_check)
        
        parser_group.setLayout(parser_layout)
        layout.addWidget(parser_group)
        
        # Кнопки
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Сбросить по умолчанию")
        reset_btn.clicked.connect(self._reset_defaults)
        reset_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #95a5a6;
                color: white;
            }}
            QPushButton:hover {{
                background-color: #7f8c8d;
            }}
        """)
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self._save_and_close)
        save_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {BUTTON_PRIMARY};
                color: white;
            }}
            QPushButton:hover {{
                background-color: {BUTTON_PRIMARY_HOVER};
            }}
        """)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        cancel_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #bdc3c7;
                color: #2c3e50;
            }}
            QPushButton:hover {{
                background-color: #95a5a6;
            }}
        """)
        
        buttons_layout.addWidget(reset_btn)
        buttons_layout.addStretch()
        buttons_layout.addWidget(cancel_btn)
        buttons_layout.addWidget(save_btn)
        
        layout.addLayout(buttons_layout)
    
    def _toggle_markers_input(self, state):
        self.markers_input.setEnabled(state != Qt.Checked)
        
    def _reset_defaults(self):
        """Сбрасывает настройки на значения по умолчанию"""
        self.auto_detect_check.setChecked(True)
        self.markers_input.setText("a), b), c), d), e)")
        self.strict_mode_check.setChecked(True)
    
    def _save_and_close(self):
        """Сохраняет настройки и закрывает диалог"""
        # Парсим маркеры
        markers_text = self.markers_input.text().strip()
        if markers_text:
            markers = [m.strip() for m in markers_text.split(",") if m.strip()]
        else:
            QMessageBox.warning(self, "Ошибка", "Введите хотя бы один маркер ответа.")
            return
        
        self.settings["auto_detect_markers"] = self.auto_detect_check.isChecked()
        self.settings["markers"] = markers
        self.settings["strict_mode"] = self.strict_mode_check.isChecked()
        
        self._save_settings()
        self.accept()
    
    def get_markers(self) -> list:
        """Возвращает список маркеров"""
        return self.settings.get("markers", ["a)", "b)", "c)", "d)", "e)"])
    
    def get_strict_mode(self) -> bool:
        """Возвращает режим строгой проверки"""
        return self.settings.get("strict_mode", True)


# Импорт для стилей (чтобы избежать циклического импорта)
from .styles import BUTTON_PRIMARY, BUTTON_PRIMARY_HOVER