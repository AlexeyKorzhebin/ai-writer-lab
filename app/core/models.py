from sqlalchemy import Column, Integer, String, Text, Float, Boolean, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.core.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Setting(Base):
    __tablename__ = "settings"

    key = Column(String(255), primary_key=True)
    value = Column(Text, nullable=True)
    encrypted = Column(Boolean, default=False)


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
    created_at = Column(DateTime, default=_utcnow)

    chapters = relationship("Chapter", back_populates="project", cascade="all, delete-orphan")
    narrative_spec = relationship("NarrativeSpecORM", back_populates="project", uselist=False, cascade="all, delete-orphan")
    locations = relationship("LocationORM", back_populates="project", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSessionORM", back_populates="project", cascade="all, delete-orphan")


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
    appearance = Column(Text, nullable=True)
    speech_style = Column(Text, nullable=True)

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
    location = Column(String(255), nullable=True)
    time_context = Column(JSON, nullable=True)

    narrative_spec = relationship("NarrativeSpecORM", back_populates="scenes")


# --- Location models ---

class LocationORM(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    location_type = Column(String(50), default="building")
    parent_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    description = Column(Text, nullable=True)
    visual_details = Column(Text, nullable=True)
    atmosphere = Column(Text, nullable=True)
    significance = Column(Text, nullable=True)
    climate = Column(Text, nullable=True)
    inhabitants = Column(Text, nullable=True)
    notable_features = Column(Text, nullable=True)
    connected_to = Column(JSON, nullable=True)
    travel_notes = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)
    first_appearance = Column(Integer, nullable=True)

    project = relationship("Project", back_populates="locations")
    parent = relationship("LocationORM", remote_side=[id], back_populates="children")
    children = relationship("LocationORM", back_populates="parent", cascade="all, delete-orphan")
    states = relationship("LocationStateORM", back_populates="location", cascade="all, delete-orphan")


class LocationStateORM(Base):
    __tablename__ = "location_states"

    id = Column(Integer, primary_key=True, index=True)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    after_scene = Column(Integer, nullable=True)
    description_override = Column(Text, nullable=True)
    change_reason = Column(Text, nullable=True)

    location = relationship("LocationORM", back_populates="states")


# --- Chat models ---

class ChatSessionORM(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    task_name = Column(String(255), default="Общий чат")
    pinned_context = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    project = relationship("Project", back_populates="chat_sessions")
    messages = relationship("ChatMessageORM", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessageORM.created_at")


class ChatMessageORM(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    references = Column(JSON, nullable=True)
    tokens = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=_utcnow)

    session = relationship("ChatSessionORM", back_populates="messages")


# --- Illustration models ---

class IllustrationPromptORM(Base):
    __tablename__ = "illustration_prompts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    scene_index = Column(Integer, nullable=True)
    template = Column(String(100), nullable=True)
    prompt_text = Column(Text, nullable=True)
    variant_data = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
