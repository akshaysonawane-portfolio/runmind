from sqlalchemy.orm import Session

from app.db_models.race import RaceDB
from app.db_models.run import RunDB

from app.services.analytics import get_running_analytics
from app.services.training_load import calculate_training_load
from app.services.race_analysis import (
    calculate_recent_average_pace,
    analyze_race_goal
)
from app.services.recommendation import generate_recommendation
from app.services.recovery import calculate_recovery


def get_coach_context(
    runner_id: int,
    db: Session
):
    # --------------------------------
    # Training analytics
    # --------------------------------

    analytics = get_running_analytics(
        runner_id=runner_id,
        db=db
    )

    # --------------------------------
    # Training load
    # --------------------------------

    training_load = calculate_training_load(
        weekly_mileage=analytics["weekly_mileage"],
        weekly_run_counts=analytics["weekly_run_counts"]
    )

    # --------------------------------
    # Get runner's runs
    # --------------------------------

    runs = (
        db.query(RunDB)
        .filter(
            RunDB.runner_id == runner_id
        )
        .order_by(RunDB.date.desc())
        .all()
    )

    # --------------------------------
    # Recovery / readiness
    # --------------------------------

    recovery = calculate_recovery(
        runs=runs,
        training_load=training_load
    )

    # --------------------------------
    # Get race goal
    # --------------------------------

    race = (
        db.query(RaceDB)
        .filter(
            RaceDB.runner_id == runner_id
        )
        .order_by(RaceDB.race_date.asc())
        .first()
    )

    race_goal = None
    race_analysis = None
    race_distance_km = None

    # --------------------------------
    # Race analysis
    # --------------------------------

    if race:
        race_distance_km = race.distance_km

        race_goal = {
            "race_name": race.race_name,
            "distance_km": race.distance_km,
            "race_date": str(race.race_date),
            "target_time_minutes": race.target_time_minutes
        }

        recent_runs = (
            db.query(RunDB)
            .filter(
                RunDB.runner_id == runner_id
            )
            .order_by(RunDB.date.desc())
            .limit(5)
            .all()
        )

        recent_average_pace = calculate_recent_average_pace(
            recent_runs
        )

        race_analysis = analyze_race_goal(
            race_distance_km=race.distance_km,
            target_time_minutes=race.target_time_minutes,
            recent_average_pace=recent_average_pace
        )

    # --------------------------------
    # Workout recommendation
    # --------------------------------

    recommendation = generate_recommendation(
        training_load=training_load,
        weekly_mileage=analytics["weekly_mileage"],
        longest_run_km=analytics["longest_run_last_28_days"],
        race_distance_km=race_distance_km
    )

    # --------------------------------
    # Final coach context
    # --------------------------------

    return {
        "runner_id": runner_id,

        "training": {
            "runs_last_7_days": analytics["runs_last_7_days"],
            "distance_last_7_days": analytics["distance_last_7_days"],
            "distance_last_28_days": analytics["distance_last_28_days"],
            "longest_run_last_28_days": analytics[
                "longest_run_last_28_days"
            ],
            "weekly_mileage": analytics["weekly_mileage"],
            "weekly_run_counts": analytics["weekly_run_counts"]
        },

        "training_load": training_load,

        "recovery": recovery,

        "race_goal": race_goal,

        "race_analysis": race_analysis,

        "recommendation": recommendation
    }