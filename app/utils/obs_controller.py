from obswebsocket import obsws, requests
from typing import Optional, Dict, Any
import logging

# Configuração do logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('obs_controller.log')
    ]
)
logger = logging.getLogger(__name__)

class OBSController:
    def __init__(self, host: str = "localhost", port: int = 4455, password: str = "", recording_directory: str = ""):
        self.host = host
        self.port = port
        self.password = password
        self.recording_directory = recording_directory
        self.ws: Optional[obsws] = None
        self._connected = False
        
    def connect(self) -> bool:
        try:
            self.ws = obsws(self.host, self.port, self.password)
            self.ws.connect()
            self._connected = True
            return True
        except Exception:
            self._connected = False
            return False
    
    def disconnect(self) -> None:
        if self.ws:
            self.ws.disconnect()
            self._connected = False
    
    def update_text_source(self, source_name: str, text: str) -> bool:
        if not self._connected or not self.ws:
            return False
            
        try:
            logger.info(f"Atualizando fonte de texto {source_name} com texto: {text}")
            if not self._source_exists(source_name):
                return False
            
            self.ws.call(requests.SetInputSettings(
                inputName=source_name,
                inputSettings={"text": text}
            ))
            return True
        except Exception:
            return False
    
    @property
    def is_connected(self) -> bool:
        return self._connected
    
    def get_version_info(self) -> Optional[Dict[str, Any]]:
        if not self._connected or not self.ws:
            return None
        try:
            version_info = self.ws.call(requests.GetVersion())
            return {
                "obs_version": version_info.getObsVersion(),
                "websocket_version": version_info.getObsWebSocketVersion()
            }
        except Exception:
             return None
    
    def start_recording(self) -> bool:
        """Inicia a gravação no OBS"""
        if not self._connected or not self.ws:
            logger.error("Não é possível iniciar gravação - OBS não conectado")
            return False
        
        try:
            self.ws.call(requests.StartRecord())
            logger.info("Gravação iniciada com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar gravação: {str(e)}")
            return False
    
    def stop_recording(self) -> bool:
        """Para a gravação no OBS"""
        if not self._connected or not self.ws:
            logger.error("Não é possível parar gravação - OBS não conectado")
            return False
        
        try:
            self.ws.call(requests.StopRecord())
            logger.info("Gravação finalizada com sucesso")
            return True
        except Exception as e:
            logger.error(f"Erro ao parar gravação: {str(e)}")
            return False
    
    def set_recording_directory(self, directory_path: str) -> bool:
        """Define o diretório onde os vídeos serão salvos"""
        if not self._connected or not self.ws:
            logger.error("Não é possível definir diretório - OBS não conectado")
            return False
        
        if not self.create_directory_if_not_exists(directory_path):
            logger.error(f"Falha ao criar/verificar diretório: {directory_path}")
            return False
        
        try:
            self.ws.call(requests.SetRecordingFolder(recordingFolder=directory_path))
            self.recording_directory = directory_path
            logger.info(f"Diretório de gravação definido para: {directory_path}")
            return True
        except Exception as e:
            logger.error(f"Erro ao definir diretório de gravação: {str(e)}")
            return False
    
    def get_recording_directory(self) -> Optional[str]:
        """Obtém o diretório atual de gravação"""
        if not self._connected or not self.ws:
            logger.error("Não é possível obter diretório - OBS não conectado")
            return None
        
        try:
            response = self.ws.call(requests.GetRecordingFolder())
            current_directory = response.getRecordingFolder()
            logger.info(f"Diretório atual de gravação: {current_directory}")
            return current_directory
        except Exception as e:
            logger.error(f"Erro ao obter diretório de gravação: {str(e)}")
            return None
    
    def create_directory_if_not_exists(self, directory_path: str) -> bool:
        """Cria o diretório especificado se ele não existir.
        
        Args:
            directory_path (str): Caminho do diretório a ser criado
            
        Returns:
            bool: True se o diretório existe ou foi criado com sucesso, False caso contrário
        """
        import os
        
        if not directory_path:
            logger.error("Caminho do diretório não pode estar vazio")
            return False
        
        try:
            # Normaliza o caminho para o sistema operacional
            normalized_path = os.path.normpath(directory_path)
            
            if os.path.exists(normalized_path):
                if os.path.isdir(normalized_path):
                    logger.info(f"Diretório já existe: {normalized_path}")
                    return True
                else:
                    logger.error(f"Caminho existe mas não é um diretório: {normalized_path}")
                    return False
            
            # Cria o diretório e todos os diretórios pais necessários
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
    
    def _source_exists(self, source_name: str) -> bool:
        """Verifica se uma fonte existe, incluindo busca recursiva em grupos."""
        try:
            # Primeiro tenta buscar diretamente
            self.ws.call(requests.GetInputSettings(inputName=source_name))
            return True
        except Exception:
            # Se não encontrar diretamente, busca recursivamente em grupos
            return self._find_source_in_groups(source_name)
    
    def _find_source_in_groups(self, source_name: str) -> bool:
        """Busca recursivamente uma fonte dentro de grupos em todas as cenas."""
        try:
            # Obtém lista de todas as cenas
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
        """Busca uma fonte específica dentro de uma cena, incluindo grupos."""
        try:
            # Obtém itens da cena
            scene_items_response = self.ws.call(requests.GetSceneItemList(sceneName=scene_name))
            scene_items = scene_items_response.getSceneItems()
            
            for item in scene_items:
                source_info = item.get('sourceName', '')
                
                # Verifica se é a fonte procurada
                if source_info == source_name:
                    return True
                
                # Se for um grupo, busca recursivamente dentro dele
                if self._is_group_source(source_info):
                    if self._search_source_in_group(source_info, source_name):
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao buscar fonte na cena {scene_name}: {e}")
            return False
    
    def _is_group_source(self, source_name: str) -> bool:
        """Verifica se uma fonte é um grupo."""
        try:
            # Tenta obter propriedades do grupo
            self.ws.call(requests.GetGroupSceneItemList(sceneName=source_name))
            return True
        except Exception:
            return False
    
    def _search_source_in_group(self, group_name: str, source_name: str) -> bool:
        """Busca uma fonte dentro de um grupo específico."""
        try:
            # Obtém itens do grupo
            group_items_response = self.ws.call(requests.GetGroupSceneItemList(sceneName=group_name))
            group_items = group_items_response.getSceneItems()
            
            for item in group_items:
                source_info = item.get('sourceName', '')
                
                # Verifica se é a fonte procurada
                if source_info == source_name:
                    return True
                
                # Se for um grupo aninhado, busca recursivamente
                if self._is_group_source(source_info):
                    if self._search_source_in_group(source_info, source_name):
                        return True
            
            return False
        except Exception as e:
            logger.error(f"Erro ao buscar fonte no grupo {group_name}: {e}")
            return False
    
    def set_scene_item_enabled(self, scene_name: str, source_name: str, enabled: bool) -> bool:
        if not self._connected or not self.ws:
            return False
        try:
            self.ws.call(requests.SetSceneItemEnabled(
                sceneName=scene_name,
                sceneItemId=self._get_scene_item_id(scene_name, source_name),
                sceneItemEnabled=enabled
            ))
            return True
        except Exception:
            return False
    
    def _get_scene_item_id(self, scene_name: str, source_name: str) -> Optional[int]:
        try:
            scene_items = self.ws.call(requests.GetSceneItemList(sceneName=scene_name))
            for item in scene_items.getSceneItems():
                if item["sourceName"] == source_name:
                    return item["sceneItemId"]
            return None
        except Exception:
            return None


# Módulo OBSController - para uso como biblioteca
# Para testes, execute o main.py na raiz do projeto
