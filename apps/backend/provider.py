import asyncio
import math
import os
import re

import httpx
from fastapi import HTTPException

API_ROOT = "https://generativelanguage.googleapis.com/v1beta/models/"
EMBEDDING_MODEL = "gemini-embedding-001"


def model_name() -> str:
    model = os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")
    if not re.fullmatch(r"[a-z0-9.-]{1,100}", model):
        raise HTTPException(503, "The answer model is not configured correctly.")
    return model


async def model_request(client: httpx.AsyncClient, operation: str, payload: dict) -> dict:
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        raise HTTPException(503, "The AI provider is not connected yet.")
    try:
        response = await client.post(API_ROOT + operation, headers={"x-goog-api-key": key}, json=payload)
        if response.status_code == 429:
            raise HTTPException(429, "The free AI quota is currently exhausted. Please try again later.")
        if response.status_code in (401, 403, 404):
            raise HTTPException(503, "The AI provider needs attention from the site operator.")
        response.raise_for_status()
        return response.json()
    except HTTPException:
        raise
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(503, "The AI provider is temporarily unavailable. Please retry.") from exc


def normalize(values: list[float]) -> list[float]:
    if len(values) != 768 or not all(isinstance(v, (float, int)) and math.isfinite(v) for v in values):
        raise ValueError("Invalid provider embedding")
    length = math.sqrt(sum(v * v for v in values))
    if length == 0:
        raise ValueError("Empty provider embedding")
    return [v / length for v in values]


async def embed(texts: list[str], *, query: bool = False) -> list[list[float]]:
    semaphore = asyncio.Semaphore(2)
    async with httpx.AsyncClient(timeout=httpx.Timeout(25, connect=5)) as client:
        async def batch(items):
            async with semaphore:
                response = await model_request(client, EMBEDDING_MODEL + ":batchEmbedContents", {
                    "requests": [{
                        "model": "models/" + EMBEDDING_MODEL,
                        "content": {"parts": [{"text": text}]},
                        "taskType": "RETRIEVAL_QUERY" if query else "RETRIEVAL_DOCUMENT",
                        "outputDimensionality": 768,
                    } for text in items],
                })
            try:
                embeddings = [normalize(item["values"]) for item in response["embeddings"]]
                if len(embeddings) != len(items):
                    raise ValueError("Incomplete embeddings")
                return embeddings
            except (KeyError, TypeError, ValueError) as exc:
                raise HTTPException(502, "The AI provider returned an unreadable embedding. Please retry.") from exc
        groups = await asyncio.gather(*(batch(texts[start:start + 32]) for start in range(0, len(texts), 32)))
    return [embedding for group in groups for embedding in group]
