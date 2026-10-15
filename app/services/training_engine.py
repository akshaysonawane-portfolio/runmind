from sqlalchemy.orm import Session

from app.db_models.run import RunDB
from app.db_models.race import RaceDB
from app.db_models.workout import WorkoutDB
from app.db_models.run_feedback import RunFeedbackDB

from app.services.analytics import get_running_analytics
from app.services.training_load import calculate_training_load
from app.services.recovery import calculate_recovery
from app.services.recommendation import generate_recommendation
from app.services.workout_analysis import analyze_workout
from app.services.adaptive_recommendation import (
    generate_adaptive_recommendation
)
from app.services.training_phase import calculate_training_phase


def get_training_decision(
    runner_id: int,
    db: Session
):
    # --------------------------------
    # 1. Running analytics
    # --------------------------------

    analytics = get_running_analytics(
        runner_id=runner_id,
        db=db
    )

    # --------------------------------
    # 2. Training load
    # --------------------------------

    training_load = calculate_training_load(
        weekly_mileage=analytics["weekly_mileage"],
        weekly_run_counts=analytics["weekly_run_counts"]
    )

    # --------------------------------
    # 3. Recent runs
    # --------------------------------

    recent_runs = (
        db.query(RunDB)
        .filter(
            RunDB.runner_id == runner_id,
            # RunDB.source == "strava"
        )
        .order_by(RunDB.date.desc())
        .limit(5)
        .all()
    )

    # All runs are still used for recovery calculation.
    runs = (
        db.query(RunDB)
        .filter(
            RunDB.runner_id == runner_id
        )
        .order_by(RunDB.date.desc())
        .all()
    )

    # --------------------------------
    # 4. Recovery
    # --------------------------------

    recovery = calculate_recovery(
        runs=runs,
        training_load=training_load
    )

    # --------------------------------
    # 5. Race goal
    # --------------------------------

    race = (
        db.query(RaceDB)
        .filter(
            RaceDB.runner_id == runner_id
        )
        .order_by(RaceDB.race_date.asc())
        .first()
    )

    race_distance_km = None
    race_goal = None
    goal_pace_min_per_km = None

    if race and race.distance_km and race.distance_km > 0:
        race_distance_km = race.distance_km

        goal_pace_min_per_km = (
            race.target_time_minutes / race.distance_km
        )

        race_goal = {
            "race_name": race.race_name,
            "distance_km": race.distance_km,
            "race_date": str(race.race_date),
            "target_time_minutes": race.target_time_minutes
        }

    # --------------------------------
    # 6. Training phase
    # --------------------------------

    training_phase = None

    if race:
        training_phase = calculate_training_phase(
            race_date=race.race_date
        )

    # --------------------------------
    # 7. Base recommendation
    # --------------------------------

    base_recommendation = generate_recommendation(
        training_load=training_load,
        weekly_mileage=analytics["weekly_mileage"],
        longest_run_km=analytics["longest_run_last_28_days"],
        race_distance_km=race_distance_km,
        training_phase=training_phase,
        recovery=recovery
    )

    # --------------------------------
    # 8. Previous RunMind workout
    # --------------------------------

    latest_workout = (
        db.query(WorkoutDB)
        .filter(
            WorkoutDB.runner_id == runner_id
        )
        .order_by(WorkoutDB.date.desc())
        .first()
    )

    previous_workout_analysis = None

    if latest_workout:

        # Find the run that was actually linked
        # to this RunMind planned workout.
        latest_workout_run = (
            db.query(RunDB)
            .filter(
                RunDB.runner_id == runner_id,
                RunDB.workout_id == latest_workout.id
            )
            .order_by(RunDB.date.desc())
            .first()
        )

        if latest_workout_run:

            # Find feedback for that specific workout run.
            latest_feedback = (
                db.query(RunFeedbackDB)
                .filter(
                    RunFeedbackDB.run_id == latest_workout_run.id
                )
                .order_by(RunFeedbackDB.id.desc())
                .first()
            )

            if latest_feedback:

                previous_workout_analysis = analyze_workout(
                    latest_workout,
                    latest_workout_run,
                    latest_feedback
                )

    # --------------------------------
    # 9. Adaptive recommendation
    # --------------------------------

    if previous_workout_analysis:

        recommendation = generate_adaptive_recommendation(
            base_recommendation,
            previous_workout_analysis,
            training_load,
            recovery,
            training_phase
        )

    else:

        recommendation = {
            **base_recommendation,
            "adaptation": "none",
            "adaptation_reason": (
                "No completed RunMind workout with feedback "
                "is available for adaptive progression."
            )
        }

    # --------------------------------
    # 10. Canonical training decision
    # --------------------------------

    return {
        "runner_id": runner_id,

        "recent_runs": [
            {
                "date": run.date.strftime("%Y-%m-%d"),
                "distance_km": round(
                    run.distance_km,
                    2
                ),
                "duration_minutes": round(
                    run.duration_minutes,
                    2
                ),
                "average_pace_min_per_km": round(
                    run.average_pace,
                    2
                ),
                "average_heart_rate": (
                    round(run.average_heart_rate)
                    if run.average_heart_rate is not None
                    else None
                ),
                "average_cadence": (
                    round(run.average_cadence)
                    if run.average_cadence is not None
                    else None
                ),
                "elevation_gain": (
                    round(run.elevation_gain, 2)
                    if run.elevation_gain is not None
                    else None
                )
            }
            for run in recent_runs
        ],

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

        "goal_pace_min_per_km": (
            round(goal_pace_min_per_km, 2)
            if goal_pace_min_per_km is not None
            else None
        ),

        "base_recommendation": base_recommendation,

        "previous_workout_analysis": previous_workout_analysis,

        "recommendation": recommendation,

        "training_phase": training_phase,
    }