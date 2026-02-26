# MCP-HN

Este es un servidor MCP (Model Context Protocol) basado en el proyecto `hackernews-report`. Expone las funcionalidades del proyecto como herramientas utilizables por clientes compatibles con MCP, como Claude Desktop, Cursor, u otras interfaces de IA y CLI.

## Requisitos

Requiere Python 3.10 o superior.

## Instalación

1. Navega al directorio raíz del proyecto o directamente a la carpeta `mcp-hackernews`.
2. Instala las dependencias, que incluyen el SDK de mcp.

```bash
cd mcp-hackernews
pip install -e .
```

o simplemente instala `mcp` en el entorno virtual activo del proyecto principal:

```bash
pip install mcp
```

## Ejecución (CLI & Otros)

Puedes ejecutar el servidor MCP localmente:

```bash
mcp run server.py
```

O directamente con Python para que escuche por `stdio` (comportamiento estándar de MCP):

```bash
python server.py
```

## Configuración en el Cliente (ej. Claude Desktop)

Agrega la siguiente configuración a tu `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hackernews-report": {
      "command": "python",
      "args": ["C:/Users/qwerty/Documents/full_code/kiro-projects/hackernews-report/mcp-hackernews/server.py"]
    }
  }
}
```

## Herramientas Expuestas

- `fetch_posts(limit=30)`: Obtiene nuevos posts de Hacker News API.
- `list_posts(category=None)`: Lista los posts guardados en la base de datos local. Opcionalmente filtra por `story`, `job`, `ask`, `poll`, `other`.
- `get_categories()`: Obtiene estadísticas de la cantidad de posts por categoría.
- `search_posts(text=None, author=None, tags=None)`: Busca posts locales filtrando por texto, autor o etiquetas.
- `get_available_tags()`: Muestra las etiquetas (tags) disponibles en el sistema de búsqueda.
