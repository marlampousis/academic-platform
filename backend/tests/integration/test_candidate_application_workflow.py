
import unittest
from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch
from uuid import uuid4

from sqlalchemy import text

from app.core.security import hash_password
from db_setup import isolated_api_client, test_engine


class TestCandidateApplicationWorkflow(unittest.TestCase):

    def insert(self, session, sql, **params):
        return session.execute(
            text(sql),
            params,
        ).scalar_one()

    def test_candidate_to_eligibility_workflow(self):
        suffix = uuid4().hex[:12]
        candidate_email = f"candidate-{suffix}@example.com"
        admin_email = f"admin-{suffix}@example.com"
        password = "TestPassword123!"

        with (
            patch("app.applications.router.send_email"),
            patch("app.application_reviews.router.send_email"),
            patch("app.applications.router.notify_application_submitted"),
            patch("app.application_reviews.router.notify_application_status_changed"),
            patch("app.committee_applications.router.send_email"),
            patch("app.committee_applications.router.notify_application_assigned"),
            patch("app.committee_applications.router.notify_evaluation_started"),
            patch("app.evaluation_results.router.send_email"),
            patch("app.evaluation_results.router.notify_evaluation_completed"),
            patch("app.evaluation_results.router.notify_final_decision"),
            isolated_api_client() as (client, db),
        ):
            # 1. Create roles.
            
            # 1. Reuse existing roles or create missing roles.
            candidate_role = self.insert(
                db,
                """
                INSERT INTO roles (code, name)
                VALUES ('CANDIDATE', 'Candidate')
                ON CONFLICT (code)
                DO UPDATE SET code = EXCLUDED.code
                RETURNING id
                """,
            )

            admin_role = self.insert(
                db,
                """
                INSERT INTO roles (code, name)
                VALUES ('SUPER_ADMIN', 'Super Admin')
                ON CONFLICT (code)
                DO UPDATE SET code = EXCLUDED.code
                RETURNING id
                """,
            )

            reviewer_role = self.insert(
                db,
                """
                INSERT INTO roles (code, name)
                VALUES ('REVIEWER', 'Reviewer')
                ON CONFLICT (code)
                DO UPDATE SET code = EXCLUDED.code
                RETURNING id
                """,
            )
            # 2. Create real users.
            hashed_password = hash_password(password)

            candidate_id = self.insert(
                db,
                """
                INSERT INTO users (
                    first_name, last_name, email,
                    hashed_password, role_id
                )
                VALUES (
                    'Test', 'Candidate', :email,
                    :password, :role_id
                )
                RETURNING id
                """,
                email=candidate_email,
                password=hashed_password,
                role_id=candidate_role,
            )

            admin_id = self.insert(
                db,
                """
                INSERT INTO users (
                    first_name, last_name, email,
                    hashed_password, role_id
                )
                VALUES (
                    'Test', 'Admin', :email,
                    :password, :role_id
                )
                RETURNING id
                """,
                email=admin_email,
                password=hashed_password,
                role_id=admin_role,
            )

            reviewer_email = f"reviewer-{suffix}@example.com"

            reviewer_id = self.insert(
                db,
                """
                INSERT INTO users (
                    first_name,
                    last_name,
                    email,
                    hashed_password,
                    role_id
                )
                VALUES (
                    'Test',
                    'Reviewer',
                    :email,
                    :password,
                    :role_id
                )
                RETURNING id
                """,
                email=reviewer_email,
                password=hashed_password,
                role_id=reviewer_role,
            )
            
            
            reviewer_2_email = f"reviewer2-{suffix}@example.com"

            reviewer_2_id = self.insert(
                db,
                """
                INSERT INTO users (
                    first_name, last_name, email,
                    hashed_password, role_id
                )
                VALUES (
                    'Second', 'Reviewer', :email,
                    :password, :role_id
                )
                RETURNING id
                """,
                email=reviewer_2_email,
                password=hashed_password,
                role_id=reviewer_role,
            )

            # 3. Create academic reference records.
            institution_id = self.insert(
                db,
                """
                INSERT INTO institutions (
                    name_el, institution_type,
                    country, is_active
                )
                VALUES (
                    'Test University',
                    'UNIVERSITY', 'Greece', TRUE
                )
                RETURNING id
                """,
            )

            department_id = self.insert(
                db,
                """
                INSERT INTO departments (
                    institution_id, name_el,
                    department_type, is_active
                )
                VALUES (
                    :institution_id,
                    'Test Economics Department',
                    'ACADEMIC', TRUE
                )
                RETURNING id
                """,
                institution_id=institution_id,
            )

            rank_id = self.insert(
                db,
                """
                INSERT INTO academic_ranks (name, level)
                VALUES ('Test Professor', 1)
                RETURNING id
                """,
            )

            employment_id = self.insert(
                db,
                """
                INSERT INTO employment_types (code, name)
                VALUES ('FULL_TIME', 'Full Time')
                RETURNING id
                """,
            )

            open_status_id = self.insert(
                db,
                """
                INSERT INTO position_statuses (code, name)
                VALUES ('OPEN', 'Open')
                RETURNING id
                """,
            )

            # 4. Create the candidate academic profile.
            profile_id = self.insert(
                db,
                """
                INSERT INTO academic_profiles (
                    user_id, specialization
                )
                VALUES (
                    :user_id, 'Finance and Economics'
                )
                RETURNING id
                """,
                user_id=candidate_id,
            )

            # 5. Create an open academic position.
            position_id = self.insert(
                db,
                """
                INSERT INTO academic_positions (
                    institution_id, department_id,
                    created_by, title,
                    academic_rank_id, field_of_study,
                    description, employment_type_id,
                    application_start_date,
                    application_deadline,
                    positions_available,
                    position_status_id,
                    created_at, updated_at
                )
                VALUES (
                    :institution_id, :department_id,
                    :created_by, 'Test Lecturer Position',
                    :rank_id, 'Finance',
                    'Integration test position',
                    :employment_id, :start_date,
                    :deadline, 1, :status_id,
                    NOW(), NOW()
                )
                RETURNING id
                """,
                institution_id=institution_id,
                department_id=department_id,
                created_by=admin_id,
                rank_id=rank_id,
                employment_id=employment_id,
                start_date=date.today() - timedelta(days=1),
                deadline=date.today() + timedelta(days=30),
                status_id=open_status_id,
            )

            db.commit()

            # 6. Authenticate both users through the API.
            def login(email):
                response = client.post(
                    "/auth/login",
                    json={
                        "email": email,
                        "password": password,
                    },
                )
                self.assertEqual(
                    response.status_code, 200,
                    response.text,
                )
                return {
                    "Authorization": (
                        "Bearer "
                        + response.json()["access_token"]
                    )
                }

            candidate_headers = login(candidate_email)
            admin_headers = login(admin_email)
            reviewer_headers = login(reviewer_email)
            reviewer_2_headers = login(reviewer_2_email)

            # 7. Candidate creates an application.
            response = client.post(
                "/applications/",
                json={"position_id": position_id},
                headers=candidate_headers,
            )

            self.assertEqual(
                response.status_code, 201,
                response.text,
            )
            self.assertEqual(response.json()["status"], "DRAFT")
            self.assertEqual(response.json()["profile_id"], profile_id)

            application_id = response.json()["id"]

            # 8. Duplicate applications must be blocked.
            duplicate = client.post(
                "/applications/",
                json={"position_id": position_id},
                headers=candidate_headers,
            )
            self.assertEqual(duplicate.status_code, 409)

            # 9. Validate and submit the application.
            validation = client.get(
                f"/applications/{application_id}/validation",
                headers=candidate_headers,
            )
            self.assertEqual(validation.status_code, 200)
            self.assertTrue(validation.json()["can_submit"])

            submitted = client.post(
                f"/applications/{application_id}/submit",
                headers=candidate_headers,
            )
            self.assertEqual(submitted.status_code, 200, submitted.text)
            self.assertEqual(
                submitted.json()["status"],
                "SUBMITTED",
            )

            # 10. Candidate must not have admin permissions.
            forbidden = client.patch(
                f"/admin/applications/{application_id}/status",
                json={"status": "UNDER_REVIEW"},
                headers=candidate_headers,
            )
            self.assertEqual(forbidden.status_code, 403)

            # 11. Super Admin starts the eligibility review.
            review = client.patch(
                f"/admin/applications/{application_id}/status",
                json={
                    "status": "UNDER_REVIEW",
                    "comment": "Review started",
                },
                headers=admin_headers,
            )
            self.assertEqual(review.status_code, 200, review.text)
            self.assertEqual(
                review.json()["status"],
                "UNDER_REVIEW",
            )

            # 12. Super Admin approves eligibility.
            eligible = client.patch(
                f"/admin/applications/{application_id}/status",
                json={
                    "status": "ELIGIBLE",
                    "comment": "Requirements satisfied",
                },
                headers=admin_headers,
            )
            self.assertEqual(eligible.status_code, 200, eligible.text)
            self.assertEqual(
                eligible.json()["status"],
                "ELIGIBLE",
            )

            # 13. Check actual PostgreSQL status history.
            history = db.execute(
                text("""
                    SELECT previous_status, new_status
                    FROM application_status_history
                    WHERE application_id = :application_id
                    ORDER BY id
                """),
                {"application_id": application_id},
            ).all()

            self.assertEqual(
                history,
                [
                    ("SUBMITTED", "UNDER_REVIEW"),
                    ("UNDER_REVIEW", "ELIGIBLE"),
                ],
            )

            final_status = db.execute(
                text("""
                    SELECT status FROM applications
                    WHERE id = :application_id
                """),
                {"application_id": application_id},
            ).scalar_one()

            self.assertEqual(final_status, "ELIGIBLE")     
        
            # 14. Admin creates an evaluation committee.
            response = client.post(
                "/evaluation-committees/",
                json={
                    "position_id": position_id,
                    "name": "Finance Evaluation Committee",
                    "description": "Integration test committee",
                },
                headers=admin_headers,
            )

            self.assertEqual(
                response.status_code,
                201,
                response.text,
            )

            committee_id = response.json()["id"]

            self.assertEqual(
                response.json()["status"],
                "DRAFT",
            )

            # 15. Candidate cannot create committees.
            forbidden = client.post(
                "/evaluation-committees/",
                json={
                    "position_id": position_id,
                    "name": "Unauthorized Committee",
                },
                headers=candidate_headers,
            )

            self.assertEqual(
                forbidden.status_code,
                403,
            )

            # 16. Add a reviewer as committee chair.
            member = client.post(
                f"/evaluation-committees/{committee_id}/members",
                json={
                    "user_id": reviewer_id,
                    "role_in_committee": "CHAIR",
                },
                headers=admin_headers,
            )

            self.assertEqual(
                member.status_code,
                201,
                member.text,
            )
            
            
            # Add second reviewer as a committee member.
            second_member = client.post(
                f"/evaluation-committees/{committee_id}/members",
                json={
                    "user_id": reviewer_2_id,
                    "role_in_committee": "MEMBER",
                },
                headers=admin_headers,
            )

            self.assertEqual(
                second_member.status_code,
                201,
                second_member.text,
            )


            # 17. Add criterion 1 (60%).
            criterion_1 = client.post(
                f"/evaluation-committees/{committee_id}/criteria",
                json={
                    "code": "RESEARCH",
                    "name": "Research Experience",
                    "weight": 60,
                    "max_score": 10,
                    "display_order": 1,
                    "is_active": True,
                },
                headers=admin_headers,
            )

            self.assertEqual(
                criterion_1.status_code,
                201,
                criterion_1.text,
            )

            # 18. Add criterion 2 (40%).
            criterion_2 = client.post(
                f"/evaluation-committees/{committee_id}/criteria",
                json={
                    "code": "TEACHING",
                    "name": "Teaching Experience",
                    "weight": 40,
                    "max_score": 10,
                    "display_order": 2,
                    "is_active": True,
                },
                headers=admin_headers,
            )

            self.assertEqual(
                criterion_2.status_code,
                201,
                criterion_2.text,
            )

            criterion_1_id = criterion_1.json()["id"]
            criterion_2_id = criterion_2.json()["id"]

            # 19. Verify the complete evaluation weighting.
            summary = client.get(
                f"/evaluation-committees/{committee_id}/criteria/summary",
                headers=admin_headers,
            )

            self.assertEqual(
                summary.status_code,
                200,
                summary.text,
            )

            self.assertTrue(
                summary.json()["is_weight_complete"]
            )

            self.assertEqual(
                float(summary.json()["total_active_weight"]),
                100.0,
            )


            # 20. Activate the evaluation committee.
            activated = client.put(
                f"/evaluation-committees/{committee_id}",
                json={"status": "ACTIVE"},
                headers=admin_headers,
            )

            self.assertEqual(
                activated.status_code,
                200,
                activated.text,
            )

            self.assertEqual(
                activated.json()["status"],
                "ACTIVE",
            )

            # 21. Criteria cannot be modified after activation.
            blocked_criterion = client.put(
                f"/evaluation-committees/{committee_id}/criteria/{criterion_1_id}",
                json={"weight": 50},
                headers=admin_headers,
            )

            self.assertEqual(
                blocked_criterion.status_code,
                400,
            )

            # 22. Assign the eligible candidate.
            assignment = client.post(
                f"/evaluation-committees/{committee_id}/applications",
                json={
                    "application_id": application_id,
                    "notes": "Candidate eligible for evaluation",
                },
                headers=admin_headers,
            )

            self.assertEqual(
                assignment.status_code,
                201,
                assignment.text,
            )

            assignment_id = assignment.json()["id"]

            self.assertEqual(
                assignment.json()["status"],
                "ASSIGNED",
            )

            # 23. Reviewer can access assigned applications.
            assigned_list = client.get(
                f"/evaluation-committees/{committee_id}/applications",
                headers=reviewer_headers,
            )

            self.assertEqual(
                assigned_list.status_code,
                200,
                assigned_list.text,
            )

            self.assertTrue(
                any(
                    item["id"] == assignment_id
                    for item in assigned_list.json()
                )
            )

            # 24. Start the evaluation process.
            evaluation = client.put(
                f"/evaluation-committees/{committee_id}/applications/{assignment_id}",
                json={"status": "IN_EVALUATION"},
                headers=admin_headers,
            )

            self.assertEqual(
                evaluation.status_code,
                200,
                evaluation.text,
            )

            self.assertEqual(
                evaluation.json()["status"],
                "IN_EVALUATION",
            )

        
            # 25. Verify the assignment in PostgreSQL.
            stored_status = db.execute(
                text("""
                    SELECT status
                    FROM committee_applications
                    WHERE id = :assignment_id
                """),
                {"assignment_id": assignment_id},
            ).scalar_one()

            self.assertEqual(
                stored_status,
                "IN_EVALUATION",
            )


            # 26. Reviewer cannot create a report without scores.
            base_url = (
                f"/evaluation-committees/{committee_id}"
                f"/applications/{assignment_id}"
            )

            incomplete_report = client.post(
                f"{base_url}/reports",
                json={
                    "final_comment": "Premature report"
                },
                headers=reviewer_headers,
            )

            self.assertEqual(
                incomplete_report.status_code,
                400,
                incomplete_report.text,
            )

            # 27. Reviewer scores Research Experience.
            research_score = client.post(
                f"{base_url}/scores",
                json={
                    "criterion_id": criterion_1_id,
                    "score": 9,
                    "comment": "Strong research background",
                },
                headers=reviewer_headers,
            )

            self.assertEqual(
                research_score.status_code,
                201,
                research_score.text,
            )

            research_score_id = research_score.json()["id"]

            # 28. Reviewer scores Teaching Experience.
            teaching_score = client.post(
                f"{base_url}/scores",
                json={
                    "criterion_id": criterion_2_id,
                    "score": 8,
                    "comment": "Good teaching experience",
                },
                headers=reviewer_headers,
            )

            self.assertEqual(
                teaching_score.status_code,
                201,
                teaching_score.text,
            )

            # 29. Verify scores through the API.
            my_scores = client.get(
                f"{base_url}/scores/me",
                headers=reviewer_headers,
            )

            self.assertEqual(
                my_scores.status_code,
                200,
                my_scores.text,
            )

            self.assertEqual(
                len(my_scores.json()),
                2,
            )

            # 30. Create evaluation report.
            report = client.post(
                f"{base_url}/reports",
                json={
                    "final_comment": (
                        "Candidate meets evaluation criteria"
                    )
                },
                headers=reviewer_headers,
            )

            self.assertEqual(
                report.status_code,
                201,
                report.text,
            )

            report_id = report.json()["id"]

            self.assertEqual(
                report.json()["status"],
                "DRAFT",
            )

            # 31. Submit the evaluation report.
            submitted_report = client.post(
                f"{base_url}/reports/{report_id}/submit",
                headers=reviewer_headers,
            )

            self.assertEqual(
                submitted_report.status_code,
                200,
                submitted_report.text,
            )

            self.assertEqual(
                submitted_report.json()["status"],
                "SUBMITTED",
            )

            self.assertIsNotNone(
                submitted_report.json()["submitted_at"]
            )

            # 32. Submitted scores must be immutable.
            blocked_score = client.put(
                f"{base_url}/scores/{research_score_id}",
                json={"score": 7},
                headers=reviewer_headers,
            )

            self.assertEqual(
                blocked_score.status_code,
                409,
                blocked_score.text,
            )

            # 33. Submitted reports must be immutable.
            blocked_report = client.put(
                f"{base_url}/reports/{report_id}",
                json={"final_comment": "Changed comment"},
                headers=reviewer_headers,
            )

            self.assertEqual(
                blocked_report.status_code,
                400,
                blocked_report.text,
            )

            # 34. Verify actual PostgreSQL records.
            score_count = db.execute(
                text("""
                    SELECT COUNT(*)
                    FROM evaluation_scores
                    WHERE committee_application_id = :assignment_id
                      AND reviewer_id = :reviewer_id
                """),
                {
                    "assignment_id": assignment_id,
                    "reviewer_id": reviewer_id,
                },
            ).scalar_one()

            self.assertEqual(score_count, 2)

            stored_report = db.execute(
                text("""
                    SELECT status, weighted_score
                    FROM evaluation_reports
                    WHERE id = :report_id
                """),
                {"report_id": report_id},
            ).one()

            self.assertEqual(
                stored_report.status,
                "SUBMITTED",
            )

            self.assertEqual(
                stored_report.weighted_score,
                Decimal("86.00"),
            )

            # 35. Ranking must fail while Reviewer 2 is incomplete.
            ranking_url = (
                f"/evaluation-committees/{committee_id}/ranking"
            )

            incomplete_ranking = client.post(
                f"{ranking_url}/generate",
                headers=admin_headers,
            )

            self.assertEqual(
                incomplete_ranking.status_code,
                409,
                incomplete_ranking.text,
            )

            # 36. Reviewer 2 submits research score.
            second_research = client.post(
                f"{base_url}/scores",
                json={
                    "criterion_id": criterion_1_id,
                    "score": 7,
                    "comment": "Good research background",
                },
                headers=reviewer_2_headers,
            )

            self.assertEqual(
                second_research.status_code,
                201,
                second_research.text,
            )

            # 37. Reviewer 2 submits teaching score.
            second_teaching = client.post(
                f"{base_url}/scores",
                json={
                    "criterion_id": criterion_2_id,
                    "score": 8,
                    "comment": "Strong teaching experience",
                },
                headers=reviewer_2_headers,
            )

            self.assertEqual(
                second_teaching.status_code,
                201,
                second_teaching.text,
            )

            # 38. Reviewer 2 creates their report.
            second_report = client.post(
                f"{base_url}/reports",
                json={
                    "final_comment": "Suitable candidate"
                },
                headers=reviewer_2_headers,
            )

            self.assertEqual(
                second_report.status_code,
                201,
                second_report.text,
            )

            self.assertEqual(
                Decimal(str(second_report.json()["weighted_score"])),
                Decimal("74.00"),
            )

            second_report_id = second_report.json()["id"]

            # 39. Reviewer 2 submits the report.
            second_submission = client.post(
                f"{base_url}/reports/{second_report_id}/submit",
                headers=reviewer_2_headers,
            )

            self.assertEqual(
                second_submission.status_code,
                200,
                second_submission.text,
            )

            self.assertEqual(
                second_submission.json()["status"],
                "SUBMITTED",
            )


            # 40. Generate completed committee ranking.
            ranking = client.post(
                f"{ranking_url}/generate",
                headers=admin_headers,
            )

            self.assertEqual(
                ranking.status_code,
                200,
                ranking.text,
            )

            ranked_items = ranking.json()

            self.assertEqual(len(ranked_items), 1)

            self.assertEqual(
                ranked_items[0]["committee_application_id"],
                assignment_id,
            )

            self.assertEqual(
                Decimal(str(ranked_items[0]["final_score"])),
                Decimal("80.00"),
            )

            self.assertEqual(
                ranked_items[0]["rank_position"],
                1,
            )

            self.assertEqual(
                ranked_items[0]["decision"],
                "PENDING",
            )

            # 41. Confirm GET ranking returns existing results.
            saved_ranking = client.get(
                ranking_url,
                headers=admin_headers,
            )

            self.assertEqual(
                saved_ranking.status_code,
                200,
                saved_ranking.text,
            )

            self.assertEqual(
                Decimal(str(saved_ranking.json()[0]["final_score"])),
                Decimal("80.00"),
            )

            # 42. Candidate cannot record final decisions.
            decision_url = f"{base_url}/result/decision"

            forbidden_decision = client.put(
                decision_url,
                json={"decision": "SELECTED"},
                headers=candidate_headers,
            )

            self.assertEqual(
                forbidden_decision.status_code,
                403,
                forbidden_decision.text,
            )

            # 43. Super Admin records final decision.
            decision = client.put(
                decision_url,
                json={
                    "decision": "SELECTED",
                    "final_comment": "Candidate selected",
                },
                headers=admin_headers,
            )

            self.assertEqual(
                decision.status_code,
                200,
                decision.text,
            )

            self.assertEqual(
                decision.json()["decision"],
                "SELECTED",
            )

            self.assertEqual(
                decision.json()["decided_by"],
                admin_id,
            )

            # 44. Finalized decisions cannot be overwritten.
            overwrite = client.put(
                decision_url,
                json={"decision": "NOT_SELECTED"},
                headers=admin_headers,
            )

            self.assertEqual(
                overwrite.status_code,
                409,
                overwrite.text,
            )

            # 45. Ranking cannot be regenerated after decision.
            regenerate = client.post(
                f"{ranking_url}/generate",
                headers=admin_headers,
            )

            self.assertEqual(
                regenerate.status_code,
                409,
                regenerate.text,
            )

            # 46. Verify persisted PostgreSQL result.
            stored_result = db.execute(
                text("""
                    SELECT final_score, rank_position,
                            decision, decided_by
                    FROM evaluation_results
                    WHERE committee_application_id = :assignment_id
                """),
                {"assignment_id": assignment_id},
            ).one()

            self.assertEqual(
                stored_result.final_score,
                Decimal("80.00"),
            )

            self.assertEqual(stored_result.rank_position, 1)
            self.assertEqual(stored_result.decision, "SELECTED")
            self.assertEqual(stored_result.decided_by, admin_id)

        # 26. Verify rollback AFTER the entire workflow.
        with test_engine.connect() as connection:
            remaining_users = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM users
                    WHERE email = :email
                """),
                {"email": candidate_email},
            ).scalar_one()

            remaining_committees = connection.execute(
                text("""
                    SELECT COUNT(*)
                    FROM evaluation_committees
                    WHERE id = :committee_id
                """),
                {"committee_id": committee_id},
            ).scalar_one()

        self.assertEqual(remaining_users, 0)
        self.assertEqual(remaining_committees, 0)
