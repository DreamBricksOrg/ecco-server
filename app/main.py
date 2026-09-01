"""Inicializador principal da aplicação OBS Controller API"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
import asyncio
import logging
from pathlib import Path

from app.core.config import get_settings
from app.api.obs import router as obs_router
from app.services.obs_service import obs_service
from app.services.cleanup_service import cleanup_old_recordings_loop
from app.web.watch_page import render_watch_page

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

    # Serve o vídeo pelo nome do arquivo (já renomeado para UUID ao parar a gravação)
    @app.get("/videos/{filename}")
    async def get_video(filename: str):
        safe_name = Path(filename).name  # evita path traversal (../)
        file_path = recordings_dir / safe_name
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="Vídeo não encontrado")

        return FileResponse(str(file_path), media_type="video/mp4", filename=safe_name)

    # Página de player + download, aberta a partir do QR code de /api/recording/getvideo
    @app.get("/watch/{filename}", response_class=HTMLResponse)
    async def watch_video(filename: str):
        safe_name = Path(filename).name  # evita path traversal (../)
        file_path = recordings_dir / safe_name
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="Vídeo não encontrado")

        return render_watch_page(safe_name, f"/videos/{safe_name}")

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
        return {"status": "healthy", "obs_connected": obs_service.is_connected}
    
    return app

app = create_app()