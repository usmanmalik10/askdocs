"""Bounded text extraction. Originals are discarded after this request."""
import io
import re
from dataclasses import dataclass

from fastapi import HTTPException
from pypdf import Configuration, PdfReader

MAX_BYTES = 3 * 1024 * 1024
MAX_CHARS = 100_000
MAX_PAGES = 50

# Cap a single compressed PDF stream before the parser can expand it without bound.
Configuration.zlib_maximum_output_length = 8 * 1024 * 1024


@dataclass(frozen=True)
class Page:
    number: int
    text: str


def clean_text(text: str) -> str:
    text = re.sub(r"[^\S\n]+", " ", text.replace("\r", "\n"))
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text).strip()


def extract(name: str, content: bytes) -> list[Page]:
    if not content or len(content) > MAX_BYTES:
        raise HTTPException(413, "Choose a non-empty file no larger than 3 MB.")
    extension = name.rsplit(".", 1)[-1].lower()
    if extension in {"txt", "md"}:
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise HTTPException(422, "Save text documents as UTF-8 and upload again.") from exc
        if "\x00" in text:
            raise HTTPException(422, "This file does not appear to contain plain text.")
        pages = [Page(1, clean_text(text))]
    elif extension == "pdf":
        if not content.lstrip().startswith(b"%PDF-"):
            raise HTTPException(422, "This file is not a valid PDF.")
        try:
            reader = PdfReader(io.BytesIO(content), strict=True)
            if reader.is_encrypted:
                raise HTTPException(422, "Password-protected PDFs are not supported. Upload an unlocked copy.")
            if len(reader.pages) > MAX_PAGES:
                raise HTTPException(422, "PDFs must have 50 pages or fewer.")
            pages = []
            count = 0
            for number, page in enumerate(reader.pages, 1):
                text = clean_text(page.extract_text() or "")
                count += len(text)
                if count > MAX_CHARS:
                    raise HTTPException(422, "This document has too much text. Upload a smaller section.")
                if text:
                    pages.append(Page(number, text))
        except HTTPException:
            raise
        except Exception as exc:
            raise HTTPException(422, "This PDF could not be read. Export a new text-based copy and retry.") from exc
    else:
        raise HTTPException(415, "Supported files are PDF, TXT, and Markdown (.md).")
    total = sum(len(page.text) for page in pages)
    if total < 20:
        raise HTTPException(422, "No usable text was found. Scanned PDFs need OCR before uploading.")
    if total > MAX_CHARS:
        raise HTTPException(422, "This document has too much text. Upload a smaller section.")
    return pages
