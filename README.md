# Cliente MCP propio con Microsoft Agent Framework

Este proyecto monta un cliente MCP (Model Context Protocol) construido sobre
el **Microsoft Agent Framework**, capaz de conectarse a cualquier servidor
MCP público —con o sin autenticación— y usar sus tools desde un agente que
razona con un modelo de **Azure AI Foundry**.

La referencia oficial que sigue este patrón es el ejemplo de Microsoft
[`mcp_api_key_auth.py`](https://github.com/microsoft/agent-framework/blob/main/python/samples/02-agents/mcp/mcp_api_key_auth.py),
que muestra cómo autenticar contra un servidor MCP remoto pasando una API
key como cabecera HTTP en tiempo de ejecución. Nuestro `agent_mcp.py` aplica
exactamente esa idea, generalizada para que el servidor de destino sea
configurable.

## Qué hace cada archivo

- `mcp_server.py` — un servidor MCP de ejemplo (transporte `streamable-http`,
  sin autenticación) con 6 tools: `sumar`, `restar`, `multiplicar`,
  `dividir`, `hora_actual` y `leer_readme_github`. Sirve como servidor de
  prueba para validar el cliente sin depender de servicios externos.
- `agent_mcp.py` — el cliente MCP propiamente dicho. No es un cliente MCP
  "a pelo" hablando JSON-RPC manualmente: usa la clase `MCPStreamableHTTPTool`
  del Agent Framework, que internamente abre la sesión MCP, descubre las
  tools del servidor (`tools/list`) y las convierte en funciones invocables
  por un agente (`FunctionTool`). El agente decide cuándo y con qué
  argumentos llamarlas mediante function calling.

## Por qué "tu propio cliente MCP" y no un MCP host genérico

Clientes MCP como Claude Desktop o GitHub Copilot vienen ya integrados y
preconfigurados para un conjunto fijo de servidores. Aquí, en cambio, el
cliente es el propio código Python: tú decides a qué servidor te conectas,
qué credenciales le pasas, qué modelo razona sobre las tools, y qué hace el
agente con cada respuesta. Es la misma idea de fondo que un MCP host
normal, pero expuesta como una pieza de software que puedes versionar,
extender y desplegar donde quieras.

## Arquitectura

```
   tu pregunta en texto
          |
          v
  +-------------------+        descubre y llama tools         +------------------+
  |   Agent (gpt-...)  |  <----------------------------------> |  Servidor MCP    |
  |  FoundryChatClient |        MCPStreamableHTTPTool           |  (cualquiera)    |
  +-------------------+                                         +------------------+
          |
          v
   respuesta final
```

El `Agent` no llama directamente al servidor MCP: la llamada pasa por
`MCPStreamableHTTPTool`, que es la capa que efectivamente habla el
protocolo MCP (streamable HTTP) contra el servidor. El modelo de Foundry
solo ve "funciones disponibles" — no sabe ni le importa que detrás haya un
servidor MCP remoto.

## Conectarse a un servidor MCP sin autenticación

Es el caso de `mcp_server.py` (nuestro servidor de prueba) o de servidores
públicos abiertos. Basta con la URL:

```python
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

async with (
    MCPStreamableHTTPTool(
        name="mi-servidor-mcp",
        url="http://127.0.0.1:8000/mcp",
    ) as mcp_tool,
    Agent(
        client=FoundryChatClient(
            project_endpoint=FOUNDRY_PROJECT_ENDPOINT,
            model=FOUNDRY_MODEL,
            credential=AzureCliCredential(),
        ),
        name="MCPAgent",
        instructions="Resuelve tareas usando las tools MCP disponibles.",
    ) as agent,
):
    resultado = await agent.run("¿Cuánto es 234 * 17?", tools=mcp_tool)
    print(resultado.text)
```

Esto es exactamente lo que hace `agent_mcp.py` tal cual está hoy.

## Conectarse a un servidor MCP que requiere API key

Muchos servidores MCP públicos de verdad (no de demo) exigen una cabecera
de autenticación. El patrón oficial de Microsoft (`mcp_api_key_auth.py`)
resuelve esto con `header_provider`: una función que se evalúa en cada
llamada y genera las cabeceras necesarias, en lugar de "hornear" la clave
dentro del cliente HTTP compartido.

```python
import os
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential

api_key = os.environ["MCP_API_KEY"]

mcp_tool = MCPStreamableHTTPTool(
    name="servidor-con-api-key",
    url=os.environ["MCP_SERVER_URL"],
    header_provider=lambda kwargs: {"Authorization": f"Bearer {kwargs['mcp_api_key']}"},
)

async with (
    mcp_tool,
    Agent(
        client=FoundryChatClient(credential=AzureCliCredential()),
        name="MCPAgent",
        instructions="Resuelve tareas usando las tools MCP disponibles.",
    ) as agent,
):
    resultado = await agent.run(
        "¿Qué tools tienes disponibles?",
        tools=mcp_tool,
        function_invocation_kwargs={"mcp_api_key": api_key},
    )
    print(resultado.text)
```

La clave nunca queda fija en el objeto `MCPStreamableHTTPTool`: solo vive
en el contexto de esa ejecución concreta (`function_invocation_kwargs`),
así que no se filtra entre llamadas ni queda persistida en el cliente.

## Variables de entorno

```bash
FOUNDRY_PROJECT_ENDPOINT   # ej. https://tu-proyecto.services.ai.azure.com
FOUNDRY_MODEL              # nombre de tu deployment, ej. gpt-4o-mini
MCP_SERVER_URL             # opcional, por defecto http://127.0.0.1:8000/mcp
```

## Instalación y ejecución

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

az login   # autenticación con Azure CLI, requerida por AzureCliCredential
```

```bash
# Terminal 1: levantar el servidor MCP de prueba
source venv/bin/activate
python3 mcp_server.py

# Terminal 2: ejecutar el cliente/agente
source venv/bin/activate
export FOUNDRY_PROJECT_ENDPOINT="https://tu-proyecto.services.ai.azure.com"
export FOUNDRY_MODEL="gpt-4o-mini"
python3 agent_mcp.py
```

El agente lanzará dos preguntas de ejemplo, decidirá qué tool MCP usar para
cada una, la ejecutará contra el servidor real, y mostrará la respuesta
final generada por el modelo.

## Llevarlo a cualquier otro servidor MCP público

Para reapuntar el cliente a otro servidor MCP, solo cambia `MCP_SERVER_URL`.
Si ese servidor exige autenticación, añade `header_provider` como en el
ejemplo anterior. Ningún otro cambio es necesario: el resto del código
(descubrimiento de tools, function calling, ejecución) es genérico y no
depende de qué servidor MCP haya al otro lado.

## Referencias

- Ejemplo oficial de autenticación con API key:
  [`mcp_api_key_auth.py`](https://github.com/microsoft/agent-framework/blob/main/python/samples/02-agents/mcp/mcp_api_key_auth.py)
- Documentación oficial de MCP tools en Agent Framework:
  [Using MCP Tools](https://learn.microsoft.com/en-us/agent-framework/agents/tools/local-mcp-tools)
- Documentación oficial de `FoundryChatClient`:
  [Microsoft Foundry provider](https://learn.microsoft.com/en-us/agent-framework/agents/providers/microsoft-foundry)
