from app.db_models.run_feedback import RunFeedbackDB


def analyze_run_feedback(
    feedback: RunFeedbackDB
):
    effort = feedback.perceived_effort
    felt_good = feedback.felt_good

    # -------------------------
    # Validate effort
    # -------------------------

    if effort < 1 or effort > 5:
        return {
            "status": "invalid",
            "reason": "Perceived effort must be between 1 and 5."
        }

    # -------------------------
    # Analyze effort
    # -------------------------

    if effort <= 2 and felt_good:
        status = "good"
        training_signal = "positive"

        reason = (
            "The run felt manageable and the runner "
            "reported feeling good."
        )

    elif effort == 3 and felt_good:
        status = "normal"
        training_signal = "neutral"

        reason = (
            "The run felt moderately difficult but "
            "the runner reported feeling good."
        )

    elif effort >= 4 and not felt_good:
        status = "poor"
        training_signal = "negative"

        reason = (
            "The run felt hard and the runner "
            "did not feel good."
        )

    elif effort >= 4:
        status = "hard"
        training_signal = "negative"

        reason = (
            "The run felt harder than expected."
        )

    else:
        status = "mixed"
        training_signal = "neutral"

        reason = (
            "The feedback contains mixed signals."
        )

    return {
        "status": status,
        "training_signal": training_signal,
        "perceived_effort": effort,
        "felt_good": felt_good,
        "reason": reason
    }