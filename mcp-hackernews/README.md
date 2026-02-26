# MCP-HN

Este es un servidor MCP (Model Context Protocol) basado en el proyecto `hackernews-report`. Expone las funcionalidades del proyecto como herramientas utilizables por clientes compatibles con MCP, como Claude Desktop, Cursor, u otras interfaces de IA y CLI.

## Requisitos

Requiere Python 3.10 o superior.

## Instalación

1. Navega al directorio raíz del proyecto o directamente a la carpeta `mcp-hackernews`.
2. Es muy recomendable **activar tu entorno virtual** existente antes de instalar.
3. Instala las dependencias y el proyecto en modo editable:

```bash
cd mcp-hackernews
pip install -e .
```

Esto instalará automáticamente dependencias como `mcp` y también registrará el comando CLI `mcp-hn`.

## Ejecución (CLI & Otros)

Puedes ejecutar el servidor MCP localmente de varias formas:

**1. Usando el comando CLI (recomendado)**:
Gracias a la instalación, puedes iniciarlo desde cualquier lugar con el entorno activo:

```bash
mcp-hn
```

**2. Usando FastMCP CLI**:

```bash
mcp run server.py
```

**3. Directamente con Python**:

```bash
python server.py
```

## Configuración en el Cliente (ej. Claude Desktop)

Para que clientes como Claude Desktop puedan interactuar con este servidor, necesitas configurar la ruta absoluta tanto de Python (el de tu entorno virtual) como del archivo `server.py`.

Agrega la siguiente configuración a tu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hackernews-report": {
      "command": "C:/Users/qwerty/Documents/full_code/kiro-projects/hackernews-report/.venv/Scripts/python.exe",
      "args": [
        "C:/Users/qwerty/Documents/full_code/kiro-projects/hackernews-report/mcp-hackernews/server.py"
      ]
    }
  }
}
```

*(Nota: Asegúrate de ajustar las rutas si tu proyecto está ubicado en otro directorio o utilizas Mac/Linux).*

## Herramientas Expuestas

- `fetch_posts(limit=30)`: Obtiene nuevos posts de Hacker News API.
- `fetch_single_post(post_id)`: Obtiene un post específico por su ID directamente desde la API de Hacker News y lo guarda localmente.
- `list_posts(category=None)`: Lista los posts guardados en la base de datos local. Opcionalmente filtra por `story`, `job`, `ask`, `poll`, `other`.
- `get_post_details(post_id)`: Obtiene todos los detalles de un post específico (incluyendo texto y etiquetas) desde la base de datos local.
- `get_categories()`: Obtiene estadísticas de la cantidad de posts por categoría.
- `search_posts(text=None, author=None, tags=None)`: Busca posts locales filtrando por texto, autor o etiquetas.
- `get_available_tags()`: Muestra las etiquetas (tags) disponibles en el sistema de búsqueda.
- `get_ai_news(limit=20)`: Filtra los posts guardados recientes para mostrar solo noticias sobre Inteligencia Artificial (OpenAI, Anthropic, Gemini, Agents, LLMs, etc).
- `open_in_browser(url)`: Abre cualquier URL directamente en el navegador del sistema operativo donde se ejecuta el servidor.
- `open_hn_comments(post_id)`: Abre la página oficial de comentarios de Hacker News para un post específico en tu navegador.
