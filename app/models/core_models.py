from ..extensions import db
from sqlalchemy import UniqueConstraint

# Модели, описывающие структуру теста и его компонентов (вопросы, варианты ответов).

class Test(db.Model):
    """
    Модель SQLAlchemy для сущности 'Test' (тест).
    Хранит информацию о тестах, является корневой сущностью
    для всех тестовых материалов, связанных с конкретным тестом.
    Позволяет идентифицировать тест, к которому относятся вопросы,
    сессии и результаты.
    """
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True) # Название теста
    description = db.Column(db.Text) # Описание теста
    # test_status = db.Column(db.String(50), default='Draft') # Пример опционального поля статуса

    # Связи с другими моделями через relationship:
    # Один тест может содержать множество вопросов.
    questions = db.relationship('Question', backref='test', lazy='select', cascade="all, delete-orphan")
    # Один тест может иметь множество прохождений (сессий).
    test_sessions = db.relationship('Test_session', backref='test', lazy='select', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Test {self.name}>"


class Question(db.Model):
    """
    Модель SQLAlchemy для сущности 'Question' (вопрос).
    Содержит сведения о каждом вопросе: к какому тесту привязан,
    содержание вопроса, его порядковый номер в рамках теста.
    Хранит формулировки вопросов, которые предъявляются кандидату
    в процессе тестирования.
    """
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на тест
    text = db.Column(db.Text, nullable=False) # Текст самого вопроса
    question_type = db.Column(db.String(50), default='multiple_choice', nullable=False) # Тип вопроса (multiple_choice, text_input и т.д.)

    # Поле для организации пошагового прохождения: порядковый номер вопроса внутри теста
    order_index = db.Column(db.Integer, nullable=False)

    # Гарантия уникальности комбинации test_id и order_index
    __table_args__ = (UniqueConstraint('test_id', 'order_index', name='_test_question_order_uc'),) # Переименовал ограничение для ясности

    # Связи с другими моделями:
    # Один вопрос может иметь множество вариантов ответов.
    options = db.relationship('Option', backref='question', lazy='select', cascade="all, delete-orphan")
    # Один вопрос может быть связан со множеством ответов пользователя (через таблицу User_answer).
    user_answers = db.relationship('User_answer', backref='question', lazy='select')

    def __repr__(self):
        return f"<Question {self.id} test_id={self.test_id} order={self.order_index}>"


class Option(db.Model):
    """
    Модель SQLAlchemy для сущности 'Option' (вариант ответа).
    Хранит варианты ответов для каждого вопроса.
    Представляет собой набор возможных ответов для вопросов,
    где требуется выбор. Выбор кандидатом определенного варианта
    фиксируется и далее используется для оценки.
    """
    __tablename__ = 'options'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на вопрос

    text = db.Column(db.String(500), nullable=False) # Текст варианта ответа

    # Связи с другими моделями:
    # Один вариант ответа определяет баллы для множества записей Option_skill_score.
    option_skill_scores = db.relationship('Option_skill_score', backref='option', lazy='select', cascade="all, delete-orphan")
    # Один вариант ответа может быть выбран в качестве ответа во множестве записей User_answer.
    user_answers = db.relationship('User_answer', backref='chosen_option', lazy='select') # chosen_option в User_answer связывается сюда

    def __repr__(self):
        return f"<Option {self.id} question_id={self.question_id}>"
