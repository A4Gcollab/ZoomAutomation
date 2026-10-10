# ZoomAutomation — COMBINED container: FastAPI/uvicorn backend (8001) + Next.js frontend (9002).
# One image, both runtimes (Python 3.12 to match the live venv + Node 20), run by supervisord.
# ffmpeg is included so the backend's yt-dlp/processing keeps working exactly as on the live box.
#
# NOTE: combining two runtimes in one container is deliberate (requested). supervisord supervises
# both processes; see docker/supervisord.conf.

# ---- Stage 1: build the Next.js frontend ----
# The NEXT_PUBLIC_* values are inlined into the CLIENT bundle at build time, so they MUST be
# present here. They are Firebase *client* config + the public API base URL (not server secrets),
# but we still never bake them into git — they come in as --build-arg (see docker/.env.example).
FROM node:20-slim AS fe-build
WORKDIR /fe
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
ARG NEXT_PUBLIC_FIREBASE_API_KEY
ARG NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN
ARG NEXT_PUBLIC_FIREBASE_PROJECT_ID
ARG NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET
ARG NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID
ARG NEXT_PUBLIC_FIREBASE_APP_ID
ARG NEXT_PUBLIC_API_BASE_URL
ARG NEXT_PUBLIC_WS_URL
ENV NEXT_PUBLIC_FIREBASE_API_KEY=$NEXT_PUBLIC_FIREBASE_API_KEY \
    NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=$NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN \
    NEXT_PUBLIC_FIREBASE_PROJECT_ID=$NEXT_PUBLIC_FIREBASE_PROJECT_ID \
    NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET=$NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET \
    NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID=$NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID \
    NEXT_PUBLIC_FIREBASE_APP_ID=$NEXT_PUBLIC_FIREBASE_APP_ID \
    NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_WS_URL=$NEXT_PUBLIC_WS_URL
RUN NODE_ENV=production npm run build

# ---- Stage 2: combined runtime ----
FROM python:3.12-slim
WORKDIR /app

# Node 20 runtime (for `next start`) + ffmpeg (libx265/HEVC + yt-dlp) + supervisor + tini.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ca-certificates curl gnupg ffmpeg supervisor tini \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Backend source (frontend/ source is copied too, then overwritten by the built copy below).
# secrets/, data/, config/, downloads/ are NOT baked in — they are mounted at runtime (.dockerignore).
COPY . .

# Built frontend (has .next + node_modules + package.json) from stage 1
COPY --from=fe-build /fe /app/frontend

# supervisord program definitions
COPY docker/supervisord.conf /etc/supervisor/conf.d/ytz.conf

EXPOSE 8001 9002
ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["supervisord","-c","/etc/supervisor/supervisord.conf"]
