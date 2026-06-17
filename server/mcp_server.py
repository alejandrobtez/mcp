"""
Servidor MCP (Model Context Protocol) desplegado como Azure Function.

Este módulo define el servidor MCP usando FastMCP y expone un conjunto de
herramientas (tools) que un agente de IA puede invocar a través del protocolo
MCP sobre HTTP (Streamable HTTP transport).
"""

from datetime import datetime
from mcp.server.fastmcp import FastMCP

# ──────────────────────────────────────────────
# Instancia principal del servidor MCP
# El nombre "mcp-azure-server" se expone en el handshake del protocolo.
# ──────────────────────────────────────────────
mcp = FastMCP("mcp-azure-server")


# ──────────────────────────────────────────────
# TOOL: get_weather
# Devuelve información meteorológica simulada para una ciudad.
# En producción se conectaría a una API real (p.ej. OpenWeatherMap).
# ──────────────────────────────────────────────
@mcp.tool()
def get_weather(city: str) -> dict:
    """
    Obtiene el tiempo actual de una ciudad (datos de ejemplo).

    Args:
        city: Nombre de la ciudad (p.ej. "Madrid").

    Returns:
        Diccionario con city, temperature y condition.
    """
    # Datos simulados; en producción llamaría a una API externa
    return {
        "city": city,
        "temperature": "22°C",
        "condition": "sunny"
    }


# ──────────────────────────────────────────────
# TOOL: add
# Suma dos enteros y devuelve el resultado.
# Útil para validar que el servidor MCP responde correctamente.
# ──────────────────────────────────────────────
@mcp.tool()
def add(a: int, b: int) -> dict:
    """
    Suma dos números enteros.

    Args:
        a: Primer operando.
        b: Segundo operando.

    Returns:
        Diccionario con la clave 'result' que contiene la suma.
    """
    return {"result": a + b}


# ──────────────────────────────────────────────
# TOOL: get_current_datetime
# Devuelve la fecha y hora actuales del servidor en UTC.
# Permite que el agente conozca el momento exacto de ejecución.
# ──────────────────────────────────────────────
@mcp.tool()
def get_current_datetime() -> dict:
    """
    Devuelve la fecha y hora actuales del servidor (UTC).

    Returns:
        Diccionario con 'date', 'time', 'datetime_iso' y 'weekday'.
    """
    now = datetime.utcnow()

    return {
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "datetime_iso": now.isoformat() + "Z",   # Formato ISO 8601 con Z = UTC
        "weekday": now.strftime("%A")             # Nombre del día en inglés
    }


# ──────────────────────────────────────────────
# TOOL: convert_temperature
# Convierte una temperatura entre Celsius, Fahrenheit y Kelvin.
# Evita que el agente tenga que razonar con fórmulas de conversión.
# ──────────────────────────────────────────────
@mcp.tool()
def convert_temperature(value: float, from_unit: str, to_unit: str) -> dict:
    """
    Convierte una temperatura entre unidades (celsius, fahrenheit, kelvin).

    Args:
        value:     Valor numérico de la temperatura a convertir.
        from_unit: Unidad de origen  ('celsius' | 'fahrenheit' | 'kelvin').
        to_unit:   Unidad de destino ('celsius' | 'fahrenheit' | 'kelvin').

    Returns:
        Diccionario con 'original', 'converted' y las unidades usadas.
    """
    # Normalizar a minúsculas para aceptar "Celsius", "CELSIUS", etc.
    from_unit = from_unit.lower()
    to_unit = to_unit.lower()

    valid_units = {"celsius", "fahrenheit", "kelvin"}
    if from_unit not in valid_units or to_unit not in valid_units:
        return {"error": f"Unidad no válida. Usa: {valid_units}"}

    # Paso 1: convertir el valor origen a Celsius como unidad intermedia
    if from_unit == "celsius":
        celsius = value
    elif from_unit == "fahrenheit":
        celsius = (value - 32) * 5 / 9
    else:  # kelvin
        celsius = value - 273.15

    # Paso 2: convertir de Celsius a la unidad destino
    if to_unit == "celsius":
        result = celsius
    elif to_unit == "fahrenheit":
        result = celsius * 9 / 5 + 32
    else:  # kelvin
        result = celsius + 273.15

    return {
        "original": value,
        "from_unit": from_unit,
        "converted": round(result, 4),
        "to_unit": to_unit
    }


# ──────────────────────────────────────────────
# TOOL: calculate_percentage
# Calcula qué porcentaje representa una parte sobre un total.
# Útil en análisis de datos o cuando el agente necesita estadísticas rápidas.
# ──────────────────────────────────────────────
@mcp.tool()
def calculate_percentage(part: float, total: float) -> dict:
    """
    Calcula el porcentaje que representa 'part' sobre 'total'.

    Args:
        part:  Valor parcial.
        total: Valor total (debe ser distinto de cero).

    Returns:
        Diccionario con 'percentage' redondeado a 2 decimales.
    """
    # Proteger contra división por cero
    if total == 0:
        return {"error": "El total no puede ser cero."}

    percentage = (part / total) * 100

    return {
        "part": part,
        "total": total,
        "percentage": round(percentage, 2)
    }


# ──────────────────────────────────────────────
# Punto de entrada para ejecución local directa
# (sin Azure Functions): python server/mcp_server.py
# ──────────────────────────────────────────────
if __name__ == "__main__":
    # transport="streamable-http" expone el servidor en http://localhost:8000/mcp
    mcp.run(transport="streamable-http")
