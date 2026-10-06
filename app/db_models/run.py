from sqlalchemy import (
    Column,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    String
)

from app.database.database import Base


class RunDB(Base):
    __tablename__ = "runs"

    id = Column(Integer, primary_key=True, index=True)

    runner_id = Column(
        Integer,
        ForeignKey("runners.id"),
        nullable=False
    )

    workout_id = Column(
        Integer,
        ForeignKey("workouts.id"),
        nullable=True
    )

    strava_activity_id = Column(
        String,
        unique=True,
        nullable=True,
        index=True
    )
    source = Column(
        String,
        nullable=False,
        default="manual"
    )
    date = Column(DateTime, nullable=False)
    distance_km = Column(Float, nullable=False)
    duration_minutes = Column(Float, nullable=False)
    average_pace = Column(Float, nullable=False)

    average_heart_rate = Column(Integer, nullable=True)
    average_cadence = Column(Integer, nullable=True)
    elevation_gain = Column(Float, nullable=True)