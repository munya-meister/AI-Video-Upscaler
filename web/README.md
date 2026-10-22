# VIDEL Web Workspace (foundation)

This is a **functional browser-based editor shell** alongside the existing PySide6 desktop app. It is not yet a production AI upscaler.

## Run locally

Install Node.js 20+ and run:

```bash
cd web
npm install
npm run dev
```

Open the URL shown by Vite. Use `npm run build` to build static assets into `web/dist`.

## Current capabilities
- Responsive dark/lime dashboard and canvas-style workspace.
- Import a video from disk or drop it onto the canvas.
- Navigate directly to workspace after importing.
- Browser video playback, seek bar, resolution and quality selections.
- Session-only current project; original-video preview.
- Honest disabled/pending AI processing and enhanced export; no fake processing.

## Architecture roadmap
- **Web UI:** React/Vite, deployable as a static site (e.g. Vercel root directory `web`).
- **Desktop:** package the same UI with Tauri and a native sidecar / local Python FastAPI bridge. The existing PySide6 desktop app remains untouched until migration is validated.
- **Local engine:** expose existing Real-ESRGAN/FFmpeg functionality behind a secure localhost API with upload/path validation, cancellation, progress streaming, and temporary-file cleanup.
- **Cloud engine:** separate authenticated API, object storage, queued GPU workers, per-user quotas, and signed output URLs. Static hosting alone cannot run GPU upscaling.
- **Projects:** add persistent project metadata and secure file storage when account features are ready.

Do not expose a local file-processing API to public internet. Do not commit engine binaries, video uploads, credentials, or outputs.

## Notes
Browser playback depends on the video's codec. Files remain local for preview. There is no cloud upload in this foundation.
