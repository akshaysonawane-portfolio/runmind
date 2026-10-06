from datetime import datetime


def calculate_recovery(
    runs,
    training_load
):
    # --------------------------------
    # No running history
    # --------------------------------

    if not runs:
        return {
            "status": "unknown",
            "score": 50,
            "days_since_last_run": None,
            "reason": [
                "There is not enough running history "
                "to estimate recovery."
            ]
        }

    # --------------------------------
    # Last run
    # --------------------------------

    latest_run = max(
        runs,
        key=lambda run: run.date
    )

    now = datetime.now()

    days_since_last_run = (
        now - latest_run.date
    ).total_seconds() / 86400

    # Prevent small negative values caused by
    # timestamp differences.
    days_since_last_run = max(
        days_since_last_run,
        0
    )

    # --------------------------------
    # Base score
    # --------------------------------

    score = 70
    reasons = []

    # --------------------------------
    # Training-load signal
    # --------------------------------

    training_status = training_load.get(
        "status"
    )

    if training_status == "rapid_increase":

        score -= 25

        reasons.append(
            "Recent training volume increased sharply."
        )

    elif training_status == "increasing":

        score -= 10

        reasons.append(
            "Recent training volume is increasing."
        )

    elif training_status == "decreasing":

        score += 5

        reasons.append(
            "Recent training volume has decreased."
        )

    elif training_status == "stable":

        reasons.append(
            "Recent training volume is relatively stable."
        )

    # --------------------------------
    # Time since last run
    # --------------------------------

    if days_since_last_run < 1:

        score -= 20

        reasons.append(
            "Your most recent run was today."
        )

    elif days_since_last_run < 2:

        score -= 10

        reasons.append(
            "Less than two days have passed "
            "since your most recent run."
        )

    elif days_since_last_run >= 3:

        score += 10

        reasons.append(
            "You have had multiple days without running."
        )

    # --------------------------------
    # Clamp score
    # --------------------------------

    score = max(
        0,
        min(score, 100)
    )

    # --------------------------------
    # Recovery status
    # --------------------------------

    if score >= 70:

        status = "good"

    elif score >= 50:

        status = "moderate"

    else:

        status = "low"

    # --------------------------------
    # Return
    # --------------------------------

    return {
        "status": status,
        "score": score,
        "days_since_last_run": round(
            days_since_last_run,
            1
        ),
        "reason": reasons
    }