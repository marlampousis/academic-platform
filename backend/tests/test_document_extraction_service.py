
import unittest
from io import BytesIO

from docx import Document
from pypdf import PdfWriter

from app.ai.services.document_extraction_service import (
    extract_document_text,
    DocumentExtractionError,
)


class TestDocumentExtractionService(unittest.TestCase):

    def test_extract_docx_paragraphs(self):
        document = Document()
        document.add_paragraph(
            "PhD in Computer Science, 2022."
        )
        document.add_paragraph(
            "Research in Machine Learning."
        )

        buffer = BytesIO()
        document.save(buffer)

        text = extract_document_text(
            filename="academic_cv.docx",
            content=buffer.getvalue(),
        )

        self.assertIn(
            "PhD in Computer Science",
            text,
        )
        self.assertIn(
            "Machine Learning",
            text,
        )

    def test_extract_docx_tables(self):
        document = Document()

        table = document.add_table(
            rows=1,
            cols=2,
        )
        table.cell(0, 0).text = "Degree"
        table.cell(0, 1).text = "PhD"

        buffer = BytesIO()
        document.save(buffer)

        text = extract_document_text(
            filename="academic_cv.docx",
            content=buffer.getvalue(),
        )

        self.assertIn("Degree", text)
        self.assertIn("PhD", text)

    def test_reject_unsupported_file(self):
        with self.assertRaises(
            DocumentExtractionError
        ):
            extract_document_text(
                filename="academic_cv.txt",
                content=b"Academic CV",
            )

    def test_reject_invalid_pdf(self):
        with self.assertRaises(
            DocumentExtractionError
        ):
            extract_document_text(
                filename="academic_cv.pdf",
                content=b"Not a real PDF",
            )

    def test_reject_empty_document(self):
        with self.assertRaises(
            DocumentExtractionError
        ):
            extract_document_text(
                filename="academic_cv.docx",
                content=b"",
            )

    def test_reject_pdf_without_text(self):
        writer = PdfWriter()
        writer.add_blank_page(
            width=595,
            height=842,
        )

        buffer = BytesIO()
        writer.write(buffer)

        with self.assertRaises(
            DocumentExtractionError
        ):
            extract_document_text(
                filename="blank.pdf",
                content=buffer.getvalue(),
            )

    def test_reject_oversized_document(self):
        with self.assertRaises(
            DocumentExtractionError
        ):
            extract_document_text(
                filename="academic_cv.pdf",
                content=b"x" * (5 * 1024 * 1024 + 1),
            )


if __name__ == "__main__":
    unittest.main()
