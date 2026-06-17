"""
Cliente del agente que consume el servidor MCP desplegado en Azure Functions.

El agente usa Azure OpenAI como LLM y descubre automáticamente las tools
disponibles en el servidor MCP a través del protocolo Streamable HTTP.
"""

import asyncio
import os

from dotenv import load_dotenv

from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.openai import OpenAIChatClient

# Cargar variables de entorno desde el fichero .env (situado en client/)
load_dotenv()


async def main():
    # ──────────────────────────────────────────────
    # Crear el cliente LLM con las credenciales de Azure OpenAI.
    # Las variables de entorno se leen del fichero .env:
    #   AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_API_KEY, AZURE_OPENAI_CHAT_MODEL
    # ──────────────────────────────────────────────
    client = OpenAIChatClient(
        azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
        api_key=os.getenv("AZURE_OPENAI_API_KEY"),
        model=os.getenv("AZURE_OPENAI_CHAT_MODEL")
    )

    # URL del servidor MCP.
    # - Local (Azure Functions Core Tools): http://localhost:7071/mcp
    # - Azure desplegado:                  https://<function-app>.azurewebsites.net/mcp
    # Se lee de la variable MCP_URL en .env para no hardcodear la URL.
    mcp_url = os.getenv("MCP_URL", "http://localhost:7071/mcp")

    # ──────────────────────────────────────────────
    # Inicializar el agente con:
    #   - client: el LLM de Azure OpenAI
    #   - name: nombre identificativo del agente
    #   - instructions: prompt de sistema que guía el comportamiento
    #   - tools: lista de herramientas MCP disponibles
    # MCPStreamableHTTPTool conecta con el servidor MCP en la URL indicada
    # y descubre automáticamente todas las tools registradas.
    # ──────────────────────────────────────────────
    async with Agent(
        client=client,
        name="mcp-azure-agent",
        instructions=(
            "Eres un asistente útil. Usa las herramientas MCP disponibles "
            "cuando el usuario necesite cálculos, información del tiempo, "
            "conversiones de temperatura, porcentajes o la fecha y hora actual."
        ),
        tools=[
            MCPStreamableHTTPTool(
                name="mcp",
                description="Servidor MCP con herramientas de utilidad general",
                url=mcp_url
            )
        ],
    ) as agent:

        # ──────────────────────────────────────────────
        # Ejecutar varias consultas para demostrar las distintas tools:
        #   1. add               → suma dos números
        #   2. get_weather       → tiempo simulado de una ciudad
        #   3. get_current_datetime → fecha y hora del servidor
        #   4. convert_temperature  → conversión de unidades de temperatura
        #   5. calculate_percentage → cálculo de porcentaje
        # ──────────────────────────────────────────────
        queries = [
            "Calcula 15 + 27 usando las herramientas disponibles.",
            "¿Qué tiempo hace en Oslo, Noruega?",
            "¿Cuál es la fecha y hora actual del servidor?",
            "Convierte 100 grados Fahrenheit a Celsius.",
            "¿Qué porcentaje representa 35 sobre un total de 200?",
        ]

        for query in queries:
            print(f"\n{'─' * 60}")
            print(f"Consulta: {query}")
            print("─" * 60)

            # agent.run() envía la consulta al LLM, que decide qué tool invocar,
            # llama al servidor MCP y devuelve la respuesta final al usuario.
            result = await agent.run(query)
            print(f"Respuesta: {result.text}")


if __name__ == "__main__":
    asyncio.run(main())
