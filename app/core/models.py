from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    model_name = Column(String(255), nullable=True)
    temperature = Column(String(50), nullable=True)
    max_tokens = Column(String(50), nullable=True)
    author_name = Column(String(255), nullable=True)
    author_style = Column(Text, nullable=True)

    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")


class Chapter(Base):
    __tablename__ = "chapters"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    project = relationship("Project", back_populates="chapters")
    versions = relationship("ChapterVersion", back_populates="chapter", cascade="all, delete-orphan")


class ChapterVersion(Base):
    __tablename__ = "chapter_versions"

    id = Column(Integer, primary_key=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id"), nullable=False)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)
    version_number = Column(Integer, nullable=False)

    chapter = relationship("Chapter", back_populates="versions")
