from fastapi import APIRouter

from db import database

router = APIRouter()


@router.post("/maintenance/cleanup")
async def cleanup():
    async with database() as conn:
        expired = await conn.execute("DELETE FROM guests WHERE expires_at <= clock_timestamp()")
        counters = await conn.execute("DELETE FROM quota_buckets WHERE day < CURRENT_DATE - 2")
        return {"expired_workspaces_removed": expired.rowcount, "old_counters_removed": counters.rowcount}
