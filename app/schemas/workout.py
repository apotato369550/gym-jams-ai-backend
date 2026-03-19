from pydantic import BaseModel
from typing import Literal


class WorkoutExercise(BaseModel):
    name: str
    sets: int
    reps: int
    weight_kg: float | None = None
    duration_mins: float | None = None


class WorkoutSession(BaseModel):
    date: str
    exercises: list[WorkoutExercise]
    notes: str | None = None


class WorkoutHistory(BaseModel):
    sessions: list[WorkoutSession]
    range: Literal["week", "month", "3months"]
