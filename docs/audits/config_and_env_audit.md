# Config & Environment Audit

## Detected Variables in Code
- `OPENJARVIS_ROOT`
- `TELEGRAM_BOT_TOKEN`
- `GITHUB_TOKEN`
- `JARVIS_BRIDGE_URL`
- `VIDEO_API_URL`
- `COMFYUI_URL`
- `N8N_WEBHOOK_URL`
- `N8N_MEDIA_WEBHOOK`
- `N8N_GITHUB_WEBHOOK`
- `N8N_MYSTIC_WEBHOOK`
- `LOCAL_LLM_URL`
- `GEMINI_API_KEY`
- `CHROMA_HOST`
- `CHROMA_PORT`
- `ZOM_ENABLE_LIVE_TRADING`

## Risk Assessment
- `ZOM_ENABLE_LIVE_TRADING` defaults to `false` (SAFE).
- `GEMINI_API_KEY` checked explicitly for missing status.
- Hardcoded fallback ports/URLs (e.g., `http://jarvis_bridge:7000/query`) are present but standard for Docker networks.
