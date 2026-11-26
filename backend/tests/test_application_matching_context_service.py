
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from app.ai.services.application_matching_context_service import (
    MatchingApplicationNotFound,
    get_application_matching_context,
)
from app.ai.services.candidate_context_service import (
    CandidateProfileAccessDenied,
)


class TestApplicationMatchingContextService(unittest.TestCase):

    def test_application_links_correct_candidate_and_position(self):
        db = Mock()

        db.get.return_value = SimpleNamespace(
            id=11,
            user_id=5,
            profile_id=2,
            position_id=18,
            status="DRAFT",
        )

        candidate = SimpleNamespace(
            profile_id=2,
            user_id=5,
        )
        position = SimpleNamespace(
            position_id=18,
        )

        with (
            patch(
                "app.ai.services."
                "application_matching_context_service."
                "get_candidate_academic_context",
                return_value=candidate,
            ) as candidate_loader,
            patch(
                "app.ai.services."
                "application_matching_context_service."
                "get_position_context",
                return_value=position,
            ) as position_loader,
        ):
            result = get_application_matching_context(
                db,
                application_id=11,
            )

        self.assertEqual(result.application_id, 11)
        self.assertEqual(result.user_id, 5)
        self.assertEqual(result.application_status, "DRAFT")
        self.assertEqual(result.candidate.profile_id, 2)
        self.assertEqual(result.position.position_id, 18)

        candidate_loader.assert_called_once_with(
            db,
            profile_id=2,
            expected_user_id=5,
        )
        position_loader.assert_called_once_with(
            db,
            position_id=18,
        )

    def test_missing_application_is_rejected(self):
        db = Mock()
        db.get.return_value = None

        with self.assertRaises(MatchingApplicationNotFound):
            get_application_matching_context(
                db,
                application_id=999,
            )

    def test_invalid_application_id_is_rejected(self):
        db = Mock()

        with self.assertRaises(ValueError):
            get_application_matching_context(
                db,
                application_id=0,
            )

        db.get.assert_not_called()

    def test_wrong_profile_owner_is_rejected(self):
        db = Mock()
        db.get.return_value = SimpleNamespace(
            id=11,
            user_id=5,
            profile_id=2,
            position_id=18,
            status="DRAFT",
        )

        with patch(
            "app.ai.services."
            "application_matching_context_service."
            "get_candidate_academic_context",
            side_effect=CandidateProfileAccessDenied(
                "Ownership mismatch"
            ),
        ):
            with self.assertRaises(
                CandidateProfileAccessDenied
            ):
                get_application_matching_context(
                    db,
                    application_id=11,
                )


if __name__ == "__main__":
    unittest.main()
