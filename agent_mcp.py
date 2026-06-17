"""
Agente construido con Microsoft Agent Framework (agent-framework + agent-framework-foundry)
que se conecta a un servidor MCP y usa sus tools mediante function calling.

Modelo: Azure AI Foundry (FoundryChatClient), autenticado con AzureCliCredential
(es decir, usa la sesion de `az login` que ya tengas activa en tu maquina).

Servidor MCP: cualquier servidor que hable streamable-http. Por defecto apunta al
servidor de ejemplo de este mismo proyecto (mcp_server.py), pero puedes cambiarlo
con la variable de entorno MCP_SERVER_URL.

Variables de entorno necesarias:
    FOUNDRY_PROJECT_ENDPOINT   -> ej. https://xxxxxxxxxxxx.ai.azure.com
    FOUNDRY_MODEL              -> ej. gpt-4o-mini
    MCP_SERVER_URL             -> opcional, por defecto http://127.0.0.1:8000/mcp

Requiere sesion de Azure CLI activa: `az login`
"""

import asyncio
import os

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential


MCP_SERVER_URL = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")
FOUNDRY_PROJECT_ENDPOINT = os.environ.get("FOUNDRY_PROJECT_ENDPOINT")
FOUNDRY_MODEL = os.environ.get("FOUNDRY_MODEL", "gpt-4o-mini")


async def main() -> None:
    if not FOUNDRY_PROJECT_ENDPOINT:
        raise RuntimeError(
            "Falta la variable de entorno FOUNDRY_PROJECT_ENDPOINT "
            "(ej. https://tu-proyecto.services.ai.azure.com)"
        )

    credential = AzureCliCredential()

    foundry_client = FoundryChatClient(
        project_endpoint=FOUNDRY_PROJECT_ENDPOINT,
        model=FOUNDRY_MODEL,
        credential=credential,
    )

    async with (
        MCPStreamableHTTPTool(
            name="demo-public-server",
            url=MCP_SERVER_URL,
        ) as mcp_tool,
        Agent(
            client=foundry_client,
            name="MCPAgent",
            instructions=(
                "Eres un asistente que resuelve tareas usando las tools MCP "
                "disponibles. Usa siempre una tool cuando la pregunta lo "
                "requiera en lugar de calcular u opinar por tu cuenta."
            ),
        ) as agent,
    ):
        preguntas = [
            "¿Cuánto es 234 multiplicado por 17?",
            "¿Qué hora es ahora en UTC?",
        ]
        for pregunta in preguntas:
            print(f"\nUsuario: {pregunta}")
            resultado = await agent.run(pregunta, tools=mcp_tool)
            print(f"Agente:  {resultado.text}")


if __name__ == "__main__":
    asyncio.run(main())
