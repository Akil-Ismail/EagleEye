from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routers import alerts, enroll, logs, recognize, reports, users
from app.vector.collections import ensure_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    ensure_collection()
    yield


app = FastAPI(title="EagleEye API", lifespan=lifespan)

app.include_router(users.router)
app.include_router(enroll.router)
app.include_router(recognize.router)
app.include_router(logs.router)
app.include_router(alerts.router)
app.include_router(reports.router)


@app.get("/health")
def health_check():
    return {"status": "ok"}
