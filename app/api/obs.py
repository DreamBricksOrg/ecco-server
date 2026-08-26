"""Router da API para controle do OBS Studio"""

from fastapi import APIRouter, HTTPException
import logging

from app.core.config import get_settings
from app.models.obs import (
    TextUpdateRequest,
    RecordingDirectoryRequest,
    SceneItemRequest,
    OBSStatusResponse,
    SuccessResponse,
    ErrorResponse
)
from app.services.obs_service import obs_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/text/update", response_model=SuccessResponse)
async def update_text_source(request: TextUpdateRequest):
    """Atualiza o texto de uma fonte de texto no OBS"""
    try:
        if not obs_service.is_connected:
            raise HTTPException(
                status_code=503,
                detail="OBS Studio não está conectado"
            )
        
        success = obs_service.update_text_source(request.source_name, request.text)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail=f"Falha ao atualizar fonte de texto '{request.source_name}'. Verifique se a fonte existe."
            )
        
        return SuccessResponse(
            message=f"Texto da fonte '{request.source_name}' atualizado com sucesso"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao atualizar texto: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        )

@router.get("/recording/start")
async def start_recording():
    """Inicia a gravação no OBS"""
    try:
        if not obs_service.ensure_connection():
            return {"status": "error", "reason": "OBS Studio não está conectado"}

        settings = get_settings()
        full_path = obs_service._get_full_recording_path(settings.OBS_RECORDING_DIR)
        if not obs_service.set_recording_directory(full_path):
            return {"status": "error", "reason": "Falha ao configurar diretório de gravação padrão"}

        success, reason = obs_service.start_recording()
        if not success:
            return {"status": "error", "reason": reason}

        return {"status": "success", "reason": ""}

    except Exception as e:
        logger.error(f"Erro inesperado ao iniciar gravação: {e}")
        return {"status": "error", "reason": str(e)}

@router.get("/recording/stop")
async def stop_recording():
    """Para a gravação no OBS"""
    try:
        if not obs_service.ensure_connection():
            return {"status": "error", "reason": "OBS Studio não está conectado"}

        success, reason = obs_service.stop_recording()
        if not success:
            return {"status": "error", "reason": reason}

        return {"status": "success", "reason": ""}

    except Exception as e:
        logger.error(f"Erro inesperado ao parar gravação: {e}")
        return {"status": "error", "reason": str(e)}

@router.get("/recording/getvideo")
async def get_last_video():
    """Retorna a URL do último vídeo gravado (já renomeado para UUID) e um QR code (base64) dessa URL"""
    try:
        filename = obs_service.ensure_latest_recording_has_uuid_name()
        if not filename:
            return {"status": "error", "reason": "Nenhum vídeo encontrado na pasta de gravações"}

        settings = get_settings()
        if not settings.PUBLIC_BASE_URL:
            return {"status": "error", "reason": "PUBLIC_BASE_URL não configurada"}

        url = f"{settings.PUBLIC_BASE_URL.rstrip('/')}/videos/{filename}"
        image = obs_service.generate_qrcode_base64(url)

        return {"status": "success", "url": url, "image": image}

    except Exception as e:
        logger.error(f"Erro inesperado ao obter último vídeo: {e}")
        return {"status": "error", "reason": str(e)}


@router.get("/status", response_model=OBSStatusResponse)
async def obs_status():
    """Retorna o status atual do OBS Studio"""
    try:
        connected = obs_service.is_connected
        version_info = None
        recording_directory = None
        
        if connected:
            version_info = obs_service.get_version_info()
            recording_directory = obs_service.get_recording_directory()
        
        return OBSStatusResponse(
            connected=connected,
            version_info=version_info,
            recording_directory=recording_directory
        )
    
    except Exception as e:
        logger.error(f"Erro inesperado ao obter status: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        )

@router.get("/recording/directory")
async def get_recording_directory():
    """Obtém o diretório de gravação atual do OBS"""
    try:
        if not obs_service.is_connected:
            raise HTTPException(
                status_code=503,
                detail="OBS Studio não está conectado"
            )
        
        directory = obs_service.get_recording_directory()
        
        if directory is None:
            raise HTTPException(
                status_code=400,
                detail="Não foi possível obter o diretório de gravação"
            )
        
        return {"directory": directory}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao obter diretório de gravação: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        )

@router.post("/recording/directory", response_model=SuccessResponse)
async def set_recording_directory(request: RecordingDirectoryRequest):
    """Configura o diretório de gravação do OBS"""
    try:
        if not obs_service.is_connected:
            raise HTTPException(
                status_code=503,
                detail="OBS Studio não está conectado"
            )
        
        # Compõe o caminho completo do diretório
        full_path = obs_service._get_full_recording_path(request.directory)
        success = obs_service.set_recording_directory(full_path)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Falha ao configurar diretório de gravação. Verifique se o caminho é válido."
            )
        
        return SuccessResponse(message=f"Diretório de gravação configurado para: {full_path}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao configurar diretório: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        )


@router.post("/disconnect", response_model=SuccessResponse)
async def disconnect_obs():
    """Desconecta do OBS Studio"""
    try:
        obs_service.disconnect()
        return SuccessResponse(message="Desconectado do OBS Studio com sucesso")
    except Exception as e:
        logger.error(f"Erro ao desconectar do OBS: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/connect", response_model=SuccessResponse)
async def connect_obs():
    """Conecta ao OBS Studio manualmente"""
    try:
        if obs_service.connect():
            return SuccessResponse(message="Conectado ao OBS Studio com sucesso")
        else:
            raise HTTPException(status_code=500, detail="Falha ao conectar com OBS Studio")
    except Exception as e:
        logger.error(f"Erro ao conectar ao OBS: {e}")
        raise HTTPException(status_code=500, detail=str(e))