import asyncio
import os
import re
from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from psycopg.types.json import Jsonb
from pydantic import BaseModel, Field, field_validator

from answering import answer_question
from chunking import chunk_pages
from db import database, document, guest, vector
from extraction import MAX_BYTES, extract
from provider import EMBEDDING_MODEL, ai_deadline, embed, model_name
from quotas import consume, lock_guest
from retrieval import retrieve

router = APIRouter()


def require_ai():
    if not os.environ.get("GEMINI_API_KEY"):
        raise HTTPException(503, "The AI provider is not connected yet.")


async def open_guest(conn, owner: str, address: str):
    existing = await (await conn.execute("SELECT 1 FROM guests WHERE owner = %s", (owner,))).fetchone()
    if existing is None:
        await consume("workspace", owner, address)
    return await guest(conn, owner)


@router.get("/workspace")
async def workspace(request: Request):
    async with database() as conn:
        expires_at = await open_guest(conn, request.state.owner, request.state.address)
        rows = await (await conn.execute(
            "SELECT id, name, byte_size, chunk_count, created_at FROM documents WHERE owner = %s ORDER BY created_at",
            (request.state.owner,),
        )).fetchall()
    return {"documents": rows, "expires_at": expires_at,
            "ai_ready": bool(os.environ.get("GEMINI_API_KEY")), "provider": "Google Gemini",
            "model": model_name(), "embedding_model": EMBEDDING_MODEL,
            "limits": {"file_bytes": MAX_BYTES, "documents": 5, "questions_per_day": 30}}


@router.post("/documents", status_code=201)
async def upload(request: Request, file: UploadFile = File(), consent: bool = Form()):
    if not consent:
        raise HTTPException(422, "Please confirm the AI data-processing notice before uploading.")
    require_ai()
    try:
        content = await file.read(MAX_BYTES + 1)
    finally:
        await file.close()
    name = re.sub(r"[\x00-\x1f]", "", (file.filename or "").replace("\\", "/").rsplit("/", 1)[-1])[:180]
    if not name:
        raise HTTPException(422, "Choose a named PDF, TXT, or Markdown file.")
    async with database() as conn:
        await open_guest(conn, request.state.owner, request.state.address)
    async with ai_deadline(), database() as conn:
        await lock_guest(conn, request.state.owner)
        await guest(conn, request.state.owner, create=False)
        count = await (await conn.execute("SELECT count(*) AS total FROM documents WHERE owner = %s", (request.state.owner,))).fetchone()
        if count["total"] >= 5:
            raise HTTPException(409, "Your workspace holds five documents. Delete one before uploading another.")
        await consume("upload", request.state.owner, request.state.address)
        pages = await asyncio.to_thread(extract, name, content)
        chunks = chunk_pages(pages)
        embeddings = await embed([chunk.content for chunk in chunks])
        await guest(conn, request.state.owner, create=False)
        document_id = uuid4()
        row = await (await conn.execute(
            "INSERT INTO documents(id, owner, name, media_type, byte_size, chunk_count) VALUES (%s,%s,%s,%s,%s,%s) "
            "RETURNING id, name, byte_size, chunk_count, created_at",
            (document_id, request.state.owner, name, "application/pdf" if name.lower().endswith(".pdf") else "text/plain", len(content), len(chunks)),
        )).fetchone()
        async with conn.cursor() as cursor:
            await cursor.executemany(
                "INSERT INTO chunks(document_id, ordinal, page, content, embedding) VALUES (%s,%s,%s,%s,%s::vector)",
                [(document_id, chunk.ordinal, chunk.page, chunk.content, vector(embedding))
                 for chunk, embedding in zip(chunks, embeddings, strict=True)],
            )
    return row


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=1200)

    @field_validator("question")
    @classmethod
    def trim_question(cls, value):
        value = value.strip()
        if len(value) < 3 or "\x00" in value:
            raise ValueError("Enter a question with at least three characters.")
        return value


@router.post("/documents/{document_id}/ask", status_code=201)
async def ask(document_id: UUID, body: Question, request: Request):
    require_ai()
    async with ai_deadline(), database() as conn:
        await lock_guest(conn, request.state.owner)
        await document(conn, request.state.owner, document_id)
        await consume("question", request.state.owner, request.state.address)
        sources = await retrieve(request.state.owner, document_id, body.question)
        result = await answer_question(body.question, sources)
        # Expiry may have passed during a provider call; do not extend guest access.
        await document(conn, request.state.owner, document_id)
        answer_id = uuid4()
        row = await (await conn.execute(
            "INSERT INTO answers(id, document_id, question, answer, citations, grounded) "
            "VALUES (%s,%s,%s,%s,%s,%s) RETURNING id, question, answer, citations, grounded, created_at",
            (answer_id, document_id, body.question, result["answer"], Jsonb(result["citations"]), result["grounded"]),
        )).fetchone()
    return row


@router.get("/documents/{document_id}/answers")
async def history(document_id: UUID, request: Request):
    async with database() as conn:
        await document(conn, request.state.owner, document_id)
        rows = await (await conn.execute(
            "SELECT id, question, answer, citations, grounded, created_at FROM answers "
            "WHERE document_id = %s ORDER BY created_at DESC LIMIT 30", (document_id,),
        )).fetchall()
    return {"answers": list(reversed(rows))}


@router.delete("/documents/{document_id}")
async def delete_document(document_id: UUID, request: Request):
    async with database() as conn:
        await lock_guest(conn, request.state.owner)
        await document(conn, request.state.owner, document_id)
        await conn.execute("DELETE FROM documents WHERE id = %s AND owner = %s", (document_id, request.state.owner))
    return {"deleted": True}


@router.delete("/workspace")
async def delete_workspace(request: Request):
    async with database() as conn:
        await lock_guest(conn, request.state.owner)
        await conn.execute("DELETE FROM guests WHERE owner = %s", (request.state.owner,))
    return {"deleted": True}
