from sqlalchemy import Column, Integer, Boolean, ForeignKey

from app.database.database import Base


class RunFeedbackDB(Base):
    __tablename__ = "run_feedback"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    run_id = Column(
        Integer,
        ForeignKey("runs.id"),
        nullable=False
    )

    perceived_effort = Column(
        Integer,
        nullable=False
    )

    felt_good = Column(
        Boolean,
        nullable=False
    )