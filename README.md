# Mi primer cliente MCP con el Agent Framework de Microsoft

## ¿Qué hemos hecho aquí?

La idea de este proyecto es sencilla: construir nuestro propio cliente que
hable con un servidor MCP, en vez de depender de una app ya hecha (como
Claude Desktop o Copilot). Así controlamos nosotros todo: a qué servidor
nos conectamos, qué modelo razona, y qué hace con las respuestas.

MCP (Model Context Protocol) es solo un estándar para que un agente de IA
pueda "pedir prestadas" herramientas a un servidor externo: sumar números,
consultar una API, leer un archivo, lo que sea. El servidor expone una
lista de tools, y cualquier cliente que hable el protocolo puede
descubrirlas y usarlas.

Aquí usamos el **Microsoft Agent Framework** (la librería `agent_framework`
en Python) para montar esa pieza de cliente, conectada a un modelo de
**Azure AI Foundry** que es quien decide qué tool usar y cuándo.

## Los dos archivos

### `mcp_server.py` — el servidor

Esto es el lado que *ofrece* las herramientas. Lo hemos montado nosotros
mismos para tener algo real con lo que probar, sin depender de servidores
externos que casi siempre piden API keys. Tiene 6 funciones sencillas:

- `sumar`, `restar`, `multiplicar`, `dividir` — operaciones básicas
- `hora_actual` — devuelve la fecha y hora UTC
- `leer_readme_github` — descarga el README de un repo público de GitHub

Cuando lo ejecutas, queda escuchando en `http://127.0.0.1:8000/mcp`,
esperando a que algún cliente le pregunte qué tools tiene o le pida que
ejecute alguna.

### `agent_mcp.py` — el cliente (la parte que pediste)

Esto es el cliente MCP de verdad. No hablamos el protocolo a mano (sería
bastante tedioso); usamos `MCPStreamableHTTPTool`, una clase que ya viene
en el Agent Framework y que se encarga de toda la mecánica del protocolo:

1. Abre la conexión con el servidor MCP.
2. Le pregunta qué tools tiene disponibles.
3. Las convierte en funciones que un agente puede llamar.

Por otro lado, montamos un `Agent` conectado a un modelo de Azure AI
Foundry (`FoundryChatClient`). Este agente es quien recibe tu pregunta en
lenguaje natural, decide si necesita usar alguna tool del servidor MCP
para responder, la ejecuta, y te devuelve la respuesta final ya elaborada.

En resumen, el flujo es: **tu pregunta → el modelo decide qué tool usar →
el cliente MCP llama al servidor → el servidor responde → el modelo
redacta la respuesta final.**

## Cómo lo pones en marcha

Primero, crea un entorno virtual para no mezclar paquetes con el resto de
tu sistema (en Arch esto es casi obligatorio):

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Necesitas tener Azure CLI instalado y haber hecho login una vez:

```bash
az login
```

Ahora, en dos terminales distintas (con el `venv` activado en ambas):

```bash
# Terminal 1 — levanta el servidor de tools
python3 mcp_server.py
```

```bash
# Terminal 2 — ejecuta el agente
export FOUNDRY_PROJECT_ENDPOINT="https://tu-proyecto.services.ai.azure.com"
export FOUNDRY_MODEL="gpt-4o-mini"
python3 agent_mcp.py
```

Verás cómo el agente responde a un par de preguntas de ejemplo
("¿cuánto es 234 por 17?", "¿qué hora es en UTC?"), usando las tools del
servidor para resolverlas en lugar de inventarse la respuesta.

## ¿Y si quiero conectarme a otro servidor MCP, no al de prueba?

Solo tienes que cambiar una línea, la URL:

```bash
export MCP_SERVER_URL="https://el-servidor-que-quieras/mcp"
```

El resto del código no cambia. Eso es lo bonito de MCP: como es un
estándar, el mismo cliente sirve para cualquier servidor que lo hable, sin
tener que reescribir nada.

Eso sí: muchos servidores MCP "de verdad" (GitHub, por ejemplo) exigen una
API key o token para conectarte. En ese caso hay que añadir una cabecera
de autenticación a la conexión. Microsoft tiene un ejemplo oficial de
cómo hacerlo aquí:
[`mcp_api_key_auth.py`](https://github.com/microsoft/agent-framework/blob/main/python/samples/02-agents/mcp/mcp_api_key_auth.py).
La idea, resumida, es pasarle al `MCPStreamableHTTPTool` un
`header_provider`, que es básicamente una función que genera la cabecera
`Authorization: Bearer ...` con tu clave en el momento de cada llamada, en
vez de dejarla fija en el código.
