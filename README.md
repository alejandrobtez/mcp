# Agente con Microsoft Agent Framework conectado a un servidor MCP

Dos archivos:

- `mcp_server.py` — servidor MCP de ejemplo (transporte `streamable-http`) con
  6 tools: `sumar`, `restar`, `multiplicar`, `dividir`, `hora_actual` y
  `leer_readme_github`. Sirve como servidor de prueba; puedes apuntar el
  agente a cualquier otro servidor MCP cambiando una variable de entorno.
- `agent_mcp.py` — agente construido con el **Microsoft Agent Framework**
  (`agent-framework` + `agent-framework-foundry`) que usa
  `MCPStreamableHTTPTool` para descubrir y ejecutar las tools del servidor
  MCP mediante function calling, razonando con un modelo desplegado en
  **Azure AI Foundry**.

## Instalación

```bash
pip install -r requirements.txt
```

## Configuración

El agente usa `FoundryChatClient`, que se autentica con tu sesión local de
Azure CLI:

```bash
az login
```

Variables de entorno necesarias:

```bash
export FOUNDRY_PROJECT_ENDPOINT="https://tu-proyecto.services.ai.azure.com"
export FOUNDRY_MODEL="gpt-4o-mini"   # nombre de tu deployment en Foundry
export MCP_SERVER_URL="http://127.0.0.1:8000/mcp"   # opcional, este es el valor por defecto
```

## Ejecución

```bash
# Terminal 1: levantar el servidor MCP
python3 mcp_server.py

# Terminal 2: ejecutar el agente
python3 agent_mcp.py
```

El agente hará dos preguntas de ejemplo ("¿cuánto es 234 * 17?" y "¿qué hora
es en UTC?"), decidirá qué tool MCP usar para cada una, la ejecutará a
través del servidor MCP, y mostrará la respuesta final.

## Cómo está conectado MCP al agente

```python
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

async with (
    MCPStreamableHTTPTool(name="demo-public-server", url=MCP_SERVER_URL) as mcp_tool,
    Agent(
        client=FoundryChatClient(
            project_endpoint=FOUNDRY_PROJECT_ENDPOINT,
            model=FOUNDRY_MODEL,
            credential=AzureCliCredential(),
        ),
        name="MCPAgent",
        instructions="...",
    ) as agent,
):
    result = await agent.run("¿Cuánto es 234 * 17?", tools=mcp_tool)
```

`MCPStreamableHTTPTool` se conecta al servidor MCP, descubre sus tools
(`list_tools` del protocolo MCP) y las expone al agente como funciones
invocables. Cuando el modelo decide llamar a una, el framework ejecuta la
llamada MCP real contra el servidor y devuelve el resultado al modelo para
que formule la respuesta final.

## Conectarlo a otro servidor MCP público

Cambia `MCP_SERVER_URL` por la URL del servidor que quieras usar. Si ese
servidor requiere autenticación (la mayoría de los MCP "de marca" como
GitHub o Microsoft Learn la requieren), añade `header_provider` a
`MCPStreamableHTTPTool`:

```python
MCPStreamableHTTPTool(
    name="otro-servidor",
    url="https://el-servidor-que-quieras/mcp",
    header_provider=lambda kwargs: {"Authorization": f"Bearer {kwargs['token']}"},
)
```
