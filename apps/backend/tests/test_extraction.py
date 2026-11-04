import io

import pytest
from fastapi import HTTPException
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

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


def test_pdf_text_keeps_original_page_after_blank_page():
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject({NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
                             NameObject("/BaseFont"): NameObject("/Helvetica")})
    page[NameObject("/Resources")] = DictionaryObject({NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 12 Tf 10 100 Td (Employees receive 20 working days of paid annual leave.) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    data = io.BytesIO()
    writer.write(data)
    pages = extract("policy.pdf", data.getvalue())
    assert [page.number for page in pages] == [2]
    assert "20 working days" in pages[0].text
