from datetime import datetime

from pydantic import BaseModel


class Workout(BaseModel):
    runner_id: int
    date: datetime
    workout_type: str
    planned_distance_km: float
    planned_intensity: str