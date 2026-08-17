# The EagleEye Backend, Explained

This document walks through **every file** in the `backend/` folder and explains what it does,
in plain language. It assumes you're new to backend programming — a few core concepts are
explained up front so the file-by-file walkthrough makes sense.

If you just want to *run* the app, see the main [README.md](../README.md) instead. This file is
for understanding *how it works*.

---

## Part 1 — Concepts you need before any of this makes sense

**What is a "backend" at all?**
The backend is a program that runs quietly in the background (no window, no buttons) and waits
for other programs to ask it to do things — "enroll this person," "recognize this face,"
"give me the list of alerts." The PyQt6 desktop app (`frontend/`) is the thing with buttons and
windows; it never touches the database or the face-recognition model directly. Instead, it sends
a request to the backend over the network (even though, here, both are running on the same
laptop) and waits for an answer. This split exists so that the "brains" of the app (database,
AI models) are in one place, and the "face" of the app (buttons, windows) is in another.

**What is FastAPI?**
FastAPI is a Python library for building exactly this kind of backend. You write normal Python
functions, and FastAPI turns them into things a network request can call. It also automatically
checks that incoming data has the right shape (see "Pydantic" below) and turns your return
values into JSON (a text format for sending structured data over a network).

**What is an "endpoint" / "route"?**
An endpoint is one specific thing the backend knows how to do, identified by a URL path and an
HTTP method. For example, `POST /enroll` means "send data to the `/enroll` address to create a
new enrolled user." `GET /logs` means "ask for the `/logs` address to read back the access log."
`POST` generally means "create/do something," `GET` means "just give me data," `PATCH` means
"update part of something." Every file in `app/routers/` defines a group of related endpoints.

**What is Pydantic, and why do `schemas/` files exist?**
Pydantic is a library that defines the *shape* of data — which fields exist, what type each one
is, which are optional. FastAPI uses these definitions (called "schemas" or "models" here) to
validate incoming requests (reject them automatically if a required field is missing) and to
decide exactly what to include when sending a response back. Think of a schema as a contract:
"a `UserResponse` always has an `id` (a number), a `full_name` (text), etc."

**What is a virtual environment (`venv`)?**
Different Python projects often need different versions of the same library. A virtual
environment is an isolated folder (`backend/venv/`) containing its own copy of Python and all
the libraries this project needs, so installing something for EagleEye can never break some
other Python project on your machine. You "activate" it before running anything, or call the
Python inside it directly (`venv\Scripts\python.exe`).

**What is a database, and why SQLite specifically?**
A database is a program dedicated to storing structured data reliably (as opposed to just
writing to a text file, which gets messy and error-prone fast). SQLite is a database that
needs **no separate server** — it's just a single file on disk (`backend/data/eagleeye.db`)
that Python's standard library already knows how to read and write. That's why this project
needs no installation step for its database — most databases (like MySQL or PostgreSQL) require
installing and running a separate background program, but SQLite doesn't.

**What is a "vector database," and what's an "embedding"?**
A face-recognition model doesn't compare images pixel-by-pixel. Instead, it converts each face
into a list of 512 numbers (called an **embedding**) that captures what makes that face unique —
two photos of the same person produce two very *similar* lists of numbers, even if the lighting
or angle is different. A vector database (here, **Qdrant**) is built specifically to answer the
question "which stored list of numbers is most similar to this new one?" quickly, which is
exactly how face matching works: embed the new face, ask Qdrant "whose stored embedding is
closest to this?", and if it's close enough, that's your match.

**What is an environment variable / `.env` file?**
Settings that differ between machines or that are secret (like the Groq API key) shouldn't be
hard-coded into the source code. Instead, they're read from the environment the program runs
in. A `.env` file is a simple way to set those values locally — `backend/.env` is never
committed to GitHub (see `.gitignore`), so your personal API key never ends up in the shared
repository.

---

## Part 2 — Folder map

```
backend/
  requirements.txt      <- list of Python libraries this project needs
  .env.example           <- template for your personal settings file
  .env                   <- your actual settings (not in git — has your real API key)
  .gitignore              <- tells git which files/folders to never track
  data/                   <- created automatically: the SQLite database + Qdrant's files
  media/                  <- created automatically: saved photos and video snapshots
  venv/                   <- the virtual environment (see above), not in git
  app/
    main.py               <- the entry point: creates the FastAPI app
    core/
      config.py           <- reads settings from .env
    db/
      schema.sql          <- defines the database tables
      session.py          <- opens/closes database connections
      migrate.py          <- runs schema.sql to create the tables
      repository/         <- one file per table, each with functions to read/write it
    vector/
      qdrant_client.py    <- connects to the embedded Qdrant vector database
      collections.py      <- stores/searches face embeddings in Qdrant
    services/             <- the actual "smart" logic (face recognition, LLM reports, etc.)
    schemas/              <- Pydantic data shapes (see Part 1)
    routers/              <- the actual endpoints the frontend calls
    workers/
      video_processing.py <- handles uploaded videos in the background
```

---

## Part 3 — File by file

### `requirements.txt`

A plain list of every third-party Python library this project depends on, one per line. Running
`pip install -r requirements.txt` reads this file and installs all of them into the virtual
environment. Here's what each one is for:

- **fastapi** — the web framework itself (see Part 1)
- **uvicorn[standard]** — the actual program that runs the FastAPI app and listens for network
  requests (FastAPI describes *what* to do; uvicorn is *the server* that does the listening)
- **python-multipart** — lets FastAPI accept file uploads (photos, videos) and form data
- **pydantic-settings** — the specific tool `core/config.py` uses to read `.env` files
- **qdrant-client** — the library for talking to Qdrant (see Part 1)
- **requests** — a simple library for making outgoing web calls; used here to call the Groq API
- **opencv-python** — image/video processing (reading webcam frames, decoding JPEGs, resizing)
- **insightface** — the actual face detection + recognition AI model
- **onnxruntime** — the engine that runs InsightFace's AI models efficiently on your CPU

### `.env.example` / `.env`

`.env.example` is a template checked into git, showing which settings exist and their default
values, but with secrets left blank. `.env` is your real copy with your actual Groq key filled
in — every setting here is read by `core/config.py`:

- `SQLITE_PATH` — where the database file lives on disk
- `QDRANT_PATH` — where Qdrant stores its face-embedding data on disk
- `QDRANT_COLLECTION` — the name Qdrant uses internally for the group of face embeddings
- `GROQ_API_KEY` / `GROQ_MODEL` — your Groq credentials and which AI model to use for reports
- `MEDIA_ROOT` — where uploaded/captured photos and video snapshots are saved

### `app/core/config.py`

Defines a `Settings` class listing every setting the app needs, with sensible defaults. When the
app starts, `pydantic-settings` automatically reads `backend/.env` and overrides any of these
defaults with what it finds there. `get_settings()` is the function every other file calls to
read a setting — it's wrapped in `@lru_cache` so the `.env` file is only actually read once, not
every single time a setting is needed.

### `app/db/schema.sql`

Plain SQL (the language databases understand) describing the five tables that make up the
database, and what columns each one has:

- **`users`** — everyone who's been enrolled: their name, role, whether they're still active,
  and when they were enrolled.
- **`media_uploads`** — tracks every video or image ever uploaded for recognition: where the
  file is stored, and whether it's still being processed, done, or failed.
- **`access_logs`** — one row *every time* a face is checked, whether it matched someone,
  whether it looked "live" or possibly spoofed, and what the final decision was
  (`authorized` / `unknown` / `spoof_suspected`).
- **`alerts`** — raised automatically when something suspicious happens (see
  `recognition_service.py` below); tracks whether an admin has resolved it yet.
- **`reports`** — saved AI-generated incident summaries, so past reports can be looked back at
  later instead of only existing for a moment on screen.

The `FOREIGN KEY` lines connect tables together — e.g. every `access_logs` row optionally points
at a `users` row, so the app can ask "which user does this log belong to?" The `CHECK` clauses
restrict a column to a fixed set of allowed text values (e.g. `decision` can only ever be one of
three exact strings) — the database itself will refuse to store anything else, which catches
typos and bugs early.

### `app/db/session.py`

Handles the low-level details of talking to the SQLite file so nothing else in the app has to.
`get_connection()` opens a fresh connection to the database file (creating the folder it lives
in if needed), and automatically **commits** (saves) the changes if everything went fine, or
**rolls back** (undoes them) if an error happened partway through — so the database can never
end up half-updated. `get_cursor()` is what the rest of the code actually uses; a "cursor" is the
object you use to run individual SQL commands. `_dict_factory` is a small customization so that
when you read a row back, you get a friendly Python dictionary (`{"id": 1, "full_name": "..."}`)
instead of SQLite's default, less convenient row format.

### `app/db/migrate.py`

A small script (not something the running app calls — you run it once yourself) that reads
`schema.sql` and executes it against the database file, actually creating the tables. This is
what `python -m app.db.migrate` runs during setup. Every `CREATE TABLE` in the schema uses
`IF NOT EXISTS`, so running this again later is harmless — it won't erase existing data.

### `app/db/repository/` — one file per table

"Repository" is a common name for "a file whose entire job is reading and writing one specific
part of the database, so nowhere else in the app has to write raw SQL." Every function here
follows the same pattern: open a cursor, run one SQL statement with `?` placeholders (which
safely inserts values without letting user input corrupt or hijack the query — this is what
protects against a class of attack called SQL injection), and return the result.

- **`users_repo.py`** — create a user, fetch one by ID, list all (optionally only active ones),
  and deactivate one.
- **`media_repo.py`** — record that a file was uploaded, fetch its info, and update its
  processing status as a background job works through it.
- **`logs_repo.py`** — insert an access-log row, fetch one, list recent ones (optionally
  filtered by decision or by a date range), list all logs belonging to one uploaded video, and
  count how many "unknown" faces showed up recently (used to detect repeat visitors).
- **`alerts_repo.py`** — create an alert, list them (optionally only unresolved ones or within a
  date range), and mark one resolved.
- **`reports_repo.py`** — save a generated report and list/fetch past ones. Note it converts
  Python `datetime` objects to plain text before storing them, since SQLite doesn't have a
  native date type — and converts the list of included log IDs to a JSON text string, since
  SQLite can't store a list directly either.

### `app/vector/qdrant_client.py`

Creates (once, and reuses from then on, thanks to `@lru_cache`) the connection to Qdrant. Notice
`QdrantClient(path=...)` — passing a folder path instead of a network address makes Qdrant run
**embedded**, directly inside this Python process, with no separate server to install or start.

### `app/vector/collections.py`

The actual face-embedding operations, all built on top of `qdrant_client.py`:

- **`ensure_collection()`** — makes sure the "face_embeddings" collection exists, creating it on
  first run. `VectorParams(size=512, distance=Distance.COSINE)` tells Qdrant every stored vector
  will have exactly 512 numbers, and that "closeness" between two vectors should be measured
  using cosine similarity (a standard way to compare directions of two vectors — well-suited to
  the kind of embeddings InsightFace produces).
- **`upsert_face_embedding()`** — stores one enrollment photo's embedding, tagged with which
  user it belongs to.
- **`search_similar_faces()`** — given a new embedding, asks Qdrant for the closest stored
  embeddings (and their similarity scores). This is the actual "who does this face look like?"
  operation.
- **`delete_user_embeddings()`** — removes all of a user's stored embeddings (not currently
  called from anywhere yet, but available for a future "delete user entirely" feature).

### `app/services/face_service.py`

The most complex file — everything involving the actual AI face model lives here.

- **`_get_face_app()`** — loads InsightFace's `buffalo_l` model pack the first time it's needed,
  then reuses it (loading it is slow, so this only happens once per run of the backend).
- **`_decode()`** — turns raw image bytes (as received over the network) into the pixel array
  format OpenCV and InsightFace expect.
- **`_liveness_score()` / `LIVENESS_SCORE_THRESHOLD`** — a hand-tuned, best-effort check for
  whether a face looks like it's being shown on a phone/monitor screen rather than a real,
  live face. It measures two things on the cropped face: `laplacian_var` (a measure of fine
  detail/sharpness) and `glare_ratio` (how many pixels are almost pure white, which happens with
  backlit-screen reflections). See the comment in the file itself for exactly how these numbers
  were calibrated against real test photos — this is **not** a trained AI model, just a formula,
  and it only reliably catches screen glare specifically (see the main README's Limitations
  section).
- **`detect_faces()`** — the main function: finds every face in an image, and for each one
  returns its embedding (for matching), its bounding box (pixel coordinates of where it is in
  the image), and the liveness score/verdict above.
- **`extract_embedding()`** — used only during enrollment, where exactly one person is expected
  per photo: finds all faces, then picks the largest one (in case someone else is visible in the
  background) and returns just its embedding.

### `app/services/recognition_service.py`

The decision-making logic that turns "here's an embedding and a liveness score" into "here's
what actually happened, and does it need an alert":

- **`match_embedding()`** — asks Qdrant (via `collections.py`) for the closest enrolled face. If
  nothing is close enough (`SIMILARITY_THRESHOLD = 0.55`), it reports "no match" rather than
  guessing at a low-confidence answer.
- **`record_recognition_event()`** — decides the final `decision`: if liveness explicitly failed,
  it's `spoof_suspected` regardless of who it might look like; otherwise it's `authorized` if a
  user matched, or `unknown` if not. It saves this as a new row in `access_logs`, and then — this
  is the alerting logic — raises an `alerts` row automatically: every spoof attempt gets a
  `spoof_attempt` alert, and every unknown face gets either a `repeated_unknown` alert (if 3+
  unknown faces have shown up in the last 5 minutes — see the constants at the top of the file)
  or a plain `unauthorized_access` alert otherwise.

### `app/services/media_service.py`

Small file-saving helpers shared by enrollment, recognition snapshots, and video uploads.
`save_bytes()` writes raw data to a uniquely-named file (using a random UUID so two uploads can
never collide) inside `MEDIA_ROOT`, in whatever subfolder you ask for. `save_upload()` is a thin
wrapper for the common case of saving directly from a FastAPI `UploadFile`.

### `app/services/groq_service.py`

Turns the raw access logs and alerts for a time period into a human-readable incident report,
using Groq's AI chat API.

- **`summarize_events()`** — sends a request to Groq's API (an "OpenAI-compatible" API, meaning
  it uses the same request format many AI providers standardized on) with a system prompt
  describing the assistant's job, and the actual log/alert data as the user's message. Note:
  only structured data (IDs, timestamps, decisions, confidence numbers) is sent — never any
  actual photos — so no biometric data leaves your machine.
- **`_collapse_logs()` / `_collapse_alerts()`** — before sending data to Groq, these merge
  consecutive, near-identical events (e.g. the same person being re-recognized every couple of
  seconds while sitting in front of the camera) into a single entry with an `occurrences` count.
  Without this, a few minutes of continuous recognition would generate hundreds of near-duplicate
  log lines, which is both wasteful and can exceed Groq's request size limit.
- **`_format_events()`** — packages the collapsed data as a JSON string, the actual text that
  gets sent to the AI model.

### `app/schemas/` — the data shapes

Every file here defines Pydantic classes (see Part 1) describing exactly what a request or
response looks like for one feature area. None of these contain logic — they're just shape
definitions FastAPI uses for validation and for building its API documentation.

- **`users.py`** — `UserCreate` (data needed to create a user — currently unused directly since
  enrollment takes form fields instead, but kept for clarity/future use) and `UserResponse`
  (what a user looks like when sent back to the frontend).
- **`recognition.py`** — `RecognitionResult` (one face's recognition outcome), `AccessLogResponse`
  (one row from the access log), and `VideoJobResponse` / `VideoJobStatusResponse` (the
  immediate "your video is processing" reply and the later "here's how it went" status check).
- **`alerts.py`** — `AlertResponse`, what one alert looks like.
- **`reports.py`** — `ReportGenerateRequest` (the time range you want a report for) and
  `ReportResponse` (the generated report).

### `app/routers/` — the actual endpoints

Each file groups related endpoints under a shared URL prefix (set via `APIRouter(prefix=...)`),
and each function decorated with `@router.get(...)`, `@router.post(...)`, or `@router.patch(...)`
is one endpoint. This is the layer the frontend actually talks to — everything above this point
(services, repositories, schemas) exists to support these functions.

- **`users.py`** (`/users`) — `GET /users` lists enrolled users; `PATCH /users/{id}/deactivate`
  marks one inactive (accounts are never hard-deleted, just deactivated, so history is preserved).
- **`enroll.py`** (`/enroll`) — `POST /enroll` takes a name and one or more photos, checks every
  photo actually has a detectable face *before* creating the user record (so a bad photo can't
  leave behind a user with zero enrolled faces), then saves each photo and stores its embedding
  in Qdrant.
- **`recognize.py`** (`/recognize`) — the busiest file:
  - `POST /recognize/frame` — the main live-recognition endpoint. Detects every face in one
    image, matches and records each one independently (so multiple people in frame are each
    logged and identified separately), and returns a list of results, one per face.
  - `POST /recognize/video` — accepts an uploaded video, saves it, and hands it off to a
    background job (see `workers/video_processing.py`) instead of processing it immediately,
    since a video can take a while — the frontend gets an instant reply with a job ID instead of
    hanging.
  - `GET /recognize/video/{id}` — lets the frontend poll "is my video done yet, and what did it
    find?"
- **`logs.py`** (`/logs`) — `GET /logs`, with optional filtering by decision type.
- **`alerts.py`** (`/alerts`) — `GET /alerts` (optionally filtered to unresolved only) and
  `PATCH /alerts/{id}/resolve`.
- **`reports.py`** (`/reports`) — `GET /reports` lists past reports; `POST /reports/generate`
  pulls the logs/alerts for the requested time window and calls `groq_service.py` to summarize
  them, then saves and returns the result. Errors from Groq (missing key, network failure) are
  turned into proper HTTP error responses instead of crashing.

### `app/workers/video_processing.py`

The background job that actually processes an uploaded video, referenced by `recognize.py`'s
`/recognize/video` endpoint. It reads the video frame by frame using OpenCV, but only actually
runs face detection on every 10th frame (`FRAME_SAMPLE_INTERVAL`) — checking every single frame
of a video would be extremely slow for very little extra benefit, since a person's face barely
changes across 10 consecutive frames. Every detected face gets matched and logged exactly like
the live camera path, tagged with which video it came from and its timestamp within that video.
If a sampled frame has no detectable face, it's skipped rather than treated as an error. The
upload's status is updated to `processing` at the start and `completed` (or `failed`, if
something goes wrong) at the end, which is what `GET /recognize/video/{id}` reports back.

### `app/main.py`

The entry point — this is the file `uvicorn app.main:app` actually loads and runs. It creates
the FastAPI application, registers every router from `app/routers/` (this is the step that
actually makes all those endpoints reachable), and defines one endpoint directly:
`GET /health`, a trivial "are you alive?" check used to confirm the backend is up before the
desktop app tries to talk to it. The `lifespan` function runs once when the server starts up —
here, it calls `ensure_collection()` so Qdrant's collection always exists before any request
could need it.

### The `__init__.py` files

Every folder under `app/` has an empty `__init__.py` file. This is a Python convention that
tells Python "treat this folder as an importable package" — it's why other files can write
`from app.services.face_service import detect_faces` instead of something more awkward. They're
intentionally empty; there's nothing to explain inside them.

---

## Part 4 — Two full request walkthroughs

Reading the pieces in isolation only goes so far — here's what actually happens, file by file,
for two real actions.

### Walkthrough A: Enrolling a new user

1. The desktop app sends a `POST /enroll` request with a name and one or more photos.
2. `routers/enroll.py`'s `enroll_user()` receives it.
3. For every photo, it calls `face_service.extract_embedding()` — this loads the InsightFace
   model (if not already loaded), finds the largest face in the photo, and returns its 512-number
   embedding. If a photo has no detectable face, the whole request fails immediately with a
   clear error, **before** any user is created.
4. Once every photo has produced an embedding successfully, `users_repo.create_user()` inserts
   the new row into the `users` table in SQLite.
5. For each photo, `media_service.save_bytes()` writes the photo to disk under
   `media/enrollment/<user_id>/`, and `collections.upsert_face_embedding()` stores that photo's
   embedding in Qdrant, tagged with the new user's ID.
6. `users_repo.get_user()` reads the freshly-created row back, and it's returned to the frontend
   as a `UserResponse`.

### Walkthrough B: Recognizing a face from the live camera

1. The desktop app sends a `POST /recognize/frame` request with one image.
2. `routers/recognize.py`'s `recognize_frame()` calls `face_service.detect_faces()`, which finds
   **every** face in the image (not just the largest — this is what lets two people in frame
   both get recognized).
3. `media_service.save_bytes()` saves the whole frame as a snapshot.
4. For each detected face:
   - `recognition_service.match_embedding()` asks Qdrant which enrolled user (if any) this
     embedding is closest to.
   - `recognition_service.record_recognition_event()` decides the final decision
     (`authorized` / `unknown` / `spoof_suspected`), writes a row to `access_logs`, and — if
     needed — raises a row in `alerts`.
   - `users_repo.get_user()` fetches that user's name (if matched) to include in the response.
5. Once every face has been processed, the full list of results is sent back to the frontend,
   which displays one line per detected face.
