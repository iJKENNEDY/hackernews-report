# Documentación de la API Interna y Web UI

Esta sección describe cómo interactuar con los componentes de software del sistema.

## API Client de Hacker News (`src/api_client.py`)

Proporciona métodos para obtener IDs de historias destacadas y detalles de posts individuales utilizando la API de Firebase.

### Métodos:
- `get_top_stories_ids()`: Devuelve una lista de IDs de las mejores historias actuales.
- `get_item_details(item_id)`: Obtiene los detalles (título, URL, autor, etc.) de un post específico por su ID.

## Endpoints de la Aplicación Web (`src/web_app.py`, `src/web/routes.py`)

La interfaz web expone varios endpoints para la navegación y filtrado.

### Principales Rutas:
- `GET /`: Página de inicio que muestra los posts actuales con paginación.
- `GET /post/<post_id>`: Detalle de un post específico y sus etiquetas asociadas.
- `GET /personal-posts`: Búsqueda avanzada y filtrado de posts por puntuación, fecha y etiquetas.
- `POST /tags/add`: Endpoint para añadir etiquetas a un post (requiere `post_id` y `tag_name`).

## Servicio de Búsqueda (`src/search_service.py`)

Encargado de construir consultas SQL dinámicas basadas en los filtros proporcionados por el usuario. Soporta:
- Filtrado por rango de puntuación.
- Filtrado por rango de fechas (desde/hasta).
- Búsqueda por texto en títulos.
- Filtrado por etiquetas específicas.
- Ordenación por fecha o puntuación.

## Utilidades de PDF (`src/utils/pdf_service.py`)

El sistema incluye una utilidad para manipular archivos PDF, permitiendo la consolidación de reportes u otros documentos generados.

### Funcionalidad de Unión (Merge):
Permite combinar 2 o más archivos PDF en un único archivo de salida.

**Uso vía CLI:**
```bash
python -m src.cli merge-pdf archivo1.pdf archivo2.pdf --output resultado.pdf
```

**Uso vía código:**
```python
from src.utils.pdf_service import merge_pdfs
merge_pdfs(["doc1.pdf", "doc2.pdf"], "consolidado.pdf")
```

