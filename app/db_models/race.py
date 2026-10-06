from sqlalchemy import Column, Integer, Float, String, Date, ForeignKey

from app.database.database import Base


class RaceDB(Base):

    __tablename__ = "races"

    id = Column(Integer, primary_key=True, index=True)

    runner_id = Column(
        Integer,
        ForeignKey("runners.id"),
        nullable=False
    )

    race_name = Column(String, nullable=False)

    distance_km = Column(Float, nullable=False)

    race_date = Column(Date, nullable=False)

    target_time_minutes = Column(Float, nullable=False)