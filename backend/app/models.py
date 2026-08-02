import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    templates = relationship("CleaningTemplate", back_populates="owner")
    jobs = relationship("CleaningJob", back_populates="owner")


class CleaningTemplate(Base):
    """A saved, reusable cleaning plan tied to a user's custom use case."""
    __tablename__ = "cleaning_templates"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    context_text = Column(Text, nullable=True)  # original plain-English instruction
    plan_json = Column(Text, nullable=False)     # the structured cleaning plan (JSON string)
    is_predefined = Column(Integer, default=0)   # 0 = user-created, 1 = system predefined
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="templates")


class CleaningJob(Base):
    """History of a cleaning run, for auditability."""
    __tablename__ = "cleaning_jobs"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String, nullable=False)
    plan_json = Column(Text, nullable=False)
    report_json = Column(Text, nullable=True)  # before/after quality report
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    owner = relationship("User", back_populates="jobs")
