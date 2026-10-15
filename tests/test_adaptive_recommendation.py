from app.services.adaptive_recommendation import (
    generate_adaptive_recommendation,
)


def get_base_recommendation():
    return {
        "workout_type": "easy_run",
        "distance_km": 6,
        "intensity": "easy",
    }


def test_low_recovery_recommends_rest():
    result = generate_adaptive_recommendation(
        base_recommendation=get_base_recommendation(),
        workout_analysis=None,
        training_load={"status": "stable"},
        recovery={
            "status": "low",
            "days_since_last_run": 2,
        },
    )

    assert result["workout_type"] == "recovery"
    assert result["distance_km"] == 0
    assert result["adaptation"] == "reduce"


def test_taper_phase_prevents_progression():
    result = generate_adaptive_recommendation(
        base_recommendation=get_base_recommendation(),
        workout_analysis={"training_signal": "positive"},
        training_load={"status": "stable"},
        recovery={
            "status": "good",
            "days_since_last_run": 2,
        },
        training_phase={"phase": "taper"},
    )

    assert result["distance_km"] == 6
    assert result["adaptation"] == "maintain"


def test_negative_workout_response_reduces_distance():
    result = generate_adaptive_recommendation(
        base_recommendation=get_base_recommendation(),
        workout_analysis={"training_signal": "negative"},
        training_load={"status": "stable"},
        recovery={
            "status": "moderate",
            "days_since_last_run": 2,
        },
    )

    assert result["distance_km"] == 5
    assert result["intensity"] == "easy"
    assert result["adaptation"] == "reduce"


def test_positive_response_allows_small_progression():
    result = generate_adaptive_recommendation(
        base_recommendation=get_base_recommendation(),
        workout_analysis={"training_signal": "positive"},
        training_load={"status": "stable"},
        recovery={
            "status": "good",
            "days_since_last_run": 2,
        },
    )

    assert result["distance_km"] == 7
    assert result["adaptation"] == "progress"


def test_race_day_recommendation_is_preserved():
    race_day_recommendation = {
        "workout_type": "race_day",
        "distance_km": 0,
        "intensity": "none",
    }

    result = generate_adaptive_recommendation(
        base_recommendation=race_day_recommendation,
        workout_analysis={"training_signal": "positive"},
        training_load={"status": "stable"},
        recovery={
            "status": "good",
            "days_since_last_run": 2,
        },
    )

    assert result["workout_type"] == "race_day"
    assert result["distance_km"] == 0
    assert result["adaptation"] == "maintain"
