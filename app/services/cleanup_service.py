"""Serviço de limpeza automática de gravações antigas"""

import asyncio
import logging
import time
from pathlib import Path

from app.core.config import get_settings
from app.services.obs_service import obs_service, VIDEO_EXTENSIONS

logger = logging.getLogger(__name__)


def _delete_expired_recordings(directory: Path, max_life_seconds: float) -> None:
    if not directory.is_dir():
        return

    now = time.time()
    for file in directory.iterdir():
        if not file.is_file() or file.suffix.lower() not in VIDEO_EXTENSIONS:
            continue

        age_seconds = now - file.stat().st_mtime
        if age_seconds > max_life_seconds:
            try:
                file.unlink()
                logger.info(f"Vídeo expirado removido: {file.name} (idade: {age_seconds / 60:.1f} min)")
            except OSError as e:
                logger.error(f"Falha ao remover vídeo expirado {file.name}: {e}")


async def cleanup_old_recordings_loop() -> None:
    """Loop assíncrono que apaga vídeos com mais de DELETE_OLD_FILES_MAX_LIFE minutos"""
    settings = get_settings()
    poll_seconds = max(1, settings.DELETE_OLD_FILES_MAX_POLL) * 60
    max_life_seconds = max(0, settings.DELETE_OLD_FILES_MAX_LIFE) * 60
    directory = Path(obs_service._get_full_recording_path(settings.OBS_RECORDING_DIR))

    logger.info(
        f"Limpeza automática de gravações ativada: vida máxima de "
        f"{settings.DELETE_OLD_FILES_MAX_LIFE} min, verificação a cada "
        f"{settings.DELETE_OLD_FILES_MAX_POLL} min (pasta: {directory})"
    )

    while True:
        try:
            _delete_expired_recordings(directory, max_life_seconds)
        except Exception as e:
            logger.error(f"Erro na limpeza automática de gravações: {e}")

        await asyncio.sleep(poll_seconds)
