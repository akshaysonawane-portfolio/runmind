from sqlalchemy import (
    Column,
    Integer,
    Float,
    String,
    DateTime,
    ForeignKey
)

from app.database.database import Base


class WorkoutDB(Base):
    __tablename__ = "workouts"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    runner_id = Column(
        Integer,
        ForeignKey("runners.id"),
        nullable=False
    )

    date = Column(
        DateTime,
        nullable=False
    )

    workout_type = Column(
        String,
        nullable=False
    )

    planned_distance_km = Column(
        Float,
        nullable=False
    )

    planned_intensity = Column(
        String,
        nullable=False
    )