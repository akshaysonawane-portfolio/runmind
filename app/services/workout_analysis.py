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
        distance_difference / planned_distance
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

    effort = feedback.perceived_effort
    felt_good = feedback.felt_good

    if effort < 1 or effort > 5:
        training_signal = "neutral"
        reason = (
            "Perceived effort is invalid. "
            "Unable to reliably assess the workout response."
        )

    elif effort <= 2 and felt_good:
        if completion == "completed":
            training_signal = "positive"
            reason = (
                "The planned workout was completed and "
                "the runner reported low effort and feeling good."
            )
        else:
            training_signal = "neutral"
            reason = (
                "The runner felt good, but the planned workout "
                "was not fully completed."
            )

    elif effort == 3 and felt_good:
        training_signal = "neutral"
        reason = (
            "The run felt moderately difficult, "
            "but the runner reported feeling good."
        )

    elif effort >= 4 and not felt_good:
        training_signal = "negative"
        reason = (
            "The run felt hard and the runner "
            "did not feel good."
        )

    elif effort >= 4:
        training_signal = "negative"
        reason = "The run felt harder than expected."

    else:
        training_signal = "neutral"
        reason = "The feedback contains mixed signals."

    return {
        "planned_distance_km": round(planned_distance, 2),
        "actual_distance_km": round(actual_distance, 2),
        "distance_difference_km": round(distance_difference, 2),
        "distance_difference_percent": round(
            distance_difference_percent, 2
        ),
        "completion": completion,
        "training_signal": training_signal,
        "reason": reason,
    }