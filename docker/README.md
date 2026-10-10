# ZoomAutomation — Docker setup (backend+frontend combined, + HEVC worker)

> **Status: NOT deployed.** These files let us build/run ytz in containers. The live box still runs
> via `pm2` (`ytz-backend`, `ytz-frontend`). Containerizing on the master/IdP box stays **deferred**
> until ytz moves to its own host. This is here so the setup is ready and reviewed.

## What's here

| File | Purpose |
|------|---------|
| `Dockerfile.app` | **Combined** container: FastAPI/uvicorn backend (`8001`) **and** Next.js frontend (`9002`), Python 3.12 + Node 20 + ffmpeg, both run by `supervisord`. |
| `Dockerfile.hevc` | Lean Python+ffmpeg image that runs `compress_worker.py`. |
| `compress_worker.py` | Night-time HEVC compressor (see below). |
| `supervisord.conf` | Runs uvicorn + `next start` inside the `app` container. |
| `docker-compose.yml` | Wires both containers + host volumes + ports. |
| `.env.example` | Build-time `NEXT_PUBLIC_*` values for the frontend (copy to `docker/.env`). |

## Runtime inputs (all on the host, mounted in — never baked into the image)

- `../.env` — backend runtime env (same file the live backend uses).
- `../secrets/` — Drive/YouTube/Zoom credentials & tokens.
- `../data/` — the shared SQLite DB (`vong_v2.db`).
- `../config/` — `playlists.json` etc.
- `../downloads/` — scratch space for the HEVC worker.
- `docker/.env` — frontend build args (`NEXT_PUBLIC_*`), **git-ignored**; copy from `.env.example`
  and fill from the live `/opt/ytz-automation/frontend/.env`. These are Firebase *client* config +
  the public API URL (safe in the browser bundle), kept out of git regardless.

## Build & run (on the server, when we eventually cut over)

```bash
cd docker
cp .env.example .env     # fill NEXT_PUBLIC_* from the live frontend .env
docker compose build
# stop pm2 first so ports 8001/9002 are free:  pm2 stop ytz-backend ytz-frontend
docker compose up -d
docker compose logs -f
```
Ports publish on `127.0.0.1` only; nginx (`za.omysha.org`) proxies to them.

## The HEVC worker (`compress_worker.py`)

**Baseline behaviour = shrink the Drive copy *in place* at night ("Plan C").** It makes **zero**
changes to the live pipeline and never touches Zoom or YouTube:

1. In the night window, pick one `COMPLETED` recording whose Drive copy is still raw (`compressed=0`).
2. Download the raw from Drive → HEVC-encode (`libx265 -crf 28`, one nice'd core) → upload the
   compressed file to the same Drive folder → verify it (size matches, and smaller than raw).
3. **Only then** delete the old raw Drive file, repoint `recordings.drive_url`, set `compressed=1`.

So the raw Drive copy is deleted only after the compressed one is verified, and YouTube stays as the
second backup the whole time. **End state = Drive holds only the compressed file** — identical to
"Plan A"; the only difference is the raw sits on Drive for a few hours instead of never.

It self-adds the `compressed` / `compressed_at` columns to the `recordings` table (idempotent).

Tunables (compose `environment:`): `HEVC_WINDOW_UTC` (default `18:00-00:30` = 23:30–06:00 IST),
`HEVC_CRF` (default `28`).

> **If we instead want "Plan A"** (never put the raw on Drive — upload to YouTube by day, download
> from Zoom at night, upload only the compressed copy to Drive): that's a small follow-up requiring
> a change to `src/main.py` (skip the Drive raw-upload + adjust the Zoom-deletion verification gate,
> which today just checks that `drive_url` is non-empty). Not done here to keep this branch
> non-invasive and the live pipeline untouched.
