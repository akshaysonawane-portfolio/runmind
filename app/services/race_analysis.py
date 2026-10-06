def calculate_target_pace(
    distance_km: float,
    target_time_minutes: float
):
    if distance_km <= 0:
        return None

    target_pace = (
        target_time_minutes / distance_km
    )

    return round(target_pace, 2)


def calculate_recent_average_pace(runs):
    if not runs:
        return None

    total_distance = sum(
        run.distance_km
        for run in runs
    )

    total_duration = sum(
        run.duration_minutes
        for run in runs
    )

    if total_distance <= 0:
        return None

    average_pace = (
        total_duration / total_distance
    )

    return round(average_pace, 2)


def analyze_race_goal(
    race_distance_km: float,
    target_time_minutes: float,
    recent_average_pace: float | None,
    longest_recent_run_km: float | None,
    average_weekly_mileage: float | None
):
    target_pace = calculate_target_pace(
        distance_km=race_distance_km,
        target_time_minutes=target_time_minutes
    )

    if target_pace is None:
        return {
            "status": "invalid_race_data"
        }

    result = {
        "race_distance_km": race_distance_km,
        "target_time_minutes": target_time_minutes,
        "target_pace_min_per_km": target_pace
    }

    # Longest recent run compared with race distance
    if (
        longest_recent_run_km is not None
        and race_distance_km > 0
    ):
        race_distance_coverage = (
            longest_recent_run_km / race_distance_km
        ) * 100

        result["longest_recent_run_km"] = round(
            longest_recent_run_km,
            2
        )

        result["race_distance_coverage_percent"] = round(
            race_distance_coverage,
            1
        )

    # Average weekly mileage over the last 28 days
    if average_weekly_mileage is not None:
        result["average_weekly_mileage"] = round(
            average_weekly_mileage,
            2
        )
    if (
        average_weekly_mileage is None
        or average_weekly_mileage == 0
    ) and (
        longest_recent_run_km is None
        or longest_recent_run_km == 0
    ):
        result["readiness"] = "insufficient_data"
        result["readiness_reason"] = (
            "There is not enough recent training data "
            "to assess race readiness."
        )

    # Developing race readiness
    if (
        longest_recent_run_km is not None
        and longest_recent_run_km > 0
        and race_distance_km > 0
        and longest_recent_run_km < race_distance_km * 0.75
    ):
        result["readiness"] = "developing"
        result["readiness_reason"] = (
            "Training has started, but the longest recent run "
            "is still below 75% of the race distance."
        )
    # No recent pace data
    if recent_average_pace is None:
        result["status"] = "insufficient_data"
        return result

    pace_difference = (
        recent_average_pace - target_pace
    )

    result["recent_average_pace"] = round(
        recent_average_pace,
        2
    )

    result["pace_difference"] = round(
        pace_difference,
        2
    )

    if recent_average_pace <= target_pace:
        result["status"] = "at_or_faster_than_target"

    elif recent_average_pace <= target_pace + 0.30:
        result["status"] = "close_to_target"

    else:
        result["status"] = "above_target"

    return result