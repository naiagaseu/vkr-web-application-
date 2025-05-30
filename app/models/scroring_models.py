from ..extensions import db
from sqlalchemy import UniqueConstraint

class Skill(db.Model):
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    type = db.Column(db.String(50), nullable=False)

    option_skill_scores = db.relationship('Option_skill_score', backref='skill', lazy=True, cascade="all, delete-orphan")
    role_skill_weights = db.relationship('Role_skill_weight', backref='skill', lazy=True, cascade="all, delete-orphan")
    test_session_skill_results = db.relationship('Test_session_skill_result', backref='skill', lazy=True, cascade="all, delete-orphan")

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text)

    role_skill_weights = db.relationship('Role_skill_weight', backref='role', lazy=True, cascade="all, delete-orphan")
    test_session_role_results = db.relationship('Test_session_role_result', backref='role', lazy=True, cascade="all, delete-orphan")

class Option_skill_score(db.Model):
    __tablename__ = 'option_skill_score'
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('options.id', ondelete='CASCADE'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)

    score = db.Column(db.Float, nullable=False)

    __table_args__ = (UniqueConstraint('option_id', 'skill_id', name='_option_skill_score_uc'),)

class Role_skill_weight(db.Model):
    __tablename__ = 'role_skill_weight'
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)

    weight = db.Column(db.Float, nullable=False)

    __table_args__ = (UniqueConstraint('role_id', 'skill_id', name='_role_skill_weight_uc'),)
