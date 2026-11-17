
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.orm import sessionmaker

from contextlib import contextmanager
from sqlalchemy.orm import Session

from fastapi.testclient import TestClient
from app.main import app
from app.core.database import get_db

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_TEST = BACKEND_DIR / ".env.test"

values = dotenv_values(ENV_TEST)
DATABASE_URL = values.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("Test DATABASE_URL is missing")

if make_url(DATABASE_URL).database != "academic_platform_test":
    raise RuntimeError(
        "SAFETY STOP: Integration tests must use academic_platform_test"
    )


test_engine = create_engine(DATABASE_URL)

TestSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False,
)


def verify_test_database():
    with test_engine.connect() as connection:
        actual_database = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        if actual_database != "academic_platform_test":
            raise RuntimeError("SAFETY STOP: Wrong database")

        revision = connection.execute(
            text("SELECT version_num FROM alembic_version")
        ).scalar_one()

        if revision != "dea6b094f78b":
            raise RuntimeError(
                f"Unexpected Alembic revision: {revision}"
            )

    return actual_database


@contextmanager
def isolated_test_session():
    """
    Run database operations inside a transaction that
    is always rolled back, even when a service calls commit().
    """
    verify_test_database()

    connection = test_engine.connect()
    outer_transaction = None
    session = None

    try:
        outer_transaction = connection.begin()

        session = Session(
            bind=connection,
            autoflush=False,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        yield session

    finally:
        try:
            if session is not None:
                session.close()
        finally:
            try:
                if (
                    outer_transaction is not None
                    and outer_transaction.is_active
                ):
                    outer_transaction.rollback()
            finally:
                connection.close()


@contextmanager
def isolated_api_client():
    """
    Provide a FastAPI TestClient whose get_db dependency
    uses the isolated PostgreSQL test transaction.

    All database changes are rolled back after the test.
    """
    verify_test_database()

    with isolated_test_session() as session:

        def override_get_db():
            yield session

        previous_override = app.dependency_overrides.get(get_db)

        app.dependency_overrides[get_db] = override_get_db

        try:
            with TestClient(app) as client:
                yield client, session

        finally:
            if previous_override is None:
                app.dependency_overrides.pop(get_db, None)
            else:
                app.dependency_overrides[get_db] = previous_override
