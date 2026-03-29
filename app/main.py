import logging
import os

from fastapi import FastAPI

logging.basicConfig(level=logging.INFO)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.responses import FileResponse

from app.routers import auth, companies, cameras, polling
from app.services import mqtt_service, redis_service


class SPAStaticFiles(StaticFiles):
    """StaticFiles with SPA fallback: unknown paths return index.html."""

    def __init__(self, directory: str, **kwargs):
        self.spa_directory = directory
        super().__init__(directory=directory, **kwargs)

    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as ex:
            if ex.status_code == 404:
                return FileResponse(os.path.join(self.spa_directory, "index.html"))
            raise

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


@app.on_event("startup")
async def start_background_tasks():
    redis_service.start()
    mqtt_service.start()


@app.on_event("shutdown")
async def stop_background_tasks():
    mqtt_service.stop()
    redis_service.stop()


@app.get("/")
def root():
    return RedirectResponse(url="/admin/")


app.mount("/admin", SPAStaticFiles(directory="static/admin", html=True), name="admin")
app.mount("/client", SPAStaticFiles(directory="static/client", html=True), name="client")
