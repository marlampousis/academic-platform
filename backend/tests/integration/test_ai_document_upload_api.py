import unittest
from io import BytesIO
from unittest.mock import patch

import app.core.model_registry

from docx import Document

from db_setup import isolated_api_client
from test_ai_extraction_api import (
    CV_TEXT,
    FakeExtractionService,
    create_candidate,
    auth_headers,
)


def make_docx(text: str) -> bytes:
    document = Document()
    document.add_paragraph(text)

    buffer = BytesIO()
    document.save(buffer)

    return buffer.getvalue()


class TestAIDocumentUploadAPI(unittest.TestCase):

    def test_candidate_uploads_docx(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)

            with patch(
                "app.ai.router.create_gemini_extraction_service",
                return_value=FakeExtractionService(),
            ):
                response = client.post(
                    "/ai/extractions/upload",
                    headers=auth_headers(user),
                    files={
                        "file": (
                            "academic_cv.docx",
                            make_docx(CV_TEXT),
                            "application/vnd.openxmlformats-"
                            "officedocument.wordprocessingml.document",
                        )
                    },
                )

            self.assertEqual(
                response.status_code,
                201,
                response.text,
            )

            result = response.json()
            self.assertEqual(
                result["status"],
                "REVIEW_REQUIRED",
            )
            self.assertGreater(
                result["artifact_id"],
                0,
            )

            # The uploaded document created a normal S03 artifact.
            loaded = client.get(
                f"/ai/extractions/{result['artifact_id']}",
                headers=auth_headers(user),
            )

            self.assertEqual(
                loaded.status_code,
                200,
                loaded.text,
            )

    def test_unsupported_file_returns_422(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)

            response = client.post(
                "/ai/extractions/upload",
                headers=auth_headers(user),
                files={
                    "file": (
                        "academic_cv.txt",
                        b"Sample CV",
                        "text/plain",
                    )
                },
            )

            self.assertEqual(response.status_code, 422)

    def test_invalid_pdf_returns_422(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)

            response = client.post(
                "/ai/extractions/upload",
                headers=auth_headers(user),
                files={
                    "file": (
                        "academic_cv.pdf",
                        b"Not a valid PDF",
                        "application/pdf",
                    )
                },
            )

            self.assertEqual(response.status_code, 422)

    def test_unauthenticated_upload_returns_401(self):
        with isolated_api_client() as (client, db):
            response = client.post(
                "/ai/extractions/upload",
                files={
                    "file": (
                        "academic_cv.docx",
                        make_docx(CV_TEXT),
                    )
                },
            )

            self.assertEqual(response.status_code, 401)

    def test_oversized_upload_returns_422(self):
        with isolated_api_client() as (client, db):
            user = create_candidate(db)

            oversized_content = (
                b"%PDF-" + b"x" * (5 * 1024 * 1024)
            )

            response = client.post(
                "/ai/extractions/upload",
                headers=auth_headers(user),
                files={
                    "file": (
                        "oversized_cv.pdf",
                        oversized_content,
                        "application/pdf",
                    )
                },
            )

            self.assertEqual(
                response.status_code,
                422,
                response.text,
            )


if __name__ == "__main__":
    unittest.main()