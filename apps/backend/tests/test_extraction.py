import io

import pytest
from fastapi import HTTPException
from pypdf import PdfWriter

from extraction import MAX_BYTES, extract


def test_plain_text_preserves_content():
    pages = extract("policy.md", b"\xef\xbb\xbf# Annual leave\nEmployees receive 20 days of leave.")
    assert pages[0].number == 1
    assert "20 days" in pages[0].text


@pytest.mark.parametrize(("name", "body", "status"), [
    ("empty.txt", b"", 413),
    ("large.txt", b"x" * (MAX_BYTES + 1), 413),
    ("secret.exe", b"Not a supported type of document.", 415),
    ("fake.pdf", b"This is a plain text file pretending to be a PDF.", 422),
    ("broken.pdf", b"%PDF-1.7\nbroken", 422),
    ("binary.txt", b"plain text with a null\x00byte", 422),
    ("bad.txt", b"\xff\xff\xff" * 20, 422),
    ("empty.md", b" \n\t " * 20, 422),
])
def test_invalid_documents_fail_clearly(name, body, status):
    with pytest.raises(HTTPException) as error:
        extract(name, body)
    assert error.value.status_code == status


def test_scanned_or_empty_pdf_requires_ocr():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    data = io.BytesIO()
    writer.write(data)
    with pytest.raises(HTTPException, match="OCR"):
        extract("scan.pdf", data.getvalue())


def test_encrypted_pdf_is_rejected():
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    writer.encrypt("secret")
    data = io.BytesIO()
    writer.write(data)
    with pytest.raises(HTTPException, match="Password-protected"):
        extract("locked.pdf", data.getvalue())
