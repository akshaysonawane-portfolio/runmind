from datetime import date
from pydantic import BaseModel


class RaceGoal(BaseModel):
    runner_id: int
    race_name: str
    distance_km: float
    race_date: date
    target_time_minutes: float


class RaceGoalUpdate(BaseModel):
    race_name: str
    distance_km: float
    race_date: date
    target_time_minutes: float