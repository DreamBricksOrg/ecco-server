"""Inicializador principal da aplicação OBS Controller API"""

from fastapi import FastAPI
import logging

from app.core.config import get_settings
from app.api.obs import router as obs_router

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
    app.include_router(obs_router, prefix="/obs", tags=["OBS"])
    
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