# Plan de Implementación: Hackernews Report

## Visión General

Este plan desglosa la implementación de la aplicación Hackernews Report en tareas incrementales. Cada tarea construye sobre las anteriores, comenzando con la estructura básica y avanzando hacia funcionalidad completa con pruebas.

## Tareas

- [x] 1. Configurar estructura del proyecto y dependencias
  - Crear estructura de directorios (src/, tests/, data/)
  - Configurar archivo requirements.txt con dependencias: requests, hypothesis, pytest
  - Crear archivo pyproject.toml para el proyecto
  - Configurar pytest.ini para configuración de pruebas
  - _Requisitos: Todos (infraestructura base)_

- [x] 2. Implementar modelos de datos y esquema de base de datos
  - [x] 2.1 Crear clase Post con dataclass
    - Implementar campos: id, title, author, score, url, created_at, type, category, fetched_at
    - Implementar método is_valid() para validación
    - Implementar métodos to_dict(), from_api_response(), from_db_row()
    - _Requisitos: 1.2, 2.2_
  
  - [x] 2.2 Crear enum Category
    - Definir categorías: STORY, JOB, ASK, POLL, OTHER
    - Implementar función categorize_post(post_type: str) -> Category
    - _Requisitos: 3.1, 3.4_
  
  - [x]* 2.3 Escribir prueba de propiedad para mapeo de categorías
    - **Propiedad 6: Mapeo correcto de categorías**
    - **Valida: Requisitos 3.1, 3.2**
  
  - [x]* 2.4 Escribir prueba de propiedad para categoría por defecto
    - **Propiedad 7: Categoría por defecto para tipos desconocidos**
    - **Valida: Requisitos 3.4**

- [x] 3. Implementar capa de base de datos (Database Layer)
  - [x] 3.1 Crear clase Database con conexión SQLite
    - Implementar __init__(db_path: str)
    - Implementar initialize_schema() con CREATE TABLE e índices
    - Implementar context manager para transacciones
    - _Requisitos: 2.1, 2.4_
  
  - [x] 3.2 Implementar operaciones CRUD básicas
    - Implementar insert_post(post: Post) -> bool
    - Implementar update_post(post: Post) -> bool
    - Implementar upsert_post(post: Post) -> bool
    - Implementar get_post_by_id(post_id: int) -> Optional[Post]
    - Implementar post_exists(post_id: int) -> bool
    - _Requisitos: 2.2, 2.3, 2.5_
  
  - [x] 3.3 Implementar operaciones de consulta
    - Implementar get_posts_by_category(category, order_by) -> List[Post]
    - Implementar get_category_counts() -> Dict[str, int]
    - _Requisitos: 3.3, 4.2_
  
  - [x]* 3.4 Escribir prueba de propiedad para round-trip de almacenamiento
    - **Propiedad 3: Round-trip de almacenamiento**
    - **Valida: Requisitos 2.2, 2.5**
  
  - [x]* 3.5 Escribir prueba de propiedad para idempotencia de upsert
    - **Propiedad 4: Idempotencia de upsert**
    - **Valida: Requisitos 2.3**
  
  - [x]* 3.6 Escribir prueba de propiedad para filtrado por categoría
    - **Propiedad 8: Filtrado por categoría**
    - **Valida: Requisitos 3.3, 4.3**
  
  - [x]* 3.7 Escribir pruebas unitarias para casos edge de base de datos
    - Probar creación de base de datos cuando no existe
    - Probar manejo de errores de conexión
    - Probar validación de datos antes de inserción
    - _Requisitos: 2.1, 2.5_

- [x] 4. Checkpoint - Verificar capa de datos
  - Asegurar que todas las pruebas pasen, preguntar al usuario si surgen dudas.

- [x] 5. Implementar cliente de API de Hacker News
  - [x] 5.1 Crear clase HNApiClient con configuración
    - Implementar __init__(base_url, max_retries, timeout)
    - Configurar constantes: BASE_URL, TIMEOUT=10s, MAX_RETRIES=3
    - _Requisitos: 1.1_
  
  - [x] 5.2 Implementar estrategia de reintentos con backoff exponencial
    - Crear clase RetryStrategy con calculate_delay(attempt)
    - Implementar decorador @retry para métodos de API
    - _Requisitos: 6.1_
  
  - [x] 5.3 Implementar métodos de obtención de datos
    - Implementar get_top_stories(limit: int) -> List[int]
    - Implementar get_item(item_id: int) -> Optional[Post]
    - Implementar get_items_batch(item_ids: List[int]) -> List[Post]
    - Agregar validación de datos recibidos
    - _Requisitos: 1.1, 1.2, 1.5_
  
  - [x] 5.4 Implementar manejo de errores de red
    - Manejar timeouts, errores HTTP, JSON inválido
    - Implementar logging apropiado para cada tipo de error
    - _Requisitos: 1.3, 6.2, 6.3_
  
  - [x]* 5.5 Escribir prueba de propiedad para validación de campos
    - **Propiedad 1: Validación de campos completos**
    - **Valida: Requisitos 1.2, 1.5**
  
  - [x]* 5.6 Escribir prueba de propiedad para reintentos
    - **Propiedad 15: Reintentos con backoff exponencial**
    - **Valida: Requisitos 6.1**
  
  - [x]* 5.7 Escribir prueba de propiedad para procesamiento parcial
    - **Propiedad 16: Procesamiento parcial con datos inválidos**
    - **Valida: Requisitos 6.3**
  
  - [x]* 5.8 Escribir pruebas unitarias para manejo de errores
    - Probar API no disponible con logging
    - Probar rate limiting
    - Probar datos incompletos
    - _Requisitos: 1.3, 1.4, 6.2_

- [x] 6. Implementar capa de servicio de aplicación
  - [x] 6.1 Crear clase HackerNewsService
    - Implementar __init__(api_client, database)
    - Crear dataclass FetchResult para resultados de operaciones
    - _Requisitos: Todos (orquestación)_
  
  - [x] 6.2 Implementar lógica de fetch y almacenamiento
    - Implementar fetch_and_store_posts(limit: int) -> FetchResult
    - Usar transacciones para atomicidad
    - Implementar validación y categorización de posts
    - Manejar errores y continuar con posts válidos
    - _Requisitos: 1.1, 2.2, 2.3, 3.1, 3.2, 5.2, 6.4_
  
  - [x] 6.3 Implementar métodos de consulta
    - Implementar get_posts_by_category(category) -> List[Post]
    - Implementar get_category_statistics() -> Dict[str, int]
    - _Requisitos: 3.3, 4.3_
  
  - [x]* 6.4 Escribir prueba de propiedad para integridad transaccional
    - **Propiedad 5: Integridad transaccional**
    - **Valida: Requisitos 6.4**
  
  - [x]* 6.5 Escribir prueba de propiedad para evitar duplicados
    - **Propiedad 12: Evitar duplicados en actualización**
    - **Valida: Requisitos 5.2**
  
  - [x]* 6.6 Escribir prueba de propiedad para conteo preciso
    - **Propiedad 13: Conteo preciso de posts nuevos**
    - **Valida: Requisitos 5.3**
  
  - [x]* 6.7 Escribir prueba de propiedad para límite especificado
    - **Propiedad 14: Respeto del límite especificado**
    - **Valida: Requisitos 5.4**

- [x] 7. Checkpoint - Verificar lógica de negocio
  - Asegurar que todas las pruebas pasen, preguntar al usuario si surgen dudas.

- [x] 8. Implementar interfaz CLI
  - [x] 8.1 Crear clase CLI con parsing de argumentos
    - Usar argparse para definir comandos: fetch, list, categories
    - Implementar run(args: List[str]) -> int como punto de entrada
    - _Requisitos: 4.1, 5.4_
  
  - [x] 8.2 Implementar comando fetch
    - Implementar handle_fetch(limit: int)
    - Mostrar progreso y resultados al usuario
    - Manejar errores y mostrar mensajes apropiados
    - _Requisitos: 1.1, 5.1, 5.3_
  
  - [x] 8.3 Implementar comando list
    - Implementar handle_list(category: Optional[str])
    - Implementar display_posts(posts: List[Post]) con formato de tabla
    - Incluir título, autor, puntuación, fecha, categoría, URL
    - Ordenar por fecha descendente por defecto
    - _Requisitos: 4.1, 4.2, 4.3, 4.4, 4.5_
  
  - [x] 8.4 Implementar comando categories
    - Implementar handle_categories()
    - Mostrar estadísticas de posts por categoría
    - _Requisitos: 3.3_
  
  - [x]* 8.5 Escribir prueba de propiedad para contenido de visualización
    - **Propiedad 9: Contenido completo de visualización**
    - **Valida: Requisitos 4.1, 4.5**
  
  - [x]* 8.6 Escribir prueba de propiedad para ordenamiento
    - **Propiedad 10: Ordenamiento por fecha**
    - **Valida: Requisitos 4.2**
  
  - [x]* 8.7 Escribir prueba de propiedad para URLs clickeables
    - **Propiedad 11: URLs clickeables**
    - **Valida: Requisitos 4.4**
  
  - [x]* 8.8 Escribir pruebas unitarias para CLI
    - Probar parsing de argumentos
    - Probar manejo de comandos inválidos
    - Probar salida formateada
    - _Requisitos: 4.1, 4.2, 4.3_

- [x] 9. Implementar punto de entrada principal y configuración
  - [x] 9.1 Crear archivo __main__.py
    - Inicializar componentes (Database, HNApiClient, HackerNewsService, CLI)
    - Configurar logging (nivel INFO por defecto)
    - Manejar excepciones no capturadas
    - _Requisitos: Todos (integración)_
  
  - [x] 9.2 Crear archivo de configuración
    - Definir constantes: DB_PATH, API_BASE_URL, DEFAULT_LIMIT
    - Permitir override mediante variables de entorno
    - _Requisitos: 2.1, 5.4_
  
  - [x] 9.3 Agregar documentación README
    - Documentar instalación y uso
    - Incluir ejemplos de comandos
    - Documentar estructura del proyecto
    - _Requisitos: Todos (documentación)_

- [x] 10. Pruebas de integración end-to-end
  - [x]* 10.1 Escribir prueba de integración para flujo completo
    - Simular fetch → store → retrieve → display
    - Usar mocks para API
    - Usar base de datos en memoria
    - _Requisitos: 1.1, 2.2, 3.3, 4.1_
  
  - [x]* 10.2 Escribir prueba de integración para manejo de errores
    - Simular fallos de API y verificar recuperación
    - Simular interrupciones y verificar integridad de BD
    - _Requisitos: 6.1, 6.3, 6.4_

- [x] 11. Checkpoint final - Verificación completa
  - Ejecutar todas las pruebas (unit, property, integration)
  - Verificar cobertura de código >90%
  - Probar comandos CLI manualmente
  - Asegurar que todas las pruebas pasen, preguntar al usuario si surgen dudas.

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Las pruebas de propiedades validan corrección universal
- Las pruebas unitarias validan ejemplos específicos y casos edge
- Se recomienda ejecutar pruebas después de cada tarea para detectar problemas temprano
- Todas las tareas principales han sido completadas exitosamente
- El proyecto incluye funcionalidad adicional (tags, web UI) que no está en los requisitos originales
