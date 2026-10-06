from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)

from app.database.database import Base


class StravaConnectionDB(Base):
    __tablename__ = "strava_connections"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    runner_id = Column(
        Integer,
        ForeignKey("runners.id"),
        nullable=False,
        unique=True
    )

    strava_athlete_id = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )

    access_token = Column(
        String,
        nullable=False
    )

    refresh_token = Column(
        String,
        nullable=False
    )

    expires_at = Column(
        Integer,
        nullable=False
    )

    scope = Column(
        String,
        nullable=False
    )

    created_at = Column(
        DateTime,
        nullable=False
    )

    updated_at = Column(
        DateTime,
        nullable=False
    )