from fastapi import APIRouter
from app.api.v1.endpoints import users, institutions, patients, files, teleconsultations, pareceres, notifications

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["Users (Médicos)"])
api_router.include_router(institutions.router, prefix="/institutions", tags=["Institutions"])
api_router.include_router(patients.router, prefix="/patients", tags=["Patients"])
api_router.include_router(files.router, prefix="/files", tags=["Files"])
api_router.include_router(teleconsultations.router, prefix="/teleconsultations", tags=["teleconsultations"])
api_router.include_router(pareceres.router, prefix="/pareceres", tags=["pareceres"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])