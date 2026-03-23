# Documentación de la Base de Datos

La aplicación utiliza **SQLite** para la persistencia de datos, almacenada por defecto en el directorio `data/`.

## Esquema Principal

### Tabla `posts`
- `id`: (Integer, PK) ID original de Hacker News.
- `title`: (Text) Título del post.
- `url`: (Text) Enlace original.
- `score`: (Integer) Puntuación de Hacker News.
- `time`: (Integer) Timestamp de creación.
- `by`: (Text) Autor original.
- `type`: (Text) Tipo de post (story, job, etc.).

### Tabla `tags`
- `id`: (Integer, PK)
- `post_id`: (Integer, FK a `posts.id`)
- `tag_name`: (Text) Nombre de la etiqueta.

## Modelos (`src/models.py`)

Se definen clases dataclass para facilitar la manipulación de datos en Python:
- `HNPost`: Estructura principal de un post.
- `Tag`: Representación de etiquetas asignadas.

## Migraciones

Cualquier cambio en el esquema se gestiona a través de scripts específicos de migración localizados en `src/migrate_add_tags.py` u otros similares. Se recomienda realizar copias de seguridad de `data/` antes de aplicar cambios estructurales.
