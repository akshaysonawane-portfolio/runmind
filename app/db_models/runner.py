from sqlalchemy import Column, Integer, Float, String, ForeignKey

from app.database.database import Base


class RunnerDB(Base):

    __tablename__ = "runners"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        unique=True,
        nullable=True,
        index=True
    )

    name = Column(
        String,
        nullable=False
    )

    age = Column(
        Integer,
        nullable=False
    )

    weekly_mileage = Column(
        Float,
        nullable=False
    )

    runs_per_week = Column(
        Integer,
        nullable=False
    )