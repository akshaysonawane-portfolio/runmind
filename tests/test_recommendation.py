from app.services.recommendation import generate_recommendation


def test_base_phase_returns_easy_run():
    result = generate_recommendation(
        training_load={
            "status": "stable"
        },
        weekly_mileage={
            "week_1": 25,
            "week_2": 25
        },
        longest_run_km=10,
        race_distance_km=21.1,
        training_phase={
            "phase": "base"
        }
    )

    assert result["workout_type"] == "easy_run"
    assert result["intensity"] == "easy"


def test_taper_phase_reduces_workout():
    result = generate_recommendation(
        training_load={
            "status": "stable"
        },
        weekly_mileage={
            "week_1": 30,
            "week_2": 30
        },
        longest_run_km=15,
        race_distance_km=21.1,
        training_phase={
            "phase": "taper"
        }
    )

    assert result["distance_km"] <= 6
    assert result["intensity"] == "easy"


def test_post_race_recommends_recovery():
    result = generate_recommendation(
        training_load={
            "status": "stable"
        },
        weekly_mileage={
            "week_1": 20,
            "week_2": 20
        },
        longest_run_km=10,
        race_distance_km=21.1,
        training_phase={
            "phase": "post_race"
        }
    )

    assert result["workout_type"] == "recovery"

def test_race_in_three_days_recommends_short_easy_run():
    result = generate_recommendation(
        training_load={"status": "stable", "current_week_km": 30},
        weekly_mileage={"week_1": 30},
        longest_run_km=10,
        race_distance_km=21.1,
        training_phase={
            "phase": "taper",
            "days_to_race": 3
        }
    )

    assert result["workout_type"] == "easy_run"
    assert result["distance_km"] == 3
    assert result["intensity"] == "easy"


def test_race_tomorrow_recommends_rest():
    result = generate_recommendation(
        training_load={"status": "stable", "current_week_km": 30},
        weekly_mileage={"week_1": 30},
        longest_run_km=10,
        race_distance_km=21.1,
        training_phase={
            "phase": "taper",
            "days_to_race": 1
        }
    )

    assert result["workout_type"] == "rest"
    assert result["distance_km"] == 0


def test_race_day_does_not_recommend_training_run():
    result = generate_recommendation(
        training_load={"status": "stable", "current_week_km": 30},
        weekly_mileage={"week_1": 30},
        longest_run_km=10,
        race_distance_km=21.1,
        training_phase={
            "phase": "taper",
            "days_to_race": 0
        }
    )

    assert result["workout_type"] == "race_day"
    assert result["distance_km"] == 0

def test_post_race_recommends_rest_within_two_days():
    result = generate_recommendation(
        training_load={"status": "stable"},
        weekly_mileage={"week_1": 20},
        longest_run_km=10,
        race_distance_km=21.1,
        training_phase={
            "phase": "post_race",
            "days_since_race": 2,
        },
        recovery={"status": "moderate"},
    )

    assert result["workout_type"] == "recovery"
    assert result["distance_km"] == 0
    assert result["intensity"] == "none"


def test_post_race_recommends_short_easy_run_after_three_days():
    result = generate_recommendation(
        training_load={"status": "stable"},
        weekly_mileage={"week_1": 20},
        longest_run_km=10,
        race_distance_km=21.1,
        training_phase={
            "phase": "post_race",
            "days_since_race": 3,
        },
        recovery={"status": "moderate"},
    )

    assert result["workout_type"] == "recovery"
    assert result["distance_km"] == 3
    assert result["intensity"] == "easy"


def test_normal_training_rules_resume_after_seven_days():
    result = generate_recommendation(
        training_load={
            "status": "stable",
            "current_week_km": 20,
        },
        weekly_mileage={"week_1": 20},
        longest_run_km=10,
        race_distance_km=21.1,
        training_phase={
            "phase": "post_race",
            "days_since_race": 8,
        },
        recovery={"status": "moderate"},
    )

    assert result["workout_type"] == "easy_run"
    assert result["distance_km"] == 6