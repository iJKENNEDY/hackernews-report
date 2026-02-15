# Hackernews Report

Una aplicación de línea de comandos para obtener, categorizar y visualizar posts de Hacker News.

## Características

- Obtiene posts de la API pública de Hacker News
- Almacena posts localmente en una base de datos SQLite
- Categoriza posts automáticamente (story, job, ask, poll, other)
- Visualiza posts en formato de tabla organizado
- Filtra posts por categoría
- Muestra estadísticas por categoría
- Manejo robusto de errores con reintentos automáticos

## Estructura del Proyecto

```
hackernews-report/
├── src/
│   ├── __init__.py         # Inicialización del paquete
│   ├── __main__.py         # Punto de entrada principal
│   ├── config.py           # Configuración de la aplicación
│   ├── models.py           # Modelos de datos (Post, Category)
│   ├── database.py         # Capa de base de datos SQLite
│   ├── api_client.py       # Cliente de API de Hacker News
│   ├── service.py          # Capa de servicio de aplicación
│   └── cli.py              # Interfaz de línea de comandos
├── tests/
│   ├── test_models.py      # Pruebas de modelos
│   ├── test_database.py    # Pruebas de base de datos
│   ├── test_api_client.py  # Pruebas de cliente API
│   ├── test_service.py     # Pruebas de servicio
│   └── test_cli.py         # Pruebas de CLI
├── .kiro/specs/            # Especificaciones del proyecto
├── requirements.txt        # Dependencias del proyecto
├── pyproject.toml          # Configuración del proyecto
└── pytest.ini              # Configuración de pytest
```

## Instalación

1. Clonar el repositorio:
```bash
git clone <repository-url>
cd hackernews-report
```

2. Crear un entorno virtual:
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

## Uso

La aplicación se ejecuta como un módulo de Python:

```bash
python -m src <command> [options]
```

### Comandos Disponibles

#### Obtener Posts

Obtiene posts nuevos desde la API de Hacker News y los almacena en la base de datos local:

```bash
python -m src fetch --limit 30
```

Opciones:
- `--limit N`: Número máximo de posts a obtener (por defecto: 30)

Ejemplo:
```bash
python -m src fetch --limit 50
```

#### Listar Posts

Muestra posts almacenados en la base de datos:

```bash
python -m src list
```

Opciones:
- `--category CATEGORY`: Filtra posts por categoría (story, job, ask, poll, other)

Ejemplos:
```bash
# Listar todos los posts
python -m src list

# Listar solo historias
python -m src list --category story

# Listar solo trabajos
python -m src list --category job
```

#### Estadísticas por Categoría

Muestra el número de posts por categoría:

```bash
python -m src categories
```

### Ejemplos de Uso Completo

```bash
# 1. Obtener 50 posts de Hacker News
python -m src fetch --limit 50

# 2. Ver todos los posts
python -m src list

# 3. Ver solo historias
python -m src list --category story

# 4. Ver estadísticas
python -m src categories
```

## Configuración

La aplicación puede configurarse mediante variables de entorno:

- `HN_DB_PATH`: Ruta a la base de datos SQLite (por defecto: `~/.hackernews_report/posts.db`)
- `HN_API_BASE_URL`: URL base de la API de Hacker News (por defecto: `https://hacker-news.firebaseio.com/v0/`)
- `HN_DEFAULT_LIMIT`: Límite por defecto de posts a obtener (por defecto: `30`)
- `HN_LOG_LEVEL`: Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL; por defecto: `INFO`)

Ejemplo:
```bash
export HN_DB_PATH="/path/to/custom/database.db"
export HN_LOG_LEVEL="DEBUG"
python -m src fetch --limit 20
```

## Desarrollo

### Ejecutar Pruebas

Ejecutar todas las pruebas:
```bash
pytest
```

Ejecutar pruebas con salida detallada:
```bash
pytest -v
```

Ejecutar pruebas con cobertura:
```bash
pytest --cov=src --cov-report=html
```

Ver reporte de cobertura:
```bash
# El reporte HTML se genera en htmlcov/index.html
open htmlcov/index.html  # En macOS
start htmlcov/index.html  # En Windows
```

### Ejecutar Pruebas Específicas

```bash
# Pruebas de modelos
pytest tests/test_models.py

# Pruebas de base de datos
pytest tests/test_database.py

# Pruebas de API client
pytest tests/test_api_client.py

# Pruebas de servicio
pytest tests/test_service.py

# Pruebas de CLI
pytest tests/test_cli.py
```

## Arquitectura

La aplicación sigue una arquitectura en capas:

1. **CLI Layer** (`cli.py`): Interfaz de usuario y parsing de comandos
2. **Service Layer** (`service.py`): Lógica de negocio y orquestación
3. **Data Access Layer**: 
   - `api_client.py`: Comunicación con API de Hacker News
   - `database.py`: Operaciones de base de datos SQLite
4. **Domain Layer** (`models.py`): Modelos de datos y lógica de dominio

## Dependencias

- **requests**: Cliente HTTP para llamadas a la API de Hacker News
- **hypothesis**: Framework de property-based testing
- **pytest**: Framework de pruebas
- **pytest-cov**: Plugin de cobertura de código para pytest

## Manejo de Errores

La aplicación implementa manejo robusto de errores:

- **Reintentos automáticos**: Hasta 3 intentos con backoff exponencial (1s, 2s, 4s) para errores de red
- **Procesamiento parcial**: Continúa procesando posts válidos incluso si algunos fallan
- **Transacciones**: Mantiene integridad de la base de datos con transacciones atómicas
- **Logging detallado**: Registra errores con información suficiente para diagnóstico

## Licencia

[Especificar licencia aquí]
