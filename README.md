# Servidor MCP en Azure Functions

Proyecto educativo que implementa un **servidor MCP (Model Context Protocol)** desplegado como **Azure Function**.

El servidor expone herramientas (tools) que un agente de IA puede invocar automáticamente usando Azure OpenAI como modelo de lenguaje.

---

## ¿Qué es MCP?

**Model Context Protocol** es un protocolo estándar que permite a los LLMs (modelos de lenguaje) llamar a funciones externas de forma estructurada. El agente decide qué herramienta usar según la pregunta del usuario y recibe el resultado para formular su respuesta.

```
Usuario → Agente (Azure OpenAI) → Servidor MCP → Tool (función Python) → Respuesta
```

---

## Estructura del proyecto

```
mcppppp/
├── function_app.py          # Punto de entrada de Azure Functions
├── host.json                # Configuración del runtime de Azure Functions
├── local.settings.json      # Variables de entorno locales (no subir a git)
├── requirements.txt         # Dependencias del servidor
├── server/
│   └── mcp_server.py        # Definición de las tools del servidor MCP
└── client/
    ├── main.py              # Agente que usa el servidor MCP
    └── .env                 # Credenciales del cliente (no subir a git)
```

---

## Herramientas disponibles en el servidor MCP

| Tool | ¿Qué hace? | Parámetros |
|---|---|---|
| `add` | Suma dos números enteros | `a: int`, `b: int` |
| `get_weather` | Devuelve el tiempo de una ciudad (simulado) | `city: str` |
| `get_current_datetime` | Fecha y hora UTC del servidor | — |
| `convert_temperature` | Convierte entre Celsius, Fahrenheit y Kelvin | `value: float`, `from_unit: str`, `to_unit: str` |
| `calculate_percentage` | Calcula el % de una parte sobre un total | `part: float`, `total: float` |

---

## Requisitos previos

Antes de empezar necesitas tener instalado:

- **Python 3.11 o superior** — [descargar](https://www.python.org/downloads/)
- **Git** — para clonar el repositorio
- Credenciales de **Azure OpenAI** (endpoint, API key y nombre del deployment)

---

## Instalación paso a paso

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd mcppppp
```

### 2. Crear el entorno virtual e instalar dependencias

```bash
# Crear entorno virtual
python -m venv .venv

# Activar el entorno virtual
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows (PowerShell)

# Instalar las dependencias del servidor y del cliente
pip install -r requirements.txt
pip install agent-framework agent-framework-openai python-dotenv
```

### 3. Configurar las credenciales del cliente

Edita el fichero `client/.env` con tus credenciales de Azure OpenAI:

```env
AZURE_OPENAI_ENDPOINT=https://TU-RECURSO.openai.azure.com/
AZURE_OPENAI_API_KEY=TU_API_KEY
AZURE_OPENAI_CHAT_MODEL=gpt-4o

# URL del servidor MCP (en local no hace falta cambiarla)
MCP_URL=http://localhost:7071/mcp
```

> **Importante:** nunca subas el fichero `.env` a GitHub. Contiene credenciales privadas.

---

## Cómo ejecutar el proyecto en local

Necesitas **dos terminales** abiertas al mismo tiempo.

### Terminal 1 — Arrancar el servidor MCP

```bash
# Asegúrate de estar en la raíz del proyecto con el venv activo
source .venv/bin/activate

.venv/bin/uvicorn function_app:asgi_app --port 7071
```

Verás algo así cuando esté listo:

```
INFO:     Started server process [12345]
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:7071
```

El servidor MCP queda disponible en: **`http://localhost:7071/mcp`**

### Terminal 2 — Ejecutar el agente (cliente)

```bash
# Entrar a la carpeta client
cd client

# Ejecutar el agente
../.venv/bin/python main.py
```

### Resultado esperado

```
────────────────────────────────────────────────────────────
Consulta: Calcula 15 + 27 usando las herramientas disponibles.
────────────────────────────────────────────────────────────
Respuesta: El resultado de sumar 15 + 27 es 42.

────────────────────────────────────────────────────────────
Consulta: ¿Qué tiempo hace en Oslo, Noruega?
────────────────────────────────────────────────────────────
Respuesta: En Oslo hace 22°C y el cielo está despejado.

────────────────────────────────────────────────────────────
Consulta: Convierte 100 grados Fahrenheit a Celsius.
────────────────────────────────────────────────────────────
Respuesta: 100 °F equivalen a aproximadamente 37.78 °C.
```

---

## Solución de problemas comunes

**Error: `address already in use` (puerto 7071 ocupado)**

```bash
# Liberar el puerto
fuser -k 7071/tcp
# Volver a arrancar el servidor
```

**Error: `No module named 'mcp'`**

```bash
# Asegúrate de tener el venv activado antes de instalar
source .venv/bin/activate
pip install -r requirements.txt
```

**Error: `401 Unauthorized` al llamar a Azure OpenAI**

Revisa que `AZURE_OPENAI_API_KEY` en `client/.env` sea correcta y que el deployment `AZURE_OPENAI_CHAT_MODEL` exista en tu recurso de Azure.

---

## Cómo funciona por dentro

```
client/main.py
  └─ Agent (Azure OpenAI)
       └─ MCPStreamableHTTPTool  ──POST──▶  http://localhost:7071/mcp
                                              └─ function_app.py (ASGI)
                                                   └─ server/mcp_server.py
                                                        ├─ add()
                                                        ├─ get_weather()
                                                        ├─ get_current_datetime()
                                                        ├─ convert_temperature()
                                                        └─ calculate_percentage()
```

1. El agente recibe una pregunta en lenguaje natural.
2. Azure OpenAI decide qué tool del servidor MCP invocar.
3. El servidor ejecuta la función Python correspondiente.
4. El resultado vuelve al agente, que formula la respuesta final.

---

## Despliegue en Azure (opcional)

Si quieres desplegar el servidor en la nube:

```bash
# 1. Instalar Azure Functions Core Tools
# https://learn.microsoft.com/azure/azure-functions/functions-run-local

# 2. Iniciar sesión en Azure
az login

# 3. Crear la Function App (solo la primera vez)
az group create --name mcp-rg --location westeurope
az storage account create --name mcpstorage<sufijo> --location westeurope \
  --resource-group mcp-rg --sku Standard_LRS
az functionapp create --resource-group mcp-rg \
  --consumption-plan-location westeurope \
  --runtime python --runtime-version 3.11 --functions-version 4 \
  --name <NOMBRE_FUNCTION_APP> \
  --storage-account mcpstorage<sufijo> --os-type linux

# 4. Desplegar el código
func azure functionapp publish <NOMBRE_FUNCTION_APP>
```

Tras el despliegue, cambia `MCP_URL` en `client/.env`:

```env
MCP_URL=https://<NOMBRE_FUNCTION_APP>.azurewebsites.net/mcp
```
