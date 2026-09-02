# OBS Controller API

API REST para controlar o OBS Studio remotamente via WebSocket.

## 📋 Funcionalidades

- ✅ Atualização de fontes de texto
- ✅ Controle de gravação (iniciar/parar)
- ✅ Habilitação/desabilitação de itens de cena
- ✅ Verificação de status do OBS
- ✅ Configuração de diretório de gravação
- ✅ Conexão inteligente ao OBS (conecta sob demanda)
- ✅ Controle manual de conexão/desconexão

## 🏗️ Estrutura do Projeto

```
ecco-server/
├── app/
│   ├── __init__.py
│   ├── main.py              # Inicializador da aplicação FastAPI, rotas /videos e /watch
│   ├── api/
│   │   ├── __init__.py
│   │   └── obs.py           # Endpoints da API OBS
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py        # Configurações centrais
│   ├── models/
│   │   ├── __init__.py
│   │   └── obs.py           # Schemas Pydantic
│   ├── services/
│   │   ├── __init__.py
│   │   ├── obs_service.py       # Lógica de negócio OBS
│   │   ├── cleanup_service.py   # Limpeza automática de gravações antigas
│   │   └── video_overlay.py     # Aplica app/assets/ecco_msg.png sobre a gravação via ffmpeg
│   ├── web/
│   │   ├── __init__.py
│   │   └── watch_page.py    # Página HTML de player/download (/watch/{filename})
│   ├── assets/
│   │   └── ecco_msg.png     # Imagem de overlay aplicada às gravações
│   ├── db/
│   │   └── __init__.py      # Stub vazio (MongoDB foi removido, ver histórico do git)
│   └── utils/                # Legado, não usado pela aplicação
├── tools/
│   └── fullscreen_clock.py  # Utilitário standalone para testar sincronização de gravação
├── main.py                  # Ponto de entrada
├── .gitignore
└── README.md
```

## 🚀 Como Usar

### Pré-requisitos

1. **OBS Studio** instalado e configurado
2. **Plugin WebSocket** habilitado no OBS:
   - Vá em `Ferramentas > obs-websocket Settings`
   - Habilite o servidor WebSocket
   - Configure a porta (padrão: 4455) e senha
3. **Python 3.8+** instalado
4. **ffmpeg** instalado e disponível no PATH (usado para aplicar o overlay `app/assets/ecco_msg.png` sobre as gravações)

### Estratégia de Conexão

- **Conexão Automática**: A API conecta automaticamente ao OBS quando necessário
- **Desconexão Manual**: Use o endpoint `/api/disconnect` para desconectar
- **Reconexão**: A API reconecta automaticamente em operações subsequentes

### Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd obs-controller-api
```

2. Instale as dependências:
```bash
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente (opcional):
```bash
# Crie um arquivo .env na raiz do projeto
OBS_HOST=localhost
OBS_PORT=4455
OBS_PASSWORD=sua_senha_aqui
OBS_RECORDING_DIR=C:\Users\SeuUsuario\Videos\OBS
```

### Execução

```bash
python main.py
```

A API estará disponível em: `http://localhost:8003`

## 📚 Documentação da API

### Endpoints Principais

#### 🏠 Básicos
- `GET /` - Informações da API
- `GET /health` - Status de saúde

#### 🔌 Conexão OBS
- `POST /api/connect` - Conectar manualmente ao OBS
- `POST /api/disconnect` - Desconectar do OBS

#### 📝 Controle de Texto
- `POST /api/text/update` - Atualiza fonte de texto

```json
{
  "source_name": "Texto Principal",
  "text": "Novo texto para exibição"
}
```

#### 🎥 Controle de Gravação
- `GET /api/recording/start` - Inicia gravação no diretório padrão (`OBS_RECORDING_DIR`)
  - Response: `{"status": "success", "reason": ""}` ou `{"status": "error", "reason": "..."}`
- `GET /api/recording/stop` - Para a gravação em andamento e já renomeia o arquivo gravado para um nome em UUID
  - Response: `{"status": "success", "reason": ""}` ou `{"status": "error", "reason": "..."}`
- `GET /api/recording/getvideo` - Busca o vídeo mais recente na pasta `OBS_RECORDING_DIR`, garante que o arquivo esteja renomeado para UUID (renomeia na hora se ainda não estiver) e retorna a URL pública da página de visualização e um QR code (base64, PNG 256x256) dessa URL
  - Response: `{"status": "success", "url": "https://<PUBLIC_BASE_URL>/watch/<uuid>.<ext>", "image": "<base64>"}` ou `{"status": "error", "reason": "..."}`
  - Requer `PUBLIC_BASE_URL` configurada. Não depende de banco de dados — o UUID é o próprio nome do arquivo em disco
- `GET /watch/{filename}` - Página HTML com player de vídeo e botão de download, pensada para ser aberta a partir do QR code
- `GET /videos/{filename}` - Serve o arquivo de vídeo diretamente (usado pelo player da página `/watch` e para download/streaming programático)
- `GET /api/recording/directory` - Obtém o diretório de gravação atual configurado no OBS
  - Response: `{"directory": "..."}`
- `POST /api/recording/directory` - Define o diretório de gravação do OBS

```json
{
  "directory": "C:\\Gravacoes\\OBS"
}
```

#### 🎬 Controle de Cena
- `POST /api/scene-item/toggle` - Habilita/desabilita item

```json
{
  "source_name": "Webcam",
  "enabled": true,
  "scene_name": "Cena Principal"  // Opcional
}
```

#### 📊 Status
- `GET /api/status` - Status da conexão OBS

### Documentação Interativa

Acesse `http://localhost:8003/docs` para a documentação Swagger interativa.

## ⚙️ Configuração

### Variáveis de Ambiente

#### OBS WebSocket
| Variável | Padrão | Descrição |
|----------|--------|----------|
| `OBS_HOST` | localhost | Host do OBS WebSocket |
| `OBS_PORT` | 4455 | Porta do OBS WebSocket |
| `OBS_PASSWORD` | v5rk4RQAqy9uX9Eb | Senha do OBS WebSocket |
| `OBS_RECORDING_DIR` | - | Diretório de gravações (obrigatório, precisa ser um caminho absoluto) |
| `PUBLIC_BASE_URL` | - | URL pública usada para montar os links de `/api/recording/getvideo` (ex: domínio do ngrok, obrigatório para esse endpoint) |

#### Limpeza Automática de Gravações
| Variável | Padrão | Descrição |
|----------|--------|----------|
| `DELETE_OLD_FILES` | false | Liga/desliga a limpeza automática de vídeos antigos |
| `DELETE_OLD_FILES_MAX_LIFE` | 60 | Vida máxima de cada vídeo, em minutos, antes de ser apagado |
| `DELETE_OLD_FILES_MAX_POLL` | 5 | Intervalo, em minutos, entre cada verificação |

#### API e Servidor
| Variável | Padrão | Descrição |
|----------|--------|----------|
| `HOST` | 0.0.0.0 | Host da API |
| `PORT` | 8000 | Porta da API (`8003` é a porta convencional usada em desenvolvimento local) |
| `RELOAD` | true | Auto-reload em desenvolvimento |
| `LOG_LEVEL` | INFO | Nível de log |

> `.env.example` também lista variáveis como `JWT_*`, `SENTRY_DSN`, `SHORTENER_*`, `CADASTRO_BASE_URL`, `UDP_PORT` e `SERIAL_*`. Elas existem na classe `Settings` mas **não são lidas em nenhum lugar de `app/`** — são resquícios de um projeto relacionado e não afetam o comportamento desta API.

## 🔧 Desenvolvimento

### Estrutura Modular

- **`app/main.py`**: Factory da aplicação FastAPI, rotas `/videos/{filename}` e `/watch/{filename}`
- **`app/api/obs.py`**: Routers e endpoints
- **`app/models/obs.py`**: Schemas de request/response
- **`app/services/obs_service.py`**: Lógica de negócio OBS (conexão, gravação, renomeio para UUID)
- **`app/services/cleanup_service.py`**: Limpeza automática de gravações antigas
- **`app/web/watch_page.py`**: Página HTML de player/download exibida em `/watch/{filename}`
- **`app/core/config.py`**: Configurações centralizadas

### Logs

Logs são salvos em:
- Console (desenvolvimento)
- Arquivo `app.log` (produção)

## 🐛 Solução de Problemas

### Erro de Conexão
- Verifique se o OBS está rodando
- Confirme se o WebSocket está habilitado
- Verifique host, porta e senha

### Fonte não Encontrada
- Confirme o nome exato da fonte no OBS
- Verifique se a fonte está na cena ativa
- Para fontes em grupos, certifique-se que estão visíveis

### Erro de Gravação
- Verifique permissões do diretório
- Confirme configurações de gravação no OBS
- Verifique espaço em disco

## 📈 Próximos Passos

- [ ] Implementar autenticação JWT
- [ ] Adicionar controle de cenas
- [ ] Implementar streaming control
- [ ] Adicionar testes automatizados
- [ ] Dockerização da aplicação
- [ ] Métricas e monitoramento

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para detalhes.