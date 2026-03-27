import asyncio
import logging
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.database import SessionLocal
from app.models.camera import CameraStatus
from app.routers import auth, companies, cameras, polling
from app.services import mqtt_service

app = FastAPI(title="Camera Cloud Manager")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(companies.router)
app.include_router(cameras.router)
app.include_router(polling.router)


async def offline_checker():
    """last_seenが10秒以上前のカメラをオフラインにする"""
    while True:
        await asyncio.sleep(5)
        threshold = datetime.now(timezone.utc) - timedelta(seconds=10)
        db = SessionLocal()
        try:
            stale = db.query(CameraStatus).filter(
                CameraStatus.is_online == True,
                CameraStatus.last_seen < threshold,
            ).all()
            for s in stale:
                s.is_online = False
            if stale:
                db.commit()
        finally:
            db.close()


@app.on_event("startup")
async def start_background_tasks():
    asyncio.create_task(offline_checker())
    mqtt_service.start()


@app.on_event("shutdown")
async def stop_background_tasks():
    mqtt_service.stop()


@app.get("/")
def root():
    return RedirectResponse(url="/admin/")


app.mount("/admin", StaticFiles(directory="static/admin", html=True), name="admin")
app.mount("/client", StaticFiles(directory="static/client", html=True), name="client")
