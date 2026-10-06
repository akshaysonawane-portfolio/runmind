from datetime import datetime

from pydantic import BaseModel


class Run(BaseModel):
    runner_id: int
    workout_id: int | None = None

    date: datetime
    distance_km: float
    duration_minutes: float
    average_pace: float

    average_heart_rate: int | None = None
    average_cadence: int | None = None
    elevation_gain: float | None = None