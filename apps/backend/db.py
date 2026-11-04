import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone

import psycopg
from fastapi import HTTPException
from psycopg.rows import dict_row


@asynccontextmanager
async def database():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        raise HTTPException(503, "Document storage is not connected yet.")
    try:
        async with await psycopg.AsyncConnection.connect(
            url, row_factory=dict_row, connect_timeout=5,
            options="-c statement_timeout=10000 -c lock_timeout=3000",
        ) as conn:
            yield conn
    except psycopg.Error as exc:
        # Never include connection strings or document text in error responses.
        raise HTTPException(503, "Document storage is temporarily unavailable. Please retry.") from exc


async def guest(conn, owner: str):
    await conn.execute("INSERT INTO guests(owner) VALUES (%s) ON CONFLICT DO NOTHING", (owner,))
    row = await (await conn.execute("SELECT expires_at FROM guests WHERE owner = %s", (owner,))).fetchone()
    if row["expires_at"] <= datetime.now(timezone.utc):
        raise HTTPException(410, "This guest workspace has expired. Start a fresh workspace.")
    return row["expires_at"]


async def document(conn, owner: str, document_id):
    row = await (await conn.execute(
        "SELECT d.* FROM documents d JOIN guests g ON g.owner = d.owner "
        "WHERE d.id = %s AND d.owner = %s AND g.expires_at > now()",
        (document_id, owner),
    )).fetchone()
    if row is None:
        raise HTTPException(404, "Document not found in this guest workspace.")
    return row


def vector(values: list[float]) -> str:
    import math

    if len(values) != 768 or not all(math.isfinite(v) for v in values):
        raise ValueError("Invalid embedding dimensions or values")
    return "[" + ",".join(str(v) for v in values) + "]"
