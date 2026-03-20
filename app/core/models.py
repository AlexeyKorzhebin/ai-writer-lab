from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON
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
    max_iterations = Column(Integer, nullable=True, default=3)

    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
    narrative_spec = relationship("NarrativeSpecORM", back_populates="project", uselist=False, cascade="all, delete-orphan")


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


# --- NarrativeSpec ORM models ---

class NarrativeSpecORM(Base):
    __tablename__ = "narrative_specs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, unique=True)
    version = Column(Integer, nullable=False, default=1)

    logline = Column(Text, nullable=True)
    genre = Column(String(50), nullable=True, default="literary_fiction")
    tone = Column(Text, nullable=True)
    themes = Column(JSON, nullable=True)
    central_conflict = Column(Text, nullable=True)
    story_format = Column(String(100), nullable=True)

    world_type = Column(String(100), nullable=True, default="realistic")
    world_rules = Column(Text, nullable=True)
    world_time_period = Column(String(255), nullable=True)
    world_power_structures = Column(Text, nullable=True)
    world_atmosphere = Column(Text, nullable=True)

    macro_structure = Column(String(50), nullable=True, default="three_act")
    turning_points = Column(JSON, nullable=True)
    climax = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)

    project = relationship("Project", back_populates="narrative_spec")
    characters = relationship("CharacterORM", back_populates="narrative_spec", cascade="all, delete-orphan")
    scenes = relationship("SceneORM", back_populates="narrative_spec", cascade="all, delete-orphan", order_by="SceneORM.order")


class CharacterORM(Base):
    __tablename__ = "characters"

    id = Column(Integer, primary_key=True, index=True)
    narrative_spec_id = Column(Integer, ForeignKey("narrative_specs.id"), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50), nullable=True, default="supporting")
    motivation = Column(Text, nullable=True)
    fear = Column(Text, nullable=True)
    secret = Column(Text, nullable=True)
    relationships = Column(JSON, nullable=True)

    arc_start_state = Column(Text, nullable=True)
    arc_inner_conflict = Column(Text, nullable=True)
    arc_key_events = Column(JSON, nullable=True)
    arc_turning_point = Column(Text, nullable=True)
    arc_end_state = Column(Text, nullable=True)

    narrative_spec = relationship("NarrativeSpecORM", back_populates="characters")


class SceneORM(Base):
    __tablename__ = "scenes"

    id = Column(Integer, primary_key=True, index=True)
    narrative_spec_id = Column(Integer, ForeignKey("narrative_specs.id"), nullable=False)
    order = Column(Integer, nullable=False, default=0)
    title = Column(String(255), nullable=True)
    participants = Column(JSON, nullable=True)
    purpose = Column(Text, nullable=True)
    emotional_state = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    narrative_spec = relationship("NarrativeSpecORM", back_populates="scenes")
