"""Apply versioned migrations explicitly; never migrate during an HTTP request."""
from pathlib import Path

from db import database
from runtime import run


async def migrate():
    async with database() as conn:
        await conn.execute("SELECT pg_advisory_xact_lock(724861309)")
        await conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (version text PRIMARY KEY)")
        for path in sorted(Path(__file__).with_name("migrations").glob("*.sql")):
            applied = await (await conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version = %s", (path.name,),
            )).fetchone()
            if not applied:
                await conn.execute(path.read_text(encoding="utf-8"))
                await conn.execute("INSERT INTO schema_migrations VALUES (%s)", (path.name,))
                print(f"Applied {path.name}")


if __name__ == "__main__":
    run(migrate())
