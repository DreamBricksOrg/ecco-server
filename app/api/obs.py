"""Router da API para controle do OBS Studio"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

from app.models.obs import (
    TextUpdateRequest,
    RecordingRequest,
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

@router.post("/recording/start", response_model=SuccessResponse)
async def start_recording(request: Optional[RecordingRequest] = None):
    """Inicia a gravação no OBS"""
    try:
        if not obs_service.is_connected:
            raise HTTPException(
                status_code=503,
                detail="OBS Studio não está conectado"
            )
        
        # Importa as configurações
        from app.core.config import get_settings
        settings = get_settings()
        
        # Se não foi passado request ou diretório, usa o padrão
        if not request or not request.directory:
            # Configura o diretório padrão
            full_path = obs_service._get_full_recording_path(settings.OBS_RECORDING_DIR)
            set_success = obs_service.set_recording_directory(full_path)
            if not set_success:
                raise HTTPException(
                    status_code=400,
                    detail="Falha ao configurar diretório de gravação padrão"
                )
            directory = None  # Usa None para que o OBS use o diretório já configurado
        else:
            directory = request.directory
        
        success = obs_service.start_recording(directory)
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Falha ao iniciar gravação. Verifique as configurações do OBS."
            )
        
        message = "Gravação iniciada com sucesso"
        used_directory = directory or settings.OBS_RECORDING_DIR
        if used_directory:
            message += f" no diretório: {used_directory}"
        
        return SuccessResponse(message=message)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao iniciar gravação: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        )

@router.post("/recording/stop", response_model=SuccessResponse)
async def stop_recording():
    """Para a gravação no OBS"""
    try:
        if not obs_service.is_connected:
            raise HTTPException(
                status_code=503,
                detail="OBS Studio não está conectado"
            )
        
        success = obs_service.stop_recording()
        
        if not success:
            raise HTTPException(
                status_code=400,
                detail="Falha ao parar gravação. Verifique se há uma gravação em andamento."
            )
        
        return SuccessResponse(message="Gravação parada com sucesso")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro inesperado ao parar gravação: {e}")
        raise HTTPException(
            status_code=500,
            detail="Erro interno do servidor"
        )


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