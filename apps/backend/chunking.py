from dataclasses import dataclass

from fastapi import HTTPException

from extraction import Page


@dataclass(frozen=True)
class Chunk:
    ordinal: int
    page: int
    content: str


def chunk_pages(pages: list[Page]) -> list[Chunk]:
    chunks = []
    for page in pages:
        start = 0
        while start < len(page.text):
            end = min(start + 1400, len(page.text))
            if end < len(page.text):
                boundary = page.text.rfind(" ", start + 1000, end)
                if boundary > start:
                    end = boundary
            text = page.text[start:end].strip()
            if text:
                chunks.append(Chunk(len(chunks), page.number, text))
            if len(chunks) > 120:
                raise HTTPException(422, "This document needs too many passages. Upload a smaller section.")
            if end == len(page.text):
                break
            start = max(start + 1, end - 150)
    return chunks
