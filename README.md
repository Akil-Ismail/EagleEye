# EagleEye

AI-powered face recognition and security defense system. Detects and recognizes faces in
real time, tells authorized users from unknown/spoofed ones, and uses an LLM (Groq) to turn
raw access logs into readable incident reports.

- **Backend**: FastAPI + SQLite + Qdrant (embedded, no server to install) + InsightFace (ArcFace) + Groq
- **Frontend**: PyQt6 desktop dashboard (live camera, enrollment, logs, alerts, reports)
- No login/setup wizard — the desktop app opens straight to the dashboard, all data stored locally.

## Features

- Real-time face detection & recognition from a webcam feed
- Multi-face support — every face in frame is detected, matched, and logged independently
- Enrollment via webcam capture or uploaded photos
- Recognition via webcam, a single uploaded image, or an uploaded video (processed as a
  background job)
- Blink-based liveness check on the live camera feed (a short burst of frames is used to detect
  a real blink, so a static photo held up to the camera is rejected) — see **Limitations** below
- Access logs, alerts (unauthorized access, suspected spoofing, repeated unknown visitors), and
  AI-generated incident reports (via Groq)

## Prerequisites

- **Python 3.11+** (built and tested on 3.14)
- **Windows** with a webcam (built and tested on Windows; not tested on macOS/Linux)
- A free **Groq API key** — only needed for the Reports feature. Get one at
  [console.groq.com](https://console.groq.com); everything else works without it.
- ~1GB free disk space (InsightFace's face model pack downloads automatically on first run)

## Project structure

```
EagleEye/
  backend/     FastAPI API — DB, vector search, face recognition, LLM reports
    app/
    requirements.txt
    .env.example
  frontend/    PyQt6 desktop app
    app/
    main.py
    requirements.txt
```

## Setup

### 1. Clone

```
git clone https://github.com/Akil-Ismail/EagleEye.git
cd EagleEye
```

### 2. Backend

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

Open `.env` and fill in `GROQ_API_KEY` (leave it blank if you don't need the Reports feature).
Everything else in `.env` already has working defaults — no MySQL/Docker/database server to
install, SQLite and Qdrant both run embedded inside the app.

Create the database schema:

```
python -m app.db.migrate
```

### 3. Frontend

In a separate terminal:

```
cd frontend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Running

**Terminal 1 — backend** (leave this running):

```
cd backend
venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
```

The **first time** you enroll or recognize a face, InsightFace downloads its model pack
(`buffalo_l`, ~300MB) automatically — this can take several minutes depending on your
connection. Wait for it to finish; it only happens once.

**Terminal 2 — desktop app:**

```
cd frontend
venv\Scripts\python.exe main.py
```

The app window opens directly to the dashboard. Use the **Enroll User** tab to add a face
(webcam capture or photo upload) before testing recognition on the **Live Camera** tab.

To stop: close the app window, then `Ctrl+C` in the backend terminal.

## Where data lives

- `backend/data/eagleeye.db` — SQLite database (users, access logs, alerts, reports)
- `backend/data/qdrant/` — face embedding vector index
- `backend/media/` — saved enrollment photos and recognition snapshots

All three are created automatically and are git-ignored. Delete `backend/data/` to reset the
app to a clean state (you'll need to re-enroll everyone).

## Limitations

- **Liveness detection** only catches what it's been tested against: a real blink is required
  on the live camera feed, and visible screen glare is rejected as a likely phone/monitor
  replay. It has **not** been tested against printed photos, or a video of a blinking face
  played on a screen — those may still pass.
- Liveness checking only applies to the **Live Camera** tab (it needs multiple frames over
  time). Single-image uploads and video-file recognition use a weaker single-frame check.
- The anti-spoofing heuristics are hand-tuned against a small number of real test samples, not
  a proper labeled dataset — thresholds in `backend/app/services/face_service.py` may need
  adjusting for different lighting/cameras.

## Troubleshooting

- **"Failed to load logs" / connection errors in the app**: the backend terminal isn't running,
  or crashed. Check that terminal for a traceback.
- **Camera feed freezes or shows a black frame**: some Windows webcams intermittently fail via
  OpenCV's default backend; stopping and restarting the camera in the Live Camera tab resets it.
- **Reports tab fails with a 503**: `GROQ_API_KEY` isn't set in `backend/.env`.
