# VIDEL Cloud GPU MVP

**Architecture:** Vercel (React) → Supabase Auth (JWT) → HTTPS FastAPI on a separate GPU VM → FFmpeg / Real-ESRGAN NCNN Vulkan → private local output → authenticated download.

The API is a **single-host MVP**, not a horizontally scalable or production-hardened paid service. It requires a GPU host with a working Vulkan driver, NCNN binary and model files. It will **not** run on Vercel. The existing Windows Python desktop engine remains unchanged.

## Setup

1. Provision a GPU machine with a Vulkan-capable GPU, installed Vulkan driver, FFmpeg, FFprobe, Python 3.11+, and Real-ESRGAN NCNN Vulkan plus the `realesrgan-x4plus` model.
2. `cd cloud && python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt` (Windows: `.venv\\Scripts\\activate`).
3. Set environment variables from `.env.example` with real values. Use a **persistent private disk** for `VIDEL_DATA_DIR`.
4. Run `uvicorn api:app --host 127.0.0.1 --port 8000 --workers 1`.
5. Put an HTTPS reverse proxy with request body limits, rate limits and timeouts in front of port 8000. Never expose raw development Uvicorn publicly.
6. Configure Supabase Auth email login and allowlisted redirect URLs for the Vercel domain.
7. In Vercel project settings for `web`, set `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` (public/publishable key, **never** service role), and `VITE_VIDEL_API_URL` (HTTPS GPU API URL). Redeploy.

**Supabase JWT compatibility:** This MVP validates asymmetric RS256/ES256 tokens via Supabase's JWKS endpoint. In Supabase, use an asymmetric JWT signing key. Legacy HS256 JWT projects must migrate their signing key before using this implementation.

## API
- `GET /health` — service health.
- `POST /jobs?scale=2&quality=High%20Quality` — authenticated multipart `file` upload; creates queued job.
- `GET /jobs/{id}` — authenticated status/progress.
- `GET /jobs/{id}/download` — authenticated MP4 output.

Limits default to 250 MB, 120 seconds, 1920×1080 source, one active job per account, four queued/running globally, one processing worker. Only 2× and 4× are supported. Processing can take significant time; 4× output from 1080p may be extremely expensive. Browser uploads go **directly to the GPU API** (not through Vercel).

## Before opening to real users
- Replace process-memory job tracking and local disk with durable Postgres/Redis queue, private object storage and signed download URLs; add job recovery on restart, cleanup/retention and cancellation.
- Add quota enforcement, billing protections, abuse prevention, storage capacity monitoring, global rate limiting, observability, antivirus/media validation as appropriate, and a tested GPU capacity plan.
- Run GPU smoke tests with short videos. Test memory pressure, concurrency, output playback and audio preservation.
- Secure the host with TLS, firewall, least-privilege execution, restricted outbound access and a maintained patch/update process.
- Consider switching to a CUDA/PyTorch engine on NVIDIA hosts; this implementation specifically uses NCNN Vulkan.

No credentials, model binaries or uploaded videos belong in Git.
