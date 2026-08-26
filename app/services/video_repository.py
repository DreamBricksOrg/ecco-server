"""Repositório de referências de vídeo (Mongo) usadas para gerar URLs por UUID"""

import uuid
from typing import Optional

from app.core.db import db


async def get_or_create_video_uuid(filename: str) -> str:
    """Retorna o UUID já associado ao arquivo, ou cria uma nova referência"""
    existing = await db.videos.find_one({"filename": filename})
    if existing:
        return existing["_id"]

    video_id = str(uuid.uuid4())
    await db.videos.insert_one({"_id": video_id, "filename": filename})
    return video_id


async def get_filename_by_uuid(video_id: str) -> Optional[str]:
    """Retorna o nome do arquivo associado ao UUID, se existir"""
    doc = await db.videos.find_one({"_id": video_id})
    return doc["filename"] if doc else None
