import base64
import os
from typing import Optional
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QByteArray, QBuffer, QIODevice


def image_to_base64(filepath: str) -> Optional[str]:
    """
    Конвертирует файл изображения в base64 строку.
    Поддерживает PNG, JPG, GIF.
    """
    if not os.path.exists(filepath):
        return None
    
    try:
        with open(filepath, 'rb') as f:
            image_data = f.read()
        
        # Определяем формат по расширению
        ext = os.path.splitext(filepath)[1].lower()
        mime_types = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.bmp': 'image/bmp',
        }
        mime_type = mime_types.get(ext, 'image/png')
        
        b64 = base64.b64encode(image_data).decode('utf-8')
        return f"data:{mime_type};base64,{b64}"
    except Exception as e:
        print(f"Ошибка конвертации изображения: {e}")
        return None


def base64_to_pixmap(b64_string: str, max_width: int = 400, max_height: int = 300) -> Optional[QPixmap]:
    """
    Конвертирует base64 строку в QPixmap для отображения.
    Автоматически масштабирует, сохраняя пропорции.
    """
    if not b64_string:
        return None
    
    try:
        # Если это data URL, извлекаем только base64 часть
        if ',' in b64_string:
            b64_string = b64_string.split(',', 1)[1]
        
        image_data = base64.b64decode(b64_string)
        pixmap = QPixmap()
        pixmap.loadFromData(image_data)
        
        if pixmap.isNull():
            return None
        
        # Масштабируем, если нужно
        if pixmap.width() > max_width or pixmap.height() > max_height:
            pixmap = pixmap.scaled(
                max_width, max_height,
                aspectRatioMode=1,  # Qt.KeepAspectRatio
                transformMode=1     # Qt.SmoothTransformation
            )
        
        return pixmap
    except Exception as e:
        print(f"Ошибка декодирования изображения: {e}")
        return None


def pixmap_to_base64(pixmap: QPixmap, format: str = 'PNG') -> Optional[str]:
    """
    Конвертирует QPixmap в base64 строку.
    """
    if pixmap.isNull():
        return None
    
    try:
        byte_array = QByteArray()
        buffer = QBuffer(byte_array)
        buffer.open(QIODevice.WriteOnly)
        
        format_map = {
            'PNG': 'png',
            'JPEG': 'jpg',
            'JPG': 'jpg',
        }
        ext = format_map.get(format.upper(), 'png')
        
        pixmap.save(buffer, ext.upper())
        
        b64 = base64.b64encode(byte_array.data()).decode('utf-8')
        return f"data:image/{ext};base64,{b64}"
    except Exception as e:
        print(f"Ошибка конвертации pixmap: {e}")
        return None


def get_resource_path(relative_path: str) -> str:
    """
    Получает абсолютный путь к ресурсу.
    Работает как при разработке, так и в собранном .exe
    """
    import sys
    if getattr(sys, 'frozen', False):
        # Запущено из .exe
        base_path = os.path.dirname(sys.executable)
    else:
        # Запущено из исходников
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    return os.path.join(base_path, relative_path)