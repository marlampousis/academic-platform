
import unittest
from types import SimpleNamespace
from unittest.mock import Mock

from app.academic_positions.models import AcademicPosition

from app.ai.services.position_context_service import (
    PositionNotFound,
    PositionContextError,
    get_position_context,
)


class TestPositionContextService(unittest.TestCase):

    def create_db(self, position):
        db = Mock()
        db.get.return_value = position
        return db

    def test_existing_position_is_loaded(self):
        position = SimpleNamespace(
            id=10,
            title="Assistant Professor in AI",
            field_of_study="Artificial Intelligence",
            description="Applicants must hold a PhD.",
        )

        db = self.create_db(position)

        context = get_position_context(
            db,
            position_id=10,
        )

        self.assertEqual(context.position_id, 10)
        self.assertEqual(
            context.field_of_study,
            "Artificial Intelligence",
        )

        db.get.assert_called_once_with(
            AcademicPosition,
            10,
        )

    def test_missing_position_is_rejected(self):
        db = self.create_db(None)

        with self.assertRaises(PositionNotFound):
            get_position_context(
                db,
                position_id=999,
            )

    def test_empty_description_is_rejected(self):
        position = SimpleNamespace(
            id=10,
            title="Assistant Professor",
            field_of_study="Computer Science",
            description="",
        )

        db = self.create_db(position)

        with self.assertRaises(PositionContextError):
            get_position_context(
                db,
                position_id=10,
            )

    def test_invalid_id_is_rejected(self):
        db = self.create_db(None)

        with self.assertRaises(ValueError):
            get_position_context(
                db,
                position_id=0,
            )

        db.get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
