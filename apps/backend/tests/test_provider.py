import httpx
import pytest
from fastapi import HTTPException

from provider import model_request


@pytest.mark.parametrize(("status", "expected"), [(429, 429), (403, 503), (500, 503)])
async def test_provider_failures_do_not_expose_response_or_credentials(monkeypatch, status, expected):
    monkeypatch.setenv("GEMINI_API_KEY", "test-secret-never-return")
    transport = httpx.MockTransport(lambda _: httpx.Response(status, json={"secret": "private-provider-error"}))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(HTTPException) as error:
            await model_request(client, "model:operation", {})
    assert error.value.status_code == expected
    assert "secret" not in error.value.detail


async def test_missing_provider_is_an_error_not_a_fake_answer(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    async with httpx.AsyncClient() as client:
        with pytest.raises(HTTPException, match="not connected"):
            await model_request(client, "model:operation", {})
