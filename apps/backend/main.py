import hmac
import os
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail closed: a missing internal key must never expose guest data.
    if len(os.environ.get("INTERNAL_API_SECRET", "")) < 32:
        raise RuntimeError("Set INTERNAL_API_SECRET to at least 32 random characters")
    yield


app = FastAPI(title="AskDocs private API", version="0.1.0", lifespan=lifespan, docs_url=None, redoc_url=None)


@app.middleware("http")
async def authorize(request: Request, call_next):
    expected = os.environ.get("INTERNAL_API_SECRET", "")
    token = request.headers.get("authorization", "").removeprefix("Bearer ")
    if len(expected) < 32 or not hmac.compare_digest(token, expected):
        return JSONResponse({"detail": "Unauthorized service request."}, status_code=401)
    owner = request.headers.get("x-guest-id", "")
    address = request.headers.get("x-guest-address", "")
    if not re.fullmatch(r"[a-f0-9]{64}", owner) or not re.fullmatch(r"[a-f0-9]{64}", address):
        return JSONResponse({"detail": "Invalid guest identity."}, status_code=400)
    request.state.owner = owner
    request.state.address = address
    try:
        response = await call_next(request)
    except HTTPException as exc:
        response = JSONResponse({"detail": exc.detail}, status_code=exc.status_code)
    response.headers["Cache-Control"] = "private, no-store"
    return response


@app.get("/health")
async def health():
    return {"status": "ok"}
