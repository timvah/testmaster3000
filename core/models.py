from dataclasses import dataclass, field
from typing import List, Optional
import uuid


@dataclass
class Answer:
    """Модель одного варианта ответа"""
    text: str
    is_correct: bool = False
    images: List[str] = field(default_factory=list)  # список base64 строк
    
    # Уникальный id для отслеживания при перемешивании
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "text": self.text,
            "is_correct": self.is_correct,
            "images": self.images
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Answer':
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            text=data.get("text", ""),
            is_correct=data.get("is_correct", False),
            images=data.get("images", [])
        )


@dataclass
class Question:
    """Модель одного вопроса"""
    question_text: str
    answers: List[Answer] = field(default_factory=list)
    question_images: List[str] = field(default_factory=list)  # base64 строки
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question_text": self.question_text,
            "question_images": self.question_images,
            "answers": [a.to_dict() for a in self.answers]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Question':
        question = cls(
            id=data.get("id", str(uuid.uuid4())),
            question_text=data.get("question_text", ""),
            question_images=data.get("question_images", [])
        )
        question.answers = [
            Answer.from_dict(a) for a in data.get("answers", [])
        ]
        return question
    
    def get_correct_answer(self) -> Optional[Answer]:
        """Возвращает правильный ответ"""
        for answer in self.answers:
            if answer.is_correct:
                return answer
        return None


@dataclass
class Test:
    """Модель всего теста"""
    title: str = "Новый тест"
    questions: List[Question] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "questions": [q.to_dict() for q in self.questions]
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Test':
        test = cls(title=data.get("title", "Новый тест"))
        test.questions = [
            Question.from_dict(q) for q in data.get("questions", [])
        ]
        return test