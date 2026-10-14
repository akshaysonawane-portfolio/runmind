import os
from pathlib import Path
from sqlalchemy import text
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# Project root: runmind/
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Use PostgreSQL in production and SQLite locally.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render may provide postgres:// or postgresql:// URLs.
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://",
            "postgresql+psycopg://",
            1,
        )
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql://",
            "postgresql+psycopg://",
            1,
        )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
    with engine.connect() as conn:
        print(
            "DB_DIAGNOSTIC",
            {
                "database": conn.execute(
                    text("SELECT current_database()")
                ).scalar(),
                "schema": conn.execute(
                    text("SELECT current_schema()")
                ).scalar(),
                "users_table_exists": conn.execute(
                    text("""
                        SELECT to_regclass('public.users')
                    """)
                ).scalar(),
                "akshay_user_exists": conn.execute(
                    text("""
                        SELECT EXISTS(
                            SELECT 1
                            FROM public.users
                            WHERE lower(email) = lower(:email)
                        )
                    """),
                    {"email": "akshay@example.com"},
                ).scalar(),
            },
        )
else:
    # Local development continues using runmind.db.
    DATABASE_PATH = PROJECT_ROOT / "runmind.db"
    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
