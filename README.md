# Cliente MCP conectado al servidor de GitHub

## ¿Qué hace este proyecto?

Este script conecta un agente de IA al servidor MCP público de GitHub. MCP
(Model Context Protocol) es un estándar que permite que un agente "pida
prestadas" herramientas a un servidor externo, en este caso las
herramientas de GitHub: buscar repositorios, leer archivos, abrir issues,
consultar pull requests, etc.

GitHub expone su propio servidor MCP en `https://api.githubcopilot.com/mcp/`.
Cualquier cliente que hable el protocolo MCP puede conectarse ahí y usar
esas herramientas, siempre que se autentique correctamente.

El agente que construye y ejecuta las llamadas está hecho con el
**Microsoft Agent Framework**, y el modelo que decide qué herramienta usar
en cada momento es un deployment de **Azure AI Foundry**.

## ¿Por qué necesito un token?

El servidor MCP de GitHub no es público en el sentido de "abierto para
cualquiera sin identificarse". Para usarlo necesitas demostrar quién eres,
igual que cuando usas `git push` o la API de GitHub desde la terminal. Eso
se hace con un **Personal Access Token (PAT)**, una clave que generas tú
mismo desde tu cuenta y que actúa como tu credencial.

El script nunca guarda ese token en ningún archivo ni lo deja fijo en el
código: lo recibe como argumento al ejecutar el script, y lo usa solo en el
momento de la llamada al servidor MCP.

## Cómo conseguir tu token de GitHub

1. Entra en [github.com/settings/tokens](https://github.com/settings/tokens).
2. Pulsa en **"Generate new token"** (puedes usar la versión "classic" o
   "fine-grained", con classic es más rápido para empezar).
3. Ponle un nombre que reconozcas, por ejemplo `mcp-test`.
4. En los permisos (*scopes*), si solo vas a consultar información pública
   (buscar repos, leer archivos públicos), te vale con marcar `public_repo`
   o incluso no marcar nada de scopes de escritura. Si más adelante quieres
   que el agente pueda crear issues o modificar algo, tendrás que darle
   permisos de escritura sobre esos recursos.
5. Genera el token y cópialo. **GitHub solo te lo muestra una vez**, así
   que guárdalo en un sitio seguro (un gestor de contraseñas, por ejemplo)
   antes de cerrar la página.

No subas nunca este token a un repositorio ni lo compartas en capturas de
pantalla, es una credencial de tu cuenta.

## Qué hace el código, paso a paso

```python
tools=MCPStreamableHTTPTool(
    name="GitHub MCP",
    description="Servidor MCP oficial de GitHub: repos, issues, pull requests, busqueda de codigo.",
    url=GITHUB_MCP_URL,
    header_provider=lambda kwargs: {"Authorization": f"Bearer {kwargs['github_pat']}"},
)
```

Esta parte es la conexión al servidor MCP. `MCPStreamableHTTPTool` es la
pieza del Agent Framework que sabe hablar el protocolo MCP: se conecta a
la URL de GitHub, le pregunta qué herramientas tiene disponibles, y las
deja listas para que el agente las use.

El detalle importante es `header_provider`. GitHub exige una cabecera
`Authorization: Bearer <tu_token>` en cada petición. En lugar de escribir
el token directamente en el código (mala práctica, quedaría fijo y
expuesto), usamos una función que genera esa cabecera al vuelo, justo
cuando se necesita.

```python
result = await agent.run(
    query,
    function_invocation_kwargs={"github_pat": github_pat},
)
```

Aquí es donde el token entra en juego de verdad. `function_invocation_kwargs`
es el mecanismo por el que el token llega hasta el `header_provider` de
arriba, pero solo durante esta ejecución concreta. No se guarda en ningún
sitio del agente ni del cliente MCP; vive únicamente en este `run()`.

```python
client=FoundryChatClient(credential=AzureCliCredential())
```

Esto es el modelo que piensa. `FoundryChatClient` se conecta a tu proyecto
de Azure AI Foundry, y `AzureCliCredential()` usa la sesión que ya tienes
abierta en tu máquina con `az login`, sin que tengas que pasar ninguna
clave a mano.

## Cómo ponerlo en marcha

Primero, crea un entorno virtual e instala las dependencias:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Autentícate con Azure (solo hace falta hacerlo una vez por sesión):

```bash
az login
```

Define las variables de tu proyecto de Azure AI Foundry. Puedes exportarlas
en la terminal, o crear un archivo `.env` en la misma carpeta con este
contenido:

```
FOUNDRY_PROJECT_ENDPOINT=https://tu-proyecto.services.ai.azure.com
FOUNDRY_MODEL=gpt-4o-mini
```

Y por último, ejecuta el script pasando tu token de GitHub como argumento:

```bash
python mcp_client.py <tu_personal_access_token>
```

Si todo está bien configurado, verás cómo el agente le pregunta al
servidor MCP de GitHub qué herramientas tiene disponibles, y te las
muestra en su respuesta.

## Si algo falla

- **Error de autenticación con GitHub (401 / 403):** revisa que el token
  no haya caducado y que tenga al menos permisos de lectura.
- **Error con Azure / Foundry:** comprueba que `az login` se hizo con la
  cuenta correcta y que `FOUNDRY_PROJECT_ENDPOINT` apunta a tu proyecto
  real (lo encuentras en el portal de Azure AI Foundry, en la vista
  general del proyecto).
- **`ModuleNotFoundError`:** asegúrate de tener el entorno virtual activado
  (`source venv/bin/activate`) antes de ejecutar el script.
