import httpx
import pytest

from main import app


@pytest.mark.parametrize("secret", ["", "too-short", "x" * 40])
async def test_private_service_rejects_missing_or_wrong_bearer(monkeypatch, secret):
    monkeypatch.setenv("INTERNAL_API_SECRET", secret)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 401


async def test_service_requires_valid_owner_and_address(monkeypatch):
    monkeypatch.setenv("INTERNAL_API_SECRET", "s" * 40)
    headers = {"Authorization": "Bearer " + "s" * 40, "X-Guest-Id": "a" * 64, "X-Guest-Address": "b" * 64}
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.get("/health", headers=headers)).status_code == 200
        headers["X-Guest-Id"] = "../../other-guest"
        assert (await client.get("/health", headers=headers)).status_code == 400
