# Copyright (c) Microsoft. All rights reserved.
import asyncio
import sys

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.foundry import FoundryChatClient
from azure.identity import AzureCliCredential
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

"""
Cliente MCP conectado al servidor publico de GitHub

Este script conecta un agente, construido con el Microsoft Agent Framework,
al servidor MCP oficial de GitHub (https://api.githubcopilot.com/mcp/).
Ese servidor expone tools como buscar repos, leer archivos, abrir issues,
etc., pero requiere autenticacion: hay que pasarle un Personal Access
Token (PAT) de GitHub en la cabecera Authorization.

Usamos el patron `header_provider` de MCPStreamableHTTPTool: el token no se
queda fijo en el cliente, sino que se inyecta en cada llamada a traves de
`function_invocation_kwargs`, pasado a `Agent.run(...)`.

Como crear un PAT de GitHub:
    https://github.com/settings/tokens
    (basta con el scope de lectura de repos publicos para probar esto)

Como ejecutarlo:
    python mcp_client.py <tu_personal_access_token>

El modelo que razona es un deployment de Azure AI Foundry (FoundryChatClient),
autenticado con tu sesion local de `az login`.

Variables de entorno necesarias (puedes ponerlas en un archivo .env):
    FOUNDRY_PROJECT_ENDPOINT   -> ej. https://tu-proyecto.services.ai.azure.com
    FOUNDRY_MODEL              -> ej. gpt-4o-mini (el nombre de tu deployment)
"""

GITHUB_MCP_URL = "https://api.githubcopilot.com/mcp/"


async def github_mcp_client(github_pat: str) -> None:
    """Conecta un agente al servidor MCP de GitHub usando un PAT como autenticacion."""
    async with Agent(
        client=FoundryChatClient(credential=AzureCliCredential()),
        name="GitHubAgent",
        instructions="Eres un asistente util. Usa tu tool MCP para responder preguntas sobre GitHub.",
        tools=MCPStreamableHTTPTool(
            name="GitHub MCP",
            description="Servidor MCP oficial de GitHub: repos, issues, pull requests, busqueda de codigo.",
            url=GITHUB_MCP_URL,
            header_provider=lambda kwargs: {"Authorization": f"Bearer {kwargs['github_pat']}"},
        ),
    ) as agent:
        query = "Usa tu tool MCP para decirme que tools tienes disponibles."
        print(f"Usuario: {query}")
        result = await agent.run(
            query,
            function_invocation_kwargs={"github_pat": github_pat},
        )
        print(f"Agente: {result.text}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python mcp_client.py <tu_personal_access_token_de_github>")
        sys.exit(1)
    asyncio.run(github_mcp_client(sys.argv[1]))
