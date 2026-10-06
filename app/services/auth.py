import os
from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import bcrypt
from jose import jwt
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from app.database.database import get_db
SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "development-secret-change-this"
)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/auth/login"
)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
STRAVA_STATE_EXPIRE_MINUTES = 10


def create_strava_state(user_id: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=STRAVA_STATE_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "purpose": "strava_oauth",
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


def verify_strava_state(state: str) -> int:
    try:
        payload = jwt.decode(
            state,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        if payload.get("purpose") != "strava_oauth":
            raise ValueError("Invalid OAuth state")

        user_id = payload.get("sub")

        if user_id is None:
            raise ValueError("Invalid OAuth state")

        return int(user_id)

    except (JWTError, ValueError, TypeError):
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired Strava OAuth state"
        )

def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


def create_access_token(
    user_id: int
) -> str:

    expires_at = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def get_current_user_id(
    token: str = Depends(oauth2_scheme)
) -> int:

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={
            "WWW-Authenticate": "Bearer"
        }
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise credentials_exception

        return int(user_id)

    except Exception:
        raise credentials_exception

def get_current_runner(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db)
):
    from app.db_models.runner import RunnerDB

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
            detail="Runner profile not found"
        )

    return runner