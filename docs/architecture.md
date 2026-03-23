# Arquitectura del Sistema

Hacker News Report es una aplicación diseñada para la obtención, almacenamiento y visualización de artículos destacados de Hacker News.

## Componentes Principales

1. **API Client (`src/api_client.py`)**: Se encarga de la comunicación con la API oficial de Hacker News (Firebase).
2. **Servicio de Base de Datos (`src/database.py`)**: Utiliza SQLite para persistir los posts, sus puntuaciones y etiquetas.
3. **Lógica de Negocio (`src/service.py`, `src/search_service.py`)**: Gestiona la lógica de filtrado, búsqueda y actualización de datos.
4. **Interfaz Web (`src/web/`)**: Aplicación Flask que sirve la interfaz de usuario utilizando plantillas Jinja2.
5. **CLI (`src/cli.py`)**: Herramienta de línea de comandos para operaciones administrativas y consultas rápidas.

## Flujo de Datos

1. El `api_client` obtiene los IDs de los posts destacados.
2. Los detalles de los posts se descargan y se insertan en la base de datos SQLite.
3. La interfaz web consulta la base de datos para mostrar los posts con filtros de puntuación, fecha y etiquetas.
4. Las etiquetas se pueden asignar manualmente o mediante servicios de etiquetado automático.
