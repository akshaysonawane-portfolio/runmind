from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.db_models.run import RunDB


def get_running_analytics(
    runner_id: int,
    db: Session
):
    now = datetime.now()

    seven_days_ago = now - timedelta(days=7)
    twenty_eight_days_ago = now - timedelta(days=28)

    # -------------------------
    # Get last 28 days of runs
    # -------------------------

    runs = (
        db.query(RunDB)
        .filter(
            RunDB.runner_id == runner_id,
            RunDB.date >= twenty_eight_days_ago,
            RunDB.source == "strava"
        )
        .all()
    )

    # -------------------------
    # Last 7 days
    # -------------------------

    runs_last_7_days = [
        run
        for run in runs
        if run.date >= seven_days_ago
    ]

    distance_last_7_days = sum(
        run.distance_km
        for run in runs_last_7_days
    )

    # -------------------------
    # Last 28 days
    # -------------------------

    distance_last_28_days = sum(
        run.distance_km
        for run in runs
    )

    longest_run = max(
        (run.distance_km for run in runs),
        default=0
    )

    # -------------------------
    # Weekly mileage
    # -------------------------

    weekly_mileage = {
        "week_1": 0,
        "week_2": 0,
        "week_3": 0,
        "week_4": 0
    }

    # -------------------------
    # Weekly run counts
    # -------------------------

    weekly_run_counts = {
        "week_1": 0,
        "week_2": 0,
        "week_3": 0,
        "week_4": 0
    }

    # -------------------------
    # Categorize runs
    # -------------------------

    for run in runs:

        days_ago = (now - run.date).days

        if days_ago < 7:

            weekly_mileage["week_1"] += run.distance_km
            weekly_run_counts["week_1"] += 1

        elif days_ago < 14:

            weekly_mileage["week_2"] += run.distance_km
            weekly_run_counts["week_2"] += 1

        elif days_ago < 21:

            weekly_mileage["week_3"] += run.distance_km
            weekly_run_counts["week_3"] += 1

        elif days_ago < 28:

            weekly_mileage["week_4"] += run.distance_km
            weekly_run_counts["week_4"] += 1

    # -------------------------
    # Round mileage
    # -------------------------

    weekly_mileage = {
        week: round(distance, 2)
        for week, distance in weekly_mileage.items()
    }

    # -------------------------
    # Mileage change
    # -------------------------

    current_week = weekly_mileage["week_1"]
    previous_week = weekly_mileage["week_2"]

    mileage_change_km = (
        current_week - previous_week
    )

    if previous_week > 0:

        mileage_change_percent = (
            (current_week - previous_week)
            / previous_week
        ) * 100

    else:

        mileage_change_percent = None

    # -------------------------
    # Final response
    # -------------------------

    return {
        "runs_last_7_days": len(
            runs_last_7_days
        ),

        "distance_last_7_days": round(
            distance_last_7_days,
            2
        ),

        "runs_last_28_days": len(
            runs
        ),

        "distance_last_28_days": round(
            distance_last_28_days,
            2
        ),

        "longest_run_last_28_days": round(
            longest_run,
            2
        ),

        "weekly_mileage": weekly_mileage,

        "weekly_run_counts": weekly_run_counts,

        "mileage_change_km": round(
            mileage_change_km,
            2
        ),

        "mileage_change_percent": (
            round(
                mileage_change_percent,
                2
            )
            if mileage_change_percent is not None
            else None
        )
    }