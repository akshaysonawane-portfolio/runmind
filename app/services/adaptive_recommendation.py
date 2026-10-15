def generate_adaptive_recommendation(
    base_recommendation,
    workout_analysis,
    training_load,
    recovery,
    training_phase=None
):
    base_distance = base_recommendation["distance_km"]
    base_type = base_recommendation["workout_type"]
    base_intensity = base_recommendation["intensity"]

    training_signal = (
        workout_analysis.get("training_signal")
        if workout_analysis
        else None
    )

    training_status = training_load.get("status")
    recovery_status = recovery.get("status")
    days_since_last_run = recovery.get(
        "days_since_last_run"
    )

    # --------------------------------
    # 1. Preserve rest and race-day decisions
    # --------------------------------

    if base_type in {"rest", "race_day"}:
        return {
            **base_recommendation,
            "adaptation": "maintain",
            "adaptation_reason": (
                "The existing plan prioritizes rest or race day. "
                "Adaptive progression will not override that decision."
            )
        }

    # --------------------------------
    # 2. Low recovery: prioritize rest
    # --------------------------------

    if recovery_status == "low":
        return {
            "workout_type": "recovery",
            "distance_km": 0,
            "intensity": "none",
            "adaptation": "reduce",
            "adaptation_reason": (
                "Estimated recovery is low. Prioritize rest "
                "rather than progressing the next workout."
            )
        }

    # --------------------------------
    # 2. Avoid progressing immediately
    #    after a run
    # --------------------------------

    if days_since_last_run is not None:
        if days_since_last_run < 1:

            return {
                "workout_type": base_type,
                "distance_km": base_distance,
                "intensity": base_intensity,
                "adaptation": "maintain",
                "adaptation_reason": (
                    "Your most recent run was today. "
                    "Maintain the planned workload rather "
                    "than progressing immediately."
                )
            }

    # --------------------------------
    # 3. Rapidly increasing training
    # --------------------------------

    if training_status == "rapid_increase":

        return {
            "workout_type": "easy_run",
            "distance_km": base_distance,
            "intensity": "easy",
            "adaptation": "maintain",
            "adaptation_reason": (
                "Recent training volume is increasing "
                "rapidly. Maintain the current workload "
                "instead of progressing."
            )
        }

    # --------------------------------
    # 4. Negative workout response
    # --------------------------------

    if training_signal == "negative":

        reduced_distance = max(
            base_distance - 1,
            3
        )

        return {
            "workout_type": "easy_run",
            "distance_km": reduced_distance,
            "intensity": "easy",
            "adaptation": "reduce",
            "adaptation_reason": (
                "The previous workout produced a "
                "negative response, so the next workout "
                "should be easier."
            )
        }

    # --------------------------------
    # 5. Increasing training
    # --------------------------------

    if training_status == "increasing":

        return {
            "workout_type": base_type,
            "distance_km": base_distance,
            "intensity": base_intensity,
            "adaptation": "maintain",
            "adaptation_reason": (
                "Training volume is already increasing. "
                "Maintain the current workload before "
                "adding more."
            )
        }
    # --------------------------------
    # Avoid progression during taper
    # --------------------------------


    phase = (
        training_phase.get("phase")
        if training_phase
        else None
    )

    if phase in {"taper", "post_race"}:
        return {
            **base_recommendation,
            "adaptation": "maintain",
            "adaptation_reason": (
                f"You are in the {phase.replace('_', ' ')} phase. "
                "Maintain the planned workload instead of "
                "progressing based on one positive workout."
            )
        }

    # --------------------------------
    # 6. Positive workout + stable load
    # --------------------------------

    if (
        training_signal == "positive"
        and training_status == "stable"
        and recovery_status == "good"
    ):

        progressed_distance = (
            base_distance + 1
        )

        return {
            "workout_type": base_type,
            "distance_km": progressed_distance,
            "intensity": base_intensity,
            "adaptation": "progress",
            "adaptation_reason": (
                "The previous workout was completed "
                "comfortably, training volume is stable, "
                "and recovery is good. A small progression "
                "is appropriate."
            )
        }

    # --------------------------------
    # 7. Positive workout but conditions
    #    are not ideal for progression
    # --------------------------------

    if training_signal == "positive":

        return {
            "workout_type": base_type,
            "distance_km": base_distance,
            "intensity": base_intensity,
            "adaptation": "maintain",
            "adaptation_reason": (
                "The previous workout was handled well, "
                "but current training or recovery signals "
                "do not support progression yet."
            )
        }

    # --------------------------------
    # 8. Neutral response
    # --------------------------------

    if training_signal == "neutral":

        return {
            "workout_type": base_type,
            "distance_km": base_distance,
            "intensity": base_intensity,
            "adaptation": "maintain",
            "adaptation_reason": (
                "The previous workout produced a neutral "
                "response, so the current workload will "
                "be maintained."
            )
        }

    # --------------------------------
    # 9. No workout feedback
    # --------------------------------

    return {
        "workout_type": base_type,
        "distance_km": base_distance,
        "intensity": base_intensity,
        "adaptation": "none",
        "adaptation_reason": (
            "There is not enough completed workout "
            "feedback to make an adaptive adjustment."
        )
    }