# Plan de Implementación: Buscador de Posts de HackerNews

## Visión General

Este plan implementa un sistema de búsqueda completo para posts de Hacker News almacenados localmente. El sistema permitirá búsquedas multi-criterio (texto, autor, tags, puntuación, fecha), ordenamiento flexible, paginación y resaltado de términos. La implementación se realizará de forma incremental, validando funcionalidad core tempranamente mediante pruebas.

## Tareas

- [x] 1. Crear modelos de datos para búsqueda
  - Implementar clase `SearchQuery` con todos los campos de criterios de búsqueda
  - Implementar clase `SearchResult` con posts y metadatos de paginación
  - Agregar métodos de validación en `SearchQuery`
  - _Requisitos: 1.1, 2.1, 3.1, 4.1, 4.2, 5.1, 5.2, 6.1, 7.1, 8.1_

- [ ]* 1.1 Escribir pruebas de propiedad para validación de SearchQuery
  - **Propiedad 5: Rechazo de búsquedas vacías**
  - **Propiedad 11: Validación de rangos de puntuación**
  - **Propiedad 12: Validación de puntuaciones no negativas**
  - **Propiedad 15: Validación de rangos de fechas**
  - **Propiedad 24: Rechazo de consultas sin criterios**
  - **Valida: Requisitos 1.5, 4.4, 4.5, 5.4, 6.3**

- [ ]* 1.2 Escribir unit tests para SearchQuery
  - Test de creación de consulta válida
  - Test de valores por defecto (page=1, page_size=20, order_by="relevance")
  - Test de formato de fecha ISO 8601
  - _Requisitos: 5.5, 8.5_

- [x] 2. Implementar SearchEngine con búsqueda básica por texto
  - Crear clase `SearchEngine` con constructor que recibe `Database`
  - Implementar método `search()` que acepta `SearchQuery`
  - Implementar construcción de consulta SQL para búsqueda por texto
  - Implementar búsqueda insensible a mayúsculas/minúsculas
  - Implementar búsqueda parcial (substring matching)
  - _Requisitos: 1.1, 1.2, 1.3_

- [ ]* 2.1 Escribir pruebas de propiedad para búsqueda por texto
  - **Propiedad 1: Coincidencia de texto en títulos**
  - **Propiedad 2: Insensibilidad a mayúsculas/minúsculas**
  - **Propiedad 3: Búsqueda parcial (substring)**
  - **Propiedad 4: Búsqueda multi-palabra con operación AND**
  - **Valida: Requisitos 1.1, 1.2, 1.3, 1.4**

- [x] 3. Agregar búsqueda por autor al SearchEngine
  - Implementar filtro por autor en construcción de SQL
  - Soportar búsqueda insensible a mayúsculas/minúsculas
  - Soportar búsqueda parcial en nombres de autor
  - _Requisitos: 2.1, 2.2, 2.3_

- [ ]* 3.1 Escribir pruebas de propiedad para búsqueda por autor
  - **Propiedad 6: Coincidencia exacta de autor**
  - **Valida: Requisitos 2.1, 2.2, 2.3**

- [ ]* 3.2 Escribir unit test para autor no existente
  - Test que verifica lista vacía cuando autor no existe
  - _Requisitos: 2.4_

- [x] 4. Agregar búsqueda por tags al SearchEngine
  - Implementar filtro por tags con operación OR
  - Integrar con TagSystem para validación de tags
  - Manejar múltiples tags en la consulta
  - _Requisitos: 3.1, 3.2, 3.3_

- [ ]* 4.1 Escribir pruebas de propiedad para búsqueda por tags
  - **Propiedad 7: Búsqueda por tags con operación OR**
  - **Propiedad 8: Validación de tags contra sistema existente**
  - **Valida: Requisitos 3.1, 3.2, 3.3**

- [ ]* 4.2 Escribir unit tests para funcionalidad de tags
  - Test de listar tags disponibles
  - Test de sugerencias para tags inválidos
  - _Requisitos: 3.4, 3.5_

- [x] 5. Agregar filtros por puntuación y fecha
  - Implementar filtro por puntuación mínima y máxima
  - Implementar filtro por fecha de inicio y fin
  - Convertir fechas ISO 8601 a timestamps Unix
  - _Requisitos: 4.1, 4.2, 5.1, 5.2, 5.5_

- [ ]* 5.1 Escribir pruebas de propiedad para filtros numéricos
  - **Propiedad 9: Filtrado por puntuación mínima**
  - **Propiedad 10: Filtrado por puntuación máxima**
  - **Propiedad 13: Filtrado por fecha de inicio**
  - **Propiedad 14: Filtrado por fecha de fin**
  - **Propiedad 16: Parsing de fechas ISO 8601**
  - **Valida: Requisitos 4.1, 4.2, 5.1, 5.2, 5.5**

- [ ]* 6. Checkpoint - Verificar búsquedas básicas
  - Asegurar que todas las pruebas pasen, preguntar al usuario si surgen dudas.

- [x] 7. Implementar combinación de múltiples criterios
  - Modificar construcción de SQL para aplicar múltiples filtros simultáneamente (AND)
  - Asegurar que todos los criterios se apliquen correctamente
  - _Requisitos: 6.1, 6.2_

- [ ]* 7.1 Escribir prueba de propiedad para criterios múltiples
  - **Propiedad 17: Aplicación simultánea de múltiples criterios (AND)**
  - **Valida: Requisitos 6.1**

- [ ]* 7.2 Escribir unit tests para casos edge de combinación
  - Test de búsqueda sin resultados con mensaje informativo
  - _Requisitos: 6.4_

- [x] 8. Implementar ordenamiento de resultados
  - Implementar ordenamiento por fecha (ascendente y descendente)
  - Implementar ordenamiento por puntuación (ascendente y descendente)
  - Implementar cálculo de relevancia para búsquedas de texto
  - Implementar ordenamiento por relevancia
  - Aplicar ordenamiento por defecto según tipo de búsqueda
  - _Requisitos: 7.1, 7.2, 7.3, 7.4, 7.5_

- [ ]* 8.1 Escribir pruebas de propiedad para ordenamiento
  - **Propiedad 18: Ordenamiento correcto de resultados**
  - **Propiedad 19: Ordenamiento por relevancia**
  - **Valida: Requisitos 7.1, 7.2, 7.3**

- [ ]* 8.2 Escribir unit tests para ordenamiento por defecto
  - Test de orden por relevancia cuando hay búsqueda de texto
  - Test de orden por fecha descendente sin búsqueda de texto
  - _Requisitos: 7.4, 7.5_

- [x] 9. Implementar paginación de resultados
  - Implementar conteo total de resultados antes de paginar
  - Implementar cálculo de offset y limit para SQL
  - Implementar cálculo de total de páginas
  - Construir objeto `SearchResult` con metadatos completos
  - _Requisitos: 8.1, 8.2, 8.3, 8.5_

- [ ]* 9.1 Escribir pruebas de propiedad para paginación
  - **Propiedad 20: División correcta en páginas**
  - **Propiedad 21: Contenido correcto de página**
  - **Propiedad 22: Metadatos de paginación correctos**
  - **Valida: Requisitos 8.1, 8.2, 8.3**

- [ ]* 9.2 Escribir unit tests para casos edge de paginación
  - Test de página fuera de rango retorna lista vacía
  - Test de tamaño de página por defecto (20)
  - _Requisitos: 8.4, 8.5_

- [ ]* 10. Checkpoint - Verificar búsqueda completa
  - Asegurar que todas las pruebas pasen, preguntar al usuario si surgen dudas.

- [x] 11. Implementar SearchService
  - Crear clase `SearchService` que coordina SearchEngine y TagSystem
  - Implementar método `search_posts()` que valida y ejecuta búsquedas
  - Implementar método `validate_query()` que retorna errores de validación
  - Implementar método `get_available_tags()` que lista tags del sistema
  - Implementar método `suggest_tags()` que sugiere tags similares
  - _Requisitos: 3.4, 3.5, 12.1, 12.5_

- [ ]* 11.1 Escribir prueba de propiedad para validación
  - **Propiedad 25: Validación completa antes de ejecución**
  - **Valida: Requisitos 12.1, 12.5**

- [ ]* 11.2 Escribir unit tests para SearchService
  - Test de listar tags disponibles
  - Test de sugerencias de tags
  - _Requisitos: 3.4, 3.5_

- [x] 12. Implementar resaltado de términos
  - Implementar método `highlight_terms()` en SearchService
  - Usar marcadores **término** para resaltado en CLI
  - Resaltar todas las ocurrencias de términos de búsqueda
  - Aplicar resaltado solo cuando hay búsqueda de texto
  - _Requisitos: 9.1, 9.2, 9.3, 9.4_

- [ ]* 12.1 Escribir prueba de propiedad para resaltado
  - **Propiedad 23: Resaltado de todos los términos**
  - **Valida: Requisitos 9.1, 9.3**

- [ ]* 12.2 Escribir unit tests para resaltado
  - Test de formato de marcadores (**término**)
  - Test de no aplicar resaltado sin búsqueda de texto
  - _Requisitos: 9.2, 9.4_

- [x] 13. Crear índices de base de datos
  - Implementar método `create_search_indices()` en SearchEngine
  - Crear índice en LOWER(title)
  - Crear índice en LOWER(author)
  - Crear índice en tags
  - Crear índice en score
  - Crear índice compuesto en (score DESC, created_at DESC)
  - Integrar creación de índices en inicialización de esquema
  - _Requisitos: 10.1, 10.2, 10.3, 10.4, 10.6_

- [ ]* 13.1 Escribir unit test para creación de índices
  - Test que verifica que todos los índices se crean correctamente
  - _Requisitos: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [ ] 14. Extender CLI con comando search
  - Agregar subparser "search" al CLI existente
  - Agregar argumentos: --text, --author, --tags, --min-score, --max-score, --start-date, --end-date
  - Agregar argumentos: --order-by, --page, --page-size
  - Agregar argumento: --list-tags
  - Implementar método `handle_search()` en clase CLI
  - Parsear argumentos y construir SearchQuery
  - Llamar a SearchService para ejecutar búsqueda
  - _Requisitos: 11.1, 11.2, 11.4_

- [ ]* 14.1 Escribir unit tests para CLI search
  - Test de comando search existe y acepta argumentos
  - Test de argumento --list-tags
  - _Requisitos: 11.1, 11.2_

- [ ] 15. Implementar visualización de resultados de búsqueda
  - Implementar método `display_search_results()` en CLI
  - Reutilizar formato de tabla del comando "list"
  - Aplicar resaltado de términos en títulos
  - Mostrar información de paginación (página X de Y, Z resultados totales)
  - Mostrar mensaje cuando no hay resultados
  - _Requisitos: 11.3, 8.3, 6.4_

- [ ]* 15.1 Escribir unit tests para visualización
  - Test de formato consistente con comando "list"
  - Test de mensaje sin resultados
  - _Requisitos: 11.3, 6.4_

- [ ] 16. Implementar manejo de errores en CLI
  - Capturar errores de validación y mostrar mensajes descriptivos
  - Mostrar formato correcto para fechas inválidas
  - Mostrar sugerencias para tags inválidos
  - Manejar errores de base de datos con logging
  - _Requisitos: 12.1, 12.2, 12.4_

- [ ]* 16.1 Escribir unit tests para manejo de errores
  - Test de mensaje de error para formato de fecha inválido
  - Test de sugerencias para tags inválidos
  - _Requisitos: 12.2, 3.5_

- [ ] 17. Checkpoint final - Verificar integración completa
  - Asegurar que todas las pruebas pasen, preguntar al usuario si surgen dudas.

- [ ]* 18. Escribir pruebas de integración end-to-end
  - Test de flujo completo: CLI → Service → Engine → Database → Resultados
  - Test de búsqueda multi-criterio compleja
  - Test de paginación con ordenamiento
  - Test de integración con TagSystem
  - _Requisitos: 1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1, 9.1_

## Notas

- Las tareas marcadas con `*` son opcionales y pueden omitirse para un MVP más rápido
- Cada tarea referencia requisitos específicos para trazabilidad
- Los checkpoints aseguran validación incremental
- Las pruebas de propiedades validan corrección universal
- Los unit tests validan ejemplos específicos y casos edge
- La implementación es incremental: cada paso construye sobre el anterior
- Todas las pruebas de propiedades deben ejecutarse con mínimo 100 iteraciones
- El formato de tag para pruebas de propiedades es: `# Feature: hackernews-search, Property N: [título]`
