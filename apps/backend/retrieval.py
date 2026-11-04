from uuid import UUID

from db import database, document, vector
from provider import embed


async def retrieve(owner: str, document_id: UUID, question: str) -> list[dict]:
    # Authorize before sending any question to a third party.
    async with database() as conn:
        await document(conn, owner, document_id)
    embedding = vector((await embed([question], query=True))[0])
    async with database() as conn:
        # Re-check ownership and expiry in the retrieval query itself.
        rows = await (await conn.execute(
            "SELECT c.ordinal, c.page, c.content, d.name, "
            "1 - (c.embedding <=> %s::vector) AS score "
            "FROM chunks c JOIN documents d ON d.id = c.document_id "
            "JOIN guests g ON g.owner = d.owner "
            "WHERE d.id = %s AND d.owner = %s AND g.expires_at > clock_timestamp() "
            "ORDER BY c.embedding <=> %s::vector LIMIT 6",
            (embedding, document_id, owner, embedding),
        )).fetchall()
    return [{"id": index, **row} for index, row in enumerate(rows, 1)]
