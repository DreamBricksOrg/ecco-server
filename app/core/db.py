"""Conexão com o MongoDB"""

from pymongo import AsyncMongoClient

from app.core.config import get_settings

settings = get_settings()

_client = AsyncMongoClient(settings.MONGO_URI, serverSelectionTimeoutMS=20000)
db = _client[settings.MONGO_DB]

async def init_db():
    await db.videos.create_index("filename", unique=True)
