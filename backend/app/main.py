import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.main import api_router
from app.start import start

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "/app/media")
os.makedirs(MEDIA_ROOT, exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, "images"), exist_ok=True)
os.makedirs(os.path.join(MEDIA_ROOT, "models"), exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Llama a la función de inicialización de la base de datos de manera asíncrona."""

    await start()
    yield


app = FastAPI(
    tittle=os.environ["APP_NAME"],
    description=os.environ["APP_DESCRIPTION"],
    contact={
        "name": os.environ["APP_CONTACT_NAME"],
        "email": os.environ["APP_CONTACT_EMAIL"],
    },
    lifespan=lifespan,
)

# Middleware para CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ["CORS_ORIGINS"].split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=os.environ["API_PREFIX"])
