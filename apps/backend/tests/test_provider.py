import asyncio

import httpx
import pytest
from fastapi import HTTPException

from provider import ai_deadline, model_request


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


@pytest.mark.parametrize("temporary_error", ["unavailable", "timeout"])
async def test_transient_provider_failure_recovers_once(monkeypatch, temporary_error):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    calls = 0

    def upstream(request):
        nonlocal calls
        calls += 1
        if calls == 1:
            if temporary_error == "timeout":
                raise httpx.ReadTimeout("Temporary timeout", request=request)
            return httpx.Response(503, json={"error": "temporary"})
        return httpx.Response(200, json={"answer": "provider response"})

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        assert await model_request(client, "model:operation", {}) == {"answer": "provider response"}
    assert calls == 2


async def test_exhausted_quota_is_not_retried(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    calls = 0

    def upstream(_request):
        nonlocal calls
        calls += 1
        return httpx.Response(429)

    async with httpx.AsyncClient(transport=httpx.MockTransport(upstream)) as client:
        with pytest.raises(HTTPException) as error:
            await model_request(client, "model:operation", {})
    assert error.value.status_code == 429
    assert calls == 1


async def test_ai_operation_has_a_total_deadline(monkeypatch):
    monkeypatch.setattr("provider.AI_DEADLINE_SECONDS", 0.01)
    with pytest.raises(HTTPException) as error:
        async with ai_deadline():
            await asyncio.Event().wait()
    assert error.value.status_code == 504
