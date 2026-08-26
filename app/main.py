"""Inicializador principal da aplicação OBS Controller API"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import asyncio
import logging
from pathlib import Path

from app.core.config import get_settings
from app.core.db import init_db
from app.api.obs import router as obs_router
from app.services.obs_service import obs_service
from app.services.cleanup_service import cleanup_old_recordings_loop
from app.services.video_repository import get_filename_by_uuid

# Configuração de logging
settings = get_settings()
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    """Factory function para criar a aplicação FastAPI"""
    settings = get_settings()
    
    app = FastAPI(
        title="OBS Controller API",
        description="API para controlar o OBS Studio remotamente",
        version="1.0.0"
    )
    
    # Incluir routers
    app.include_router(obs_router, prefix="/api", tags=["OBS"])

    # Garante que a pasta de gravações existe (usada por /api/recording/getvideo)
    recordings_dir = Path(obs_service._get_full_recording_path(settings.OBS_RECORDING_DIR))
    recordings_dir.mkdir(parents=True, exist_ok=True)

    # Serve um vídeo pelo UUID referenciado no Mongo (não pelo nome real do arquivo)
    @app.get("/videos/{video_id}")
    async def get_video(video_id: str):
        filename = await get_filename_by_uuid(video_id)
        if not filename:
            raise HTTPException(status_code=404, detail="Vídeo não encontrado")

        file_path = recordings_dir / filename
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="Arquivo de vídeo não encontrado no servidor")

        return FileResponse(str(file_path))

    @app.on_event("startup")
    async def start_db():
        await init_db()

    # Limpeza automática de gravações antigas
    @app.on_event("startup")
    async def start_cleanup_task():
        if settings.DELETE_OLD_FILES:
            app.state.cleanup_task = asyncio.create_task(cleanup_old_recordings_loop())

    @app.on_event("shutdown")
    async def stop_cleanup_task():
        task = getattr(app.state, "cleanup_task", None)
        if task:
            task.cancel()

    # Endpoint raiz
    @app.get("/")
    async def root():
        return {"message": "OBS Controller API", "version": "1.0.0"}
    
    # Health check
    @app.get("/health")
    async def health_check():
        from app.services.obs_service import obs_service
        return {"status": "healthy", "obs_connected": obs_service.is_connected()}
    
    return app

app = create_app()