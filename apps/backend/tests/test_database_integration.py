"""Real PostgreSQL tests with a deliberately isolated local database only.

Model calls are replaced with deterministic test doubles; these tests do not
claim that Gemini credentials or live answer quality have been verified.
"""
import asyncio
import os
from urllib.parse import urlparse

import httpx
import pytest

from answering import validate_answer
from db import database
from main import app
from migrate import migrate
from quotas import consume

TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(not TEST_URL, reason="Set TEST_DATABASE_URL to an isolated local askdocs_test database")
OWNER_A = "a" * 64
OWNER_B = "b" * 64
TEXT = "Employees receive 20 working days of paid annual leave. Requests need manager approval."


@pytest.fixture(autouse=True)
async def isolated_database(monkeypatch):
    parsed = urlparse(TEST_URL)
    if parsed.hostname not in {"127.0.0.1", "localhost"} or parsed.path != "/askdocs_test":
        pytest.fail("Integration tests refuse every database except local askdocs_test")
    monkeypatch.setenv("DATABASE_URL", TEST_URL)
    monkeypatch.setenv("INTERNAL_API_SECRET", "test-service-secret-" + "s" * 32)
    monkeypatch.setenv("GEMINI_API_KEY", "test-double-not-a-real-key")
    await migrate()
    async with database() as conn:
        actual = await (await conn.execute("SELECT current_database() AS name")).fetchone()
        assert actual["name"] == "askdocs_test"
        await conn.execute("TRUNCATE guests, quota_buckets CASCADE")

    async def embeddings(texts, **_kwargs):
        return [[1.0] + [0.0] * 767 for _ in texts]

    async def answer(_question, sources):
        return validate_answer({"answer": "Employees receive 20 working days of paid annual leave. [1]",
                                "grounded": True, "evidence": [{"id": 1, "quote": TEXT}]}, sources)

    monkeypatch.setattr("routes.embed", embeddings)
    monkeypatch.setattr("retrieval.embed", embeddings)
    monkeypatch.setattr("routes.answer_question", answer)


def headers(owner):
    return {"Authorization": "Bearer test-service-secret-" + "s" * 32,
            "X-Guest-Id": owner, "X-Guest-Address": owner}


async def upload(client, owner=OWNER_A):
    response = await client.post("/documents", headers=headers(owner), data={"consent": "true"},
                                 files={"file": ("policy.txt", TEXT.encode(), "text/plain")})
    assert response.status_code == 201, response.text
    return response.json()["id"]


async def test_upload_retrieve_answer_history_and_cross_guest_isolation():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        doc = await upload(client)
        workspace = await client.get("/workspace", headers=headers(OWNER_B))
        assert workspace.json()["documents"] == []
        for method, suffix, kwargs in [
            ("GET", "/answers", {}),
            ("POST", "/ask", {"json": {"question": "How much annual leave?"}}),
            ("DELETE", "", {}),
        ]:
            response = await client.request(method, f"/documents/{doc}{suffix}", headers=headers(OWNER_B), **kwargs)
            assert response.status_code == 404
        answer = await client.post(f"/documents/{doc}/ask", headers=headers(OWNER_A), json={"question": "How much annual leave?"})
        assert answer.status_code == 201, answer.text
        assert answer.json()["citations"][0]["quote"] == TEXT
        history = await client.get(f"/documents/{doc}/answers", headers=headers(OWNER_A))
        assert len(history.json()["answers"]) == 1
        assert history.headers["cache-control"] == "private, no-store"


async def test_delete_cascades_without_affecting_another_guest():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        doc = await upload(client)
        other = await upload(client, OWNER_B)
        await client.post(f"/documents/{doc}/ask", headers=headers(OWNER_A), json={"question": "How much annual leave?"})
        assert (await client.delete(f"/documents/{doc}", headers=headers(OWNER_A))).status_code == 200
        assert (await client.get(f"/documents/{doc}/answers", headers=headers(OWNER_A))).status_code == 404
        rows = (await client.get("/workspace", headers=headers(OWNER_B))).json()["documents"]
        assert [row["id"] for row in rows] == [other]
    async with database() as conn:
        assert (await (await conn.execute("SELECT count(*) AS n FROM answers")).fetchone())["n"] == 0
        assert (await (await conn.execute("SELECT count(*) AS n FROM chunks WHERE document_id = %s", (doc,))).fetchone())["n"] == 0


async def test_expiry_denies_access_and_cleanup_removes_data():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        doc = await upload(client)
        async with database() as conn:
            await conn.execute("UPDATE guests SET expires_at = clock_timestamp() - interval '1 second' WHERE owner = %s", (OWNER_A,))
        assert (await client.get("/workspace", headers=headers(OWNER_A))).status_code == 410
        assert (await client.get(f"/documents/{doc}/answers", headers=headers(OWNER_A))).status_code == 404
        cleanup = await client.post("/maintenance/cleanup", headers=headers(OWNER_A))
        assert cleanup.json()["expired_workspaces_removed"] == 1
    async with database() as conn:
        assert (await (await conn.execute("SELECT count(*) AS n FROM documents")).fetchone())["n"] == 0


async def test_concurrent_quota_reservations_cannot_exceed_limit():
    results = await asyncio.gather(*(consume("upload", OWNER_A, OWNER_A) for _ in range(12)), return_exceptions=True)
    assert sum(result is None for result in results) == 5
    assert all(getattr(result, "status_code", None) == 429 for result in results if result is not None)
    async with database() as conn:
        row = await (await conn.execute("SELECT used FROM quota_buckets WHERE bucket = 'upload:site'")).fetchone()
        assert row["used"] == 5


async def test_upload_requires_consent_and_rolls_back_failed_extraction():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/documents", headers=headers(OWNER_A), data={"consent": "false"},
                                     files={"file": ("policy.txt", TEXT.encode(), "text/plain")})
        assert response.status_code == 422
        response = await client.post("/documents", headers=headers(OWNER_A), data={"consent": "true"},
                                     files={"file": ("bad.pdf", b"not a PDF", "application/pdf")})
        assert response.status_code == 422
        workspace = await client.get("/workspace", headers=headers(OWNER_A))
        assert workspace.json()["documents"] == []
