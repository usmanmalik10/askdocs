from fastapi import HTTPException

from db import database

LIMITS = {"upload": (5, 10, 20), "question": (30, 60, 100)}


async def consume(action: str, owner: str, address: str):
    # Commit counters before external work; failed attempts still consume the public demo budget.
    async with database() as conn:
        for identity, limit in zip(("guest:" + owner, "address:" + address, "site"), LIMITS[action], strict=True):
            row = await (await conn.execute(
                "INSERT INTO quota_buckets(bucket, used) VALUES (%s, 1) "
                "ON CONFLICT (bucket, day) DO UPDATE SET used = quota_buckets.used + 1 "
                "WHERE quota_buckets.used < %s RETURNING used",
                (action + ":" + identity, limit),
            )).fetchone()
            if row is None:
                raise HTTPException(429, "The daily free-demo limit has been reached. Please try again tomorrow.")


async def lock_guest(conn, owner: str):
    row = await (await conn.execute(
        "SELECT pg_try_advisory_xact_lock(hashtextextended(%s, 0)) AS locked", (owner,),
    )).fetchone()
    if not row["locked"]:
        raise HTTPException(409, "Another operation is running in this workspace. Please wait and retry.")
