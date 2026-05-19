import re
from typing import List, Optional, Tuple
from .models import Question, Answer


class QuestionParser:
    """
    Парсер текста вопроса с ответами.
    Поддерживает автоматическое определение маркеров и ручную настройку.
    """
    
    # Стандартные маркеры ответов (в порядке ожидания)
    DEFAULT_MARKERS = [
        # Латиница
        ["a)", "b)", "c)", "d)", "e)", "f)", "g)", "h)"],
        # Кириллица
        ["а)", "б)", "в)", "г)", "д)", "е)", "ж)", "з)"],
        # Цифры
        ["1)", "2)", "3)", "4)", "5)", "6)", "7)", "8)"],
        # Латиница с точкой
        ["a.", "b.", "c.", "d.", "e.", "f.", "g.", "h."],
        # Кириллица с точкой
        ["а.", "б.", "в.", "г.", "д.", "е.", "ж.", "з."],
    ]
    
    def __init__(self, custom_markers: Optional[List[str]] = None, strict_mode: bool = False):
        """
        Args:
            custom_markers: Список маркеров, например ["a)", "b)", "c)", "d)", "e)"]
            strict_mode: Если True — искать маркеры только в начале строки
        """
        self.custom_markers = custom_markers
        self.strict_mode = strict_mode
    
    def _detect_markers(self, lines: List[str]) -> Optional[List[str]]:
        """
        Пытается автоматически определить маркеры ответов по содержимому строк.
        Смотрит на первые символы строк.
        """
        if self.custom_markers:
            return self.custom_markers
        
        # Собираем все потенциальные маркеры из строк
        candidates = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Пробуем найти маркер в начале строки (2-3 символа)
            match = re.match(r'^([a-zA-Zа-яА-ЯёЁ]\s*[.)]\s*|\d+\s*[.)](?!\d)\s*)', line)
            if match:
                marker = match.group(1).strip()
                if marker not in candidates:
                    candidates.append(marker)
        
        if not candidates:
            return None
        
        # Пытаемся найти последовательность в стандартных наборах
        candidates_sorted = sorted(candidates, key=lambda x: (len(x), x))
        
        # Проверяем каждый стандартный набор
        for marker_set in self.DEFAULT_MARKERS:
            # Смотрим, совпадают ли найденные маркеры с началом набора
            if all(c in marker_set for c in candidates_sorted):
                # Берём первые N маркеров из набора, где N = количество найденных
                result = []
                for m in marker_set:
                    if m in candidates_sorted:
                        result.append(m)
                    else:
                        break
                if len(result) == len(candidates_sorted):
                    return result
        
        # Если не нашли в стандартных — возвращаем найденные как есть
        return candidates_sorted
    
    def parse(self, raw_text: str) -> Question:
        """
        Парсит сырой текст вопроса с ответами.
        
        Пример входа:
        "1. Электропривод это
        a) электромеханическое устройство...
        b) конвертор электрической энергии..."
        
        Возвращает объект Question.
        """
        lines = raw_text.strip().split('\n')
        # Убираем пустые строки в конце и начале, но сохраняем внутри
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
            
        if not lines:
            return Question(question_text="", answers=[])
            
        # Убираем номер вопроса в начале первой строки, чтобы он не определялся как маркер ответа
        first_line_stripped = lines[0].strip()
        num_match = re.match(r'^(\d+[.)])(?!\d)\s*', first_line_stripped)
        if num_match:
            lines[0] = first_line_stripped[len(num_match.group(0)):].strip()
        
        markers = self._detect_markers(lines)
        
        if not markers:
            # Если маркеры не найдены — весь текст считаем вопросом без ответов
            return Question(
                question_text=raw_text.strip(),
                answers=[]
            )
        
        # Нормализуем маркеры (убираем лишние пробелы)
        normalized_markers = []
        for m in markers:
            # Приводим к виду "a)", "b)" — без лишних пробелов
            clean = re.sub(r'\s+', '', m)
            normalized_markers.append(clean)
        
        # Находим индексы строк, где начинаются ответы
        answer_line_indices = []
        question_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped:
                # Пустая строка
                if not answer_line_indices:
                    question_lines.append(line)
                continue
            
            # Проверяем, начинается ли строка с маркера
            is_answer_line = False
            matched_marker = None
            
            for marker in normalized_markers:
                # Экранируем скобки для regex
                escaped_marker = re.escape(marker)
                
                if self.strict_mode:
                    # Только в начале строки
                    pattern = r'^\s*' + escaped_marker + r'\s*'
                else:
                    # В любом месте строки (но предпочитаем начало)
                    pattern = r'(?:^|\s)' + escaped_marker + r'\s*'
                
                if re.match(pattern, stripped, re.IGNORECASE):
                    is_answer_line = True
                    matched_marker = marker
                    break
            
            if is_answer_line and matched_marker:
                answer_line_indices.append((i, matched_marker))
            else:
                # Если ответы ещё не начались — это часть вопроса
                if not answer_line_indices:
                    question_lines.append(line)
        
        # Текст вопроса — всё, что до первого ответа
        question_text = '\n'.join(question_lines).strip()
        
        # Собираем ответы
        answers = []
        
        for idx, (line_idx, marker) in enumerate(answer_line_indices):
            # Текст ответа: от этого маркера до следующего маркера или конца
            start_pos = lines[line_idx].find(marker) + len(marker)
            answer_text = lines[line_idx][start_pos:].strip()
            
            # Если ответ продолжается на следующих строках (до следующего маркера)
            next_line_idx = answer_line_indices[idx + 1][0] if idx + 1 < len(answer_line_indices) else len(lines)
            
            continuation_lines = []
            for j in range(line_idx + 1, next_line_idx):
                if lines[j].strip():
                    continuation_lines.append(lines[j].strip())
            
            full_answer_text = answer_text
            if continuation_lines:
                full_answer_text += ' ' + ' '.join(continuation_lines)
            
            # Первый ответ считаем правильным
            is_correct = (idx == 0)
            
            answers.append(Answer(
                text=full_answer_text.strip(),
                is_correct=is_correct
            ))
        
        # Проверка: если получился только 1 ответ, возможно парсер ошибся
        if len(answers) <= 1 and len(lines) > 2:
            # Возможно, это не тестовый вопрос, а просто текст
            pass
        
        return Question(
            question_text=question_text,
            answers=answers
        )


def parse_question_text(raw_text: str, custom_markers: Optional[List[str]] = None) -> Question:
    """
    Удобная функция для быстрого парсинга.
    """
    parser = QuestionParser(custom_markers=custom_markers)
    return parser.parse(raw_text)