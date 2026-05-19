import json
import random
import os
from typing import List, Optional, Tuple
from .models import Question, Answer, Test


class TestManager:
    """Управление тестом: загрузка, сохранение, рандомизация"""
    
    def __init__(self):
        self.test: Optional[Test] = None
        self.current_path: Optional[str] = None
        
        # Состояние текущего прохождения
        self._randomized_questions: List[Question] = []
        self._current_index: int = 0
        self._user_answers: dict = {}  # question_id -> answer_id
        self._wrong_questions: List[str] = []  # список id неправильных
    
    def load_test(self, path: str) -> bool:
        """Загружает тест из JSON файла"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.test = Test.from_dict(data)
            self.current_path = path
            return True
        except Exception as e:
            print(f"Ошибка загрузки теста: {e}")
            return False
    
    def save_test(self, path: str = None) -> bool:
        """Сохраняет тест в JSON файл"""
        if path:
            self.current_path = path
        
        if not self.test or not self.current_path:
            return False
        
        try:
            # Создаём папку, если её нет
            os.makedirs(os.path.dirname(self.current_path), exist_ok=True)
            
            with open(self.current_path, 'w', encoding='utf-8') as f:
                json.dump(self.test.to_dict(), f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка сохранения теста: {e}")
            return False
    
    def create_new_test(self, title: str = "Новый тест"):
        """Создаёт новый пустой тест"""
        self.test = Test(title=title)
        self.current_path = None
    
    def add_question(self, question: Question):
        """Добавляет вопрос в тест"""
        if not self.test:
            self.create_new_test()
        self.test.questions.append(question)
    
    def remove_question(self, index: int) -> bool:
        """Удаляет вопрос по индексу"""
        if self.test and 0 <= index < len(self.test.questions):
            self.test.questions.pop(index)
            return True
        return False
    
    def get_question_count(self) -> int:
        """Возвращает количество вопросов"""
        if self.test:
            return len(self.test.questions)
        return 0
    
    # ========== Методы для прохождения теста ==========
    
    def start_test_session(self, shuffle_questions: bool = True):
        """
        Начинает новую сессию тестирования.
        Перемешивает вопросы и подготавливает состояние.
        """
        if not self.test or not self.test.questions:
            return
        
        self._randomized_questions = self.test.questions.copy()
        if shuffle_questions:
            random.shuffle(self._randomized_questions)
        
        self._current_index = 0
        self._user_answers = {}
        self._wrong_questions = []
    
    def get_current_question(self) -> Optional[Question]:
        """Возвращает текущий вопрос"""
        if 0 <= self._current_index < len(self._randomized_questions):
            return self._randomized_questions[self._current_index]
        return None
    
    def get_shuffled_answers(self, question: Question) -> List[Tuple[Answer, int]]:
        """
        Перемешивает ответы вопроса.
        Возвращает список кортежей: (Answer, оригинальный_индекс)
        оригинальный_индекс нужен для определения правильного ответа
        """
        answers_with_index = list(enumerate(question.answers))
        random.shuffle(answers_with_index)
        return [(answer, idx) for idx, answer in answers_with_index]
    
    def submit_answer(self, question_id: str, answer_id: str) -> bool:
        """
        Фиксирует ответ пользователя.
        Возвращает True если ответ правильный.
        """
        self._user_answers[question_id] = answer_id
        
        # Проверяем правильность
        question = self._get_question_by_id(question_id)
        if question:
            correct_answer = question.get_correct_answer()
            if correct_answer and correct_answer.id == answer_id:
                return True
            else:
                self._wrong_questions.append(question_id)
                return False
        return False
    
    def next_question(self) -> bool:
        """Переходит к следующему вопросу. Возвращает False если вопросов больше нет."""
        self._current_index += 1
        return self._current_index < len(self._randomized_questions)
    
    def get_progress(self) -> Tuple[int, int]:
        """Возвращает (текущий_номер, всего_вопросов)"""
        return (self._current_index + 1, len(self._randomized_questions))
    
    def get_results(self) -> dict:
        """Возвращает результаты теста"""
        total = len(self._randomized_questions)
        correct = total - len(self._wrong_questions)
        wrong = len(self._wrong_questions)
        
        wrong_details = []
        for q_id in self._wrong_questions:
            q = self._get_question_by_id(q_id)
            if q:
                user_answer_id = self._user_answers.get(q_id)
                user_answer = next((a for a in q.answers if a.id == user_answer_id), None)
                correct_answer = q.get_correct_answer()
                wrong_details.append({
                    "question": q,
                    "user_answer": user_answer,
                    "correct_answer": correct_answer
                })
        
        return {
            "total": total,
            "correct": correct,
            "wrong": wrong,
            "percentage": round(correct / total * 100, 1) if total > 0 else 0,
            "wrong_details": wrong_details
        }
    
    def retry_wrong_questions(self):
        """Подготавливает сессию только с неправильными вопросами"""
        wrong_qs = []
        for q_id in self._wrong_questions:
            q = self._get_question_by_id(q_id)
            if q:
                wrong_qs.append(q)
        
        self._randomized_questions = wrong_qs
        random.shuffle(self._randomized_questions)
        self._current_index = 0
        self._user_answers = {}
        self._wrong_questions = []
    
    def _get_question_by_id(self, question_id: str) -> Optional[Question]:
        """Ищет вопрос по id во всём тесте"""
        if not self.test:
            return None
        for q in self.test.questions:
            if q.id == question_id:
                return q
        return None
    
    def has_wrong_questions(self) -> bool:
        """Есть ли неправильные ответы для перепрохождения"""
        return len(self._wrong_questions) > 0