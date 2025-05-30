from ..extensions import db
from sqlalchemy import UniqueConstraint

class Test(db.Model):
    __tablename__ = 'tests'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)

    questions = db.relationship('Question', backref='test', lazy=True, cascade="all, delete-orphan")
    test_sessions = db.relationship('Test_session', backref='test', lazy=True, cascade="all, delete-orphan")

class Question(db.Model):
    __tablename__ = 'questions'
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id', ondelete='CASCADE'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    question_type = db.Column(db.String(50), default='multiple_choice', nullable=False)

    order_index = db.Column(db.Integer, nullable=False)

    __table_args__ = (UniqueConstraint('test_id', 'order_index', name='_test_order_uc'),)

    options = db.relationship('Option', backref='question', lazy=True, cascade="all, delete-orphan")
    user_answers = db.relationship('User_answer', backref='question', lazy=True)

class Option(db.Model):
    __tablename__ = 'options'
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)

    text = db.Column(db.String(500), nullable=False)

    option_skill_scores = db.relationship('Option_skill_score', backref='option', lazy=True, cascade="all, delete-orphan")
    user_answers = db.relationship('User_answer', backref='chosen_option', lazy=True)
