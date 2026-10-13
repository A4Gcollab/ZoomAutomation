# ZoomAutomation — Developer Guide

**Repo:** `A4Gcollab/ZoomAutomation`  ·  **Production branch:** `feature/hevc-hibernation` (pending merge to `main`)
**Live at:** https://za.omysha.org  ·  **Host:** master prod box `139.84.154.64`, path `/opt/ZoomAutomation`
**Last updated:** 2026-10-13

> This guide documents the current architecture, deployment, auth, operations, and **every change made
> from the original version**. For the quick inventory of config/token files see also
> `docs/MASTER_DOCUMENTATION.md`.

---

## 1. What it does

ZoomAutomation ("ytz") automatically offloads Zoom cloud recordings so Zoom storage stays clear:

```
Zoom cloud recording
   → downloaded to the server
   → uploaded to YouTube (unlisted) and added to the right playlist
   → (night) HEVC-compressed and uploaded to Google Drive
   → once YouTube + Drive are both verified, the recording is trashed from Zoom
```

A Next.js dashboard (`za.omysha.org`) shows the pending queue, completed history, and system logs, and
lets an admin assign a playlist to recordings that didn't auto-match.

---

## 2. Architecture

| Component | Tech | Notes |
|---|---|---|
| **Backend / pipeline** | FastAPI + a `BackgroundService` thread (`src/api.py` → `src/main.py`) | uvicorn `src.api:app` on **127.0.0.1:8001**. The pipeline runs inside the API process via the app lifespan. |
| **Frontend** | Next.js 15 (`frontend/`) | `next start` on **9002**. Firebase auth (client config via `NEXT_PUBLIC_*`). |
| **DB** | SQLite — `data/vong_v2.db` (`src/db_sql.py`) | Table `recordings` + `system_logs`. (`src/db.py` is dead TinyDB code — ignore.) |
| **Zoom** | `src/zoom_client.py` | Two Server-to-Server OAuth accounts ("Zoom Account 1/2"). |
| **YouTube** | `src/youtube_client.py` | Upload, playlist add, caption upload, quota handling. |
| **Drive** | `src/drive_client.py` | User-OAuth (default) or service-account mode. |
| **Sheets** | `src/sheets_integration.py` | Optional status mirror (service account). |
| **Playlists/config** | `config/playlists.json` | **Authoritative** map: playlist name → YouTube playlist id, Drive folder ids, matching `meeting_ids`/`keywords`. New YouTube playlists MUST be added here. |
| **HEVC worker** | `docker/compress_worker.py` | Night-only compression container (see §5). |

### Pipeline phases (one `BackgroundService` cycle, ~every 60 s)
1. **Scan** — pull new recordings from both Zoom accounts; auto-match to a playlist by `meeting_id` then
   `keywords` → `APPROVED`, else `PENDING_PLAYLIST` (admin picks via the dashboard / `api.py` approve).
2. **Process queue** — for each `APPROVED`: download from Zoom → upload to YouTube (unlisted) + add to
   playlist → mark `COMPLETED`. (Transcript → Drive; **video → Drive is now deferred to the HEVC worker**, see §6.)
3. **Compressing queue** — recordings waiting on YouTube's own post-upload processing.
4. **Cleanup (Zoom deletion gate)** — `_cleanup_zoom_recordings`: for `COMPLETED` records past
   `deletion_ready_at` (= completion + `DELETE_DELAY_HOURS`, default **24h**), **re-verify** and trash from Zoom
   **only if** `get_video_status(video_id) ∈ {uploaded, processed}` **AND** `drive_url` is set. Otherwise →
   `VERIFICATION_FAILED` and the recording stays in Zoom. Deletion uses `action="trash"` (30-day recoverable).

### `recordings` key columns
`zoom_id` (PK, per-instance UUID), `meeting_id`, `topic`, `start_time`/`date_str`, `status`
(`PENDING`→`PENDING_PLAYLIST`/`APPROVED`→`PROCESSING`→`COMPLETED`; also `ERROR`, `UNRECOVERABLE`,
`YOUTUBE_COMPRESSING`), `youtube_url`, `drive_url`, `playlist`, `team`, `zoom_deletion_status`
(`PENDING`/`DELETED`/`FAILED`/`VERIFICATION_FAILED`), `deletion_ready_at`, `drive_uploaded_at`.
**Added by the HEVC worker:** `compressed`, `compressed_at`, `compress_attempts`, `compress_error`,
`compress_last_attempt`.

---

## 3. Deployment (Docker)

Production runs in **Docker** (migrated off pm2 on 2026-10-12). Files live in `docker/`.

| File | Purpose |
|---|---|
| `docker/Dockerfile.app` | **One combined container**: FastAPI backend (8001) **and** Next.js frontend (9002). Python 3.12 + Node 20 + ffmpeg, both run by **`supervisord -n`** (foreground — the `-n` is required or the container crash-loops). |
| `docker/Dockerfile.hevc` | Lean Python+ffmpeg image for the compression worker. |
| `docker/supervisord.conf` | Runs `uvicorn …:8001` + `next start …:9002`. |
| `docker/docker-compose.yml` | `app` service (always on) + `hevc` service (profile-gated, `restart:"no"`, started by a timer). |
| `docker/.env` | Build-time `NEXT_PUBLIC_*` (Firebase client + API URL). **git-ignored**; seeded from the live frontend `.env.local`. |
| `docker/systemd/ytz-hevc.{service,timer}` | Host timer that starts the hevc container nightly. |
| `.github/workflows/deploy.yml` | Manual (`workflow_dispatch`) deploy: SSH → `git` checkout → `docker compose build` + `up -d`. |

**Runtime volumes (on the host, mounted in):** `secrets/`, `data/` (SQLite), `config/` (playlists.json),
`downloads/` (scratch), and `.env` (backend runtime env).

### Build / deploy (manual, first time)
```bash
cd /opt/ZoomAutomation/docker
cp .env.example .env     # fill NEXT_PUBLIC_* from the live frontend .env.local
docker compose build
pm2 stop ytz-backend ytz-frontend && pm2 save   # free ports 8001/9002 (first cutover only)
docker compose up -d app                         # hevc is profile-gated, NOT started here
# nightly HEVC timer:
sudo cp systemd/ytz-hevc.service systemd/ytz-hevc.timer /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now ytz-hevc.timer
```
`app` has `restart: unless-stopped` (survives reboot). nginx proxies `za.omysha.org` → 9002/8001.

**Deploy user:** `ytz-deploy` (docker group, SSH key authorized). GitHub secrets: `SSH_HOST`, `SSH_USER`,
`SSH_KEY`. ⚠️ The deploy workflow pulls the ref you choose — **prod currently runs `feature/hevc-hibernation`,
not `main`**; merge that branch to `main` before deploying `main`, or it reverts Plan A.

---

## 4. Authentication & Google projects

There are **three distinct Google identities** — keep them straight:

| Thing | Identity | Used for |
|---|---|---|
| **OAuth client** `148894103613-….apps.googleusercontent.com` | Cloud project **`yt-quota-test`** (#148894103613), owned by **`vong.meetings2@gmail.com`** | The app registration. Mints the YouTube **and** Drive user-tokens. |
| **User tokens** `secrets/token_youtube.json`, `secrets/token_drive.json` (pickled `google.oauth2` Credentials) | Whoever clicked **Allow** → **`a4gcollab@gmail.com`** for Drive (owns the folders), and the A4G-channel account for YouTube | Acting on the user's behalf. |
| **Service account** `yt-to-drive-uploader@yt-and-zoom-automation.iam.gserviceaccount.com` | Cloud project `yt-and-zoom-automation` | Sheets + **read-only** Drive helper. **Cannot upload** ("Service Accounts do not have storage quota" — folders are in a user My Drive). |

- `DRIVE_AUTH_MODE=user` (default). `client_secret.json` on the server is a *leftover* `vong-youtube`
  (`382895926502`) client — **not** what the live tokens use; the tokens carry their own client_id/secret.
- **Drive folders** are owned by **`a4gcollab@gmail.com`** (writers also include `mohommadshahjad22112002@gmail.com`
  and the service account); a couple of folders are owned by the service account. Folder ids are in
  `config/playlists.json`.
- The OAuth consent screen (`yt-quota-test`) is published **"In production"** → refresh tokens are **long-lived**
  (don't time-expire). They can still be **revoked** (re-auth elsewhere, manual removal, >50-token limit, 6-month
  inactivity, password change).

### Re-authorizing Drive (runbook — tokens are pickled Credentials)
The repo ships `scripts/setup_youtube.py` (YouTube token). Drive uses the same flow with Drive scopes
(`…/auth/drive` + `…/auth/spreadsheets`) saved to `token_drive.json`. Because the server is headless:

1. Build an `InstalledAppFlow` from the client_id/secret (reuse the ones embedded in `token_youtube.json`, or a
   downloaded `yt-quota-test` Desktop client).
2. On the server: `flow.run_local_server(host="127.0.0.1", port=<P>, open_browser=False)` → prints the auth URL.
3. From your PC: `ssh -L 127.0.0.1:<P>:127.0.0.1:<P> root@139.84.154.64` (tunnel), open the auth URL, **sign in
   as `a4gcollab@gmail.com`**, pass the "unverified app" screen (**Advanced → Go to yt-quota-test**), **Allow**.
4. The redirect hits the tunnel → the flow saves `secrets/token_drive.json`. Restart `ytz-app` (or wait a cycle —
   `_init_clients` retries) → `Drive client ready`.

Tokens are backed up under `secrets/_backup/` before any change.

---

## 5. The HEVC compression worker (`docker/compress_worker.py`)

Nightly, resource-capped container that shrinks recordings to HEVC (~72% smaller).

- **Hibernation:** NOT always-on. `ytz-hevc.timer` starts it at **16:30 UTC (22:00 IST)**; the worker drains
  the queue + retries then **exits** when nothing's left or the window (`HEVC_WINDOW_UTC=16:30-01:30`) closes.
  `restart:"no"` + the compose `hevc` profile mean it uses **0 RAM during the day**.
- **Two tiers (new first):**
  1. **New (from Zoom):** `COMPLETED` + on YouTube + **no Drive copy yet** → re-fetch the raw MP4 from **Zoom** →
     HEVC-encode → upload **only the compressed** file to the playlist's Drive folder → set `drive_url`.
  2. **Backlog (fill-in, only when no new left):** recordings that already have a raw Drive copy → download
     from Drive → compress → replace → delete the old raw.
  New videos (including ones in retry cooldown) have **absolute priority**; the worker waits for them rather than
  starting a long backlog encode.
- **Retry:** `compress_attempts` per row, `HEVC_MAX_ATTEMPTS=3` lifetime, ≥`HEVC_COOLDOWN_MIN=15` min apart. A
  failure never touches Zoom. Errors go to the row (`compress_error`) **and** `system_logs` (dashboard "System
  Logs" tab). Reset a parked video: `UPDATE recordings SET compress_attempts=0, compress_error=NULL WHERE zoom_id='…';`
- Reuses `BackgroundService._init_clients()` for the Zoom/Drive clients (no duplicated logic).

Tunables (compose `environment:`): `HEVC_WINDOW_UTC`, `HEVC_CRF` (28), `HEVC_MAX_ATTEMPTS`, `HEVC_COOLDOWN_MIN`,
`HEVC_IGNORE_WINDOW=1` (run once on demand).

---

## 6. Changes from the original version

| Area | Original | Now |
|---|---|---|
| **Repo state** | Original GitHub code (archived at tag/branch `old-archived-do-not-deploy`, `a6bc95a`). | The **live server code** became `main` (`043b9af`); Docker/HEVC work on `feature/hevc-hibernation`. |
| **Runtime** | Two `pm2` processes (`ytz-backend` on `/opt/ZoomAutomation`, `ytz-frontend` on `/opt/ytz-automation/frontend`). | **One combined Docker container** `ytz-app` (backend+frontend via `supervisord`), `restart:unless-stopped`. pm2 kept stopped for rollback. |
| **Drive copy** | Pipeline uploaded the **raw** video to Drive during processing. | **Plan A:** pipeline no longer uploads the raw video to Drive; the **HEVC worker uploads only the compressed copy** (no double upload). The Zoom-deletion gate now naturally waits for that compressed copy. |
| **Compression** | None. | **HEVC (libx265 CRF 28)** in a hibernating night-only worker + nightly `systemd` timer; new-first + backlog fill-in; retry + logging. |
| **Deploy** | Manual / ad-hoc. | `.github/workflows/deploy.yml` (manual dispatch, Docker build+up) + `ytz-deploy` user + GitHub secrets. |
| **Dependencies** | Unpinned. | **Google stack pinned** to the host's proven versions (`google-auth==2.49.1`, `google-auth-oauthlib==1.3.1`, `google-api-python-client==2.193.0`, `gspread==6.2.1`, `oauth2client==4.1.3`) — newer `google-auth` couldn't read the **pickled** Drive token. |
| **Container fix** | — | `supervisord` must run with **`-n`** (foreground) or the container crash-loops. |
| **Auth docs** | Implicit. | This guide + the re-auth runbook (§4); identified that the live OAuth client is `yt-quota-test`/`148894103613` (not the leftover `vong-youtube` `client_secret.json`). |

### Notable incidents resolved
- **Cryptominer era (separate repo A4G Hub):** unrelated to this repo; ytz was a CPU-starved victim on the old
  shared box, since migrated.
- **Drive token revoked (~2026-10-10):** `invalid_grant: Token has been expired or revoked` — a **revocation**,
  not the Docker migration and not a Testing-mode expiry (the consent app is in Production). Fixed by re-auth
  (§4). The migration was proven innocent (Drive was already failing before the cutover).

---

## 7. Operations quick-reference

```bash
# --- SSH ---
ssh -i "<key>" root@139.84.154.64           # master box, /opt/ZoomAutomation

# --- app ---
cd /opt/ZoomAutomation/docker
docker compose ps                            # app status
docker logs -f ytz-app                        # live logs (backend + frontend)
docker compose up -d app                      # (re)start the app container

# --- HEVC worker ---
systemctl list-timers ytz-hevc.timer          # next night run
HEVC_IGNORE_WINDOW=1 docker compose --profile hevc up hevc   # run once now (heavy encode)

# --- DB (no sqlite3 CLI installed; use the venv python) ---
venv/bin/python -c "import sqlite3;c=sqlite3.connect('data/vong_v2.db'); \
  print(c.execute(\"SELECT status,COUNT(*) FROM recordings GROUP BY status\").fetchall())"

# --- rollback to pm2 (if a deploy goes bad) ---
docker compose stop app && cd /opt/ZoomAutomation && pm2 start ytz-backend ytz-frontend
```

### Common gotchas
- **`playlists.json` is authoritative** — add new YouTube playlists there (name, playlist_id, drive folders,
  keywords/meeting_ids) or videos default to "Miscellaneous".
- A recording stuck as **`VERIFICATION_FAILED`** means the Zoom-deletion gate failed (usually no Drive copy) —
  it stays safe in Zoom. Fix the Drive side, then it clears.
- **Repo/secrets:** `secrets/`, `data/`, `.env*` are git-ignored and must never be committed.
- The dashboard's `pending-queue` / `completed-history` still carry mock-data fallbacks — wire to the real API
  before trusting any baked-in numbers.
