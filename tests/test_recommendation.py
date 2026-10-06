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