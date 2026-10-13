def generate_recommendation(
    training_load,
    weekly_mileage,
    longest_run_km,
    race_distance_km,
    training_phase=None
):
    status = training_load["status"]

    phase = None

    if training_phase:
        phase = training_phase.get("phase")

    # -------------------------
    # Post-race
    # -------------------------

    if phase == "post_race":

        return {
            "workout_type": "recovery",
            "distance_km": 3,
            "intensity": "easy",
            "reason": (
                "You are in the post-race phase. "
                "Prioritize recovery before returning "
                "to normal training."
            )
        }

    # -------------------------
    # Taper
    # -------------------------

    if phase == "taper":

        return {
            "workout_type": "easy_run",
            "distance_km": 5,
            "intensity": "easy",
            "reason": (
                "You are in the taper phase. "
                "Reduce training volume while keeping "
                "the run easy."
            )
        }

    # current_week_km is only needed
    # for the normal training-load rules.
    current_week_km = training_load.get(
        "current_week_km",
        weekly_mileage.get("week_1", 0)
    )

    # -------------------------
    # Rapid increase
    # -------------------------

    if status == "rapid_increase":

        distance = 5

        if race_distance_km and race_distance_km >= 21:
            distance = 6

        return {
            "workout_type": "easy_run",
            "distance_km": distance,
            "intensity": "easy",
            "reason": (
                "Your recent training volume has increased "
                "substantially. Keep the next run easy instead "
                "of adding more training stress."
            )
        }

    # -------------------------
    # Increasing
    # -------------------------

    if status == "increasing":

        distance = 6

        if race_distance_km and race_distance_km >= 21:
            distance = 7

        return {
            "workout_type": "easy_run",
            "distance_km": distance,
            "intensity": "easy",
            "reason": (
                "Your training volume is increasing. "
                "An easy run allows you to continue building "
                "fitness without adding excessive intensity."
            )
        }

    # -------------------------
    # Stable
    # -------------------------

    if status == "stable":

        if longest_run_km < current_week_km * 0.4:

            long_run_distance = longest_run_km + 2

            if race_distance_km and race_distance_km >= 21:
                long_run_distance = longest_run_km + 2

            return {
                "workout_type": "long_run",
                "distance_km": round(
                    long_run_distance,
                    1
                ),
                "intensity": "easy",
                "reason": (
                    "Your training volume is stable. "
                    "A gradual long-run progression can help "
                    "develop endurance for your race."
                )
            }

        return {
            "workout_type": "easy_run",
            "distance_km": 6,
            "intensity": "easy",
            "reason": (
                "Your training volume is stable. "
                "Continue building consistency with an easy run."
            )
        }

    # -------------------------
    # Decreasing
    # -------------------------

    if status == "decreasing":

        return {
            "workout_type": "easy_run",
            "distance_km": 5,
            "intensity": "easy",
            "reason": (
                "Your recent training volume has decreased. "
                "A shorter easy run can help rebuild consistency."
            )
        }

    # -------------------------
    # Base phase
    # -------------------------

    if phase == "base":

        return {
            "workout_type": "easy_run",
            "distance_km": 5,
            "intensity": "easy",
            "reason": (
                "You are in the base phase. "
                "Focus on consistent easy aerobic running "
                "before adding more training stress."
            )
        }

    # -------------------------
    # Build phase
    # -------------------------

    if phase == "build":

        return {
            "workout_type": "easy_run",
            "distance_km": 6,
            "intensity": "easy",
            "reason": (
                "You are in the build phase. "
                "Continue developing aerobic fitness "
                "with a gradual increase in workload."
            )
        }

    # -------------------------
    # Peak phase
    # -------------------------

    if phase == "peak":

        if race_distance_km and race_distance_km >= 21:

            long_run_distance = longest_run_km + 1

            return {
                "workout_type": "long_run",
                "distance_km": round(
                    long_run_distance,
                    1
                ),
                "intensity": "easy",
                "reason": (
                    "You are in the peak phase for a "
                    "long-distance race. Prioritize a gradual "
                    "long-run progression to build race-specific "
                    "endurance."
                )
            }

        return {
            "workout_type": "easy_run",
            "distance_km": 7,
            "intensity": "easy",
            "reason": (
                "You are in the peak phase. "
                "Continue developing race-specific fitness "
                "while controlling training stress."
            )
        }

    # -------------------------
    # Insufficient data
    # -------------------------

    return {
        "workout_type": "easy_run",
        "distance_km": 5,
        "intensity": "easy",
        "reason": (
            "There is not enough training history yet. "
            "Start with an easy run while RunMind collects "
            "more data."
        )
    }