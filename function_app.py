"""
Azure Function App — Punto de entrada HTTP para el servidor MCP.

Este fichero conecta el servidor MCP (definido en server/mcp_server.py)
con el runtime de Azure Functions a través de la interfaz ASGI.

Flujo de una petición:
  Cliente HTTP  →  Azure Functions HTTP Trigger  →  AsgiFunctionApp  →  FastMCP ASGI app
"""

import azure.functions as func

# Importar la instancia de FastMCP configurada con todas las tools
from server.mcp_server import mcp

# ──────────────────────────────────────────────
# Obtener la aplicación ASGI del servidor MCP.
# streamable_http_app() devuelve una app Starlette/ASGI compatible
# con el Streamable HTTP transport del protocolo MCP.
# El endpoint quedará en: <base_url>/mcp
# ──────────────────────────────────────────────
asgi_app = mcp.streamable_http_app()

# ──────────────────────────────────────────────
# Envolver la app ASGI dentro de AsgiFunctionApp para que
# Azure Functions la exponga como HTTP Trigger.
#
# http_auth_level=ANONYMOUS → no requiere Function Key para llamar al endpoint.
# Cambiar a func.AuthLevel.FUNCTION para proteger con API key en producción.
# ──────────────────────────────────────────────
app = func.AsgiFunctionApp(
    app=asgi_app,
    http_auth_level=func.AuthLevel.ANONYMOUS
)
