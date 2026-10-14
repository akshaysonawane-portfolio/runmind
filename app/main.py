import httpx

from datetime import datetime, timezone, timedelta

from app.services.auth import get_current_runner

from sqlalchemy.orm import Session

from app.models.race import RaceGoalUpdate

from fastapi import FastAPI, Depends, HTTPException

from fastapi.responses import RedirectResponse

from fastapi.middleware.cors import CORSMiddleware

from app.models.auth import LoginRequest

from app.services.auth import verify_password, create_access_token

from app.database.database import engine, Base, get_db

from app.services.auth import get_current_user_id

from app.models.run_feedback import RunFeedback

from app.models.run import Run

from app.models.runner import Runner, RunnerUpdate

from app.models.race import RaceGoal

from app.models.coach import CoachQuestion

from app.models.workout import Workout

from fastapi.security import OAuth2PasswordRequestForm

from app.db_models.run_feedback import RunFeedbackDB

from app.db_models.runner import RunnerDB

from app.db_models.run import RunDB

from app.db_models.race import RaceDB

from app.db_models.workout import WorkoutDB

from app.db_models.strava_connection import StravaConnectionDB

from app.services.analytics import get_running_analytics

from app.services.training_load import calculate_training_load

from app.services.recommendation import generate_recommendation

from app.services.race_analysis import (

    calculate_recent_average_pace,

    analyze_race_goal

)

from app.services.training_engine import get_training_decision

from app.services.coach_context import get_coach_context

from app.services.ai_coach import generate_coaching_response

from app.services.recovery import calculate_recovery

from app.services.feedback_analysis import analyze_run_feedback

from app.services.workout_analysis import analyze_workout

from app.services.adaptive_recommendation import (

    generate_adaptive_recommendation

)

from app.services.strava import (

    get_strava_authorization_url,

    exchange_code_for_token,

    get_strava_activities,

    convert_strava_activity_to_run,

    get_valid_strava_access_token,

    get_strava_connection

)

from app.models.auth import RegisterRequest

from app.db_models.user import UserDB

from app.services.auth import hash_password

# ---------------------------------------------------------

# DATABASE

# ---------------------------------------------------------

Base.metadata.create_all(bind=engine)

# ---------------------------------------------------------

# AUTHORIZATION HELPER

# ---------------------------------------------------------

def get_authorized_runner(

    runner_id: int,

    current_user_id: int,

    db: Session

):

    runner = (

        db.query(RunnerDB)

        .filter(

            RunnerDB.id == runner_id,

            RunnerDB.user_id == current_user_id

        )

        .first()

    )

    if not runner:

        raise HTTPException(

            status_code=403,

            detail="Not authorized to access this runner"

        )

    return runner

# ---------------------------------------------------------

# FASTAPI APP

# ---------------------------------------------------------

app = FastAPI(

    title="RunMind",

    description="Adaptive running coach",

    version="0.1.0"

)

# ---------------------------------------------------------

# CORS

# ---------------------------------------------------------

app.add_middleware(

    CORSMiddleware,

    allow_origins=[

        "http://localhost:5173",

        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "https://runmind-eight.vercel.app",

    ],

    allow_credentials=True,

    allow_methods=["*"],

    allow_headers=["*"],

)

# =========================================================

# STRAVA

# =========================================================

@app.get("/strava/connect")

def strava_connect(

    current_user_id: int = Depends(get_current_user_id)

):

    from app.services.auth import create_strava_state

    state = create_strava_state(current_user_id)

    authorization_url = get_strava_authorization_url(

        state=state

    )

    return RedirectResponse(

        url=authorization_url

    )

@app.get("/strava/callback")

def strava_callback(

    code: str | None = None,

    state: str | None = None,

    error: str | None = None,

    db: Session = Depends(get_db)

):

    from app.services.auth import verify_strava_state

    if error:

        raise HTTPException(

            status_code=400,

            detail=f"Strava authorization failed: {error}"

        )

    if not code:

        raise HTTPException(

            status_code=400,

            detail="Authorization code missing."

        )

    if not state:

        raise HTTPException(

            status_code=400,

            detail="OAuth state missing."

        )

    # ---------------------------------------------

    # Recover the RunMind user from OAuth state

    # ---------------------------------------------

    current_user_id = verify_strava_state(state)

    # ---------------------------------------------

    # Find this user's runner profile

    # ---------------------------------------------

    runner = (

        db.query(RunnerDB)

        .filter(

            RunnerDB.user_id == current_user_id

        )

        .first()

    )

    if not runner:

        raise HTTPException(

            status_code=404,

            detail="Runner profile not found."

        )

    runner_id = runner.id

    # ---------------------------------------------

    # Exchange Strava authorization code

    # ---------------------------------------------

    try:

        token_data = exchange_code_for_token(code)

    except httpx.HTTPStatusError as exc:

        raise HTTPException(

            status_code=400,

            detail="Failed to exchange Strava authorization code."

        ) from exc

    # ---------------------------------------------

    # Get Strava athlete

    # ---------------------------------------------

    athlete = token_data.get("athlete", {})

    strava_athlete_id = str(

        athlete["id"]

    )

    # ---------------------------------------------

    # Check existing connection

    # ---------------------------------------------

    existing_connection = (

        db.query(StravaConnectionDB)

        .filter(

            StravaConnectionDB.runner_id == runner_id

        )

        .first()

    )

    now = datetime.now(

        timezone.utc

    ).replace(

        tzinfo=None

    )

    if existing_connection:

        existing_connection.strava_athlete_id = (

            strava_athlete_id

        )

        existing_connection.access_token = (

            token_data["access_token"]

        )

        existing_connection.refresh_token = (

            token_data["refresh_token"]

        )

        existing_connection.expires_at = (

            token_data["expires_at"]

        )

        existing_connection.scope = (

            token_data.get("scope", "")

        )

        existing_connection.updated_at = now

    else:

        connection = StravaConnectionDB(

            runner_id=runner_id,

            strava_athlete_id=strava_athlete_id,

            access_token=token_data["access_token"],

            refresh_token=token_data["refresh_token"],

            expires_at=token_data["expires_at"],

            scope=token_data.get("scope", ""),

            created_at=now,

            updated_at=now

        )

        db.add(connection)

    db.commit()

    return {

        "message": "Strava connected successfully",

        "athlete": {

            "id": athlete.get("id"),

            "firstname": athlete.get("firstname"),

            "lastname": athlete.get("lastname")

        },

        "scope": token_data.get("scope")

    }

@app.get("/strava/activities")
def strava_activities(
    runner_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    get_authorized_runner(runner_id, current_user_id, db)
    connection = get_strava_connection(db=db, runner_id=runner_id)
    if not connection:
        raise HTTPException(status_code=401, detail="Strava is not connected.")
    try:
        access_token = get_valid_strava_access_token(connection=connection, db=db)
        activities = get_strava_activities(
            access_token=access_token, page=1, per_page=30
        )
    except httpx.HTTPStatusError as exc:
        print(
            "STRAVA_SYNC_DIAGNOSTIC",
            {
                "status_code": exc.response.status_code,
                "response_body": exc.response.text[:500],
            },
        )
        raise HTTPException(
            status_code=400,
            detail="Strava request failed. Check backend logs.",
        ) from exc
    return {"count": len(activities), "activities": activities}

@app.post("/strava/sync")
def sync_strava_activities(
    runner_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    get_authorized_runner(runner_id, current_user_id, db)
    connection = get_strava_connection(db=db, runner_id=runner_id)
    if not connection:
        raise HTTPException(status_code=401, detail="Strava is not connected.")
    try:
        access_token = get_valid_strava_access_token(connection=connection, db=db)
        activities = get_strava_activities(
            access_token=access_token, page=1, per_page=30
        )
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=exc.response.status_code,
            detail="Failed to fetch activities from Strava.",
        ) from exc

    imported = 0
    skipped = 0
    for activity in activities:
        strava_activity_id = str(activity["id"])
        existing_run = db.query(RunDB).filter(
            RunDB.strava_activity_id == strava_activity_id
        ).first()
        if existing_run:
            skipped += 1
            continue
        run_data = convert_strava_activity_to_run(
            activity=activity, runner_id=runner_id
        )
        run_data["source"] = "strava"
        db.add(RunDB(**run_data))
        imported += 1

    db.commit()
    return {
        "runner_id": runner_id,
        "activities_found": len(activities),
        "imported": imported,
        "skipped": skipped,
    }

@app.get("/")

def root():

    return {

        "message": "Welcome to RunMind 🏃"

    }

@app.get("/health")

def health():

    return {

        "status": "healthy"

    }



# =========================================================

# RUNNERS

# =========================================================

@app.post("/runners")
def create_runner(
    runner: Runner,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # A runner profile must always be associated with the authenticated user.
    existing_runner = db.query(RunnerDB).filter(
        RunnerDB.user_id == current_user_id
    ).first()
    if existing_runner:
        raise HTTPException(
            status_code=409,
            detail="A runner profile already exists for this user.",
        )

    db_runner = RunnerDB(
        user_id=current_user_id,
        name=runner.name,
        age=runner.age,
        weekly_mileage=runner.weekly_mileage,
        runs_per_week=runner.runs_per_week,
    )
    db.add(db_runner)
    db.commit()
    db.refresh(db_runner)
    return db_runner

@app.put("/runners/{runner_id}")

def update_runner(

    runner_id: int,

    request: RunnerUpdate,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    runner = get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    runner.name = request.name

    runner.age = request.age

    runner.weekly_mileage = request.weekly_mileage

    runner.runs_per_week = request.runs_per_week

    db.commit()

    db.refresh(runner)

    return {

        "message": "Runner profile updated successfully",

        "runner_id": runner.id,

        "user_id": runner.user_id,

        "name": runner.name,

        "age": runner.age,

        "weekly_mileage": runner.weekly_mileage,

        "runs_per_week": runner.runs_per_week

    }

# =========================================================

# RUN LIST

# =========================================================

@app.get("/runners/{runner_id}/runs")

def get_runs(

    runner_id: int,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    runner = (

        db.query(RunnerDB)

        .filter(

            RunnerDB.id == runner_id,

            RunnerDB.user_id == current_user_id

        )

        .first()

    )

    if not runner:

        raise HTTPException(

            status_code=403,

            detail="Not authorized to access this runner"

        )

    # Keep your existing runs query here

    runs = (

        db.query(RunDB)

        .filter(

            RunDB.runner_id == runner_id,

            # RunDB.source == "strava"

        )

        .order_by(

            RunDB.date.desc()

        )

        .limit(10)

        .all()

    )

    return [

        {

            "id": run.id,

            "date": run.date,

            "distance_km": run.distance_km,

            "duration_minutes": run.duration_minutes,

            "average_pace": run.average_pace,

            "average_heart_rate": run.average_heart_rate,

            "average_cadence": run.average_cadence,

            "elevation_gain": run.elevation_gain,

        }

        for run in runs

    ]

# =========================================================

# SINGLE RUN

# =========================================================

@app.get("/runners/{runner_id}/runs/{run_id}")

def get_runner_run(

    runner_id: int,

    run_id: int,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    run = (

        db.query(RunDB)

        .filter(

            RunDB.id == run_id,

            RunDB.runner_id == runner_id,

            # RunDB.source == "strava"

        )

        .first()

    )

    if not run:

        raise HTTPException(

            status_code=404,

            detail="Run not found"

        )

    return {

        "id": run.id,

        "date": run.date,

        "distance_km": run.distance_km,

        "duration_minutes": run.duration_minutes,

        "average_pace": run.average_pace,

        "average_heart_rate": run.average_heart_rate,

        "average_cadence": run.average_cadence,

        "elevation_gain": run.elevation_gain,

    }

@app.get("/runners/{runner_id}/runs/{run_id}/analysis")

def get_run_analysis(

    runner_id: int,

    run_id: int,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    # -------------------------------------------------

    # Find the selected Strava run

    # -------------------------------------------------

    run = (

        db.query(RunDB)

        .filter(

            RunDB.id == run_id,

            RunDB.runner_id == runner_id,

            # RunDB.source == "strava"

        )

        .first()

    )

    if not run:

        raise HTTPException(

            status_code=404,

            detail="Run not found"

        )

    # -------------------------------------------------

    # Running analytics

    # -------------------------------------------------

    analytics = get_running_analytics(

        runner_id=runner_id,

        db=db

    )

    # -------------------------------------------------

    # Training load

    # -------------------------------------------------

    training_load = calculate_training_load(

        weekly_mileage=analytics["weekly_mileage"],

        weekly_run_counts=analytics["weekly_run_counts"]

    )

    # -------------------------------------------------

    # Get all runs for recovery

    # -------------------------------------------------

    runs = (

        db.query(RunDB)

        .filter(

            RunDB.runner_id == runner_id

        )

        .order_by(

            RunDB.date.desc()

        )

        .all()

    )

    recovery = calculate_recovery(

        runs=runs,

        training_load=training_load

    )

    # -------------------------------------------------

    # Race goal

    # -------------------------------------------------

    race = (

        db.query(RaceDB)

        .filter(

            RaceDB.runner_id == runner_id

        )

        .order_by(

            RaceDB.race_date.asc()

        )

        .first()

    )

    race_goal = None

    if race:

        race_goal = {

            "race_name": race.race_name,

            "distance_km": race.distance_km,

            "race_date": str(race.race_date),

            "target_time_minutes": race.target_time_minutes

        }

    # -------------------------------------------------

    # Build response

    # -------------------------------------------------

    result = {

        "run": {

            "id": run.id,

            "date": run.date,

            "distance_km": run.distance_km,

            "duration_minutes": run.duration_minutes,

            "average_pace": run.average_pace,

            "average_heart_rate": run.average_heart_rate,

            "average_cadence": run.average_cadence,

            "elevation_gain": run.elevation_gain

        },

        "training_load": training_load,

        "recovery": recovery,

        "race_goal": race_goal

    }

    print("RUN ANALYSIS RESULT:")

    print(result)

    return result

@app.post("/runners/{runner_id}/runs/{run_id}/coach-analysis")

def get_run_coach_analysis(

    runner_id: int,

    run_id: int,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    # -------------------------------------------------

    # Find selected run

    # -------------------------------------------------

    run = (

        db.query(RunDB)

        .filter(

            RunDB.id == run_id,

            RunDB.runner_id == runner_id,

            # RunDB.source == "strava"

        )

        .first()

    )

    if not run:

        raise HTTPException(

            status_code=404,

            detail="Run not found"

        )

    # -------------------------------------------------

    # Get complete training decision

    # -------------------------------------------------

    training_decision = get_training_decision(

        runner_id=runner_id,

        db=db

    )

    # -------------------------------------------------

    # Add selected run to AI context

    # -------------------------------------------------

    coach_context = {

        **training_decision,

        "selected_run": {

            "id": run.id,

            "date": str(run.date),

            "distance_km": run.distance_km,

            "duration_minutes": run.duration_minutes,

            "average_pace": run.average_pace,

            "average_heart_rate": run.average_heart_rate,

            "average_cadence": run.average_cadence,

            "elevation_gain": run.elevation_gain

        }

    }

    # -------------------------------------------------

    # Ask AI to explain this specific run

    # -------------------------------------------------

    response = generate_coaching_response(

        coach_context=coach_context,

        user_question=(

            "Analyze this specific run for me. "

            "Explain what this run tells me about my "

            "current training, recovery, and race goal. "

            "Use only the provided data. "

            "Do not invent metrics. "

            "Keep the explanation concise and practical."

        )

    )

    return {

        "run_id": run.id,

        "analysis": response

    }

    # -------------------------------------------------

    # Get training analytics

    # -------------------------------------------------

    analytics = get_running_analytics(

        runner_id=runner_id,

        db=db

    )

    # -------------------------------------------------

    # Calculate training load

    # -------------------------------------------------

    training_load = calculate_training_load(

        weekly_mileage=analytics["weekly_mileage"],

        weekly_run_counts=analytics["weekly_run_counts"]

    )

    # -------------------------------------------------

    # Get recent runs for recovery

    # -------------------------------------------------

    runs = (

        db.query(RunDB)

        .filter(

            RunDB.runner_id == runner_id

        )

        .order_by(

            RunDB.date.desc()

        )

        .all()

    )

    recovery = calculate_recovery(

        runs=runs,

        training_load=training_load

    )

    # -------------------------------------------------

    # Get race goal

    # -------------------------------------------------

    race = (

        db.query(RaceDB)

        .filter(

            RaceDB.runner_id == runner_id

        )

        .order_by(

            RaceDB.race_date.asc()

        )

        .first()

    )

    race_goal = None

    if race:

        race_goal = {

            "race_name": race.race_name,

            "distance_km": race.distance_km,

            "race_date": str(race.race_date),

            "target_time_minutes": race.target_time_minutes

        }

    # -------------------------------------------------

    # Return structured analysis context

    # -------------------------------------------------

    return {

        "run": {

            "id": run.id,

            "date": run.date,

            "distance_km": run.distance_km,

            "duration_minutes": run.duration_minutes,

            "average_pace": run.average_pace,

            "average_heart_rate": run.average_heart_rate,

            "average_cadence": run.average_cadence,

            "elevation_gain": run.elevation_gain

        },

        "training_load": training_load,

        "recovery": recovery,

        "race_goal": race_goal

    }

# =========================================================

# RACES

# =========================================================

@app.post("/races")
def create_race(
    race: RaceGoal,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    get_authorized_runner(
        runner_id=race.runner_id,
        current_user_id=current_user_id,
        db=db,
    )
    db_race = RaceDB(
        runner_id=race.runner_id,
        race_name=race.race_name,
        distance_km=race.distance_km,
        race_date=race.race_date,
        target_time_minutes=race.target_time_minutes,
    )
    db.add(db_race)
    db.commit()
    db.refresh(db_race)
    return db_race

@app.post("/runs")
def create_run(
    run: Run,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    get_authorized_runner(
        runner_id=run.runner_id,
        current_user_id=current_user_id,
        db=db,
    )
    if run.workout_id is not None:
        workout = db.query(WorkoutDB).filter(
            WorkoutDB.id == run.workout_id,
            WorkoutDB.runner_id == run.runner_id,
        ).first()
        if not workout:
            raise HTTPException(
                status_code=400,
                detail="Workout does not belong to this runner.",
            )

    db_run = RunDB(
        runner_id=run.runner_id,
        workout_id=run.workout_id,
        date=run.date,
        distance_km=run.distance_km,
        duration_minutes=run.duration_minutes,
        average_pace=run.average_pace,
        average_heart_rate=run.average_heart_rate,
        average_cadence=run.average_cadence,
        elevation_gain=run.elevation_gain,
    )
    db.add(db_run)
    db.commit()
    db.refresh(db_run)
    return db_run

@app.post("/runs/bulk")
def create_runs_bulk(
    runs: list[Run],
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    # Validate every item before inserting any rows, so a mixed-owner batch
    # cannot partially write data.
    for run in runs:
        get_authorized_runner(
            runner_id=run.runner_id,
            current_user_id=current_user_id,
            db=db,
        )
        if run.workout_id is not None:
            workout = db.query(WorkoutDB).filter(
                WorkoutDB.id == run.workout_id,
                WorkoutDB.runner_id == run.runner_id,
            ).first()
            if not workout:
                raise HTTPException(
                    status_code=400,
                    detail="Workout does not belong to this runner.",
                )

    db_runs = [
        RunDB(
            runner_id=run.runner_id,
            workout_id=run.workout_id,
            date=run.date,
            distance_km=run.distance_km,
            duration_minutes=run.duration_minutes,
            average_pace=run.average_pace,
            average_heart_rate=run.average_heart_rate,
            average_cadence=run.average_cadence,
            elevation_gain=run.elevation_gain,
        )
        for run in runs
    ]
    db.add_all(db_runs)
    db.commit()
    return {"message": "Runs added successfully", "count": len(db_runs)}

@app.get("/runners/{runner_id}/analytics")

def get_analytics(

    runner_id: int,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    return get_running_analytics(

        runner_id=runner_id,

        db=db

    )

# =========================================================

# TRAINING LOAD

# =========================================================

@app.get("/runners/{runner_id}/training-load")

def get_training_load(

    runner_id: int,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    analytics = get_running_analytics(

        runner_id=runner_id,

        db=db

    )

    return calculate_training_load(

        analytics["weekly_mileage"],

        weekly_run_counts=analytics["weekly_run_counts"]

    )

# =========================================================

# RECOMMENDATION

# =========================================================

@app.get("/runners/{runner_id}/recommendation")

def get_recommendation(

    runner_id: int,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    runner = (

        db.query(RunnerDB)

        .filter(

            RunnerDB.id == runner_id,

            RunnerDB.user_id == current_user_id

        )

        .first()

    )

    if not runner:

        raise HTTPException(

            status_code=403,

            detail="Not authorized to access this runner"

        )

    return get_training_decision(

        runner_id=runner_id,

        db=db

    )

# =========================================================

# RACE ANALYSIS

# =========================================================

@app.get("/runners/{runner_id}/race-analysis")

def get_race_analysis(

    runner_id: int,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    race = (

        db.query(RaceDB)

        .filter(

            RaceDB.runner_id == runner_id

        )

        .order_by(

            RaceDB.race_date.asc()

        )

        .first()

    )

    if not race:

        return {

            "status": "no_race_goal",

            "message": "No race goal found for this runner."

        }

    # Race analysis should use all recorded runs, including

    # manually created runs. The general analytics service currently

    # focuses on Strava runs, but race analysis must also work before

    # Strava is connected.

    twenty_eight_days_ago = (

        datetime.utcnow() - timedelta(days=28)

    )

    recent_training_runs = (

        db.query(RunDB)

        .filter(

            RunDB.runner_id == runner_id,

            RunDB.date >= twenty_eight_days_ago

        )

        .order_by(

            RunDB.date.desc()

        )

        .all()

    )

    recent_runs = recent_training_runs[:5]

    recent_average_pace = calculate_recent_average_pace(

        recent_runs

    )

    if recent_training_runs:

        longest_recent_run_km = max(

            run.distance_km

            for run in recent_training_runs

        )

        distance_last_28_days = sum(

            run.distance_km

            for run in recent_training_runs

        )

    else:

        longest_recent_run_km = 0

        distance_last_28_days = 0

    average_weekly_mileage = (

        distance_last_28_days / 4

    )

    analysis = analyze_race_goal(

        race_distance_km=race.distance_km,

        target_time_minutes=race.target_time_minutes,

        recent_average_pace=recent_average_pace,

        longest_recent_run_km=longest_recent_run_km,

        average_weekly_mileage=average_weekly_mileage

    )

    return {

        "race": {

            "name": race.race_name,

            "distance_km": race.distance_km,

            "race_date": race.race_date,

            "target_time_minutes": race.target_time_minutes

        },

        "analysis": analysis

    }

# =========================================================

# COACH CONTEXT

# =========================================================

@app.get("/runners/{runner_id}/coach-context")

def get_coach_context_endpoint(

    runner_id: int,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    return get_coach_context(

        runner_id=runner_id,

        db=db

    )

# =========================================================

# AI COACH

# =========================================================

@app.post("/runners/{runner_id}/ask")

def ask_coach(

    runner_id: int,

    question: CoachQuestion,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    training_decision = get_training_decision(

        runner_id=runner_id,

        db=db

    )

    response = generate_coaching_response(

        coach_context=training_decision,

        user_question=question.question

    )

    return {

        "runner_id": runner_id,

        "question": question.question,

        "response": response

    }

# =========================================================

# RECOVERY

# =========================================================

@app.get("/runners/{runner_id}/recovery")

def get_recovery(

    runner_id: int,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    runs = (

        db.query(RunDB)

        .filter(

            RunDB.runner_id == runner_id

        )

        .order_by(

            RunDB.date.desc()

        )

        .all()

    )

    analytics = get_running_analytics(

        runner_id=runner_id,

        db=db

    )

    training_load = calculate_training_load(

        weekly_mileage=analytics["weekly_mileage"],

        weekly_run_counts=analytics["weekly_run_counts"]

    )

    recovery = calculate_recovery(

        runs=runs,

        training_load=training_load

    )

    return recovery

# =========================================================

# RUN FEEDBACK

# =========================================================

@app.post("/runs/{run_id}/feedback")
def add_run_feedback(
    run_id: int,
    feedback: RunFeedback,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    run = db.query(RunDB).filter(RunDB.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    get_authorized_runner(run.runner_id, current_user_id, db)

    db_feedback = RunFeedbackDB(
        run_id=run_id,
        perceived_effort=feedback.perceived_effort,
        felt_good=feedback.felt_good,
    )
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback

@app.get("/runs/{run_id}/feedback")
def get_run_feedback(
    run_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    run = db.query(RunDB).filter(RunDB.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found.")
    get_authorized_runner(run.runner_id, current_user_id, db)

    feedback = (
        db.query(RunFeedbackDB)
        .filter(RunFeedbackDB.run_id == run_id)
        .order_by(RunFeedbackDB.id.desc())
        .first()
    )
    if not feedback:
        return {"status": "not_found", "message": "No feedback found for this run."}
    analysis = analyze_run_feedback(feedback)
    return {
        "run_id": run_id,
        "feedback": {
            "perceived_effort": feedback.perceived_effort,
            "felt_good": feedback.felt_good,
        },
        "analysis": analysis,
    }

@app.post("/workouts")
def create_workout(
    workout: Workout,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    get_authorized_runner(
        runner_id=workout.runner_id,
        current_user_id=current_user_id,
        db=db,
    )
    db_workout = WorkoutDB(
        runner_id=workout.runner_id,
        date=workout.date,
        workout_type=workout.workout_type,
        planned_distance_km=workout.planned_distance_km,
        planned_intensity=workout.planned_intensity,
    )
    db.add(db_workout)
    db.commit()
    db.refresh(db_workout)
    return db_workout

@app.get("/workouts/{workout_id}/analysis")
def get_workout_analysis(
    workout_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    workout = db.query(WorkoutDB).filter(WorkoutDB.id == workout_id).first()
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found.")
    get_authorized_runner(workout.runner_id, current_user_id, db)

    run = (
        db.query(RunDB)
        .filter(
            RunDB.workout_id == workout_id,
            RunDB.runner_id == workout.runner_id,
        )
        .order_by(RunDB.date.desc())
        .first()
    )
    if not run:
        return {
            "status": "pending",
            "message": "No run has been associated with this workout yet.",
        }

    feedback = (
        db.query(RunFeedbackDB)
        .filter(RunFeedbackDB.run_id == run.id)
        .order_by(RunFeedbackDB.id.desc())
        .first()
    )
    if not feedback:
        return {
            "status": "pending_feedback",
            "message": "Run exists but feedback has not been submitted yet.",
        }

    analysis = analyze_workout(workout=workout, run=run, feedback=feedback)
    return {
        "workout_id": workout.id,
        "run_id": run.id,
        "workout": {
            "type": workout.workout_type,
            "planned_distance_km": workout.planned_distance_km,
            "planned_intensity": workout.planned_intensity,
        },
        "run": {
            "distance_km": run.distance_km,
            "duration_minutes": run.duration_minutes,
            "average_pace": run.average_pace,
        },
        "feedback": {
            "perceived_effort": feedback.perceived_effort,
            "felt_good": feedback.felt_good,
        },
        "analysis": analysis,
    }

@app.put("/runners/{runner_id}/race-goal")

def update_race_goal(

    runner_id: int,

    goal: RaceGoalUpdate,

    current_user_id: int = Depends(get_current_user_id),

    db: Session = Depends(get_db)

):

    get_authorized_runner(

        runner_id=runner_id,

        current_user_id=current_user_id,

        db=db

    )

    race = (

        db.query(RaceDB)

        .filter(

            RaceDB.runner_id == runner_id

        )

        .first()

    )

    if not race:

        race = RaceDB(

            runner_id=runner_id

        )

        db.add(race)

    race.race_name = goal.race_name

    race.distance_km = goal.distance_km

    race.race_date = goal.race_date

    race.target_time_minutes = goal.target_time_minutes

    db.commit()

    db.refresh(race)

    return {

        "id": race.id,

        "runner_id": race.runner_id,

        "race_name": race.race_name,

        "distance_km": race.distance_km,

        "race_date": str(race.race_date),

        "target_time_minutes": race.target_time_minutes

    }

@app.post("/auth/register")

def register_user(

    request: RegisterRequest,

    db: Session = Depends(get_db)

):

    # Check if email already exists

    existing_user = (

        db.query(UserDB)

        .filter(UserDB.email == request.email)

        .first()

    )

    if existing_user:

        raise HTTPException(

            status_code=400,

            detail="Email already registered"

        )

    # Hash password

    password_hash = hash_password(

        request.password

    )

    # Create user

    new_user = UserDB(

        email=request.email,

        password_hash=password_hash

    )

    db.add(new_user)

    db.flush()

    # Create runner profile linked to user

    new_runner = RunnerDB(

        user_id=new_user.id,

        name=request.name,

        age=request.age,

        weekly_mileage=0,

        runs_per_week=0

    )

    db.add(new_runner)

    db.commit()

    db.refresh(new_user)

    db.refresh(new_runner)

    return {

        "message": "User registered successfully",

        "user_id": new_user.id,

        "runner_id": new_runner.id,

        "email": new_user.email,

        "name": new_runner.name

    }

@app.post("/auth/login")

def login_user(

    form_data: OAuth2PasswordRequestForm = Depends(),

    db: Session = Depends(get_db)

):

    user = (

        db.query(UserDB)

        .filter(UserDB.email == form_data.username)

        .first()

    )

    print(f"LOGIN_DIAGNOSTIC user_found={user is not None}")

    if not user:

        raise HTTPException(

            status_code=401,

            detail="Invalid email or password"

        )

    password_valid = verify_password(
        form_data.password,
        user.password_hash
    )

    print(f"LOGIN_DIAGNOSTIC password_valid={password_valid}")

    if not password_valid:

        raise HTTPException(

            status_code=401,

            detail="Invalid email or password"

        )

    access_token = create_access_token(

        user_id=user.id

    )

    return {

        "access_token": access_token,

        "token_type": "bearer",

        "user_id": user.id

    }

@app.get("/auth/me")
def get_me(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.query(UserDB).filter(UserDB.id == current_user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"user_id": user.id, "email": user.email}

@app.get("/auth/runner")

def get_my_runner(

    runner: RunnerDB = Depends(get_current_runner)

):

    return {

        "runner_id": runner.id,

        "user_id": runner.user_id,

        "name": runner.name,

        "age": runner.age,

        "weekly_mileage": runner.weekly_mileage,

        "runs_per_week": runner.runs_per_week

    }