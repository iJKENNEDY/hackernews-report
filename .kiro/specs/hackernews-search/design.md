# Documento de Diseño: Buscador de Posts de HackerNews

## Visión General

El Sistema de Búsqueda de HackerNews es un módulo que se integra con la aplicación existente Hackernews Report para proporcionar capacidades avanzadas de búsqueda sobre posts almacenados localmente. El sistema permite búsquedas multi-criterio (texto, autor, tags, puntuación, fecha), ordenamiento flexible, paginación y resaltado de términos, todo optimizado con índices de base de datos.

### Objetivos del Diseño

- Integración transparente con la arquitectura existente de Hackernews Report
- Búsquedas eficientes mediante índices apropiados en SQLite
- API flexible que soporte combinación de múltiples criterios
- Interfaz CLI consistente con comandos existentes
- Código modular y testeable con propiedades de corrección verificables

## Arquitectura

El sistema de búsqueda se integra como un nuevo módulo en la arquitectura existente:

```
┌─────────────────────────────────────────┐
│         CLI Interface Layer             │
│  (Comandos existentes + nuevo "search") │
└──────────────┬──────────────────────────┘
               │
┌──────────────▼──────────────────────────┐
│      Application Service Layer          │
│  (HackerNewsService + SearchService)    │
└──────┬───────────────────────┬──────────┘
       │                       │
┌──────▼──────────┐   ┌────────▼─────────┐
│  HN API Client  │   │  Database Layer  │
│   (existente)   │   │  + SearchEngine  │
└─────────────────┘   └──────────────────┘
```

### Flujo de Búsqueda

1. **Entrada**: Usuario ejecuta comando `search` con criterios → CLI
2. **Validación**: CLI valida parámetros → SearchService
3. **Construcción**: SearchService construye SearchQuery → SearchEngine
4. **Ejecución**: SearchEngine ejecuta consulta SQL optimizada → SQLite
5. **Procesamiento**: SearchEngine aplica resaltado y paginación → Resultados
6. **Visualización**: CLI muestra resultados formateados → Usuario

## Componentes e Interfaces

### 1. SearchQuery (Modelo de Consulta)

**Responsabilidad**: Encapsular todos los criterios de búsqueda en un objeto inmutable.

**Interfaz**:
```python
@dataclass(frozen=True)
class SearchQuery:
    # Criterios de búsqueda
    text: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Opciones de presentación
    order_by: str = "relevance"  # relevance, date_desc, date_asc, score_desc, score_asc
    page: int = 1
    page_size: int = 20
    
    def validate() -> List[str]  # Retorna lista de errores de validación
    def has_text_search() -> bool
    def has_any_criteria() -> bool
    def to_sql_conditions() -> Tuple[str, List[Any]]
```

**Reglas de Validación**:
- Al menos un criterio de búsqueda debe estar presente
- Si min_score y max_score están presentes: min_score <= max_score
- Si start_date y end_date están presentes: start_date <= end_date
- page >= 1
- page_size >= 1 y <= 100
- order_by debe ser uno de los valores válidos
- Puntuaciones deben ser >= 0

### 2. SearchResult (Modelo de Resultado)

**Responsabilidad**: Encapsular resultados de búsqueda con metadatos de paginación.

**Interfaz**:
```python
@dataclass
class SearchResult:
    posts: List[Post]
    total_results: int
    page: int
    page_size: int
    total_pages: int
    query: SearchQuery
    
    def has_more_pages() -> bool
    def has_previous_page() -> bool
    def get_page_info() -> str  # "Página 2 de 5 (100 resultados totales)"
```

### 3. SearchEngine (Motor de Búsqueda)

**Responsabilidad**: Ejecutar consultas de búsqueda contra la base de datos SQLite.

**Interfaz**:
```python
class SearchEngine:
    def __init__(database: Database)
    
    def search(query: SearchQuery) -> SearchResult
    def count_results(query: SearchQuery) -> int
    def create_search_indices() -> None
    
    # Métodos privados
    def _build_sql_query(query: SearchQuery) -> Tuple[str, List[Any]]
    def _apply_text_filter(conditions: List[str], params: List[Any], text: str) -> None
    def _apply_author_filter(conditions: List[str], params: List[Any], author: str) -> None
    def _apply_tags_filter(conditions: List[str], params: List[Any], tags: List[str]) -> None
    def _apply_score_filter(conditions: List[str], params: List[Any], 
                           min_score: Optional[int], max_score: Optional[int]) -> None
    def _apply_date_filter(conditions: List[str], params: List[Any],
                          start_date: Optional[date], end_date: Optional[date]) -> None
    def _get_order_clause(order_by: str, has_text_search: bool) -> str
    def _calculate_relevance_score(text: str, title: str) -> float
```

**Construcción de Consultas SQL**:

El motor construye consultas SQL dinámicamente basándose en los criterios presentes:

```sql
-- Ejemplo: búsqueda por texto + tags + rango de puntuación
SELECT id, title, author, score, url, created_at, type, category, fetched_at, tags
FROM posts
WHERE 
    LOWER(title) LIKE ? AND           -- búsqueda de texto
    (tags LIKE ? OR tags LIKE ?) AND  -- búsqueda de tags (OR)
    score >= ? AND score <= ?         -- rango de puntuación
ORDER BY score DESC                    -- ordenamiento
LIMIT ? OFFSET ?                       -- paginación
```

**Cálculo de Relevancia**:

Para ordenamiento por relevancia (cuando hay búsqueda de texto):
- Coincidencia exacta de palabra completa: +10 puntos
- Coincidencia al inicio del título: +5 puntos
- Coincidencia parcial: +1 punto por término
- Normalizado por longitud del título

### 4. SearchService (Servicio de Búsqueda)

**Responsabilidad**: Coordinar operaciones de búsqueda, validación y formateo de resultados.

**Interfaz**:
```python
class SearchService:
    def __init__(search_engine: SearchEngine, tag_system: TagSystem)
    
    def search_posts(query: SearchQuery) -> SearchResult
    def validate_query(query: SearchQuery) -> Tuple[bool, List[str]]
    def get_available_tags() -> List[str]
    def suggest_tags(partial: str) -> List[str]
    def highlight_terms(text: str, search_terms: List[str]) -> str
```

**Resaltado de Términos**:

```python
def highlight_terms(text: str, search_terms: List[str]) -> str:
    """
    Resalta términos de búsqueda en el texto usando marcadores.
    
    Para CLI: usa **término** para resaltado
    Para Web: podría usar <mark>término</mark>
    
    Ejemplo:
        text = "Python 3.11 released"
        terms = ["python"]
        resultado = "**Python** 3.11 released"
    """
```

### 5. CLI Extension (Extensión de CLI)

**Responsabilidad**: Agregar comando `search` a la CLI existente.

**Nuevo Comando**:
```bash
# Búsqueda básica por texto
hackernews-report search --text "python"

# Búsqueda por autor
hackernews-report search --author "pg"

# Búsqueda por tags
hackernews-report search --tags "AI,Python"

# Búsqueda por rango de puntuación
hackernews-report search --min-score 100 --max-score 500

# Búsqueda por rango de fechas
hackernews-report search --start-date 2024-01-01 --end-date 2024-12-31

# Combinación de criterios
hackernews-report search --text "machine learning" --tags "AI" --min-score 50

# Ordenamiento y paginación
hackernews-report search --text "rust" --order-by score_desc --page 2 --page-size 10

# Listar tags disponibles
hackernews-report search --list-tags
```

**Interfaz CLI**:
```python
class CLI:
    # ... métodos existentes ...
    
    def handle_search(args: SearchArgs) -> None
    def display_search_results(result: SearchResult, highlight: bool) -> None
    def display_available_tags() -> None
```

## Modelos de Datos

### Extensión del Esquema SQLite

**Nuevos Índices** (agregados a la tabla `posts` existente):

```sql
-- Índice para búsqueda de texto en títulos
CREATE INDEX IF NOT EXISTS idx_posts_title_lower 
ON posts(LOWER(title));

-- Índice para búsqueda por autor
CREATE INDEX IF NOT EXISTS idx_posts_author_lower 
ON posts(LOWER(author));

-- Índice para búsqueda por tags
CREATE INDEX IF NOT EXISTS idx_posts_tags 
ON posts(tags);

-- Índice para filtrado por puntuación
CREATE INDEX IF NOT EXISTS idx_posts_score 
ON posts(score);

-- Índice compuesto para ordenamiento común
CREATE INDEX IF NOT EXISTS idx_posts_score_created 
ON posts(score DESC, created_at DESC);
```

**Nota**: No se modifica la estructura de la tabla `posts` existente, solo se agregan índices.

### Modelo SearchQuery Detallado

```python
@dataclass(frozen=True)
class SearchQuery:
    """
    Consulta de búsqueda inmutable con validación integrada.
    
    Ejemplos:
        # Búsqueda simple por texto
        query = SearchQuery(text="python")
        
        # Búsqueda multi-criterio
        query = SearchQuery(
            text="machine learning",
            tags=["AI", "Python"],
            min_score=100,
            start_date=date(2024, 1, 1),
            order_by="score_desc"
        )
    """
    text: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    min_score: Optional[int] = None
    max_score: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    order_by: str = "relevance"
    page: int = 1
    page_size: int = 20
    
    def __post_init__(self):
        """Validación automática al crear la instancia."""
        errors = self.validate()
        if errors:
            raise ValueError(f"Invalid search query: {', '.join(errors)}")
    
    def validate(self) -> List[str]:
        """Valida la consulta y retorna lista de errores."""
        errors = []
        
        # Al menos un criterio debe estar presente
        if not self.has_any_criteria():
            errors.append("At least one search criterion must be provided")
        
        # Validar rangos de puntuación
        if self.min_score is not None and self.min_score < 0:
            errors.append("min_score must be non-negative")
        if self.max_score is not None and self.max_score < 0:
            errors.append("max_score must be non-negative")
        if (self.min_score is not None and self.max_score is not None 
            and self.min_score > self.max_score):
            errors.append("min_score must be <= max_score")
        
        # Validar rangos de fechas
        if (self.start_date is not None and self.end_date is not None 
            and self.start_date > self.end_date):
            errors.append("start_date must be <= end_date")
        
        # Validar paginación
        if self.page < 1:
            errors.append("page must be >= 1")
        if self.page_size < 1 or self.page_size > 100:
            errors.append("page_size must be between 1 and 100")
        
        # Validar orden
        valid_orders = ["relevance", "date_desc", "date_asc", "score_desc", "score_asc"]
        if self.order_by not in valid_orders:
            errors.append(f"order_by must be one of: {', '.join(valid_orders)}")
        
        # Validar texto no vacío
        if self.text is not None and not self.text.strip():
            errors.append("text search term cannot be empty or whitespace only")
        
        return errors
    
    def has_text_search(self) -> bool:
        """Retorna True si la consulta incluye búsqueda de texto."""
        return self.text is not None and len(self.text.strip()) > 0
    
    def has_any_criteria(self) -> bool:
        """Retorna True si al menos un criterio de búsqueda está presente."""
        return any([
            self.text,
            self.author,
            self.tags,
            self.min_score is not None,
            self.max_score is not None,
            self.start_date is not None,
            self.end_date is not None,
        ])
```

## Manejo de Errores

### Categorías de Errores

1. **Errores de Validación de Consulta**:
   - Parámetros inválidos (rangos incorrectos, valores negativos)
   - Formatos de fecha incorrectos
   - Texto de búsqueda vacío
   - Acción: Rechazar consulta, mostrar mensaje descriptivo

2. **Errores de Base de Datos**:
   - Fallo de conexión
   - Error en ejecución de consulta SQL
   - Acción: Registrar error, notificar usuario, retornar resultado vacío

3. **Errores de Tags**:
   - Tag no válido proporcionado
   - Acción: Sugerir tags válidos similares

4. **Errores de Paginación**:
   - Página solicitada fuera de rango
   - Acción: Retornar lista vacía con información de páginas disponibles

### Estrategia de Logging

```python
import logging

logger = logging.getLogger(__name__)

# Niveles de log:
# ERROR: Fallos de base de datos, errores inesperados
# WARNING: Consultas sin resultados, parámetros subóptimos
# INFO: Búsquedas exitosas con conteo de resultados
# DEBUG: Consultas SQL generadas, tiempos de ejecución
```

### Manejo de Casos Edge

```python
# Búsqueda sin resultados
if not results:
    logger.info(f"Search returned no results for query: {query}")
    return SearchResult(
        posts=[],
        total_results=0,
        page=query.page,
        page_size=query.page_size,
        total_pages=0,
        query=query
    )

# Página fuera de rango
if query.page > total_pages:
    logger.warning(f"Requested page {query.page} exceeds total pages {total_pages}")
    # Retornar resultado vacío pero con información correcta de paginación
```


## Propiedades de Corrección

*Una propiedad es una característica o comportamiento que debe mantenerse verdadero en todas las ejecuciones válidas de un sistema - esencialmente, una declaración formal sobre lo que el sistema debe hacer. Las propiedades sirven como puente entre especificaciones legibles por humanos y garantías de corrección verificables por máquinas.*

### Propiedades de Búsqueda por Texto

**Propiedad 1: Coincidencia de texto en títulos**
*Para cualquier* término de búsqueda no vacío y conjunto de posts, todos los resultados retornados deben contener el término de búsqueda en su título.
**Valida: Requisitos 1.1**

**Propiedad 2: Insensibilidad a mayúsculas/minúsculas**
*Para cualquier* término de búsqueda y campo de búsqueda (título o autor), buscar con diferentes combinaciones de mayúsculas y minúsculas debe producir resultados equivalentes.
**Valida: Requisitos 1.2, 2.2**

**Propiedad 3: Búsqueda parcial (substring)**
*Para cualquier* post con título conocido, buscar por cualquier substring del título debe incluir ese post en los resultados.
**Valida: Requisitos 1.3, 2.3**

**Propiedad 4: Búsqueda multi-palabra con operación AND**
*Para cualquier* consulta con múltiples palabras separadas por espacios, todos los resultados deben contener todas las palabras en su título, independientemente del orden.
**Valida: Requisitos 1.4**

**Propiedad 5: Rechazo de búsquedas vacías**
*Para cualquier* string compuesto únicamente de espacios en blanco o vacío, el sistema debe rechazar la consulta con un error de validación.
**Valida: Requisitos 1.5**

### Propiedades de Búsqueda por Autor

**Propiedad 6: Coincidencia exacta de autor**
*Para cualquier* nombre de autor especificado, todos los resultados retornados deben tener exactamente ese autor (ignorando mayúsculas/minúsculas).
**Valida: Requisitos 2.1**

### Propiedades de Búsqueda por Tags

**Propiedad 7: Búsqueda por tags con operación OR**
*Para cualquier* conjunto de tags válidos proporcionados, todos los resultados deben contener al menos uno de los tags especificados.
**Valida: Requisitos 3.1, 3.3**

**Propiedad 8: Validación de tags contra sistema existente**
*Para cualquier* tag proporcionado, el sistema debe aceptarlo solo si existe en el TagSystem, rechazando tags inválidos.
**Valida: Requisitos 3.2**

### Propiedades de Filtrado por Puntuación

**Propiedad 9: Filtrado por puntuación mínima**
*Para cualquier* valor de puntuación mínima especificado, todos los resultados deben tener puntuación mayor o igual a ese valor.
**Valida: Requisitos 4.1**

**Propiedad 10: Filtrado por puntuación máxima**
*Para cualquier* valor de puntuación máxima especificado, todos los resultados deben tener puntuación menor o igual a ese valor.
**Valida: Requisitos 4.2**

**Propiedad 11: Validación de rangos de puntuación**
*Para cualquier* par de valores (min_score, max_score) donde min_score > max_score, el sistema debe rechazar la consulta con un error de validación.
**Valida: Requisitos 4.4**

**Propiedad 12: Validación de puntuaciones no negativas**
*Para cualquier* valor de puntuación negativo proporcionado, el sistema debe rechazar la consulta con un error de validación.
**Valida: Requisitos 4.5, 12.3**

### Propiedades de Filtrado por Fecha

**Propiedad 13: Filtrado por fecha de inicio**
*Para cualquier* fecha de inicio especificada, todos los resultados deben tener fecha de creación mayor o igual a esa fecha.
**Valida: Requisitos 5.1**

**Propiedad 14: Filtrado por fecha de fin**
*Para cualquier* fecha de fin especificada, todos los resultados deben tener fecha de creación menor o igual a esa fecha.
**Valida: Requisitos 5.2**

**Propiedad 15: Validación de rangos de fechas**
*Para cualquier* par de fechas (start_date, end_date) donde start_date > end_date, el sistema debe rechazar la consulta con un error de validación.
**Valida: Requisitos 5.4**

**Propiedad 16: Parsing de fechas ISO 8601**
*Para cualquier* fecha válida en formato ISO 8601 (YYYY-MM-DD), el sistema debe parsearla correctamente y usarla en el filtrado.
**Valida: Requisitos 5.5**

### Propiedades de Combinación de Criterios

**Propiedad 17: Aplicación simultánea de múltiples criterios (AND)**
*Para cualquier* consulta con múltiples criterios de búsqueda, todos los resultados deben satisfacer todos los criterios simultáneamente.
**Valida: Requisitos 6.1**

### Propiedades de Ordenamiento

**Propiedad 18: Ordenamiento correcto de resultados**
*Para cualquier* criterio de ordenamiento especificado (fecha ascendente/descendente, puntuación ascendente/descendente), los resultados deben estar ordenados correctamente según ese criterio.
**Valida: Requisitos 7.2, 7.3**

**Propiedad 19: Ordenamiento por relevancia**
*Para cualquier* búsqueda de texto, cuando se ordene por relevancia, los posts con mayor puntuación de relevancia deben aparecer primero.
**Valida: Requisitos 7.1**

### Propiedades de Paginación

**Propiedad 20: División correcta en páginas**
*Para cualquier* tamaño de página especificado y conjunto de resultados, el número total de páginas debe ser ceil(total_results / page_size).
**Valida: Requisitos 8.1**

**Propiedad 21: Contenido correcto de página**
*Para cualquier* número de página solicitado, los resultados retornados deben ser exactamente los elementos en el rango [page_size * (page - 1), page_size * page) del conjunto completo de resultados ordenados.
**Valida: Requisitos 8.2**

**Propiedad 22: Metadatos de paginación correctos**
*Para cualquier* resultado de búsqueda, los metadatos (total_results, total_pages, page) deben ser matemáticamente consistentes entre sí.
**Valida: Requisitos 8.3**

### Propiedades de Resaltado

**Propiedad 23: Resaltado de todos los términos**
*Para cualquier* búsqueda de texto, todos los términos de búsqueda que aparezcan en los títulos de los resultados deben estar marcados con el formato de resaltado.
**Valida: Requisitos 9.1, 9.3**

### Propiedades de Validación

**Propiedad 24: Rechazo de consultas sin criterios**
*Para cualquier* consulta que no contenga ningún criterio de búsqueda, el sistema debe rechazarla con un error de validación.
**Valida: Requisitos 6.3**

**Propiedad 25: Validación completa antes de ejecución**
*Para cualquier* consulta con parámetros inválidos, el sistema debe detectar y rechazar la consulta antes de ejecutar cualquier operación en la base de datos.
**Valida: Requisitos 12.1**

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
- Formato de tag: `# Feature: hackernews-search, Property N: [texto de propiedad]`

**Ejemplo de estructura**:
```python
from hypothesis import given, strategies as st

# Feature: hackernews-search, Property 1: Coincidencia de texto en títulos
@given(search_term=st.text(min_size=1).filter(lambda s: s.strip()))
def test_text_search_matches_titles(search_term):
    # Crear posts de prueba con el término
    posts = create_test_posts_with_term(search_term)
    
    # Ejecutar búsqueda
    query = SearchQuery(text=search_term)
    results = search_engine.search(query)
    
    # Verificar que todos los resultados contengan el término
    for post in results.posts:
        assert search_term.lower() in post.title.lower()
```

### Estrategias de Generación de Datos

Para property-based testing, necesitaremos estrategias para generar:

1. **Términos de búsqueda**: Strings no vacíos, con y sin espacios
2. **Nombres de autor**: Strings válidos de nombres de usuario
3. **Tags**: Selección de tags válidos del TagSystem
4. **Puntuaciones**: Enteros no negativos en rangos razonables (0-1000)
5. **Fechas**: Fechas válidas en formato ISO 8601
6. **Consultas complejas**: Combinaciones de múltiples criterios
7. **Posts de prueba**: Posts con campos aleatorios pero válidos

### Cobertura de Pruebas

**Pruebas Unitarias** (ejemplos y casos edge):
- Comando CLI "search" existe y acepta argumentos
- Formato de salida consistente con comando "list"
- Listar tags disponibles retorna lista correcta
- Sugerencias de tags para tags inválidos
- Búsqueda sin resultados retorna lista vacía con mensaje
- Página fuera de rango retorna lista vacía
- Ordenamiento por defecto según tipo de búsqueda
- Tamaño de página por defecto es 20
- Formato de resaltado usa marcadores correctos
- Resaltado no se aplica sin búsqueda de texto
- Formato de fecha inválido muestra mensaje de ayuda

**Pruebas de Propiedades** (verificación universal):
- Todas las 25 propiedades de corrección listadas arriba
- Cada propiedad implementada como una prueba separada
- Mínimo 100 iteraciones por propiedad

### Pruebas de Integración

Además de unit y property tests:

1. **Flujo completo de búsqueda**: CLI → Service → Engine → Database → Resultados
2. **Búsquedas complejas multi-criterio**: Verificar que todos los filtros se apliquen correctamente
3. **Paginación con ordenamiento**: Verificar consistencia entre páginas
4. **Integración con TagSystem**: Verificar que tags se validen correctamente
5. **Creación de índices**: Verificar que índices se creen al inicializar

### Mocking y Fixtures

**Mocks necesarios**:
- Base de datos en memoria (`:memory:`) para pruebas rápidas
- TagSystem con conjunto conocido de tags

**Fixtures**:
- Conjunto de posts de prueba con variedad de:
  - Títulos con diferentes palabras clave
  - Autores diversos
  - Tags variados
  - Rangos de puntuación (0-1000)
  - Rangos de fechas (últimos 2 años)
- Consultas de búsqueda válidas e inválidas
- Resultados esperados para consultas conocidas

### Criterios de Éxito

Las pruebas deben:
- Alcanzar >90% de cobertura de código
- Todas las 25 propiedades deben pasar con 100 iteraciones
- Tiempo de ejecución total <60 segundos
- Cero fallos en casos edge conocidos
- Todas las pruebas de integración pasan

### Balance entre Unit Tests y Property Tests

**Unit tests** deben enfocarse en:
- Ejemplos específicos de uso común
- Casos edge conocidos (páginas fuera de rango, búsquedas vacías)
- Integración entre componentes
- Comportamientos por defecto
- Formato de salida y mensajes de error

**Property tests** deben enfocarse en:
- Validación de entrada con valores aleatorios
- Corrección de filtros con datos generados
- Consistencia de ordenamiento
- Corrección matemática de paginación
- Propiedades de búsqueda con términos aleatorios

Evitar escribir demasiados unit tests para casos que ya están cubiertos por property tests. Por ejemplo, no necesitamos unit tests para cada valor posible de puntuación si tenemos un property test que verifica el filtrado con valores aleatorios.
