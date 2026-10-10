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
docker compose build     # builds app (+ the hevc image via its profile)
# stop pm2 first so ports 8001/9002 are free:  pm2 stop ytz-backend ytz-frontend && pm2 save
docker compose up -d     # starts ONLY the always-on `app` (hevc is profile-gated out)
docker compose logs -f
```
Ports publish on `127.0.0.1` only; nginx (`za.omysha.org`) proxies to them.

The **hevc** worker is *not* started by `up -d` — install its nightly timer instead:
```bash
sudo cp systemd/ytz-hevc.service systemd/ytz-hevc.timer /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now ytz-hevc.timer
# optional immediate test (bypasses the clock): HEVC_IGNORE_WINDOW=1 docker compose --profile hevc up hevc
```

## The HEVC worker (`compress_worker.py`)

**What it does = shrink the Drive copy *in place* at night.** Zero changes to the live pipeline;
never touches Zoom or YouTube:

1. Pick a `COMPLETED` recording whose Drive copy is still raw (`compressed=0`).
2. Download the raw from Drive → HEVC-encode (`libx265 -crf 28`, one nice'd core) → upload the
   compressed file to the same Drive folder → verify (size matches, and smaller than raw).
3. **Only then** delete the old raw Drive file, repoint `recordings.drive_url`, set `compressed=1`.

The raw is deleted only after the compressed copy is verified, and YouTube stays as the second
backup throughout. **End state = Drive holds only the compressed file.**

### Hibernation (0 RAM during the day)
The worker is **not** always-on. A systemd timer (`docker/systemd/`) starts the container nightly;
the worker drains the queue + retries, then **exits** when nothing eligible is left or the window
closes. With `restart: "no"` + the compose `hevc` profile (so `up -d` skips it), the container is
**stopped all day → 0 RAM**, and only runs at night. Set `HEVC_IGNORE_WINDOW=1` to run once on demand.

### Retry (round-robin, same night)
Always takes the eligible video with the **fewest attempts** whose cooldown has elapsed: tries A,
and if A fails it moves to B, C… then comes back to A. Each video gets up to **`HEVC_MAX_ATTEMPTS`
(3)** lifetime attempts, at least **`HEVC_COOLDOWN_MIN` (15)** minutes apart — so a transient blip is
retried, a sole failing video isn't hammered, and unfinished retries spill to the next night if the
window closes. After MAX attempts it's **parked**; reset it with:
```sql
UPDATE recordings SET compress_attempts=0, compress_error=NULL WHERE zoom_id='<uuid>';
```
A failure **never touches Zoom** — the Zoom-deletion gate is independent, so a bad encode can't cost
a recording.

### Error logging
On the recording's row: `compress_error`, `compress_attempts`, `compress_last_attempt`. Also inserted
into the app's **`system_logs`** table (same shape as the pipeline's `db.add_log`), so failures show
up in the **dashboard's "System Logs" tab**, e.g. `[hevc] FAILED <topic> (attempt 2/3): <error>`.

The worker self-adds `compressed, compressed_at, compress_attempts, compress_error,
compress_last_attempt` to `recordings` on first run (idempotent).

### Tunables (compose `environment:`)
`HEVC_WINDOW_UTC` (default `16:30-01:30` UTC = **22:00–07:00 IST**), `HEVC_CRF` (default `28`),
`HEVC_MAX_ATTEMPTS` (default `3`), `HEVC_COOLDOWN_MIN` (default `15`).
