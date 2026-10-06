from pydantic import BaseModel


class Runner(BaseModel):
    name: str
    age: int
    weekly_mileage: float
    runs_per_week: int


class RunnerUpdate(BaseModel):
    name: str
    age: int
    weekly_mileage: float
    runs_per_week: int