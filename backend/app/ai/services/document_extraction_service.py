
from io import BytesIO
from pathlib import Path
from zipfile import BadZipFile, ZipFile

from docx import Document
from pypdf import PdfReader


MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TEXT_CHARS = 40000
MAX_PDF_PAGES = 50
MAX_DOCX_UNCOMPRESSED_BYTES = 15 * 1024 * 1024
MAX_DOCX_ENTRIES = 200


class DocumentExtractionError(ValueError):
    """Document cannot be safely processed."""


def extract_document_text(
    *,
    filename: str,
    content: bytes,
) -> str:
    if not filename:
        raise DocumentExtractionError(
            "A filename is required"
        )

    extension = Path(filename).suffix.lower()

    if extension not in (".pdf", ".docx"):
        raise DocumentExtractionError(
            "Only PDF and DOCX files are supported"
        )

    if not content:
        raise DocumentExtractionError(
            "The uploaded document is empty"
        )

    if len(content) > MAX_FILE_BYTES:
        raise DocumentExtractionError(
            "The document exceeds the 5 MB upload limit"
        )

    try:
        if extension == ".pdf":
            if not content.startswith(b"%PDF-"):
                raise DocumentExtractionError(
                    "Invalid PDF file"
                )

            reader = PdfReader(BytesIO(content))

            if reader.is_encrypted:
                raise DocumentExtractionError(
                    "Encrypted PDFs are not supported"
                )

            if len(reader.pages) > MAX_PDF_PAGES:
                raise DocumentExtractionError(
                    "PDF exceeds the 50-page limit"
                )

            parts = []

            for page in reader.pages:
                parts.append(page.extract_text() or "")

            text = "\n\n".join(parts)

        else:
            if not content.startswith(b"PK"):
                raise DocumentExtractionError(
                    "Invalid DOCX file"
                )

            # Apply basic ZIP archive safety limits.
            with ZipFile(BytesIO(content)) as archive:
                entries = archive.infolist()

                if len(entries) > MAX_DOCX_ENTRIES:
                    raise DocumentExtractionError(
                        "DOCX contains too many archive entries"
                    )

                expanded_size = sum(
                    entry.file_size for entry in entries
                )

                if expanded_size > MAX_DOCX_UNCOMPRESSED_BYTES:
                    raise DocumentExtractionError(
                        "DOCX exceeds the expanded-size limit"
                    )

                if "word/document.xml" not in archive.namelist():
                    raise DocumentExtractionError(
                        "Invalid DOCX structure"
                    )

            document = Document(BytesIO(content))

            parts = [
                paragraph.text
                for paragraph in document.paragraphs
                if paragraph.text.strip()
            ]

            # Include text stored inside document tables.
            for table in document.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text.strip():
                            parts.append(cell.text)

            text = "\n".join(parts)

    except DocumentExtractionError:
        raise

    except (
        ValueError,
        BadZipFile,
        Exception,
    ) as exc:
        raise DocumentExtractionError(
            "Could not read the uploaded document"
        ) from exc

    text = text.strip()

    if not text:
        raise DocumentExtractionError(
            "No extractable text found. "
            "Scanned documents may require OCR."
        )

    if len(text) > MAX_TEXT_CHARS:
        raise DocumentExtractionError(
            "Extracted text exceeds the 40000-character limit"
        )

    return text
