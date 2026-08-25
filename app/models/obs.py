"""Modelos Pydantic para requests e responses da API OBS"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class TextUpdateRequest(BaseModel):
    """Request para atualizar texto de uma fonte"""
    source_name: str = Field(..., description="Nome da fonte de texto")
    text: str = Field(..., description="Novo texto a ser definido")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_name": "Texto Principal",
                "text": "Novo texto para exibição"
            }
        }

class RecordingRequest(BaseModel):
    """Request para controle de gravação"""
    directory: Optional[str] = Field(None, description="Diretório para salvar a gravação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "directory": "C:\\Gravacoes\\OBS"
            }
        }

class SceneItemRequest(BaseModel):
    """Request para controle de itens de cena"""
    source_name: str = Field(..., description="Nome da fonte/item de cena")
    enabled: bool = Field(..., description="Se o item deve estar habilitado")
    scene_name: Optional[str] = Field(None, description="Nome da cena (opcional, usa cena atual se não especificado)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_name": "Webcam",
                "enabled": True,
                "scene_name": "Cena Principal"
            }
        }

class OBSStatusResponse(BaseModel):
    """Response com status do OBS"""
    connected: bool = Field(..., description="Se está conectado ao OBS")
    version_info: Optional[Dict[str, str]] = Field(None, description="Informações de versão do OBS")
    recording_directory: Optional[str] = Field(None, description="Diretório atual de gravação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "connected": True,
                "version_info": {
                    "obs_version": "30.0.0",
                    "obs_web_socket_version": "5.0.0"
                },
                "recording_directory": "C:\\Gravacoes\\OBS"
            }
        }

class SuccessResponse(BaseModel):
    """Response padrão para operações bem-sucedidas"""
    success: bool = Field(True, description="Indica se a operação foi bem-sucedida")
    message: str = Field(..., description="Mensagem descritiva da operação")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operação realizada com sucesso"
            }
        }

class RecordingDirectoryRequest(BaseModel):
    """Request para configurar diretório de gravação"""
    directory: str = Field(..., description="Caminho do diretório para gravações")
    
    class Config:
        json_schema_extra = {
            "example": {
                "directory": "/path/to/recordings"
            }
        }

class ErrorResponse(BaseModel):
    """Response padrão para erros"""
    success: bool = Field(False, description="Indica que a operação falhou")
    error: str = Field(..., description="Descrição do erro")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": False,
                "error": "OBS Studio não está conectado"
            }
        }