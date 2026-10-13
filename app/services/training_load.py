def calculate_training_load(
    weekly_mileage: dict,
    weekly_run_counts: dict
):
    current_week = weekly_mileage.get("week_1", 0)
    previous_week = weekly_mileage.get("week_2", 0)
    week_3 = weekly_mileage.get("week_3", 0)
    week_4 = weekly_mileage.get("week_4", 0)

    current_runs = weekly_run_counts.get("week_1", 0)
    previous_runs = weekly_run_counts.get("week_2", 0)
    week_3_runs = weekly_run_counts.get("week_3", 0)
    week_4_runs = weekly_run_counts.get("week_4", 0)

    # Only consider periods that actually contain training data.
    previous_mileages = [
        mileage
        for mileage, run_count in [
            (previous_week, previous_runs),
            (week_3, week_3_runs),
            (week_4, week_4_runs)
        ]
        if run_count > 0
    ]

    weeks_with_data = len(previous_mileages)

    # We need at least one previous training period
    # to compare against the current period.
    if current_runs == 0:
        return {
            "status": "insufficient_data",
            "confidence": "low",
            "reason": (
                "There is no recorded training "
                "in the current 7-day period."
            ),
            "current_week_km": round(current_week, 2),
            "previous_week_km": round(previous_week, 2),
            "current_week_runs": current_runs,
            "previous_week_runs": previous_runs
        }

    if previous_runs == 0:
        return {
            "status": "insufficient_history",
            "confidence": "low",
            "reason": (
                "There is current training data, but not enough "
                "historical training to assess the training trend."
            ),
            "current_week_km": round(current_week, 2),
            "previous_week_km": round(previous_week, 2),
            "current_week_runs": current_runs,
            "previous_week_runs": previous_runs
        }

    mileage_change_km = current_week - previous_week

    mileage_change_percent = (
        mileage_change_km / previous_week
    ) * 100

    average_previous_mileage = (
        sum(previous_mileages)
        / len(previous_mileages)
    )

    average_change_percent = (
        (
            current_week
            - average_previous_mileage
        )
        / average_previous_mileage
    ) * 100

    # Determine training-load trend.
    if weeks_with_data < 1:
        status = "insufficient_data"
        confidence = "low"

    elif average_change_percent > 30:
        status = "rapid_increase"
        confidence = "medium"

    elif average_change_percent > 10:
        status = "increasing"
        confidence = "medium"

    elif average_change_percent >= -10:
        status = "stable"
        confidence = "medium"

    else:
        status = "decreasing"
        confidence = "medium"

    if status == "rapid_increase":
        reason = (
            "Current weekly mileage is substantially "
            "higher than recent training volume."
        )

    elif status == "increasing":
        reason = (
            "Current weekly mileage is higher "
            "than recent training volume."
        )

    elif status == "stable":
        reason = (
            "Current weekly mileage is relatively "
            "consistent with recent training."
        )

    elif status == "decreasing":
        reason = (
            "Current weekly mileage is lower "
            "than recent training volume."
        )

    else:
        reason = (
            "More consistent training history "
            "is needed."
        )

    # Compare running frequency.
    if current_runs > previous_runs:
        frequency_trend = "increasing"

    elif current_runs < previous_runs:
        frequency_trend = "decreasing"

    else:
        frequency_trend = "stable"

    return {
        "status": status,
        "confidence": confidence,

        "current_week_km": round(
            current_week, 2
        ),

        "previous_week_km": round(
            previous_week, 2
        ),

        "change_km": round(
            mileage_change_km, 2
        ),

        "change_percent": round(
            mileage_change_percent, 2
        ),

        "average_previous_mileage": round(
            average_previous_mileage, 2
        ),

        "average_change_percent": round(
            average_change_percent, 2
        ),

        "weeks_with_data": weeks_with_data,

        "current_week_runs": current_runs,

        "previous_week_runs": previous_runs,

        "frequency_trend": frequency_trend,

        "reason": reason
    }