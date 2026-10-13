def analyze_workout(
    workout,
    run,
    feedback
):
    # --------------------------------
    # Distance comparison
    # --------------------------------

    planned_distance = workout.planned_distance_km
    actual_distance = run.distance_km

    distance_difference = (
        actual_distance - planned_distance
    )

    distance_difference_percent = (
        distance_difference
        / planned_distance
    ) * 100

    # --------------------------------
    # Determine completion
    # --------------------------------

    if actual_distance >= planned_distance * 0.95:
        completion = "completed"

    elif actual_distance >= planned_distance * 0.75:
        completion = "mostly_completed"

    else:
        completion = "incomplete"

    # --------------------------------
    # Determine training signal
    # --------------------------------

    # --------------------------------
    # Determine training signal
    # --------------------------------

    if (
        completion == "completed"
        and feedback.perceived_effort <= 3
        and feedback.felt_good
    ):
        training_signal = "positive"

    elif (
        feedback.perceived_effort >= 8
        or not feedback.felt_good
    ):
        training_signal = "negative"

    else:
        training_signal = "neutral"

    # --------------------------------
    # Reason
    # --------------------------------

    if training_signal == "positive":
        reason = (
            "The planned workout was completed and "
            "the runner reported low effort and feeling good."
        )

    elif training_signal == "negative":
        reason = (
            "The workout produced signs of higher-than-"
            "expected difficulty or poor subjective response."
        )

    else:
        reason = (
            "The workout was completed with a neutral "
            "training response."
        )

    return {
        "planned_distance_km": round(
            planned_distance,
            2
        ),
        "actual_distance_km": round(
            actual_distance,
            2
        ),
        "distance_difference_km": round(
            distance_difference,
            2
        ),
        "distance_difference_percent": round(
            distance_difference_percent,
            2
        ),
        "completion": completion,
        "training_signal": training_signal,
        "reason": reason
    }