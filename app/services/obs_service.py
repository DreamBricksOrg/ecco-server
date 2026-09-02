"""Serviço para controle do OBS Studio via WebSocket"""

from obswebsocket import obsws, requests
from typing import Optional, Dict, Any, Tuple
import os
import time
import uuid
import base64
import logging
from io import BytesIO
from pathlib import Path

import qrcode

from app.core.config import get_settings
from app.services.video_overlay import apply_overlay

logger = logging.getLogger(__name__)

VIDEO_EXTENSIONS = {".mp4", ".mkv", ".flv", ".mov", ".ts", ".avi"}

class OBSService:
    """Serviço para controlar o OBS Studio via WebSocket"""

    def __init__(self):
        settings = get_settings()
        self.host = settings.OBS_HOST
        self.port = settings.OBS_PORT
        self.password = settings.OBS_PASSWORD
        self.ws: Optional[obsws] = None
        self._connected = False
        
    def connect(self) -> bool:
        """Conecta ao OBS Studio"""
        try:
            if self._connected:
                return True
                
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            self._connected = True
            logger.info(f"Conectado ao OBS Studio em {self.host}:{self.port}")
            return True
        except Exception as e:
            self._connected = False
            logger.error(f"Erro ao conectar ao OBS Studio: {e}")
            return False
    
    def ensure_connection(self) -> bool:
        """Garante que há uma conexão ativa com o OBS, conectando se necessário"""
        if not self.is_connected:
            return self.connect()
        return True
    
    def disconnect(self) -> None:
        """Desconecta do OBS Studio"""
        if self.ws:
            try:
                self.ws.disconnect()
                logger.info("Desconectado do OBS Studio")
            except Exception as e:
                logger.error(f"Erro ao desconectar do OBS Studio: {e}")
            finally:
                self._connected = False
    
    @property
    def is_connected(self) -> bool:
        """Retorna se está conectado ao OBS Studio"""
        return self._connected
    
    def get_version_info(self) -> Optional[Dict[str, Any]]:
        """Obtém informações de versão do OBS Studio"""
        if not self._connected or not self.ws:
            return None
        try:
            response = self.ws.call(requests.GetVersion())
            return {
                "obs_version": response.getObsVersion(),
                "obs_web_socket_version": response.getObsWebSocketVersion()
            }
        except Exception as e:
            logger.error(f"Erro ao obter versão do OBS: {e}")
            return None
    
    def update_text_source(self, source_name: str, text: str) -> bool:
        """Atualiza o texto de uma fonte de texto"""
        if not self.ensure_connection() or not self.ws:
            logger.warning("Não foi possível conectar ao OBS")
            return False
            
        try:
            logger.info(f"Atualizando fonte de texto {source_name} com texto: {text}")
            if not self._source_exists(source_name):
                logger.error(f"Fonte {source_name} não encontrada")
                return False
            
            self.ws.call(requests.SetInputSettings(
                inputName=source_name,
                inputSettings={"text": text}
            ))
            logger.info(f"Texto da fonte {source_name} atualizado com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao atualizar fonte de texto {source_name}: {e}")
            return False
    
    def start_recording(self, directory: Optional[str] = None) -> Tuple[bool, str]:
        """Inicia a gravação"""
        if not self.ensure_connection() or not self.ws:
            logger.warning("Não foi possível conectar ao OBS")
            return False, "Não foi possível conectar ao OBS Studio"

        try:
            # Compõe o caminho completo do diretório de gravação
            full_recording_path = self._get_full_recording_path(directory)

            if full_recording_path and not self.set_recording_directory(full_recording_path):
                reason = f"Falha ao definir diretório de gravação: {full_recording_path}"
                logger.error(reason)
                return False, reason

            self.ws.call(requests.StartRecord())
            logger.info(f"Gravação iniciada com sucesso{f' no diretório: {full_recording_path}' if full_recording_path else ''}")
            return True, ""
        except Exception as e:
            logger.error(f"Erro ao iniciar gravação: {e}")
            return False, str(e)

    def stop_recording(self) -> Tuple[bool, str]:
        """Para a gravação e renomeia o arquivo salvo para um nome baseado em UUID"""
        if not self.ensure_connection() or not self.ws:
            logger.warning("Não foi possível conectar ao OBS")
            return False, "Não foi possível conectar ao OBS Studio"

        try:
            self.ws.call(requests.StopRecord())
            logger.info("Gravação parada com sucesso")

            filename = self.ensure_latest_recording_has_uuid_name()
            if filename:
                settings = get_settings()
                directory = Path(self._get_full_recording_path(settings.OBS_RECORDING_DIR))
                apply_overlay(directory / filename)

            return True, ""
        except Exception as e:
            logger.error(f"Erro ao parar gravação: {e}")
            return False, str(e)

    @staticmethod
    def _is_valid_uuid(value: str) -> bool:
        """Verifica se a string já é um UUID no formato canônico (ex: gerado por uuid.uuid4())"""
        try:
            return str(uuid.UUID(value)) == value.lower()
        except (ValueError, AttributeError):
            return False

    def ensure_latest_recording_has_uuid_name(self, retries: int = 20, retry_delay: float = 0.5) -> Optional[str]:
        """Garante que o vídeo mais recente da pasta tenha o nome em UUID, renomeando se necessário.

        Chamado tanto ao parar a gravação quanto ao consultar /getvideo: se o OBS ainda
        estiver com o arquivo aberto logo após o StopRecord, o rename pode falhar ali;
        essa segunda checagem cobre esse caso e também arquivos antigos (nome com data).

        Se o rename falhar em todas as tentativas (arquivo ainda travado), retorna None
        em vez do nome original — o nome com data nunca deve ser exposto pelo /getvideo.
        """
        filename = self.get_latest_recording_filename()
        if not filename:
            return None

        stem, suffix = os.path.splitext(filename)
        if self._is_valid_uuid(stem):
            return filename

        settings = get_settings()
        directory = Path(self._get_full_recording_path(settings.OBS_RECORDING_DIR))
        original_path = directory / filename
        new_name = f"{uuid.uuid4()}{suffix.lower()}"
        new_path = directory / new_name

        for attempt in range(1, retries + 1):
            try:
                original_path.rename(new_path)
                logger.info(f"Arquivo de gravação renomeado para UUID: {filename} -> {new_name}")
                return new_name
            except OSError as e:
                if attempt == retries:
                    logger.error(
                        f"Falha ao renomear arquivo de gravação {filename} para UUID "
                        f"após {retries} tentativas: {e}"
                    )
                    return None
                logger.warning(
                    f"Falha ao renomear {filename} para UUID (tentativa {attempt}/{retries}), "
                    f"tentando novamente: {e}"
                )
                time.sleep(retry_delay)

        return None

    def get_latest_recording_filename(self) -> Optional[str]:
        """Busca o arquivo de vídeo mais recente na pasta de gravações (OBS_RECORDING_DIR)"""
        settings = get_settings()
        directory = Path(self._get_full_recording_path(settings.OBS_RECORDING_DIR))

        if not directory.is_dir():
            return None

        videos = [f for f in directory.iterdir() if f.is_file() and f.suffix.lower() in VIDEO_EXTENSIONS]
        if not videos:
            return None

        latest = max(videos, key=lambda f: f.stat().st_mtime)
        return latest.name

    def generate_qrcode_base64(self, data: str, size: int = 256) -> str:
        """Gera um QR code 256x256 (PNG) da string informada, retornado em base64"""
        qr = qrcode.QRCode(border=1)
        qr.add_data(data)
        qr.make(fit=True)
        image = qr.make_image(fill_color="black", back_color="white").convert("RGB")
        image = image.resize((size, size))

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")

    def set_recording_directory(self, directory_path: str) -> bool:
        """Define o diretório de gravação"""
        if not self._connected or not self.ws:
            return False

        try:
            if not self.create_directory_if_not_exists(directory_path):
                return False

            try:
                # SetRecordDirectory define o caminho realmente usado pelo OBS,
                # independente do modo de saída (Simple ou Advanced).
                self.ws.call(requests.SetRecordDirectory(recordDirectory=directory_path))
            except Exception:
                # Fallback para OBS Studio/obs-websocket mais antigos, que não suportam
                # SetRecordDirectory (só existe a partir do obs-websocket 5.3 / OBS 29).
                # Só reflete no caminho real de gravação se o OBS estiver em modo Simple.
                self.ws.call(requests.SetProfileParameter(
                    parameterCategory="SimpleOutput",
                    parameterName="FilePath",
                    parameterValue=directory_path
                ))
            logger.info(f"Diretório de gravação definido: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao definir diretório de gravação: {e}")
            return False
    
    def get_recording_directory(self) -> Optional[str]:
        """Obtém o diretório atual de gravação"""
        if not self._connected or not self.ws:
            return None

        try:
            # GetRecordDirectory reflete o caminho realmente usado pelo OBS,
            # independente do modo de saída (Simple ou Advanced).
            response = self.ws.call(requests.GetRecordDirectory())
            return response.datain.get("recordDirectory")
        except Exception:
            try:
                # Fallback para OBS Studio/obs-websocket mais antigos, que não
                # suportam GetRecordDirectory (só existe a partir do 5.3 / OBS 29).
                response = self.ws.call(requests.GetProfileParameter(
                    parameterCategory="SimpleOutput",
                    parameterName="FilePath"
                ))
                return response.getParameterValue()
            except Exception as e:
                logger.error(f"Erro ao obter diretório de gravação: {e}")
                return None
    
    def _get_full_recording_path(self, directory: Optional[str] = None) -> str:
        """Retorna o caminho de gravação, que precisa ser absoluto"""
        settings = get_settings()

        # Usa o diretório especificado ou o padrão das configurações
        recording_dir = directory or settings.OBS_RECORDING_DIR

        if not recording_dir:
            raise ValueError("OBS_RECORDING_DIR não foi configurado")

        if not os.path.isabs(recording_dir):
            raise ValueError(
                f"OBS_RECORDING_DIR precisa ser um caminho absoluto, recebido: '{recording_dir}'"
            )

        return recording_dir
    
    def create_directory_if_not_exists(self, directory_path: str) -> bool:
        """Cria o diretório se não existir"""
        try:
            normalized_path = os.path.normpath(directory_path)
            
            if os.path.exists(normalized_path):
                if os.path.isdir(normalized_path):
                    logger.info(f"Diretório já existe: {normalized_path}")
                    return True
                else:
                    logger.error(f"Caminho existe mas não é um diretório: {normalized_path}")
                    return False
            
            os.makedirs(normalized_path, exist_ok=True)
            logger.info(f"Diretório criado com sucesso: {normalized_path}")
            return True
            
        except PermissionError:
            logger.error(f"Permissão negada para criar diretório: {directory_path}")
            return False
        except OSError as e:
            logger.error(f"Erro do sistema ao criar diretório {directory_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Erro inesperado ao criar diretório {directory_path}: {e}")
            return False
    
    def set_scene_item_enabled(self, scene_name: str, source_name: str, enabled: bool) -> bool:
        """Habilita/desabilita um item de cena"""
        if not self.ensure_connection() or not self.ws:
            return False
        
        try:
            scene_item_id = self._get_scene_item_id(scene_name, source_name)
            if scene_item_id is None:
                logger.error(f"Item de cena não encontrado: {source_name} na cena {scene_name}")
                return False
            
            self.ws.call(requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=scene_item_id,
                sceneItemEnabled=enabled
            ))
            logger.info(f"Item de cena {source_name} {'habilitado' if enabled else 'desabilitado'}")
            return True
        except Exception as e:
            logger.error(f"Erro ao alterar estado do item de cena: {e}")
            return False
    
    def _source_exists(self, source_name: str) -> bool:
        """Verifica se uma fonte existe"""
        try:
            self.ws.call(requests.GetInputSettings(inputName=source_name))
            return True
        except Exception:
            return self._find_source_in_groups(source_name)
    
    def _find_source_in_groups(self, source_name: str) -> bool:
        """Busca recursivamente uma fonte dentro de grupos"""
        try:
            scenes_response = self.ws.call(requests.GetSceneList())
            scenes = scenes_response.getScenes()
            
            for scene in scenes:
                scene_name = scene['sceneName']
                if self._search_source_in_scene(scene_name, source_name):
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao buscar fonte em grupos: {e}")
            return False
    
    def _search_source_in_scene(self, scene_name: str, source_name: str) -> bool:
        """Busca uma fonte específica dentro de uma cena"""
        try:
            scene_items_response = self.ws.call(requests.GetSceneItemList(sceneName=scene_name))
            scene_items = scene_items_response.getSceneItems()
            
            for item in scene_items:
                source_info = item.get('sourceName', '')
                
                if source_info == source_name:
                    return True
                
                if self._is_group_source(source_info):
                    if self._search_source_in_group(source_info, source_name):
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao buscar fonte na cena {scene_name}: {e}")
            return False
    
    def _is_group_source(self, source_name: str) -> bool:
        """Verifica se uma fonte é um grupo"""
        try:
            self.ws.call(requests.GetGroupSceneItemList(sceneName=source_name))
            return True
        except Exception:
            return False
    
    def _search_source_in_group(self, group_name: str, source_name: str) -> bool:
        """Busca uma fonte dentro de um grupo específico"""
        try:
            group_items_response = self.ws.call(requests.GetGroupSceneItemList(sceneName=group_name))
            group_items = group_items_response.getSceneItems()
            
            for item in group_items:
                source_info = item.get('sourceName', '')
                
                if source_info == source_name:
                    return True
                
                if self._is_group_source(source_info):
                    if self._search_source_in_group(source_info, source_name):
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao buscar fonte no grupo {group_name}: {e}")
            return False
    
    def _get_scene_item_id(self, scene_name: str, source_name: str) -> Optional[int]:
        """Obtém o ID de um item de cena"""
        try:
            scene_items = self.ws.call(requests.GetSceneItemList(sceneName=scene_name))
            for item in scene_items.getSceneItems():
                if item["sourceName"] == source_name:
                    return item["sceneItemId"]
            return None
        except Exception as e:
            logger.error(f"Erro ao obter ID do item de cena: {e}")
            return None

# Instância global do serviço
obs_service = OBSService()