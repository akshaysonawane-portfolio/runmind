from datetime import date

from app.services.training_phase import calculate_training_phase


def test_base_phase():
    result = calculate_training_phase(
        race_date=date(2027, 1, 1),
        current_date=date(2026, 9, 27)
    )

    assert result["phase"] == "base"


def test_build_phase():
    result = calculate_training_phase(
        race_date=date(2026, 12, 15),
        current_date=date(2026, 9, 27)
    )

    assert result["phase"] == "build"


def test_peak_phase():
    result = calculate_training_phase(
        race_date=date(2026, 11, 5),
        current_date=date(2026, 9, 27)
    )

    assert result["phase"] == "peak"


def test_taper_phase():
    result = calculate_training_phase(
        race_date=date(2026, 10, 5),
        current_date=date(2026, 9, 27)
    )

    assert result["phase"] == "taper"


def test_post_race():
    result = calculate_training_phase(
        race_date=date(2026, 9, 20),
        current_date=date(2026, 9, 27)
    )

    assert result["phase"] == "post_race"