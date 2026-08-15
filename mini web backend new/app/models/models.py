from datetime import datetime, date

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean,
    ForeignKey, DateTime, Date, UniqueConstraint
)
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    first_name = Column(String(255))
    username = Column(String(255), nullable=True)
    is_premium = Column(Boolean, default=False)  # paid access flag
    created_at = Column(DateTime, default=datetime.utcnow)

    progress = relationship("Progress", back_populates="user")
    free_usage = relationship("DailyFreeUsage", back_populates="user")


class Subject(Base):
    """Top level: one of the 35 qonunchilik (legal) subjects."""
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    order = Column(Integer, default=0)  # controls display order

    modules = relationship("Module", back_populates="subject", order_by="Module.order")


class Module(Base):
    """A module groups ~10 moddas (articles). Label auto-extends as moddas are added."""
    __tablename__ = "modules"

    id = Column(Integer, primary_key=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    label = Column(String(50), nullable=False)  # e.g. "11-19", auto-updated elsewhere
    order = Column(Integer, default=0)

    subject = relationship("Subject", back_populates="modules")
    materials = relationship("Material", back_populates="module")
    questions = relationship("Question", back_populates="module")


class Material(Base):
    """A PDF study document attached to a module."""
    __tablename__ = "materials"

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    title = Column(String(255), nullable=False)
    filename = Column(String(512), nullable=False)  # stored filename on disk
    page_count = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    module = relationship("Module", back_populates="materials")


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_option = Column(String(1), nullable=False)  # 'a' | 'b' | 'c' | 'd'

    module = relationship("Module", back_populates="questions")


class Progress(Base):
    """Tracks how far a user has gotten in a module's quiz."""
    __tablename__ = "progress"
    __table_args__ = (UniqueConstraint("user_id", "module_id", name="uq_user_module"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    module_id = Column(Integer, ForeignKey("modules.id"), nullable=False)
    last_question_index = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="progress")


class DailyFreeUsage(Base):
    """Counts free questions answered per calendar day for non-paying users."""
    __tablename__ = "daily_free_usage"
    __table_args__ = (UniqueConstraint("user_id", "usage_date", name="uq_user_date"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    usage_date = Column(Date, default=date.today)
    questions_answered = Column(Integer, default=0)

    user = relationship("User", back_populates="free_usage")
