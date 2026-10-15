from datetime import date


def calculate_training_phase(
    race_date,
    current_date=None
):
    if current_date is None:
        current_date = date.today()

    days_to_race = (
        race_date - current_date
    ).days

    weeks_to_race = days_to_race / 7

    if days_to_race < 0:
        phase = "post_race"
    elif weeks_to_race <= 2:
        phase = "taper"
    elif weeks_to_race <= 6:
        phase = "peak"
    elif weeks_to_race <= 12:
        phase = "build"
    else:
        phase = "base"

    return {
        "phase": phase,
        "days_to_race": max(days_to_race, 0),
        "days_since_race": max(-days_to_race, 0),
        "weeks_to_race": round(
            max(weeks_to_race, 0),
            1
        )
    }
