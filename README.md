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
obs-controller-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # Inicializador da aplicação FastAPI
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
│   │   └── obs_service.py   # Lógica de negócio OBS
│   ├── db/
│   │   └── __init__.py
│   └── util/
│       └── __init__.py
├── utils/                   # Legado (será removido)
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

### Estratégia de Conexão

- **Conexão Automática**: A API conecta automaticamente ao OBS quando necessário
- **Desconexão Manual**: Use o endpoint `/obs/disconnect` para desconectar
- **Reconexão**: A API reconecta automaticamente em operações subsequentes

### Instalação

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd obs-controller-api
```

2. Instale as dependências:
```bash
pip install fastapi uvicorn obs-websocket-py pydantic-settings
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
- `GET /api/recording/stop` - Para a gravação em andamento
  - Response: `{"status": "success", "reason": ""}` ou `{"status": "error", "reason": "..."}`
- `GET /api/recording/getvideo` - Busca o vídeo mais recente na pasta `OBS_RECORDING_DIR` e retorna sua URL e um QR code (base64, PNG 256x256) dessa URL
  - Response: `{"status": "success", "url": "...", "image": "<base64>"}` ou `{"status": "error", "reason": "..."}`
  - O vídeo fica disponível para download/streaming diretamente em `url` (servido estaticamente em `/videos/<arquivo>`)

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

#### Configurações de Banco de Dados
| Variável | Padrão | Descrição |
|----------|--------|----------|
| `MONGO_URI` | - | URI de conexão MongoDB (obrigatório) |
| `MONGO_DB` | intel | Nome do banco de dados |

#### Configurações JWT
| Variável | Padrão | Descrição |
|----------|--------|----------|
| `JWT_SECRET` | - | Chave secreta JWT (obrigatório) |
| `JWT_ALGORITHM` | HS256 | Algoritmo de criptografia JWT |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | 1440 | Tempo de expiração do token (minutos) |
| `ADMIN_CREATION_TOKEN` | - | Token para criação de admin (obrigatório) |

#### Monitoramento (Opcional)
| Variável | Padrão | Descrição |
|----------|--------|----------|
| `SENTRY_DSN` | None | DSN do Sentry para monitoramento |
| `LOG_API` | None | API de logs externa |
| `LOG_ID` | None | ID do sistema de logs |

#### Serviços Externos
| Variável | Padrão | Descrição |
|----------|--------|----------|
| `SHORTENER_BASE_URL` | https://go.dbpe.com.br | URL base do encurtador |
| `SHORTENER_USER` | - | Usuário do encurtador (obrigatório) |
| `SHORTENER_PASSWORD` | - | Senha do encurtador (obrigatório) |
| `CADASTRO_BASE_URL` | https://skynelite.ngrok.app/api/skyn/cta | URL do sistema de cadastro |

#### Comunicação
| Variável | Padrão | Descrição |
|----------|--------|----------|
| `UDP_PORT` | 5004 | Porta UDP para comunicação |
| `SERIAL_PORT` | COM3 | Porta serial |
| `SERIAL_BAUDRATE` | 9600 | Taxa de transmissão serial |

#### OBS WebSocket
| Variável | Padrão | Descrição |
|----------|--------|----------|
| `OBS_HOST` | localhost | Host do OBS WebSocket |
| `OBS_PORT` | 4455 | Porta do OBS WebSocket |
| `OBS_PASSWORD` | v5rk4RQAqy9uX9Eb | Senha do OBS WebSocket |
| `OBS_RECORDING_DIR` | - | Diretório de gravações (obrigatório, precisa ser um caminho absoluto) |

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
| `PORT` | 8000 | Porta da API |
| `RELOAD` | true | Auto-reload em desenvolvimento |
| `LOG_LEVEL` | INFO | Nível de log |

## 🔧 Desenvolvimento

### Estrutura Modular

- **`app/main.py`**: Factory da aplicação FastAPI
- **`app/api/obs.py`**: Routers e endpoints
- **`app/models/obs.py`**: Schemas de request/response
- **`app/services/obs_service.py`**: Lógica de negócio
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