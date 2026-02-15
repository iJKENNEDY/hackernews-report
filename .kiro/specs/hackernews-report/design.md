# Documento de Diseño: Hackernews Report

## Visión General

La aplicación Hackernews Report es un sistema de línea de comandos que permite obtener, almacenar, categorizar y visualizar posts de Hacker News. El sistema se conecta a la API pública de Hacker News, almacena los datos en una base de datos SQLite local, y proporciona capacidades de consulta y visualización organizadas por categorías.

### Objetivos del Diseño

- Arquitectura modular con separación clara de responsabilidades
- Manejo robusto de errores y reintentos
- Almacenamiento eficiente con SQLite
- Interfaz de línea de comandos simple e intuitiva

## Arquitectura

El sistema sigue una arquitectura en capas con los siguientes componentes principales:

```
┌─────────────────────────────────────────┐
│         CLI Interface Layer             │
│  (Comandos de usuario y visualización)  │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Application Service Layer          │
│  (Lógica de negocio y orquestación)     │
└──────┬───────────────────────┬──────────┘
       │                       │
┌──────▼──────────┐   ┌────────▼─────────┐
│  HN API Client  │   │  Database Layer  │
│   (HTTP calls)  │   │  (SQLite ops)    │
└─────────────────┘   └──────────────────┘
```

### Flujo de Datos

1. **Obtención**: CLI → Service → API Client → Hacker News API
2. **Almacenamiento**: API Client → Service → Database Layer → SQLite
3. **Consulta**: CLI → Service → Database Layer → SQLite
4. **Visualización**: Database Layer → Service → CLI → Usuario

## Componentes e Interfaces

### 1. CLI Interface Layer

**Responsabilidad**: Manejar la interacción con el usuario a través de línea de comandos.

**Comandos principales**:
```
fetch [--limit N]     # Obtener N posts nuevos (default: 30)
list [--category C]   # Listar posts, opcionalmente filtrados por categoría
categories            # Mostrar estadísticas por categoría
```

**Interfaz**:
```python
class CLI:
    def run(args: List[str]) -> int
    def handle_fetch(limit: int) -> None
    def handle_list(category: Optional[str]) -> None
    def handle_categories() -> None
    def display_posts(posts: List[Post]) -> None
```

### 2. Application Service Layer

**Responsabilidad**: Coordinar operaciones entre la API y la base de datos, implementar lógica de negocio.

**Interfaz**:
```python
class HackerNewsService:
    def __init__(api_client: HNApiClient, db: Database)
    
    def fetch_and_store_posts(limit: int) -> FetchResult
    def get_posts_by_category(category: Optional[str]) -> List[Post]
    def get_category_statistics() -> Dict[str, int]
    def categorize_post(post: Post) -> Category
```

**Tipos**:
```python
@dataclass
class FetchResult:
    new_posts: int
    updated_posts: int
    errors: List[str]

enum Category:
    STORY = "story"
    JOB = "job"
    ASK = "ask"
    POLL = "poll"
    OTHER = "other"
```

### 3. HN API Client

**Responsabilidad**: Comunicación con la API de Hacker News, manejo de reintentos y rate limiting.

**Interfaz**:
```python
class HNApiClient:
    def __init__(base_url: str, max_retries: int = 3)
    
    def get_top_stories(limit: int) -> List[int]
    def get_item(item_id: int) -> Optional[Post]
    def get_items_batch(item_ids: List[int]) -> List[Post]
```

**Configuración**:
- Base URL: `https://hacker-news.firebaseio.com/v0/`
- Timeout: 10 segundos por request
- Reintentos: 3 intentos con backoff exponencial (1s, 2s, 4s)
- Rate limiting: Máximo 10 requests por segundo

### 4. Database Layer

**Responsabilidad**: Operaciones CRUD sobre SQLite, gestión de esquema y transacciones.

**Interfaz**:
```python
class Database:
    def __init__(db_path: str)
    
    def initialize_schema() -> None
    def insert_post(post: Post) -> bool
    def update_post(post: Post) -> bool
    def upsert_post(post: Post) -> bool
    def get_post_by_id(post_id: int) -> Optional[Post]
    def get_posts_by_category(category: Optional[str], 
                              order_by: str = "created_desc") -> List[Post]
    def get_category_counts() -> Dict[str, int]
    def post_exists(post_id: int) -> bool
```

## Modelos de Datos

### Esquema SQLite

```sql
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    author TEXT NOT NULL,
    score INTEGER DEFAULT 0,
    url TEXT,
    created_at INTEGER NOT NULL,
    type TEXT NOT NULL,
    category TEXT NOT NULL,
    fetched_at INTEGER NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_posts_type ON posts(type);
CREATE INDEX IF NOT EXISTS idx_posts_category ON posts(category);
CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at DESC);
```

### Modelo de Dominio

```python
@dataclass
class Post:
    id: int
    title: str
    author: str
    score: int
    url: Optional[str]
    created_at: int  # Unix timestamp
    type: str
    category: Category
    fetched_at: int  # Unix timestamp
    
    def is_valid() -> bool
    def to_dict() -> Dict[str, Any]
    @staticmethod
    def from_api_response(data: Dict[str, Any]) -> Post
    @staticmethod
    def from_db_row(row: Tuple) -> Post
```

### Mapeo de Categorías

```python
TYPE_TO_CATEGORY = {
    "story": Category.STORY,
    "job": Category.JOB,
    "ask": Category.ASK,
    "poll": Category.POLL,
}

def categorize_post(post_type: str) -> Category:
    return TYPE_TO_CATEGORY.get(post_type, Category.OTHER)
```


## Manejo de Errores

### Estrategia de Reintentos

Para operaciones de red (llamadas a la API de Hacker News):

```python
class RetryStrategy:
    max_attempts: int = 3
    base_delay: float = 1.0  # segundos
    max_delay: float = 10.0
    
    def calculate_delay(attempt: int) -> float:
        # Backoff exponencial: 1s, 2s, 4s
        return min(base_delay * (2 ** attempt), max_delay)
```

### Categorías de Errores

1. **Errores de Red**:
   - Timeout de conexión
   - Errores HTTP (4xx, 5xx)
   - Acción: Reintentar con backoff exponencial

2. **Errores de Datos**:
   - JSON inválido
   - Campos faltantes en respuesta API
   - Acción: Registrar error, omitir item, continuar

3. **Errores de Base de Datos**:
   - Fallo de conexión
   - Violación de constraints
   - Acción: Registrar error, rollback de transacción, notificar usuario

4. **Errores de Validación**:
   - Datos incompletos
   - Tipos incorrectos
   - Acción: Rechazar datos, registrar advertencia

### Logging

```python
import logging

# Niveles de log:
# ERROR: Fallos críticos que impiden operación
# WARNING: Problemas recuperables (ej: post inválido omitido)
# INFO: Operaciones exitosas (ej: N posts obtenidos)
# DEBUG: Detalles de debugging (ej: requests HTTP individuales)
```

### Manejo de Transacciones

Todas las operaciones de escritura a la base de datos deben usar transacciones:

```python
def fetch_and_store_posts(limit: int) -> FetchResult:
    with db.transaction():
        # Obtener posts
        # Validar posts
        # Insertar/actualizar posts
        # Si hay error, rollback automático
```


## Propiedades de Corrección

*Una propiedad es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas de un sistema - esencialmente, una declaración formal sobre lo que el sistema debe hacer. Las propiedades sirven como puente entre especificaciones legibles por humanos y garantías de corrección verificables por máquinas.*

### Propiedades de Obtención de Datos

**Propiedad 1: Validación de campos completos**
*Para cualquier* post obtenido de la API, el sistema debe validar que contiene todos los campos requeridos (id, título, autor, puntuación, URL, fecha de creación, tipo) antes de procesarlo.
**Valida: Requisitos 1.2, 1.5**

**Propiedad 2: Manejo de rate limiting**
*Para cualquier* secuencia de requests que exceda el límite de tasa, el sistema debe implementar espera apropiada sin fallar.
**Valida: Requisitos 1.4**

### Propiedades de Almacenamiento

**Propiedad 3: Round-trip de almacenamiento**
*Para cualquier* post válido, almacenarlo en la base de datos y luego recuperarlo debe producir un objeto equivalente con todos los campos preservados.
**Valida: Requisitos 2.2, 2.5**

**Propiedad 4: Idempotencia de upsert**
*Para cualquier* post, insertarlo múltiples veces con el mismo id debe resultar en exactamente una entrada en la base de datos con los datos más recientes.
**Valida: Requisitos 2.3**

**Propiedad 5: Integridad transaccional**
*Para cualquier* operación de actualización que se interrumpa, la base de datos debe mantener un estado consistente sin datos parciales o corruptos.
**Valida: Requisitos 6.4**

### Propiedades de Categorización

**Propiedad 6: Mapeo correcto de categorías**
*Para cualquier* post con tipo conocido (story, job, ask, poll), el sistema debe asignarle la categoría correspondiente correcta.
**Valida: Requisitos 3.1, 3.2**

**Propiedad 7: Categoría por defecto para tipos desconocidos**
*Para cualquier* post con tipo no reconocido, el sistema debe asignarlo a la categoría "otros".
**Valida: Requisitos 3.4**

**Propiedad 8: Filtrado por categoría**
*Para cualquier* consulta filtrada por categoría, todos los posts devueltos deben pertenecer exclusivamente a esa categoría.
**Valida: Requisitos 3.3, 4.3**

### Propiedades de Visualización

**Propiedad 9: Contenido completo de visualización**
*Para cualquier* post mostrado en lista, su representación debe incluir título, autor, puntuación, fecha y categoría de forma visible.
**Valida: Requisitos 4.1, 4.5**

**Propiedad 10: Ordenamiento por fecha**
*Para cualquier* lista de posts visualizada sin filtro de ordenamiento, los posts deben estar ordenados por fecha de creación en orden descendente (más recientes primero).
**Valida: Requisitos 4.2**

**Propiedad 11: URLs clickeables**
*Para cualquier* post con URL no nula, la visualización debe incluir la URL en formato utilizable.
**Valida: Requisitos 4.4**

### Propiedades de Sincronización

**Propiedad 12: Evitar duplicados en actualización**
*Para cualquier* operación de actualización, el sistema debe obtener solo posts que no existan previamente en la base de datos.
**Valida: Requisitos 5.2**

**Propiedad 13: Conteo preciso de posts nuevos**
*Para cualquier* operación de actualización completada, el número de posts nuevos reportado debe coincidir exactamente con el número de posts realmente insertados en la base de datos.
**Valida: Requisitos 5.3**

**Propiedad 14: Respeto del límite especificado**
*Para cualquier* límite N especificado por el usuario, el sistema debe intentar obtener exactamente N posts (o menos si no hay suficientes disponibles).
**Valida: Requisitos 5.4**

### Propiedades de Manejo de Errores

**Propiedad 15: Reintentos con backoff exponencial**
*Para cualquier* fallo de conexión a la API, el sistema debe realizar exactamente 3 reintentos con delays exponenciales (1s, 2s, 4s) antes de reportar el error.
**Valida: Requisitos 6.1**

**Propiedad 16: Procesamiento parcial con datos inválidos**
*Para cualquier* lote de posts que contenga algunos posts inválidos, el sistema debe procesar exitosamente todos los posts válidos y omitir solo los inválidos.
**Valida: Requisitos 6.3**


## Estrategia de Pruebas

### Enfoque Dual de Testing

El sistema utilizará un enfoque complementario que combina:

1. **Pruebas unitarias**: Para verificar ejemplos específicos, casos edge y condiciones de error
2. **Pruebas basadas en propiedades**: Para verificar propiedades universales a través de múltiples entradas generadas

Ambos tipos de pruebas son necesarios para cobertura completa:
- Las pruebas unitarias capturan bugs concretos y casos específicos
- Las pruebas de propiedades verifican corrección general a través de randomización

### Configuración de Property-Based Testing

**Biblioteca**: Utilizaremos `hypothesis` para Python, que es la biblioteca estándar para property-based testing en el ecosistema Python.

**Configuración de pruebas**:
- Mínimo 100 iteraciones por prueba de propiedad (debido a randomización)
- Cada prueba debe referenciar su propiedad del documento de diseño
- Formato de tag: `# Feature: hackernews-report, Property N: [texto de propiedad]`

**Ejemplo de estructura**:
```python
from hypothesis import given, strategies as st

# Feature: hackernews-report, Property 3: Round-trip de almacenamiento
@given(post=valid_post_strategy())
def test_storage_roundtrip(post):
    db.upsert_post(post)
    retrieved = db.get_post_by_id(post.id)
    assert retrieved == post
```

### Estrategias de Generación de Datos

Para property-based testing, necesitaremos estrategias para generar:

1. **Posts válidos**: Con todos los campos requeridos
2. **Posts inválidos**: Con campos faltantes o tipos incorrectos
3. **IDs de posts**: Enteros positivos
4. **Tipos de posts**: Valores del enum Category
5. **Timestamps**: Unix timestamps válidos
6. **URLs**: Strings válidos de URL o None

### Cobertura de Pruebas

**Pruebas Unitarias** (ejemplos y casos edge):
- Inicialización de base de datos vacía
- Manejo de API no disponible
- Creación de índices en esquema
- Logging de errores de base de datos
- Casos específicos de categorización

**Pruebas de Propiedades** (verificación universal):
- Todas las 16 propiedades de corrección listadas arriba
- Cada propiedad implementada como una prueba separada
- Mínimo 100 iteraciones por propiedad

### Pruebas de Integración

Además de unit y property tests:

1. **Flujo completo fetch-store-retrieve**: Simular API → almacenar → consultar
2. **Manejo de transacciones**: Interrumpir operaciones y verificar consistencia
3. **Rate limiting**: Verificar comportamiento con múltiples requests rápidos
4. **CLI end-to-end**: Ejecutar comandos CLI y verificar salida

### Mocking y Fixtures

**Mocks necesarios**:
- `HNApiClient`: Para simular respuestas de API sin llamadas reales
- Respuestas HTTP: Para simular errores de red, timeouts, rate limits
- Sistema de archivos: Para pruebas de creación de base de datos

**Fixtures**:
- Base de datos en memoria (`:memory:`) para pruebas rápidas
- Conjunto de posts de ejemplo con diferentes categorías
- Respuestas de API simuladas (válidas e inválidas)

### Criterios de Éxito

Las pruebas deben:
- Alcanzar >90% de cobertura de código
- Todas las 16 propiedades deben pasar con 100 iteraciones
- Tiempo de ejecución total <30 segundos
- Cero fallos en casos edge conocidos
