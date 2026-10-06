import os

from urllib.parse import urlencode
from datetime import datetime, timezone

import httpx

from dotenv import load_dotenv


load_dotenv()


STRAVA_CLIENT_ID = os.getenv(
    "STRAVA_CLIENT_ID"
)

STRAVA_CLIENT_SECRET = os.getenv(
    "STRAVA_CLIENT_SECRET"
)

STRAVA_REDIRECT_URI = os.getenv(
    "STRAVA_REDIRECT_URI"
)


STRAVA_AUTH_URL = (
    "https://www.strava.com/oauth/authorize"
)

STRAVA_TOKEN_URL = (
    "https://www.strava.com/oauth/token"
)

STRAVA_ACTIVITIES_URL = (
    "https://www.strava.com/api/v3/athlete/activities"
)


# --------------------------------------------------
# OAuth
# --------------------------------------------------

def get_strava_authorization_url(state: str):

    params = {
        "client_id": STRAVA_CLIENT_ID,
        "response_type": "code",
        "redirect_uri": STRAVA_REDIRECT_URI,
        "approval_prompt": "force",
        "scope": "activity:read",
        "state": state,
    }

    return (
        f"{STRAVA_AUTH_URL}?"
        f"{urlencode(params)}"
    )


def exchange_code_for_token(
    code: str
):

    response = httpx.post(
        STRAVA_TOKEN_URL,
        data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=10.0,
    )

    response.raise_for_status()

    return response.json()


# --------------------------------------------------
# Token refresh
# --------------------------------------------------

def refresh_strava_token(
    refresh_token: str
):

    response = httpx.post(
        STRAVA_TOKEN_URL,
        data={
            "client_id": STRAVA_CLIENT_ID,
            "client_secret": STRAVA_CLIENT_SECRET,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
        timeout=10.0,
    )

    response.raise_for_status()

    return response.json()


def get_valid_strava_access_token(
    connection,
    db
):

    now = int(
        datetime.now(
            timezone.utc
        ).timestamp()
    )

    # Refresh if the token expires
    # within the next 5 minutes.

    token_is_valid = (
        connection.expires_at
        > now + 300
    )

    if token_is_valid:

        return connection.access_token

    token_data = refresh_strava_token(
        connection.refresh_token
    )

    connection.access_token = (
        token_data["access_token"]
    )

    connection.refresh_token = (
        token_data["refresh_token"]
    )

    connection.expires_at = (
        token_data["expires_at"]
    )

    connection.updated_at = (
        datetime.now(
            timezone.utc
        ).replace(tzinfo=None)
    )

    db.commit()

    return connection.access_token


# --------------------------------------------------
# Strava activities
# --------------------------------------------------

def get_strava_activities(
    access_token: str,
    page: int = 1,
    per_page: int = 30
):

    response = httpx.get(
        STRAVA_ACTIVITIES_URL,
        headers={
            "Authorization": (
                f"Bearer {access_token}"
            )
        },
        params={
            "page": page,
            "per_page": per_page
        },
        timeout=10.0
    )

    response.raise_for_status()

    activities = response.json()

    # RunMind currently only imports
    # running activities.

    running_activities = [
        activity
        for activity in activities
        if activity.get("sport_type") in {
            "Run",
            "TrailRun",
            "VirtualRun"
        }
    ]

    return running_activities


# --------------------------------------------------
# Strava → RunMind conversion
# --------------------------------------------------

def convert_strava_activity_to_run(
    activity: dict,
    runner_id: int
):

    distance_km = (
        activity["distance"] / 1000
    )

    duration_minutes = (
        activity["moving_time"] / 60
    )

    average_speed = (
        activity.get("average_speed")
    )

    if (
        average_speed
        and average_speed > 0
    ):

        # meters/second → minutes/km

        average_pace = (
            1000 / average_speed
        ) / 60

    else:

        average_pace = 0

    start_date = (
        activity.get("start_date_local")
        or activity.get("start_date")
    )

    run_date = datetime.fromisoformat(
        start_date.replace(
            "Z",
            "+00:00"
        )
    ).replace(
        tzinfo=None
    )

    return {
        "runner_id": runner_id,

        "strava_activity_id": str(
            activity["id"]
        ),

        "date": run_date,

        "distance_km": round(
            distance_km,
            2
        ),

        "duration_minutes": round(
            duration_minutes,
            2
        ),

        "average_pace": round(
            average_pace,
            2
        ),

        "average_heart_rate": (
            activity.get(
                "average_heartrate"
            )
        ),

        "average_cadence": (
            activity.get(
                "average_cadence"
            )
        ),

        "elevation_gain": (
            activity.get(
                "total_elevation_gain"
            )
        )
    }

def get_strava_connection(
    db,
    runner_id: int
):
    from app.db_models.strava_connection import (
        StravaConnectionDB
    )

    return (
        db.query(StravaConnectionDB)
        .filter(
            StravaConnectionDB.runner_id == runner_id
        )
        .first()
    )