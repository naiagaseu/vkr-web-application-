from ..extensions import db
from sqlalchemy import UniqueConstraint

# Модели, описывающие структуру скоринга теста (навыки, роли, связи между ними для оценки и весов).

class Skill(db.Model):
    """
    Модель SQLAlchemy для сущности 'Skill' (навык/компетенция).
    Содержит перечень оцениваемых в тесте компетенций.
    Является ключевым справочником компетенций, используемых в методике.
    Тип навыка важен для применения разных алгоритмов расчета и интерпретации.
    """
    __tablename__ = 'skills'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True) # Название навыка/компетенции
    type = db.Column(db.String(50), nullable=False) # Тип навыка: 'Hard' или 'Soft'

    # Связи с другими моделями через relationship:
    # Один навык оценивается множеством записей Option_skill_score (т.е. может быть связан с оценками вариантов ответов разных вопросов).
    option_skill_scores = db.relationship('Option_skill_score', backref='skill', lazy='select', cascade="all, delete-orphan")
    # Один навык может иметь разные весовые коэффициенты в зависимости от роли (связь через Role_skill_weight).
    role_skill_weights = db.relationship('Role_skill_weight', backref='skill', lazy='select', cascade="all, delete-orphan")
    # Один навык имеет результаты во множестве записей Test_session_skill_result (т.е. результаты по этому навыку для разных сессий).
    test_session_skill_results = db.relationship('Test_session_skill_result', backref='skill', lazy='select', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Skill {self.name} ({self.type})>"


class Role(db.Model):
    """
    Модель SQLAlchemy для сущности 'Role' (роль).
    Хранит сведения о профессиональных ролях ИБ, для которых определяется
    готовность кандидата по результатам теста.
    Является ключевым справочником целевых профессиональных ролей,
    используемых в методике для расчета интегральной оценки.
    """
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True) # Название роли
    description = db.Column(db.Text) # Описание роли (опционально, полезно для фронтенда)

    # Связи с другими моделями:
    # Каждая роль может быть связана со множеством записей Role_skill_weight (веса навыков для этой роли).
    role_skill_weights = db.relationship('Role_skill_weight', backref='role', lazy='select', cascade="all, delete-orphan")
    # Одна роль имеет результаты во множестве записей Test_session_role_result (результаты по этой роли для разных сессий).
    test_session_role_results = db.relationship('Test_session_role_result', backref='role', lazy='select', cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Role {self.name}>"


class Option_skill_score(db.Model):
    """
    Модель SQLAlchemy для сущности 'Option_skill_score'
    (Оценка навыка по варианту ответа).
    Связующая таблица между Option и Skill для хранения информации о баллах (0, 0.5, 1),
    которые начисляются по каждому навыку при выборе конкретного варианта ответа на вопрос.
    Критически важна для реализации этапа определения первичных баллов по компетенциям.
    Напрямую отражает связь между выбором ответа кандидатом и получаемыми баллами
    по каждому оцениваемому этим ответом навыку согласно трехступенчатой шкале.
    """
    __tablename__ = 'option_skill_score'
    id = db.Column(db.Integer, primary_key=True)
    option_id = db.Column(db.Integer, db.ForeignKey('options.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на Option
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на Skill

    score = db.Column(db.Float, nullable=False) # Начисленный балл (0.0, 0.5, 1.0)

    # Гарантируем уникальность пары option_id + skill_id
    __table_args__ = (UniqueConstraint('option_id', 'skill_id', name='_option_skill_score_uc'),) # Имя ограничения оставлено как есть

    def __repr__(self):
        return f"<OptionSkillScore option={self.option_id} skill={self.skill_id} score={self.score}>"


class Role_skill_weight(db.Model):
    """
    Модель SQLAlchemy для сущности 'Role_skill_weight'
    (Вес навыка для роли).
    Связующая таблица между Role и Skill для хранения весовых коэффициентов (w_j).
    Критически важна для реализации этапа расчета интегральной оценки готовности по ролям.
    Хранит коэффициенты, необходимые для применения формулы (13) для Hard Skills.
    """
    __tablename__ = 'role_skill_weight'
    id = db.Column(db.Integer, primary_key=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на Role
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False) # Внешний ключ на Skill

    weight = db.Column(db.Float, nullable=False) # Весовой коэффициент w_j

    # Гарантируем уникальность пары role_id + skill_id
    __table_args__ = (UniqueConstraint('role_id', 'skill_id', name='_role_skill_weight_uc'),) # Имя ограничения оставлено как есть

    def __repr__(self):
        return f"<RoleSkillWeight role={self.role_id} skill={self.skill_id} weight={self.weight}>"
