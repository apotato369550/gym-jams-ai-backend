from pydantic import BaseModel


class UserProfile(BaseModel):
    name: str
    age_range: str  # one of: "15-18", "19-24", "25-30", "30+"
    height_cm: float
    weight_kg: float
    location: str
    activity_level: str  # one of: "mostly_inactive", "lightly_active", "active", "very_active"
    goal: str  # one of: "lose_weight", "gain_muscle", "maintain", "improve_endurance", "just_be_healthier"
    intent: str
    constraints: list[str]
