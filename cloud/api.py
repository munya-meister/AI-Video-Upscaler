"""VIDEL single-host GPU MVP. Supabase JWT required; jobs owned per user.

IMPORTANT: disk jobs are process-local. Deploy with ONE Uvicorn worker and
persistent private volume. Use durable DB/object storage + queue before scaling.
"""
from __future__ import annotations
import asyncio
import os
import re
import secrets
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

import jwt
from jwt import PyJWKClient
from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from engine import enhance, probe

SUPABASE_URL = os.environ.get("VIDEL_SUPABASE_URL", "").rstrip("/")
if not SUPABASE_URL or urlparse(SUPABASE_URL).scheme != "https" or not re.fullmatch(
    r"[a-zA-Z0-9-]+\\.supabase\\.co", urlparse(SUPABASE_URL).hostname or ""
):
    raise RuntimeError("Set VIDEL_SUPABASE_URL to your HTTPS Supabase project URL")
JWKS = PyJWKClient(f"{SUPABASE_URL}/auth/v1/.well-known/jwks.json", cache_keys=True)
ISSUER = f"{SUPABASE_URL}/auth/v1"
DATA = Path(os.getenv("VIDEL_DATA_DIR", "/data/videl")).resolve()
DATA.mkdir(parents=True, exist_ok=True)
MAX_BYTES = int(os.getenv("VIDEL_MAX_UPLOAD_MB", "250")) * 1024 * 1024
MAX_SECONDS = int(os.getenv("VIDEL_MAX_DURATION_SECONDS", "120"))
MAX_PIXELS = int(os.getenv("VIDEL_MAX_PIXELS", "2073600"))
origins = [x.strip() for x in os.getenv("VIDEL_CORS_ORIGINS", "").split(",") if x.strip()]
if not origins or any(not x.startswith("https://") for x in origins):
    raise RuntimeError("Set VIDEL_CORS_ORIGINS to explicit HTTPS frontend origins")

app = FastAPI(title="VIDEL GPU API", docs_url=None, redoc_url=None)
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST"],
                   allow_headers=["Authorization", "Content-Type"], allow_credentials=False)
executor = ThreadPoolExecutor(max_workers=1)
jobs: dict[str, dict] = {}
lock = threading.Lock()

def current_user(authorization: Annotated[str | None, Header()] = None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "Sign in required")
    token = authorization[7:]
    try:
        key = JWKS.get_signing_key_from_jwt(token)
        payload = jwt.decode(token, key.key, algorithms=["RS256", "ES256"],
                             audience="authenticated", issuer=ISSUER,
                             options={"require": ["exp", "sub", "iss", "aud"]})
        if payload.get("role") != "authenticated":
            raise ValueError("Invalid role")
        return str(payload["sub"])
    except Exception:
        raise HTTPException(401, "Invalid or expired session") from None

def owned(job_id: str, user: str) -> dict:
    with lock:
        job = jobs.get(job_id)
        if not job or job["user"] != user:
            raise HTTPException(404, "Job not found")
        return dict(job)

def public(job: dict) -> dict:
    return {key: job[key] for key in ("id", "state", "progress", "error", "filename", "created_at")}

def update(job_id: str, **changes) -> None:
    with lock:
        jobs[job_id].update(changes)

def process(job_id: str, source: Path, target: Path, scale: int, quality: str) -> None:
    try:
        update(job_id, state="processing", progress=3)
        enhance(source, target, scale, quality, lambda pct: update(job_id, progress=pct))
        update(job_id, state="completed", progress=100)
    except Exception as exc:
        target.unlink(missing_ok=True)
        update(job_id, state="failed", error=str(exc)[:500])
    finally:
        source.unlink(missing_ok=True)

class Settings(BaseModel):
    scale: int = Field(default=2)
    quality: str = Field(default="High Quality")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/jobs", status_code=201)
async def create_job(file: Annotated[UploadFile, File()], user: Annotated[str, Depends(current_user)],
                     scale: int = 2, quality: str = "High Quality"):
    if scale not in (2, 4) or quality not in ("Standard", "High Quality", "Maximum Quality"):
        raise HTTPException(422, "Invalid processing settings")
    if not file.filename or Path(file.filename).suffix.lower() not in (".mp4", ".mov", ".webm", ".mkv", ".avi"):
        raise HTTPException(415, "Unsupported video extension")
    with lock:
        active = sum(j["user"] == user and j["state"] in ("queued", "processing") for j in jobs.values())
        if active >= 1:
            raise HTTPException(429, "Finish your current job before starting another")
        if sum(j["state"] in ("queued", "processing") for j in jobs.values()) >= 4:
            raise HTTPException(503, "Processing queue full; retry later")
        job_id = secrets.token_hex(16)
        directory = DATA / job_id
        directory.mkdir(mode=0o700)
        source = directory / ("input" + Path(file.filename).suffix.lower())
        target = directory / "enhanced.mp4"
        jobs[job_id] = {"id": job_id, "user": user, "state": "uploading",
                        "progress": 0, "error": None, "filename": Path(file.filename).name[:150],
                        "created_at": int(time.time())}
    size = 0
    try:
        with source.open("wb") as stream:
            while chunk := await file.read(1024 * 1024):
                size += len(chunk)
                if size > MAX_BYTES:
                    raise HTTPException(413, "Video exceeds upload limit")
                stream.write(chunk)
        if size == 0:
            raise HTTPException(400, "Empty upload")
        info = await asyncio.to_thread(probe, source)
        if info["duration"] > MAX_SECONDS or info["width"] * info["height"] > MAX_PIXELS:
            raise HTTPException(413, "Video duration or resolution exceeds MVP limit")
        update(job_id, state="queued", progress=1)
        executor.submit(process, job_id, source, target, scale, quality)
        return public(owned(job_id, user))
    except HTTPException:
        with lock:
            jobs.pop(job_id, None)
        shutil.rmtree(directory, ignore_errors=True)
        raise
    except Exception:
        with lock:
            jobs.pop(job_id, None)
        shutil.rmtree(directory, ignore_errors=True)
        raise HTTPException(400, "Invalid or unsupported video") from None
    finally:
        await file.close()

@app.get("/jobs/{job_id}")
def get_job(job_id: str, user: Annotated[str, Depends(current_user)]):
    return public(owned(job_id, user))

@app.get("/jobs/{job_id}/download")
def download(job_id: str, user: Annotated[str, Depends(current_user)]):
    job = owned(job_id, user)
    if job["state"] != "completed":
        raise HTTPException(409, "Job is not complete")
    output = DATA / job_id / "enhanced.mp4"
    if not output.is_file():
        raise HTTPException(410, "Output no longer available")
    return FileResponse(output, media_type="video/mp4", filename="videl-enhanced.mp4")
