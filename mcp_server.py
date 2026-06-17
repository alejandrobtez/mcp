"""
Servidor MCP de ejemplo, expuesto via Streamable HTTP.
Implementa varias tools de demostracion: calculadora, consulta de
repositorios publicos de GitHub, y utilidades de fecha/hora.

Ejecutar con:
    python3 mcp_server.py
"""

from datetime import datetime, timezone
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("demo-public-server", host="127.0.0.1", port=8000)


@mcp.tool()
def sumar(a: float, b: float) -> float:
    """Suma dos numeros."""
    return a + b


@mcp.tool()
def restar(a: float, b: float) -> float:
    """Resta b a a."""
    return a - b


@mcp.tool()
def multiplicar(a: float, b: float) -> float:
    """Multiplica dos numeros."""
    return a * b


@mcp.tool()
def dividir(a: float, b: float) -> float:
    """Divide a entre b. Lanza error si b es cero."""
    if b == 0:
        raise ValueError("No se puede dividir entre cero")
    return a / b


@mcp.tool()
def hora_actual() -> str:
    """Devuelve la fecha y hora actual en formato UTC ISO 8601."""
    return datetime.now(timezone.utc).isoformat()


@mcp.tool()
def leer_readme_github(owner: str, repo: str, rama: str = "main") -> dict:
    """
    Descarga el contenido del README.md de un repositorio publico de GitHub.

    Args:
        owner: Usuario u organizacion propietaria del repo (ej. 'alejandrobtez').
        repo: Nombre del repositorio.
        rama: Rama del repositorio (por defecto 'main').
    """
    url = f"https://raw.githubusercontent.com/{owner}/{repo}/{rama}/README.md"
    resp = httpx.get(url, timeout=10)
    if resp.status_code == 404:
        return {"error": "README.md no encontrado en esa rama/repo"}
    resp.raise_for_status()
    contenido = resp.text
    return {
        "repo": f"{owner}/{repo}",
        "rama": rama,
        "longitud_caracteres": len(contenido),
        "primeras_lineas": "\n".join(contenido.splitlines()[:8]),
    }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
