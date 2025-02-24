from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.main import api_router
import os

app = FastAPI(
    tittle=os.environ["APP_NAME"],
    description=os.environ["APP_DESCRIPTION"],
    contact={
        "name": os.environ["APP_CONTACT_NAME"],
        "email": os.environ["APP_CONTACT_EMAIL"],
    },
)

# Middleware for CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ["CORS_ORIGINS"].split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
