# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A FastAPI REST API that remotely controls OBS Studio via its WebSocket plugin (`obs-websocket`, v5 protocol). It lets an external system update text sources, toggle scene items, start/stop recordings, and fetch the most recent recording as a downloadable/streamable URL with a QR code. Everything is in Portuguese (docstrings, log messages, README) — match that when editing existing files.

## Commands

```powershell
# First run: creates .venv, installs requirements.txt, then starts the API
./start.ps1

# Manual equivalent
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
python main.py
```

There is no test suite, linter, or formatter configured in this repo.

`ffmpeg` must be installed and on `PATH` — `app/services/video_overlay.py` shells out to it to composite the overlay image onto recordings.

The API listens on `HOST:PORT` from settings (default `0.0.0.0:8000`; `.env.example`/README show `8003` as the conventional local port). Interactive docs are served at `/docs`.

## Configuration

Settings are defined in `app/core/config.py` as a pydantic-settings `Settings` class, loaded from a `.env` file (see `.env.example` for the full list with defaults). Key ones for this API's actual behavior:

- `OBS_HOST` / `OBS_PORT` / `OBS_PASSWORD` — obs-websocket connection.
- `OBS_RECORDING_DIR` — **must be an absolute path**; `OBSService._get_full_recording_path` raises `ValueError` otherwise. Recordings are written here and also read back from here to find/rename the latest file.
- `PUBLIC_BASE_URL` — required for `/api/recording/getvideo`; used to build the public `/videos/{uuid}` URL that gets QR-encoded.
- `DELETE_OLD_FILES(_MAX_LIFE|_MAX_POLL)` — enables a background loop (started in `app/main.py` on FastAPI startup) that deletes recordings older than `DELETE_OLD_FILES_MAX_LIFE` minutes.
- A number of settings fields (JWT_*, SENTRY_DSN, SHORTENER_*, CADASTRO_BASE_URL, UDP_PORT, SERIAL_*) exist in `Settings` and `.env.example` but are **not read anywhere in `app/`** — they're leftovers from a related/future project, not active configuration for this API.

MongoDB was used historically for video URL storage; it has since been removed in favor of pure UUID filename mapping (see git history). `app/db/__init__.py` is now an empty stub. **The README still describes the old MongoDB-based flow — it's out of date; trust the code, not the README, for `/api/recording/getvideo` behavior.**

## Architecture

```
main.py                        # entrypoint: uvicorn.run("app.main:app", ...)
app/
├── main.py                    # FastAPI app factory (create_app), startup/shutdown hooks, /videos/{filename}, /, /health
├── api/obs.py                 # all HTTP routes, under prefix /api
├── models/obs.py               # Pydantic request/response schemas
├── services/
│   ├── obs_service.py          # OBSService — owns the obs-websocket connection + all OBS logic; module-level singleton `obs_service`
│   ├── cleanup_service.py      # background loop that deletes recordings older than DELETE_OLD_FILES_MAX_LIFE
│   └── video_overlay.py        # apply_overlay() — composites app/assets/ecco_msg.png over a recording via ffmpeg
├── core/config.py              # pydantic-settings Settings + get_settings() (lru_cache'd)
└── utils/                      # legacy/unused code, not imported by app/ (see below)
tools/
└── fullscreen_clock.py         # standalone pygame utility to visually test recording sync (not part of the API)
```

**Connection model**: `obs_service` (in `app/services/obs_service.py`) is a single module-level `OBSService` instance shared by the whole app — not a per-request dependency. Most endpoints call `obs_service.ensure_connection()` to lazily (re)connect rather than requiring an existing connection; a few (`/api/text/update`, `/api/status`, `/api/recording/directory` GET/POST) check `obs_service.is_connected` and fail instead of auto-connecting. Keep this distinction in mind when adding endpoints.

**Video file flow**: OBS writes recordings with its own filename to `OBS_RECORDING_DIR`. `OBSService.ensure_latest_recording_has_uuid_name()` finds the newest video file there (by mtime, matched against `VIDEO_EXTENSIONS`) and renames it to `<uuid4>.<ext>` if it isn't already UUID-named — with retries, since OBS may still hold the file open right after `StopRecord`. This is called both when recording stops and when `/api/recording/getvideo` is hit, so a file that was open during stop still gets renamed on the next `getvideo` poll. If renaming fails on every retry, the endpoint returns an error rather than ever exposing the OBS-generated (date-based) filename publicly. Immediately after a successful rename in `stop_recording()`, `video_overlay.apply_overlay()` re-encodes the file in place (via ffmpeg, same UUID filename) to burn `app/assets/ecco_msg.png` over the whole video; if ffmpeg is missing or fails, this is logged and the original (un-overlaid) recording is left in place rather than failing the stop-recording call. This overlay step only fires from `stop_recording()` — a recording whose rename was still locked at stop time and only completes later via a `getvideo` poll will not get the overlay. `app/main.py` serves the file straight off disk at `GET /videos/{filename}`, sanitizing the filename via `Path(filename).name` to prevent path traversal — there is no database lookup involved.

**Scene item / text source lookups**: OBS's WebSocket API doesn't support looking up a source nested inside a group directly, so `OBSService` implements recursive group search (`_find_source_in_groups` → `_search_source_in_scene` → `_is_group_source` / `_search_source_in_group`) to locate sources by name for both `update_text_source` and `set_scene_item_enabled`.

**`app/utils/`** (`obs_controller.py`, `shotener_client.py`, `singleton.py`) is dead code not imported by anything under `app/`: `obs_controller.py` is an earlier, unused duplicate of `OBSService`; `shotener_client.py` imports modules (`schemas.shortener`, `core.config` at the repo root) that don't exist in this project. Don't extend these — extend `app/services/obs_service.py` instead. If you're cleaning up, confirm with the user before deleting, since it's unclear whether this is meant to be wired in later.

**`tools/fullscreen_clock.py`** is a standalone dev utility (own `tools/requirements.txt`, pygame) for visually verifying recording timing/sync — not imported by the API, run directly with `python tools/fullscreen_clock.py`.
