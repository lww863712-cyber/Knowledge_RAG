from fastapi import APIRouter

from app.api.v1 import auth, chat, documents, health, ingestion, knowledge_bases, retrieval, settings, usage, users

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(knowledge_bases.router)
api_router.include_router(documents.router)
api_router.include_router(ingestion.router)
api_router.include_router(retrieval.router)
api_router.include_router(chat.router)
api_router.include_router(settings.router)
api_router.include_router(usage.router)