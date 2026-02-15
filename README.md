# Hackernews Report

Una aplicación para obtener, categorizar y visualizar posts de Hacker News, disponible tanto en línea de comandos como en interfaz web.

## Características

- 📥 Obtiene posts de la API pública de Hacker News
- 💾 Almacena posts localmente en una base de datos SQLite
- 🏷️ Categoriza posts automáticamente (story, job, ask, poll, other)
- 📊 Visualiza posts en formato de tabla organizado (CLI) o interfaz web moderna
- 🔍 Filtra posts por categoría
- 📈 Muestra estadísticas por categoría
- 🔄 Manejo robusto de errores con reintentos automáticos
- 🌐 **Interfaz web** con diseño responsive y API REST (rama `feature/web-ui`)
- ✅ Suite completa de pruebas (unitarias, property-based, integración)

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
│   ├── cli.py              # Interfaz de línea de comandos
│   └── web_app.py          # Aplicación web Flask (rama feature/web-ui)
├── templates/              # Templates HTML para web UI
│   ├── base.html
│   ├── index.html
│   ├── post_detail.html
│   └── 404.html
├── static/                 # Archivos estáticos (CSS, JS)
│   └── style.css
├── tests/
│   ├── test_models.py      # Pruebas de modelos
│   ├── test_database.py    # Pruebas de base de datos
│   ├── test_api_client.py  # Pruebas de cliente API
│   ├── test_service.py     # Pruebas de servicio
│   ├── test_cli.py         # Pruebas de CLI
│   └── test_integration.py # Pruebas de integración end-to-end
├── .kiro/specs/            # Especificaciones del proyecto
├── requirements.txt        # Dependencias del proyecto
├── pyproject.toml          # Configuración del proyecto
├── pytest.ini              # Configuración de pytest
├── README.md               # Este archivo
└── WEB_UI_README.md        # Documentación de la interfaz web
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

La aplicación ofrece dos interfaces: **línea de comandos (CLI)** y **interfaz web**.

### Interfaz de Línea de Comandos (CLI)

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

### Interfaz Web (rama `feature/web-ui`)

Para usar la interfaz web, cambia a la rama `feature/web-ui`:

```bash
git checkout feature/web-ui
pip install -r requirements.txt
```

Luego inicia el servidor web:

```bash
python -m src.web_app
```

La interfaz web estará disponible en: **http://localhost:5000**

#### Características de la Web UI:

- 🎨 Interfaz moderna y limpia inspirada en Hacker News
- 📱 Diseño responsive para móvil y desktop
- 🏷️ Filtros por categoría en sidebar
- 📊 Estadísticas en tiempo real
- 🔗 Enlaces directos a posts originales y discusiones de HN
- 🌐 API REST endpoints (`/api/posts`, `/api/stats`)

Para más detalles, consulta [WEB_UI_README.md](WEB_UI_README.md) en la rama `feature/web-ui`.

#### API Endpoints:

```bash
# Obtener todos los posts
curl http://localhost:5000/api/posts

# Filtrar por categoría
curl http://localhost:5000/api/posts?category=story

# Limitar resultados
curl http://localhost:5000/api/posts?limit=10

# Obtener estadísticas
curl http://localhost:5000/api/stats
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

La aplicación incluye una suite completa de pruebas (69 tests):
- **Pruebas unitarias**: Verifican componentes individuales
- **Property-based tests**: Validan propiedades universales con Hypothesis
- **Pruebas de integración**: Verifican flujos end-to-end

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

# Pruebas de integración
pytest tests/test_integration.py
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

### Core
- **requests**: Cliente HTTP para llamadas a la API de Hacker News
- **hypothesis**: Framework de property-based testing
- **pytest**: Framework de pruebas
- **pytest-cov**: Plugin de cobertura de código para pytest

### Web UI (rama `feature/web-ui`)
- **flask**: Framework web para la interfaz de usuario

## Manejo de Errores

La aplicación implementa manejo robusto de errores:

- **Reintentos automáticos**: Hasta 3 intentos con backoff exponencial (1s, 2s, 4s) para errores de red
- **Procesamiento parcial**: Continúa procesando posts válidos incluso si algunos fallan
- **Transacciones**: Mantiene integridad de la base de datos con transacciones atómicas
- **Logging detallado**: Registra errores con información suficiente para diagnóstico

## Ramas del Proyecto

- **`main`**: Aplicación CLI estable con suite completa de pruebas
- **`feature/web-ui`**: Interfaz web con Flask (en desarrollo)

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Licencia

[Especificar licencia aquí]

## Enlaces

- **Repositorio**: https://github.com/iJKENNEDY/hackernews-report
- **Rama Web UI**: https://github.com/iJKENNEDY/hackernews-report/tree/feature/web-ui
- **Hacker News API**: https://github.com/HackerNews/API
