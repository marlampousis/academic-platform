
import unittest

from sqlalchemy import text

from db_setup import (
    test_engine,
    verify_test_database,
    isolated_test_session,
)


TABLE = "s01_transaction_probe"


class TestTransactionIsolation(unittest.TestCase):

    def test_service_commit_is_rolled_back(self):
        verify_test_database()

        # Ensure the probe name does not already exist.
        with test_engine.connect() as connection:
            existing = connection.execute(
                text("SELECT to_regclass('public.s01_transaction_probe')")
            ).scalar_one()

        self.assertIsNone(
            existing,
            "Safety stop: probe table already exists",
        )

        with isolated_test_session() as session:
            session.execute(
                text("""
                    CREATE TABLE public.s01_transaction_probe (
                        id INTEGER PRIMARY KEY,
                        note TEXT NOT NULL
                    )
                """)
            )

            session.execute(
                text("""
                    INSERT INTO public.s01_transaction_probe (id, note)
                    VALUES (1, 'temporary test record')
                """)
            )

            session.commit()

            count = session.execute(
                text("""
                    SELECT COUNT(*)
                    FROM public.s01_transaction_probe
                """)
            ).scalar_one()

            self.assertEqual(count, 1)

        # The outer rollback must undo even the committed
        # savepoint, including the temporary test table.
        with test_engine.connect() as connection:
            remaining = connection.execute(
                text("SELECT to_regclass('public.s01_transaction_probe')")
            ).scalar_one()

        self.assertIsNone(remaining)

    def test_test_database_remains_accessible(self):
        self.assertEqual(
            verify_test_database(),
            "academic_platform_test",
        )


if __name__ == "__main__":
    unittest.main()
