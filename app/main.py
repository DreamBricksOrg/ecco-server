"""Inicializador principal da aplicação OBS Controller API"""

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel
import asyncio
import logging
from pathlib import Path

from app.core.config import get_settings
from app.core.logcenter import init_logcenter, get_sender
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

class WatchEventRequest(BaseModel):
    """Evento de interação do usuário na página /watch (download ou compartilhamento)"""
    action: str

_WATCH_EVENT_NAMES = {"download": "video_baixado", "share": "video_compartilhado"}

def create_app() -> FastAPI:
    """Factory function para criar a aplicação FastAPI"""
    settings = get_settings()

    app = FastAPI(
        title="OBS Controller API",
        description="API para controlar o OBS Studio remotamente",
        version="1.0.0"
    )

    # Registra middleware de auditoria HTTP (loga erros 5xx automaticamente)
    if settings.LOG_API and settings.LOG_ID:
        try:
            from logcenter_sdk import LogCenterAuditMiddleware
            sender = init_logcenter(settings.LOG_API, settings.LOG_ID, settings.LOG_API_KEY)
            app.add_middleware(LogCenterAuditMiddleware, sender=sender)
        except Exception:
            logger.warning("LogCenter não pôde ser inicializado; logs remotos desativados")

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

        sender = get_sender()
        if sender:
            asyncio.create_task(sender.send("INFO", "video_acessado", data={"filename": safe_name}, status="OK"))

        return FileResponse(
            str(file_path),
            media_type="video/mp4",
            filename=safe_name,
            # Nome é um UUID gerado uma única vez por gravação: o conteúdo nunca muda,
            # então o navegador pode cachear indefinidamente e evitar redownloads.
            headers={"Cache-Control": "public, max-age=31536000, immutable"},
        )

    # Página de player + download, aberta a partir do QR code de /api/recording/getvideo
    @app.get("/watch/{filename}", response_class=HTMLResponse)
    async def watch_video(filename: str):
        safe_name = Path(filename).name  # evita path traversal (../)
        file_path = recordings_dir / safe_name
        if not file_path.is_file():
            raise HTTPException(status_code=404, detail="Vídeo não encontrado")

        sender = get_sender()
        if sender:
            asyncio.create_task(sender.send("INFO", "pagina_download_acessada", data={"filename": safe_name}, status="OK"))

        return render_watch_page(safe_name, f"/videos/{safe_name}")

    # Registra ações do usuário na página de watch (download/compartilhamento)
    @app.post("/watch/{filename}/event")
    async def watch_event(filename: str, event: WatchEventRequest):
        safe_name = Path(filename).name  # evita path traversal (../)
        event_name = _WATCH_EVENT_NAMES.get(event.action)
        if not event_name:
            raise HTTPException(status_code=400, detail="Ação inválida")

        sender = get_sender()
        if sender:
            asyncio.create_task(sender.send("INFO", event_name, data={"filename": safe_name}, status="OK"))

        return {"status": "ok"}

    # Limpeza automática de gravações antigas
    @app.on_event("startup")
    async def start_cleanup_task():
        if settings.DELETE_OLD_FILES:
            app.state.cleanup_task = asyncio.create_task(cleanup_old_recordings_loop())
        try:
            sender = get_sender()
            if sender:
                sender.start_background_flush()
        except Exception:
            logger.warning("Falha ao iniciar flush periódico do LogCenter")

    @app.on_event("shutdown")
    async def stop_cleanup_task():
        task = getattr(app.state, "cleanup_task", None)
        if task:
            task.cancel()
        try:
            sender = get_sender()
            if sender:
                await sender.stop_background_flush()
        except Exception:
            logger.warning("Falha ao encerrar flush do LogCenter")

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