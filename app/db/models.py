from datetime import datetime
from typing import Optional
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, DateTime, Date, SmallInteger, ForeignKey, Enum, func
from sqlalchemy.dialects.mysql import DECIMAL, JSON


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class UserProfile(Base):
    __tablename__ = "user_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    age_range: Mapped[str] = mapped_column(String(20), nullable=False)
    height_cm: Mapped[float] = mapped_column(DECIMAL(6, 2), nullable=False)
    weight_kg: Mapped[float] = mapped_column(DECIMAL(6, 2), nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    activity_level: Mapped[str] = mapped_column(String(50), nullable=False)
    goal: Mapped[str] = mapped_column(String(100), nullable=False)
    intent: Mapped[str] = mapped_column(Text, nullable=False)
    constraints: Mapped[str] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class GymProfile(Base):
    __tablename__ = "gym_profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    archetype: Mapped[str] = mapped_column(String(255), nullable=False)
    read_description: Mapped[str] = mapped_column(Text, nullable=False)
    modalities_youll_enjoy: Mapped[str] = mapped_column(JSON, nullable=False)
    first_week_suggestion: Mapped[str] = mapped_column(Text, nullable=False)
    watch_out_for: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date: Mapped[str] = mapped_column(Date, nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    sets: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    reps: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    weight_kg: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2), nullable=True)
    duration_mins: Mapped[Optional[float]] = mapped_column(DECIMAL(6, 2), nullable=True)


class WorkoutAnalysisResult(Base):
    __tablename__ = "workout_analysis_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("workout_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    total_volume_kg: Mapped[Optional[float]] = mapped_column(DECIMAL(10, 2), nullable=True)
    total_reps: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    muscle_groups_targeted: Mapped[str] = mapped_column(JSON, nullable=False)
    estimated_calories_burned: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    intensity_rating: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    observation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class WorkoutHistorySummary(Base):
    __tablename__ = "workout_history_summaries"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    range: Mapped[str] = mapped_column(Enum("week", "month", "3months"), nullable=False)
    consistency_score: Mapped[Optional[float]] = mapped_column(DECIMAL(4, 2), nullable=True)
    consistency_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    top_exercises: Mapped[str] = mapped_column(JSON, nullable=False)
    volume_trend: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    volume_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    plateaus_detected: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    trajectory_suggestion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    thing_youre_doing_well: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(Enum("user", "assistant"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
