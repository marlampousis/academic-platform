
import unittest

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app

from db_setup import (
    isolated_api_client,
    verify_test_database,
)


class TestAPIDatabaseOverride(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Test-only route, registered only in this test process.
        router = APIRouter()

        @router.get("/__integration_test_database")
        def integration_database(
            db: Session = Depends(get_db),
        ):
            name = db.execute(
                text("SELECT current_database()")
            ).scalar_one()

            return {"database": name}

        app.include_router(router)

    def test_api_uses_test_database(self):
        verify_test_database()

        with isolated_api_client() as (client, session):
            response = client.get(
                "/__integration_test_database"
            )

            self.assertEqual(response.status_code, 200)
            self.assertEqual(
                response.json()["database"],
                "academic_platform_test",
            )

    def test_database_session_can_execute_queries(self):
        with isolated_api_client() as (client, session):
            result = session.execute(
                text("SELECT 1")
            ).scalar_one()

            self.assertEqual(result, 1)


if __name__ == "__main__":
    unittest.main()
