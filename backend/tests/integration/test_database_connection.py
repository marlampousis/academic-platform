
import unittest

from sqlalchemy import inspect

from db_setup import (
    test_engine,
    verify_test_database,
)


class TestPostgreSQLConnection(unittest.TestCase):

    def test_correct_database(self):
        database_name = verify_test_database()

        self.assertEqual(
            database_name,
            "academic_platform_test",
        )

    def test_core_tables_exist(self):
        verify_test_database()

        inspector = inspect(test_engine)
        existing_tables = set(inspector.get_table_names())

        required_tables = {
            "users",
            "academic_positions",
            "applications",
            "evaluation_committees",
            "committee_members",
            "committee_applications",
            "evaluation_criteria",
            "evaluation_scores",
            "evaluation_reports",
            "evaluation_results",
        }

        self.assertTrue(
            required_tables.issubset(existing_tables),
            f"Missing tables: {required_tables - existing_tables}",
        )


if __name__ == "__main__":
    unittest.main()
