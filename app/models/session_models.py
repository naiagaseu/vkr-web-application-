from ..extensions import db
from datetime import datetime
from sqlalchemy import UniqueConstraint

class Test_session(db.Model):
    __tablename__ = 'test_session'
    id = db.Column(db.Integer, primary_key=True)
    # user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True) # Оставлено закомментированным, как было
    test_id = db.Column(db.Integer, db.ForeignKey('tests.id', ondelete='CASCADE'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)

    current_question_index = db.Column(db.Integer, default=0, nullable=False)

    user_answers = db.relationship('User_answer', backref='test_session', lazy=True, cascade="all, delete-orphan")
    test_session_skill_results = db.relationship('Test_session_skill_result', backref='test_session', lazy=True, cascade="all, delete-orphan")
    test_session_role_results = db.relationship('Test_session_role_result', backref='test_session', lazy=True, cascade="all, delete-orphan")
    # Relationships defined in other models point back here (test) # Оставлено закомментированным, как было


class User_answer(db.Model):
    __tablename__ = 'user_answers'
    id = db.Column(db.Integer, primary_key=True)
    test_session_id = db.Column(db.Integer, db.ForeignKey('test_session.id', ondelete='CASCADE'), nullable=False)

    question_id = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)

    chosen_option_id = db.Column(db.Integer, db.ForeignKey('options.id', ondelete='SET NULL'), nullable=True)

    text_response = db.Column(db.Text, nullable=True)

    __table_args__ = (UniqueConstraint('test_session_id', 'question_id', name='_user_answer_uc'),)


class Test_session_skill_result(db.Model):
    __tablename__ = 'test_session_skill_result'
    id = db.Column(db.Integer, primary_key=True)
    test_session_id = db.Column(db.Integer, db.ForeignKey('test_session.id', ondelete='CASCADE'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)

    obtained_primary_score = db.Column(db.Float, nullable=False)
    max_possible_primary_score = db.Column(db.Float, nullable=False)
    normalized_score = db.Column(db.Float, nullable=False)

    __table_args__ = (UniqueConstraint('test_session_id', 'skill_id', name='_test_session_skill_result_uc'),)


class Test_session_role_result(db.Model):
    __tablename__ = 'test_session_role_result'
    id = db.Column(db.Integer, primary_key=True)
    test_session_id = db.Column(db.Integer, db.ForeignKey('test_session.id', ondelete='CASCADE'), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)

    integral_score = db.Column(db.Float, nullable=False)

    __table_args__ = (UniqueConstraint('test_session_id', 'role_id', name='_test_session_role_result_uc'),)
