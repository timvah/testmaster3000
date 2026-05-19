"""
TestMaster3000 — Конструктор тестов для подготовки к сессии
============================================================
Запуск: python main.py
"""

import sys
import os

# Добавляем корневую папку в путь для импортов
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

from gui.main_window import MainWindow


def main():
    """Точка входа в приложение"""
    
    # Создаём приложение
    app = QApplication(sys.argv)
    app.setApplicationName("TestMaster3000")
    app.setOrganizationName("TestMaster")
    
    # Устанавливаем шрифт по умолчанию
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Создаём и показываем главное окно
    window = MainWindow()
    window.show()
    
    # Запускаем цикл обработки событий
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()