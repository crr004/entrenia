from fastapi import APIRouter

from app.api.routes import users, login, signup, datasets, images, classifiers

api_router = APIRouter()

api_router.include_router(login.router)
api_router.include_router(signup.router)
api_router.include_router(users.router)
api_router.include_router(datasets.router)
api_router.include_router(images.router)
api_router.include_router(classifiers.router)
